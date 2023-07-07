import openai
import paho.mqtt.client as mqtt
import requests
import os
import json
from dotenv import load_dotenv
load_dotenv()
import threading
import time

# Set OpenAI API credentials
openai.api_key = os.getenv('OPENAI_API_KEY')

# MQTT broker information
mqtt_broker = os.getenv('MQTT_BROKER')
mqtt_port = int(os.getenv('MQTT_PORT'))
mqtt_topic = "speech_detected" 

def timer_function(duration): 
    duration = int(duration)
    print('timer runs', duration)
    time.sleep(duration)
    print('timer done')

commands = {
    'timer': timer_function,
}

# Pre-prompt for calling external APIs
def generateProompt(goal, history):
    return f"""You are Atlas, a home assistant
CONSTRAINTS:

1. If you are unsure how you previously did something or want to recall past events, thinking about similar events will help you remember.
2. minimal user assistance, if you did not find relevant information after searching the files you can ask the user. do not ask for approval.
3. Exclusively use the commands listed in double quotes e.g. "command name"
4. Check with the provided history of your current executed actions if your goal has already archived, if so run the command "task_complete" with the reason "goal already archived"


COMMANDS:

- set timer: "timer", args: "duration": "<duration in seconds>"
- wait for trigger to happen: "wait"
- Task Complete (Shutdown): "task_complete", args: "reason": "<reason>"

PERFORMANCE EVALUATION:

1. Continuously review and analyze your actions to ensure you are performing to the best of your abilities. 
2. Constructively self-criticize your big-picture behavior constantly.
3. Reflect on past decisions and strategies to refine your approach.
4. Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps.

You should only respond in JSON format as described below

RESPONSE FORMAT:
{{
    "thoughts":
    {{
        "text": "thought",
        "reasoning": "reasoning",
        "plan": "- short bulleted\n- list that conveys\n- long-term plan",
        "criticism": "constructive self-criticism",
        "speak": "thoughts summary to say to user", 
        "current_step": "next command summary written as if it is aleady done"
    }},
    "command": {{
        "name": "command name",
        "args":{{
            "arg name": "value"
        }}
    }}
}}

Ensure the response can be parsed by Python json.loads


GOAL:
{goal}

HISTORY:
{history}

Determine which next command to use, and respond using the format specified above:"""

# Initialize MQTT client
mqtt_client = mqtt.Client()

# Define callback function for MQTT client to process incoming messages
def on_message(client, userdata, message):
    # Get the text from the incoming MQTT message
    text = message.payload.decode()
    print("User Input for AI: {}".format(text))
    history = ""
    ended = False
    maxIterations = 2
    currentIteration = 0
    # Generate a response using OpenAI's GPT-3 model
    # while not ended and currentIteration < maxIterations: 
    currentIteration += 1 
    goal = text
    #print("proompt:", generateProompt(goal, history)) 

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
             {
                "role": "system", 
                "content": "You are a homeassistant please, answer in one sentence and keep things short." #generateProompt(goal, history)
            },
            {
                "role": "system", 
                "content": goal #generateProompt(goal, history)
            },
        ],
        temperature=0.5,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        n=1,
        stop=["\nUser:"],
    )

    bot_response = response["choices"][0]["message"]["content"]
    print("bot response:", bot_response)
        #bot_response = json.loads(bot_response)
        #print("Bot's response:", json.dumps(bot_response, indent=2))  
        # final bot response
    mqtt_client.publish("assistant_response", bot_response)
        # if bot_response['command']['name'] == "task_complete":
        #     ended = True
        # else:
        #     # run the command and get the output 
        #     if bot_response['command']['name'] in commands:
        #         command = commands[bot_response['command']['name']](bot_response['command']['args']['duration'])
        #     # run it in a seperate thread
        #     my_thread = threading.Thread(target=command)  
        #     my_thread.start()
        #     # my_thread.join()
        #     command_output = "done"
        #     # add command output to history
        #     history += "\n"+ bot_response['thoughts']['current_step'] + command_output
        
       

# Connect to MQTT broker and subscribe to topic
mqtt_client.connect(mqtt_broker, mqtt_port)
mqtt_client.subscribe(mqtt_topic)

# Set MQTT client's message callback function
mqtt_client.on_message = on_message

print('✅ AI waiting for recognized text')
# Start MQTT client loop to listen for messages
mqtt_client.loop_forever()
