# NOT IN USE RIGHT NOW. THESE ARE THE SKILLS.
# Test if triggering everything through a vector database is better.

# send an email to my brother.

# maybe use llama 2 function calling model for identifying the chain

import paho.mqtt.client as mqtt
import json
import threading
import os
from dotenv import load_dotenv
import setproctitle
import json
import os

from datetime import datetime
from src.ai import selected_ai

load_dotenv()

if __name__ == "__main__":
    # MQTT broker information
    mqtt_broker = os.getenv("MQTT_BROKER")
    mqtt_port = int(os.getenv("MQTT_PORT"))
    mqtt_client = mqtt.Client()

    def on_message(client, userdata, message):
        setproctitle.setproctitle("Orbit-Module Commands")
        if message.topic == "command":
            # Get the text from the incoming MQTT message
            payload = message.payload.decode()
            json_payload = json.loads(payload)
            intent = json_payload["intent"]
            query = json_payload["query"]
            print("got command {} and query {}".format(intent, query))
            # run the commands function for this command if it exists

            def no_relevant_function(user_query):
                print("converse called")
                print("unknown intent")
                response = selected_ai.predict(query)
                print("Assistant response:", response)
                mqtt_client.publish("assistant_response", response)

            def get_time(seconds=False):
                print("function call getTime:", datetime.now().strftime("%H:%M"))
                mqtt_client.publish("assistant_response", 'the current time is ' + datetime.now().strftime("%H:%M"))

            def get_date(weekday=False):
                print("the current date is", datetime.now().strftime("%d/%m/%Y"))
                mqtt_client.publish("assistant_response", "the current date is " + datetime.now().strftime("%d/%m/%Y"))

            def set_timer(hours=None, minutes=None, seconds=None):
                print("setTimer called with", hours, minutes, seconds)
                response = selected_ai.predict(
                    f"""you just successfully set a timer for {hours} hours, {minutes} minutes and {seconds} seconds, as the user requested, please inform them of this.""")
                if int(os.getenv('DEBUG_LEVEL')) >= 2:
                    print("Assistant response:", response)
                mqtt_client.publish("assistant_response", response)

            exec(intent)

            # TODO: run it in a separate thread
            # threading.Thread(target=intent).start()


    # Connect to MQTT broker and subscribe to topic
    mqtt_client.connect(mqtt_broker, mqtt_port)
    mqtt_client.subscribe("command")
    mqtt_client.on_message = on_message
    print("✅ commands ready")
    mqtt_client.loop_forever()
