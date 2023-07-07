import pvporcupine
import pyaudio
import paho.mqtt.client as mqtt
import struct 
from datetime import datetime as dt
from dotenv import load_dotenv
import setproctitle
import os
load_dotenv()


def run():
    setproctitle.setproctitle('Orbit-Module Hotword')
    # MQTT broker information
    mqtt_broker = os.getenv('MQTT_BROKER')
    mqtt_port = int(os.getenv('MQTT_PORT'))
    mqtt_topic = "microphone_audio"

    # PyAudio configuration
    audio_chunk_size = 512
    audio_format = pyaudio.paInt16
    audio_channels = 1
    audio_rate = 16000

    # Initialize Porcupine
    porcupine = pvporcupine.create(
        keyword_paths=["wakewords/Atlas_en_mac_v2_2_0.ppn"],
        access_key=os.getenv('PORCUPINE_ACCESS_KEY')

        )

    # Define MQTT callback function
    def on_message(client, userdata, message):
        pcm = struct.unpack_from("h" * 512, message.payload)
        # audio_chunk = message.payload
        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            print("{} Hotword detected!".format(str(dt.now())))
            mqtt_client.publish("hotword_detected", 'atlas,room1')
            # mqtt_client.publish("command", '{"command": "play", "args": "https://www.youtube.com/watch?v=5qap5aO4i9A"}')


    # Initialize MQTT client
    mqtt_client = mqtt.Client()

    # Connect to MQTT broker and subscribe to topic
    mqtt_client.connect(mqtt_broker, mqtt_port)
    mqtt_client.subscribe(mqtt_topic)

    # Set MQTT callback function
    mqtt_client.on_message = on_message

    print("✅ Hotword Atlas ready")
    mqtt_client.loop_forever()


if __name__ == "__main__":
    run()