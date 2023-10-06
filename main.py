import os
import signal
import sys
import paho.mqtt.client as mqtt
import threading

# list of all threads we boot up (tts, ai, etc...)
processes = []
exit_events = []

def monitor_process_output(process, script, exit_event):
    for line in iter(process.stdout.readline, ''):
        line_stripped = line.strip()
        if "✅" in line_stripped and "ready" in line_stripped:
            print(f"✅ module {script['log_prefix']} {script['name']} is ready")
            exit_event.set()
        else:
            print(f"{script['log_prefix']}: {line_stripped}")
            # if you want to hide output of the submodules uncomment the following line
            # break

# signum and fame are not used, but required by the signal handler
def handle_termination(signum, frame):
    # Terminate all subprocesses
    print("🛑 Terminating all modules...")
    for process in processes:
        process.terminate()
    # check again for pids running, just in case they didn't terminate
    for process in processes:
        if process.poll() is None:
            print("🛑 Terminating module", process.pid)
            process.kill()

    # Exit the main application
    sys.exit(0)


# invoked when running "python3 anyfile.py"
if __name__ == "__main__":
    import subprocess
    import setproctitle

    # clear terminal
    subprocess.call("clear", shell=True)

    # Start all subprocesses and put them in the process list
    scripts = [
        {"script": "audio_satelite.py", "log_prefix": "🎤", "name": "AudioSatelite"},  # capture audio from mic and send via mqtt permanently
        {"script": "hotword_detect.py", "log_prefix": "❗","name": "HotwordDetection"},  # listen for hotword and send to mqtt
        {"script": "speech_to_text.py", "log_prefix": "🎧","name": "Transcription"},  # transcribe audio via faster whisper and send to mqtt
        {"script": "ai.py", "log_prefix": "🧠", "name": "AI"},  # LLM answering quetions, managing history, etc...
        {"script": "commands.py", "log_prefix": "⚙️ ","name": "Commands"},  # commands like "what is the weather"
        {"script": "text_to_speech.py", "log_prefix": "💬", "name": "VoiceOutput"},  # tts
    ]
    setproctitle.setproctitle("OrbitManager")
    print(f"🚀 starting all {len(scripts)} modules")
    for script in scripts:
        process = subprocess.Popen(str("venv/bin/python3 -u src/" + script["script"]).split(" "),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # combine stdout and stderr
            bufsize=1,   # line-buffered
            universal_newlines=True)
        print("🚀 starting module", script['log_prefix'],script['name'])
        processes.append(process)
        exit_event = threading.Event()  # event to signal when emoji is found
        exit_events.append(exit_event)
        threading.Thread(target=monitor_process_output, args=(process, script, exit_event)).start()
    # check if the output of a process contains an emoji

    # Register the signal handler for termination signals, for pressing Ctrl+C
    signal.signal(signal.SIGINT, handle_termination)
    signal.signal(signal.SIGTERM, handle_termination)

    # Wait for user to input anything. Input resolves on return (Enter)
    # also interaction via chat
    for event in exit_events:
        event.wait()

    subprocess.call("clear", shell=True)

    print("🚀 all modules are ready")
    # Initialize MQTT client
    mqtt_client = mqtt.Client()
    MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

    while True:
        user_text = input("ask something: ")
        mqtt_client.publish("speech_transcribed", user_text)

