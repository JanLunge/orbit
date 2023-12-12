from datetime import datetime
import setproctitle
import json
from mqtt import MqttClient
from llm import Ai
from hyperdb import HyperDB
import subprocess
import re
import os


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
        # documents = []
        # with open("data/commands.jsonl", "r") as f:
        #     for line in f:
        #         documents.append(json.loads(line))
        # Instantiate HyperDB with the list of documents
        # db = HyperDB(documents, key="text")

        # Save the HyperDB instance to a file
        # db.save("data/commands_hyperdb.pickle.gz")

        # Load the HyperDB instance from the save file
        # db = HyperDB()
        # db.load("data/commands_hyperdb.pickle.gz")
        #
        # additional_context = ""
        # results = db.query(text, top_k=5)
        # results = []
        # print("results from hyperdb:", results)
        # if len(results) != 0:
        #     first_intent, similarity = results[0]  # eg. [{'text': 'what time is it?', 'function': 'getTime'}, 0.88]
        #     print('first matched intent, similarity:', first_intent, similarity)  # trust over 0.88
        #     if similarity > 0.88:
        #         print("call function", first_intent["function"])
        #         if first_intent["function"] == "getTime":
        #             additional_context = "Additional Context: the current time is:" + datetime.now().strftime("%H:%M:%S")
        #         elif first_intent["function"] == "getDate":
        #             additional_context = "Additional Context: the current date is:" + datetime.now().strftime("%d/%m/%Y")
        #         elif first_intent["function"] == "setTimer":
        #             # get the duration from the text
        #             # find the first number in th text
        #             duration = extract_duration(text)
        #             print("duration extracted:", duration)
        #             additional_context = "you can set a timer with the function "
        #     print("added context from intent recognition:", additional_context)
        # TODO: allow chatgpt for ppl who dont need nsfw
        # TODO: add parameter extraction and call functions from llm

        # Intent recognition (skill check)
        skill_list = [
            {
                "name": "setTimer",
                "examples": [
                    "set a timer for 5 minutes"
                ]
            },
            {
                "name": "searchOnline",
                "examples": [
                    "search for cats online",
                    "lookup heaperdb on google",
                ]
            },
            {
                "name": "getWeather",
                "examples": [
                    "what is the weather like today"
                ]
            },
            {
                "name": "getTime",
                "examples": [
                    "what time is it"
                ]
            },
            {
                "name": "getDate",
                "examples": [
                    "what is the date today"
                ]
            },
            {
                "name": "unknown",
                "examples": [

                ]
            }
        ]
        skill_list_prompt = ""
        for skill in skill_list:
            skill_list_prompt += "- " + skill["name"] + ", examples: " + ", ".join(skill["examples"]) + "\n "

        # intent clasification with mistral7b
        # intenttext = f"""Your Job is to recognize the intent of a user message: "{text}". Make sure your response includes the most matching one of these intents: [ {skill_list_prompt} ]. only answer with the intent. """
        # intenttext = f"""You are an intent classifier, this is the list of intents and example sentences for each intent:\n {skill_list_prompt}\n Your job is to recognize the intent of a user message: "{text}". Make sure your response includes the most matching one of these intents and only answer with the intent name. """
        # intent = Ai().predict(intenttext)

        # intent classification with nexus raven
        prompt_template = \
'''
Function:
def get_time():
    """
    tells the user the time
    
    Returns:
    String: the current time in the format HH:MM
    """

Function:
def set_timer(hours, minutes, seconds):
    """
    sets a timer for the given duration, only used when explicitly asked for a timer.

    Args:
    hours(Optional): if set adds this amount of hours to the timer.
    minutes(Optional): If set adds this amount of minutes to the timer.
    seconds(Optional): If set adds this amount of seconds to the timer.
    """
    
def no_relevant_function(user_query : str):
  """
  Call this when no other provided function can be called to answer the user query.

  Args:
     user_query: The user_query that cannot be answered by any other function calls.
  """


User Query: {query}
'''
        intent = Ai(model="nexusraven", stop=['Thought:']).predict(prompt_template.format(query=text) )
        print("intent:", intent)
        intent = intent.split("Call: ")[1]
        print("intent:", intent)
        def no_relevant_function():
            print("converse called")
        def get_time(args=None):
            print("function call getTime:", datetime.now().strftime("%H:%M"))
            mqtt_client.publish("assistant_response", 'the current time is ' + datetime.now().strftime("%H:%M"))
        def set_timer(hours=None, minutes=None, seconds=None):
            print("setTimer called with", hours, minutes, seconds)
        exec(intent)
        # only exec
        return
        for skill in skill_list:
            if skill["name"] in intent:
                print("intent recognized:", skill["name"])
                if skill["name"] == "getTime":
                    print("function call getTime:", datetime.now().strftime("%H:%M"))
                    mqtt_client.publish("assistant_response", 'the current time is ' + datetime.now().strftime("%H:%M"))
                if skill["name"] == "getDate":
                    print("the current date is", datetime.now().strftime("%d/%m/%Y"))
                if skill["name"] == "setTimer":
                    duration = Ai().predict(f"""extract the time from the following text: "{text}". Word your answer exactly like this: 'there are x hours, x minutes and x seconds.' Make sure to replace x with the correct number, respectively. Make sure to use numerals and not words. If you encounter expressions such as half an hour, translate them to the appropriate amount of minutes """)
                    print("duration ai: ", duration)
                    # extract the duration from the text with regex
                    hours = re.findall(r"(\d+)\s*hour", duration)
                    minutes = re.findall(r"(\d+)\s*minute", duration)
                    seconds = re.findall(r"(\d+)\s*second", duration)
                    if len(hours) == 0:
                        hours = 0
                    else:
                        hours = int(hours[0])
                    if len(minutes) == 0:
                        minutes = 0
                    else:
                        minutes = int(minutes[0])
                    if len(seconds) == 0:
                        seconds = 0
                    else:
                        seconds = int(seconds[0])
                    print("duration extracted:", hours, minutes, seconds)
                    response = selected_ai.predict(f"""you just successfully set a timer for {hours} hours, {minutes} minutes and {seconds} seconds, as the user requested, please inform them of this.""")
                    if int(os.getenv('DEBUG_LEVEL')) >= 2:
                        print("Assistant response:", response)
                    mqtt_client.publish("assistant_response", response)
                if skill["name"] == "unknown":
                    print("unknown intent")
                    response = selected_ai.predict(text)
                    print("Assistant response:", response)
                    mqtt_client.publish("assistant_response", response)

    # Initialize MQTT client
    mqtt_client = MqttClient(subscribeTopics=["speech_transcribed"], onMessage=on_message)

    print("✅ AI ready and waiting for recognized text")
    # Start MQTT client loop to listen for messages
    mqtt_client.run()
