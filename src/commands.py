import paho.mqtt.client as mqtt
import json
import os
from dotenv import load_dotenv
import setproctitle
from datetime import datetime
from llm import Ai

import inspect

load_dotenv()
selected_ai = Ai("atlas")

# Function mapping
functions = {
}


def add_func(exec, id=None):
    name = exec.__name__
    if id is not None:
        name = id
    signature = inspect.signature(exec)
    functions[name] = {
        "exec": exec,
        "docstring": 'Function:\ndef '+ name + str(signature) + '\n' + '"""' + exec.__doc__ + '"""\n'
    }
    if int(os.getenv('DEBUG_LEVEL')) >= 2:
        print(f"Added function {name}")


# Function definitions

def no_relevant_function(user_query: str):
    """
    Call this when no other provided function can be called to answer the user query.

    Args:
    user_query (str): The user's query that could not be addressed by any other function.

    Returns:
    None: This function does not return any value but prints and publishes the AI's response.
    """
    # Log the received query
    print(f"No relevant function called with query: {user_query}")

    # Get the response from the AI model
    response = selected_ai.predict(user_query)

    # Log and publish the response
    print(f"Assistant response: {response}")
    mqtt_client.publish("assistant_response", response)


add_func(no_relevant_function)


def get_time(seconds=False):
    """
    tells the user the time

    Args:
    seconds(bool): if set to true, the seconds will be included in the response, only needed in very specific cases default False.

    Returns:
    String: the current time in the format HH:MM

    Examples:
    what time is it?
    """
    print("Function call getTime:", datetime.now().strftime("%H:%M"))
    mqtt_client.publish("assistant_response", 'The current time is ' + datetime.now().strftime("%H:%M"))

add_func(get_time)

def stop(verbose=False):
    """
    interrupts the assistant and stops the current conversation

    Args:
    verbose(bool): if set to true, logs will be printed to the console, only needed in very specific cases default False.

    Returns:
    String: the stopped actions

    Examples:
    stop
    """
    print("the assistant was interrupted by the user")

add_func(exec=stop)

def get_date(weekday=False):
    """
    tells the user the date in the format %d/%m/%Y

    Args:
    weekday(bool): if set to true, the weekday will be included in the response, only needed in very specific cases default False.

    Returns:
    String: the current date in the format %d/%m/%Y

    Examples:
    what day is it?
    """
    print("the current date is", datetime.now().strftime("%d/%m/%Y"))
    mqtt_client.publish("assistant_response", "the current date is " + datetime.now().strftime("%d/%m/%Y"))

add_func(get_date)

def set_timer(hours=None, minutes=None, seconds=None):
    """
    sets a timer for the given duration, only used when explicitly asked for a timer.

    Args:
    hours(Optional): if set adds this amount of hours to the timer.
    minutes(Optional): If set adds this amount of minutes to the timer.
    seconds(Optional): If set adds this amount of seconds to the timer.

    Examples:
    set a timer for 5 minutes
    remind me in 8 hours
    """
    print("setTimer called with", hours, minutes, seconds)
    hour_text = ""
    if hours is not None and hours != 0:
        hour_text = f"{hours} hours"
    minutes_text = ""
    if minutes is not None and minutes != 0:
        minutes_text = f"{minutes} minutes"
    seconds_text = ""
    if seconds is not None and seconds != 0:
        seconds_text = f"{seconds} seconds"
    response = selected_ai.predict(
        f"""you just successfully started a timer for {hour_text} {minutes_text} {seconds_text}, as the user requested, please inform them of the duration of the timer that is now running. be straight to the point with no smalltalk.""")
    if int(os.getenv('DEBUG_LEVEL')) >= 2:
        print("Assistant response:", response)
    mqtt_client.publish("assistant_response", response)

add_func(set_timer)


## End of function definitions

# always updates the functions.json files
def save_functions():
    # used for the similarity search
    function_examples = []
    function_docs = {}
    for id, obj in functions.items():
        docstring = functions[id]["docstring"]
        halves = docstring.split("Examples:\n")
        func_docstring = ""
        func_examples = ""
        if len(halves) > 1:
            func_docstring = halves[0]
            func_examples = halves[1].replace('"""\n', "").split("\n")
            func_examples = [line.strip() for line in halves[1].replace('"""\n', "").split("\n") if line.strip()]
        else:
            func_docstring = docstring
        for example in func_examples:
            function_examples.append((id, example))
        function_docs[id] = func_docstring

    with open("./function_examples.json", "w") as f:
        json.dump(function_examples, f, indent=4)

    with open("./function_docs.json", "w") as f:
        json.dump(function_docs, f, indent=4)

save_functions()

def on_message(client, userdata, message):
    setproctitle.setproctitle("Orbit-Module Commands")
    if message.topic == "command":
        payload = message.payload.decode()
        json_payload = json.loads(payload)
        intent_str = json_payload["intent"]
        query = json_payload["query"]
        print("Received command:", intent_str)

        # Parse the intent string to extract function name and arguments
        try:
            func_name, args_str = intent_str.split('(', 1)
            args_str = args_str.rstrip(')')
            args = eval(f'dict({args_str})', {}, {})  # Safe eval for arguments
        except Exception as e:
            print(f"Error parsing intent: {e}")
            no_relevant_function(query)
            return

        # Execute the function if it exists
        if func_name in functions:
            try:
                functions[func_name]["exec"](**args)
            except TypeError:
                # Handle case where arguments don't match function signature
                print(f"Argument mismatch for function {func_name}")
                no_relevant_function(query)
        else:
            print(f"Unknown function: {func_name}")
            no_relevant_function(query)


# MQTT setup
if __name__ == "__main__":
    mqtt_broker = os.getenv("MQTT_BROKER")
    mqtt_port = int(os.getenv("MQTT_PORT"))
    mqtt_client = mqtt.Client()

    mqtt_client.connect(mqtt_broker, mqtt_port)
    mqtt_client.subscribe("command")
    mqtt_client.on_message = on_message

    print("✅ commands ready")
    mqtt_client.loop_forever()
