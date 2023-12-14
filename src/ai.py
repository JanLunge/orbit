import json
import os

import setproctitle
from mqtt import MqttClient
from llm import Ai

selected_ai = Ai("atlas")

if __name__ == "__main__":
    from similarity_search import find_similar_functions
    setproctitle.setproctitle("Orbit-Module AI")
    function_docs = []
    if os.path.exists("./function_docs.json"):
        with open("./function_docs.json", "r") as f:
            function_docs = json.load(f)

    # Define callback function for MQTT client to process incoming messages
    def on_message(client, userdata, message):
        # Get the text from the incoming MQTT message
        text = message.payload.decode()
        if text.strip() == "":
            return

        print("User Input for AI: {}".format(text))

        # get the top 5 most similar functions for the given query
        functions = find_similar_functions(text, k=10)
        unique_intents = []
        if functions:  # Check if the list is not empty
            # get a list of the top 5 unique intents preserving the order they are listed in
            for func in functions:
                if func[0] not in unique_intents:
                    unique_intents.append(func[0])
                if len(unique_intents) >= 5:
                    break
            print("unique intents:", ', '.join(unique_intents))

        # get the docstring of the top 5 unique intents
        docstrings = []
        for intent in unique_intents:
            if intent in function_docs:
                docstrings.append(function_docs[intent])

        docstring_prompt = "\n".join(docstrings)
        # intent classification with nexus raven
        prompt_template = \
            '''
Function:
{docs}
    
def no_relevant_function(user_query : str):
  """
  Call this when no other provided function can be called to answer the user query.

  Args:
     user_query: The user_query that cannot be answered by any other function calls.
  """


User Query: {query}
'''
        intent = Ai(model="nexusraven", stop=['Thought:']).predict(prompt_template.format(docs=docstring_prompt, query=text.replace("'", "")))
        intent = intent.split("Call: ")[1]
        print("intent:", intent)

        mqtt_client.publish("command", json.dumps({"intent": intent, "query": text}))


    # Initialize MQTT client
    mqtt_client = MqttClient(subscribeTopics=["speech_transcribed"], onMessage=on_message)

    print("✅ AI ready and waiting for recognized text")
    # Start MQTT client loop to listen for messages
    mqtt_client.run()
