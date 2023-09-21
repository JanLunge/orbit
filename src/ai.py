from datetime import datetime
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import setproctitle
import os
import requests
import json

load_dotenv()


Kobold_api_url = 'http://localhost:8888'

# command for using koboldcpp
# python3 koboldcpp.py ~/Downloads/wizard-vicuna-13b-uncensored-superhot-8k.ggmlv3.q4_K_M.bin 8888 --stream --contextsize 8192 --unbantokens --threads 8 --usemlock
class KoboldApiLLM():
    def _call(self, prompt: str, stop: str = None) -> str:
        data = {
            "prompt": prompt,
            "use_story": False,
            "use_authors_note": False,
            "use_world_info": False,
            "use_memory": False,
            "max_context_length": 8000,
            "max_length": 512,
            "rep_pen": 1.12,
            "rep_pen_range": 1024,
            "rep_pen_slope": 0.9,
            "temperature": 0.6,
            "tfs": 0.9,
            "top_p": 0.95,
            # "top_k": 0.6,
            "typical": 1,
            "frmttriminc": True
        }

        # Add the stop sequences to the data if they are provided
        if stop is not None:
            data["stop_sequence"] = stop

        # Send a POST request to the Kobold API with the data
        response = requests.post(f"{Kobold_api_url}/api/v1/generate", json=data)

        # Raise an exception if the request failed
        response.raise_for_status()

        # Check for the expected keys in the response JSON
        json_response = response.json()
        if 'results' in json_response and len(json_response['results']) > 0 and 'text' in json_response['results'][0]:
            # Return the generated text
            text = json_response['results'][0]['text'].strip().replace("'''", "```")

            # Remove the stop sequence from the end of the text, if it's there
            if stop is not None:
                for sequence in stop:
                    if text.endswith(sequence):
                        text = text[: -len(sequence)].rstrip()

            # Todo: Add the generated text to the prompt history
            print(text)
            return text
        else:
            raise ValueError('Unexpected response format from Ooba API')

    def __call__(self, prompt: str, stop: str = None) -> str:
        return self._call(prompt, stop)

def generatePrompt(text):
    prompt = ""
    prompt_history = []
    max_items = 5  # Maximum number of items to take from prompt history
    items_to_take = min(max_items, len(prompt_history))

    items_taken = prompt_history[-items_to_take:]
    print("history used:", items_taken)
    for i in items_taken:
        prompt += "USER: " + i["user"] + " ASSISTANT: " + i["assistant"] + "\n"
    prompt += "USER: " + text + " ASSISTANT:"
    print(prompt)
    return prompt

def run():
    luna = ai('luna')
    def computeLocal(text):
        # import fastchat
        # fastchat.load_model()
        # agent_chain = localLangChain.agent_chain
        # result = agent_chain.predict(input=text)
        # print(result)
        # return result
        prompt = generatePrompt(text)
        # output = llm(prompt, max_tokens=200, stop=["USER:", "\n"])
        output = luna.predict(prompt)
        print('luna response',output)
        return output

    setproctitle.setproctitle('Orbit-Module AI')

    # MQTT broker information
    mqtt_broker = os.getenv('MQTT_BROKER')
    mqtt_port = int(os.getenv('MQTT_PORT'))
    mqtt_topic = "speech_detected"

    # Initialize MQTT client
    mqtt_client = mqtt.Client()

    # Define callback function for MQTT client to process incoming messages
    def on_message(client, userdata, message):
        # Get the text from the incoming MQTT message
        text = message.payload.decode()
        print("User Input for AI: {}".format(text))
        if text.strip() == "":
            return
        history = ""
        ended = False
        maxIterations = 2
        currentIteration = 0
        # Generate a response using OpenAI's GPT-3 model
        # while not ended and currentIteration < maxIterations:
        currentIteration += 1
        goal = text
        # print("proompt:", generateProompt(goal, history))

        provider = os.getenv("AI_PROVIDER")
        # response = ""
        # if(provider == "openai"):
        #     response = compute_OpenAI(text)
        # elif(provider == "local"):
        response = computeLocal(text)

        mqtt_client.publish("assistant_response", response)


    # Connect to MQTT broker and subscribe to topic
    mqtt_client.connect(mqtt_broker, mqtt_port)
    mqtt_client.subscribe(mqtt_topic)

    # Set MQTT client's message callback function
    mqtt_client.on_message = on_message

    print('✅ AI waiting for recognized text')
    # Start MQTT client loop to listen for messages
    mqtt_client.loop_forever()

