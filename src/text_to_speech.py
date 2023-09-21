import requests
import json
import io
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import setproctitle
load_dotenv()


def run():
    setproctitle.setproctitle('Orbit-Module TTS')
    # MQTT broker information
    mqtt_broker = os.getenv('MQTT_BROKER')
    mqtt_port = int(os.getenv('MQTT_PORT'))
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
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

    def macSay(text):
        import os
        os.system('say "{}"'.format(text))

    def on_message(client, userdata, message):
        if message.topic == "assistant_response":
            if os.getenv('TTS_ENABLED') == "0":
                print("TTS is disabled")
                return
            # start speaking the text
            text = message.payload.decode()
            print("text to speak: {}".format(text))
            engine = os.getenv('TTS_ENGINE')
            if(engine=="elevenlabs"):
                getElevenLabsAudio(text)
            elif(engine=="tts3"):
                getTTS3Audio(text)
            elif(engine=="mac"):
                macSay(text)
        if message.topic == "hotword_detected":
            # Play sound that the wakeword was detected
            ping_sound = pygame.mixer.Sound('assets/ping.wav')
            ping_sound.play()


    # Connect to MQTT broker and subscribe to topic
    mqtt_client.connect(mqtt_broker, mqtt_port)
    mqtt_client.subscribe("assistant_response")
    mqtt_client.subscribe('hotword_detected')

    # Set MQTT client's message callback function
    mqtt_client.on_message = on_message

    print('✅ TTS ready')
    # Start MQTT client loop to listen for messages
    mqtt_client.loop_forever()


if __name__ == "__main__":
    run()