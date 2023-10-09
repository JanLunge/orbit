from datetime import datetime
import setproctitle
import json
from mqtt import MqttClient
from llm import Ai
from hyperdb import HyperDB
import subprocess
import re

def extract_duration(text):
    # Define the regex patterns for hours, minutes, and seconds
    patterns = {
        "hours": r"(\d+)\s*hours?",
        "minutes": r"(\d+)\s*minutes?",
        "seconds": r"(\d+)\s*seconds?"
    }

    # Store the results here
    durations = {}

    for unit, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            durations[unit] = int(match.group(1))

    return durations

if __name__ == "__main__":
    selected_ai = Ai("auto")
    setproctitle.setproctitle("Orbit-Module AI")
    # Define callback function for MQTT client to process incoming messages
    def on_message(client, userdata, message):
        # Get the text from the incoming MQTT message
        text = message.payload.decode()
        if text.strip() == "":
            return

        print("User Input for AI: {}".format(text))

        # vector db for live injected info for simple questions speedup
        documents = []
        with open("data/commands.jsonl", "r") as f:
            for line in f:
                documents.append(json.loads(line))
        # Instantiate HyperDB with the list of documents
        db = HyperDB(documents, key="text")

        # Save the HyperDB instance to a file
        db.save("data/commands_hyperdb.pickle.gz")

        # Load the HyperDB instance from the save file
        db.load("data/commands_hyperdb.pickle.gz")

        additional_context = ""
        results = db.query(text, top_k=5)
        print("results from hyperdb:", results)
        first_intent, similarity = results[0]  # eg. [{'text': 'what time is it?', 'function': 'getTime'}, 0.88]
        print('first matched intent, similarity:', first_intent, similarity)  # trust over 0.88
        if similarity > 0.88:
            print("call function", first_intent["function"])
            if first_intent["function"] == "getTime":
                additional_context = "Additional Context: the current time is:" + datetime.now().strftime("%H:%M:%S")
            elif first_intent["function"] == "getDate":
                additional_context = "Additional Context: the current date is:" + datetime.now().strftime("%d/%m/%Y")
            elif first_intent["function"] == "setTimer":
                # get the duration from the text
                # find the first number in th text
                duration = extract_duration(text)
                print("duration extracted:", duration)
                additional_context = "you can set a timer with the function "
        print("added context from intent recognition:", additional_context)

        # TODO: allow chatgpt for ppl who dont need nsfw
        # TODO: add parameter extraction and call functions from llm
        return
        response = selected_ai.predict(text, additional_context=additional_context)
        print("Assistant response:", response)

        mqtt_client.publish("assistant_response", response)

    # Initialize MQTT client
    mqtt_client = MqttClient(subscribeTopics=["speech_transcribed"], onMessage=on_message)

    print("✅ AI ready and waiting for recognized text")
    # Start MQTT client loop to listen for messages
    mqtt_client.run()
