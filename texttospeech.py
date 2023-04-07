import requests
import json
import io
import pygame
import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv
load_dotenv()
import pyttsx3

# MQTT broker information
mqtt_broker = "localhost"
mqtt_port = 1883
api_key = os.getenv('ELEVENLABS_API_KEY')
api_endpoint = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
mqtt_client = mqtt.Client()
pygame.mixer.init()
def getElevenLabsAudio(text):
    # Define the request body
    request_body = {
        "text": text,
        "voice_settings": {
            "stability": 0,
            "similarity_boost": 0
        }
    }

    # Convert the request body to JSON
    request_body_json = json.dumps(request_body)

    # Define the request headers
    request_headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }

    # Send the request to the API endpoint and get the audio response
    response = requests.post(api_endpoint, headers=request_headers, data=request_body_json)

    audio_bytes = io.BytesIO(response.content)
     # Load the audio bytes using Pygame mixer
    pygame.mixer.music.load(audio_bytes)

    # Play the audio file
    pygame.mixer.music.play()


def getTTS3Audio(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def on_message(client, userdata, message):
    if message.topic == "assistant_response":
        # Get the text from the incoming MQTT message
        text = message.payload.decode()
        print("got text {}".format(text))

        # getElevenLabsAudio(text)
        getTTS3Audio(text)
    if message.topic == "hotword_detected":
        # Load the ping sound file
        ping_sound = pygame.mixer.Sound('ping.wav')
        # Play the ping sound once
        ping_sound.play()
   

# Connect to MQTT broker and subscribe to topic
mqtt_client.connect(mqtt_broker, mqtt_port)
mqtt_client.subscribe("assistant_response")
mqtt_client.subscribe('hotword_detected')

# Set MQTT client's message callback function
mqtt_client.on_message = on_message

print('waiting for text to speak')
# Start MQTT client loop to listen for messages
mqtt_client.loop_forever()
