import json

import setproctitle
from mqtt import MqttClient
from llm import Ai

from src.similarity_search import find_similar_functions
selected_ai = Ai("atlas")
if __name__ == "__main__":
    setproctitle.setproctitle("Orbit-Module AI")

    # Define callback function for MQTT client to process incoming messages
    def on_message(client, userdata, message):
        # Get the text from the incoming MQTT message
        text = message.payload.decode()
        if text.strip() == "":
            return

        print("User Input for AI: {}".format(text))

        # get the top 5 most similar functions for the given query
        functions = find_similar_functions(text, k=10)
        if functions:  # Check if the list is not empty
            first_elements = [func[0] for func in functions]
            print("functions that match the prompt:", ', '.join(first_elements))
        # intent classification with nexus raven
        prompt_template = \
            '''
Function:
def get_time(seconds):
    """
    tells the user the time
    
    Args:
    seconds(bool): if set to true, the seconds will be included in the response, only needed in very specific cases default False.
    
    Returns:
    String: the current time in the format HH:MM
    """
    
Function:
def get_date(weekday):
    """
    tells the user the date
    
    Args:
    weekday(bool): if set to true, the weekday will be included in the response, only needed in very specific cases default False.
    
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
        intent = Ai(model="nexusraven", stop=['Thought:']).predict(prompt_template.format(query=text.replace("'", "")))
        intent = intent.split("Call: ")[1]
        print("intent:", intent)

        mqtt_client.publish("command", json.dumps({"intent": intent, "query": text}))




    # Initialize MQTT client
    mqtt_client = MqttClient(subscribeTopics=["speech_transcribed"], onMessage=on_message)

    print("✅ AI ready and waiting for recognized text")
    # Start MQTT client loop to listen for messages
    mqtt_client.run()
