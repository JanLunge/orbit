import pyaudio
import time
import sys
import json
import paho.mqtt.client as mqtt

def run():
    # MQTT broker information
    mqtt_broker = "localhost"
    mqtt_port = 1883
    mqtt_topic = "microphone_audio"

    # PyAudio configuration
    audio_chunk_size = 512
    audio_format = pyaudio.paInt16
    audio_channels = 1
    audio_rate = 16000

    # Initialize PyAudio
    audio = pyaudio.PyAudio()

    # Start streaming microphone audio
    stream = audio.open(format=audio_format,
                        channels=audio_channels,
                        rate=audio_rate,
                        input=True,
                        frames_per_buffer=audio_chunk_size)

    # Initialize MQTT client
    mqtt_client = mqtt.Client()

    # Connect to MQTT broker
    mqtt_client.connect(mqtt_broker, mqtt_port)
    print("✅ audio streaming via mqtt to {}".format(mqtt_broker + ":"+ str(mqtt_port)))
    # Main loop
    while True:
        try:
            # Read audio chunk from microphone
            audio_chunk = stream.read(512)
            # Publish audio chunk to MQTT broker
            mqtt_client.publish(mqtt_topic, audio_chunk)


        except KeyboardInterrupt:
            # Clean up PyAudio and MQTT client
            stream.stop_stream()
            stream.close()
            audio.terminate()
            mqtt_client.disconnect()
            sys.exit()

if __name__ == "__main__":
    run()