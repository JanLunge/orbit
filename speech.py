import speech_recognition as sr
import paho.mqtt.client as mqtt
import pyaudio
import wave
import audioop
import os
import whisper


# MQTT broker information
mqtt_broker = "localhost"
mqtt_port = 1883
mqtt_topic = "microphone_audio"

# Initialize speech recognition
r = sr.Recognizer()
energy_threshold = 300  # Adjust this value as per requirement.
silence_duration = 1
audio_channels = 1
audio_chunk_size = 512
audio_rate = 16000

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Initialize MQTT client
mqtt_client = mqtt.Client()

def record_audio():
    # Start streaming microphone audio
    stream = audio.open(
        format=audio.get_format_from_width(2),
        channels=audio_channels,
        rate=audio_rate,
        input=True,
        frames_per_buffer=audio_chunk_size)

    # Initialize variables for recording
    frames = []
    silence_count = 0
    max_silence_count = int(silence_duration * audio_rate / audio_chunk_size)

    # Record audio until a certain amount of silence is detected
    while True:
        # Read audio chunk from microphone
        audio_data = stream.read(audio_chunk_size)

        # Append audio chunk to list of recorded frames
        frames.append(audio_data)

        # Detect energy level of audio chunk
        rms = audioop.rms(audio_data, 2)
        if rms > energy_threshold:
            # Reset silence counter
            silence_count = 0
        else:
            # Increment silence counter
            silence_count += 1

        # If the silence counter reaches the threshold, stop recording
        if silence_count > max_silence_count:
            break

    # Stop streaming audio from microphone
    stream.stop_stream()
    stream.close()

    # Save recorded audio to WAV file
    with wave.open('recorded_audio.wav', 'wb') as wf:
        wf.setnchannels(audio_channels)
        wf.setsampwidth(audio.get_sample_size(audio.get_format_from_width(2)))
        wf.setframerate(audio_rate)
        wf.writeframes(b''.join(frames))

    # Recognize speech from recorded audio
    with sr.AudioFile('recorded_audio.wav') as audio_file:
        audio_data = r.record(audio_file)

    try:
        # Print recognized speech
        # text = r.recognize_google(audio_data)
        # print("You said:", text)
        model = whisper.load_model("base")
        result = model.transcribe("recorded_audio.wav", fp16=False)
        user_input = result["text"]
        print(f"You said: {user_input}")
        mqtt_client.publish('speech_detected', user_input)
    except sr.UnknownValueError:
        print("Speech recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))

    # Delete the recorded audio file
    # os.remove('recorded_audio.wav')

# Define callback function for MQTT client to process incoming messages
def on_message(client, userdata, message):
    if message.topic == "hotword_detected":
        print("Listening for commands!")
        record_audio()

# Connect to MQTT broker and subscribe to topic
mqtt_client.connect(mqtt_broker, mqtt_port)
mqtt_client.subscribe('hotword_detected')

# Set MQTT client's message callback function
mqtt_client.on_message = on_message

print('waiting for hotword')
# Start MQTT client loop to listen for messages
mqtt_client.loop_forever()

# Terminate PyAudio
audio.terminate()
