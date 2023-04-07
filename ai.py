import openai
import paho.mqtt.client as mqtt
import requests
import os
from dotenv import load_dotenv
load_dotenv()


# Set OpenAI API credentials
openai.api_key = os.getenv('OPENAI_API_KEY')

# MQTT broker information
mqtt_broker = "localhost"
mqtt_port = 1883
mqtt_topic = "speech_detected"

# Pre-prompt for calling external APIs
pre_prompt = "You are atlas a conversational agent, a homeassistant and helper that speaks casually and is straight to the point. Answer in 2 sentences or less. prefer using the metric system for measurements."

# Initialize MQTT client
mqtt_client = mqtt.Client()

# Define callback function for MQTT client to process incoming messages
def on_message(client, userdata, message):
    # Get the text from the incoming MQTT message
    text = message.payload.decode()
    print("got text {}".format(text))

    # Generate a response using OpenAI's GPT-3 model
    response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system", 
                            "content": pre_prompt},
                        {
                            "role": "user", 
                            "content": text
                        },
                    ],
                    temperature=0.5,
                    max_tokens=150,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    n=1,
                    stop=["\nUser:"],
                )

    bot_response = response["choices"][0]["message"]["content"]        
    print("Bot's response:", bot_response)

    mqtt_client.publish("assistant_response", bot_response)

# Connect to MQTT broker and subscribe to topic
mqtt_client.connect(mqtt_broker, mqtt_port)
mqtt_client.subscribe(mqtt_topic)

# Set MQTT client's message callback function
mqtt_client.on_message = on_message

# Start MQTT client loop to listen for messages
mqtt_client.loop_forever()