class ai():
    userName = "USER"
    assistantName = "ASSISTANT"
    prompt_template = f"""{{memory}}
    {{history}}
    {userName}: {{text}}
    {assistantName}: {{preassistant}}"""
    history = [] # List of dictionaries containing the user and assistant messages
    memory = "" # The memory of the AI with its personality
    def __init__(self, name="Assistant", preassistant="", memory="", history=[], stop=None):
        self.agentName = name
        self.llm = KoboldApiLLM()
        self.history = history
        self.memory = memory
        self.preassistant = preassistant
        self.stop = stop
        # check if character json exits in ./characters/name.json if not create it other wise load it
        if not os.path.exists("./characters/" + name + ".json"):
            with open("./characters/" + name + ".json", "w") as f:
                json.dump({"name":name,  "description": "","memory": "", "history": []}, f)
        else:
            with open("./characters/" + name + ".json", "r") as f:
                data = json.load(f)
                self.memory = data["memory"]
                self.history = data["history"]



    def generatePrompt(self, text):
        max_items = 5  # Maximum number of items to take from prompt history
        items_to_take = min(max_items, len(self.history))
        items_taken = self.history[-items_to_take:]
        history = ''
        for i in items_taken:
            history += i["sender"] + ": " + i["text"] + "\n"

        prompt = self.prompt_template.replace('{memory}', self.memory)
        prompt = prompt.replace('{history}', history)
        prompt = prompt.replace('{text}', text)
        prompt = prompt.replace('{preassistant}', self.preassistant)
        return prompt

    def predict(self, text):
        response = self.llm(self.generatePrompt(text), self.stop)
        print("prepared prompt:", self.generatePrompt(text))
        self.history.append({"sender": self.userName, "text": text})
        self.history.append({"sender": self.assistantName, "text": response})
        # after each prediction, check if the history is too long maybe compact it
        # also persist the history to a file

        return response

if __name__ == "__main__":
    run()
    pass
    from hyperdb import HyperDB

    # vector db for live injected info for simple questions speedup
    documents = []

    # with open("data/commands.jsonl", "r") as f:
    #     for line in f:
    #         documents.append(json.loads(line))

    # Instantiate HyperDB with the list of documents
    db = HyperDB(documents, key="text")

    # Save the HyperDB instance to a file
    # db.save("data/commands_hyperdb.pickle.gz")

    # Load the HyperDB instance from the save file
    db.load("data/commands_hyperdb.pickle.gz")

    # Query the HyperDB instance with a text input
    luna = ai('luna')
    while True:
        question = input("ask something:")
        additionalContext = ""
        results = db.query(question, top_k=5)
        print(results[0][0]["function"], results[0][1])  # trust over 0.88
        if results[0][1] > 0.88:
            print("call function", results[0][0]["function"])
            if results[0][0]["function"] == "getTime":
                additionalContext = "time is:" + datetime.now().strftime("%H:%M:%S")
            elif results[0][0]["function"] == "getDate":
                additionalContext = "date is:" + datetime.now().strftime("%d/%m/%Y")

        luna.predict(question + " \nSYSTEM:" + additionalContext + "")

    # functionCaller = ai('function', preassistant="```", stop="```")
    # while True:
    #     question = input("ask something:")
    #     response = functionCaller.predict(question)
    #     # check if response is valid json
    #     print("response",response)
    #     call = response.split(',')
    #     if call[0] == 'checkTime':
    #         timestr = "time is: " + datetime.now().strftime("%H:%M:%S")
    #         luna.predict(question + " \n(system info :" + timestr + ")")
    #     elif call[0] == 'checkDate':
    #         datestr = "date is: " + datetime.now().strftime("%d/%m/%Y")
    #         luna.predict(question + " \n(system info :" + datestr + ")")

    # run()
