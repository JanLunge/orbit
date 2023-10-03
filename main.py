import signal
import sys
import os
from mqtt import MqttClient

from dotenv import load_dotenv

load_dotenv()

# list of all threads we boot up (tts, ai, etc...)
processes = []


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
        "audio_satelite.py",  # capture audio from mic and send via mqtt permanently
        "hotword_detect.py",  # listen for hotword and send to mqtt
        "speech_to_text.py",  # transcribe audio via faster whisper and send to mqtt
        "ai.py",  # LLM answering quetions, managing history, etc...
        "commands.py",
        "text_to_speech.py",
    ]
    setproctitle.setproctitle("OrbitManager")
    for script in scripts:
        process = subprocess.Popen(["python3","src/" + script])
        print("🚀 started module", process.pid, script)
        processes.append(process)

    # Register the signal handler for termination signals, for pressing Ctrl+C
    signal.signal(signal.SIGINT, handle_termination)
    signal.signal(signal.SIGTERM, handle_termination)

    # Wait for user to input anything. Input resolves on return (Enter)
    # also interaction via chat

    # Initialize MQTT client
    mqtt_client = MqttClient()
    while True:
        user_text = input("ask something:")
        mqtt_client.publish("speech_transcribed", user_text)

