from datetime import datetime
import setproctitle
import json
from src.mqtt import MqttClient
from src.ai.llm import Ai
from hyperdb import HyperDB

if __name__ == "__main__":
    selected_ai = Ai("atlas")
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
        first_intent, similarity = results[0]  # eg. [{'text': 'what time is it?', 'function': 'getTime'}, 0.88]
        print('first matched intent', first_intent, similarity)  # trust over 0.88
        if similarity > 0.88:
            print("call function", first_intent["function"])
            if first_intent["function"] == "getTime":
                additional_context = "Additional Context: the current time is:" + datetime.now().strftime("%H:%M:%S")
            elif first_intent["function"] == "getDate":
                additional_context = "Additional Context: the current date is:" + datetime.now().strftime("%d/%m/%Y")
            elif first_intent["function"] == "setTimer":
                additional_context = "you can set a timer with the function "
        print("added context from intent recognition:", additional_context)

        # TODO: allow chatgpt for ppl who dont need nsfw
        # TODO: add parameter extraction and call functions from llm
        response = selected_ai.predict(text, additional_context=additional_context)
        print("Assistant response:", response)

        mqtt_client.publish("assistant_response", response)

    # Initialize MQTT client
    mqtt_client = MqttClient(subscribeTopics=["speech_transcribed"], onMessage=on_message)

    print("✅ AI waiting for recognized text")
    # Start MQTT client loop to listen for messages
    mqtt_client.run()
