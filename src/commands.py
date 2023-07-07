import paho.mqtt.client as mqtt
import json
import threading
import os
from dotenv import load_dotenv
import setproctitle
load_dotenv()

# MQTT broker information
mqtt_broker = os.getenv('MQTT_BROKER')
mqtt_port = int(os.getenv('MQTT_PORT'))
mqtt_client = mqtt.Client()

commands = {
    'play': lambda url: 
        print('play', url),
    'timer': lambda duration: 
        print('timer runs', duration),
}

def on_message(client, userdata, message):
    setproctitle.setproctitle('Orbit-Module Commands')
    print('yes')
    if message.topic == "command":
        # Get the text from the incoming MQTT message
        json_string = message.payload.decode()
        print("got command json {}".format(json_string))
        json_data = json.loads(json_string)
        # run the commands function for this command if it exists
        if json_data['command'] in commands:
            command = commands[json_data['command']](json_data['args'])
            # run it in a seperate thread
            threading.Thread(target=command).start()
        else:
            print('command not found')


        
        
        
# Connect to MQTT broker and subscribe to topic
mqtt_client.connect(mqtt_broker, mqtt_port)
mqtt_client.subscribe("command")
mqtt_client.on_message = on_message
print("✅ commands ready")
mqtt_client.loop_forever()