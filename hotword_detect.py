import pvporcupine
import pyaudio
import paho.mqtt.client as mqtt
import struct 
from datetime import datetime as dt 

# MQTT broker information
mqtt_broker = "localhost"
mqtt_port = 1883
mqtt_topic = "microphone_audio"

# PyAudio configuration
audio_chunk_size = 512
audio_format = pyaudio.paInt16
audio_channels = 1
audio_rate = 16000

# Initialize Porcupine
porcupine = pvporcupine.create(
    keyword_paths=["./atlas.ppn"], 
    access_key="HtHCR915oUKYsDHfMNmjeFQhduql86VRqFgPlyrSu6+maoVQHjHJWA=="
    )

# Define MQTT callback function
def on_message(client, userdata, message):
    pcm = struct.unpack_from("h" * 512, message.payload)
    # audio_chunk = message.payload
    keyword_index = porcupine.process(pcm)
    if keyword_index >= 0:
        print("{} Hotword detected!".format(str(dt.now())))
        mqtt_client.publish("hotword_detected", 'atlas,room1')


# Initialize MQTT client
mqtt_client = mqtt.Client()

# Connect to MQTT broker and subscribe to topic
mqtt_client.connect(mqtt_broker, mqtt_port)
mqtt_client.subscribe(mqtt_topic)

# Set MQTT callback function
mqtt_client.on_message = on_message

mqtt_client.loop_forever()
