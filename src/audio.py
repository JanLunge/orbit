import pyaudio
import pvporcupine
import sys
import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv
import setproctitle
import struct
from datetime import datetime as dt
import wave
from faster_whisper import WhisperModel
import speech_recognition as sr
import audioop

load_dotenv()

if __name__ == "__main__":
    # Set process title
    setproctitle.setproctitle("Orbit-Module Audio-Satelite")

    # MQTT broker information
    mqtt_broker = os.getenv("MQTT_BROKER")
    mqtt_port = int(os.getenv("MQTT_PORT"))

    # PyAudio configuration
    audio_chunk_size = 1024
    audio_format = pyaudio.paInt16
    audio_channels = 1
    audio_rate = 16000

    # Initialize speech recognition
    r = sr.Recognizer()
    energy_threshold = 300  # Adjust this value as per requirement.
    silence_duration = 1

    # Initialize PyAudi
    audio = pyaudio.PyAudio()

    # Start streaming microphone audio
    try:
        stream = audio.open(
            format=audio_format,
            channels=audio_channels,
            rate=audio_rate,
            input=True,
            frames_per_buffer=audio_chunk_size,
        )
    except IOError as e:
        print(f"Error opening audio stream: {e}")
        audio.terminate()  # Clean up the PyAudio instance

    # Initialize MQTT client. One process is one MQTT client
    mqtt_client = mqtt.Client()

    # Connect to MQTT broker
    mqtt_client.connect(mqtt_broker, mqtt_port)

    try:
        # Initialize Porcupine
        porcupine = pvporcupine.create(
            keyword_paths=["wakewords/" + os.getenv('WAKEWORD')],
            access_key=os.getenv("PORCUPINE_ACCESS_KEY"),
        )
    except pvporcupine.PorcupineException as e:
        print(f"Porcupine initialization failed: {e}")
        sys.exit()


    def recognize_fast_whisper(audio_file):
        try:
            # variants are large-v2
            model = WhisperModel("base", device="cpu", compute_type="int8")  # or "cuda"
            segments, info = model.transcribe(audio_file, beam_size=5)
            print(
                "Detected language '%s' with probability %f"
                % (info.language, info.language_probability)
            )
            result_text = []
            for segment in segments:
                result_text.append(segment.text)
            return " ".join(result_text).strip()
        except Exception as e:
            print("Error transcribing audio:", e)


    def record_audio_to_transcribe():
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

            # Save recorded audio to WAV file
        with wave.open("recorded_audio.wav", "wb") as wf:
            wf.setnchannels(audio_channels)
            wf.setsampwidth(audio.get_sample_size(audio.get_format_from_width(2)))
            wf.setframerate(audio_rate)
            wf.writeframes(b"".join(frames))

        try:
            print("starting transcription")
            result_text = recognize_fast_whisper("recorded_audio.wav")
            mqtt_client.publish("speech_transcribed", result_text)
        except sr.UnknownValueError:
            print("Speech recognition could not understand audio")


    print("✅ audio satellite ready and streaming via mqtt to {}".format(mqtt_broker + ":" + str(mqtt_port)))


    def process_audio_stream(stream, porcupine, mqtt_client):
        while True:
            try:
                # Read audio chunk from microphone porcupine only handles 512 samples at a time
                try:
                    audio_chunk = stream.read(512,exception_on_overflow=False )
                except IOError as e:
                    # Clear the buffer by reading and discarding
                    print("Input overflowed")
                    audio_chunk = stream.read(2048)
                    continue  # Skip this loop iteration
                # Publish audio chunk to MQTT broker
                pcm = struct.unpack_from("h" * 512, audio_chunk)
                # we could have multiple hotwords, that's why there is an index
                keyword_index = porcupine.process(pcm)
                if keyword_index >= 0:
                    print("{} Hotword detected!".format(str(dt.now())))
                    mqtt_client.publish("hotword_detected", "atlas,room1")
                    record_audio_to_transcribe()

            except KeyboardInterrupt:
                # Clean up PyAudio and MQTT client
                stream.stop_stream()
                stream.close()
                audio.terminate()
                mqtt_client.disconnect()
                sys.exit()


    process_audio_stream(stream, porcupine, mqtt_client)
