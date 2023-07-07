import speech_recognition as sr
import paho.mqtt.client as mqtt
import pyaudio
import wave
import audioop
import os
import setproctitle
from dotenv import load_dotenv
load_dotenv()

def run():
    setproctitle.setproctitle('Orbit-Module speech_to_text')
    from faster_whisper import WhisperModel
    # MQTT broker information
    mqtt_broker = os.getenv('MQTT_BROKER')
    mqtt_port = int(os.getenv('MQTT_PORT'))
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

    def recognize_fast_whisper(audio_file):
        # variants are large-v2
        model = WhisperModel("base", device="cpu", compute_type="int8") # or "cuda"
        segments, info = model.transcribe(audio_file, beam_size=5)
        print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
        result_text = []
        for segment in segments:
            result_text.append(segment.text)
        return " ".join(result_text).strip()

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
        # with sr.AudioFile('../recorded_audio.wav') as audio_file:
        #     audio_data = r.record(audio_file)

        try:
            print("starting transcription")
            result_text = recognize_fast_whisper('recorded_audio.wav')
            # Print recognized speech
            # text = r.recognize_google(audio_data)
            # print("You said:", text)
            # result = model.transcribe("../recorded_audio.wav", fp16=False)
            # user_input = result["text"]
            # print(f"You said: {user_input}")
            mqtt_client.publish('speech_detected', result_text)
        except sr.UnknownValueError:
            print("Speech recognition could not understand audio")

        # Delete the recorded audio file
        # os.remove('recorded_audio.wav')

    # Define callback function for MQTT client to process incoming messages
    def on_message(client, userdata, message):
        if message.topic == "hotword_detected":
            print("Listening for Speech!")
            record_audio()

    # Connect to MQTT broker and subscribe to topic
    mqtt_client.connect(mqtt_broker, mqtt_port)
    mqtt_client.subscribe('hotword_detected')

    # Set MQTT client's message callback function
    mqtt_client.on_message = on_message

    print('✅ whisper ready')
    # Start MQTT client loop to listen for messages
    mqtt_client.loop_forever()

    # Terminate PyAudio
    audio.terminate()

if __name__ == '__main__':
    run()