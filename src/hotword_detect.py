import pvporcupine
import pyaudio
import paho.mqtt.client as mqtt
import struct
from datetime import datetime as dt
from dotenv import load_dotenv
import setproctitle
import os

load_dotenv()

if __name__ == "__main__":
    # Set process title
    setproctitle.setproctitle("Orbit-Module Hotword")

    # MQTT broker information
    mqtt_broker = os.getenv("MQTT_BROKER")
    mqtt_port = int(os.getenv("MQTT_PORT"))
    mqtt_topic = "microphone_audio"

    # PyAudio configuration
    audio_chunk_size = 512
    audio_format = pyaudio.paInt16
    audio_channels = 1
    audio_rate = 16000

    # Initialize Porcupine
    porcupine = pvporcupine.create(
        keyword_paths=["wakewords/"+os.getenv('WAKEWORD')],
        access_key=os.getenv("PORCUPINE_ACCESS_KEY"),
    )

    # Define MQTT callback function
    # This is where we receive the audio chunks from the audio_satelite.py
    def on_message(client, userdata, message):
        # imagine pcm as a small audio chunk
        pcm = struct.unpack_from("h" * 512, message.payload)
        # we could have multiple hotwords, that's why there is an index
        keyword_index = porcupine.process(pcm)

        if keyword_index >= 0:
            print("{} Hotword detected!".format(str(dt.now())))
            mqtt_client.publish("hotword_detected", "atlas,room1")

    # Initialize MQTT client
    mqtt_client = mqtt.Client()

    # Connect to MQTT broker and subscribe to the microphone audio stream
    # We publish a hotword detected and we listen to audio chunks
    mqtt_client.connect(mqtt_broker, mqtt_port)
    mqtt_client.subscribe(mqtt_topic)

    # Set MQTT callback function. This triggers when a new audio chunk is received.
    mqtt_client.on_message = on_message

    print("✅ Hotword Atlas ready")
    mqtt_client.loop_forever()
