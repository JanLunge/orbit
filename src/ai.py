from datetime import datetime
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import setproctitle
import os
import requests
import json
from env import AI_MODEL, AI_API_URL, AI_PROVIDER, MQTT_BROKER, MQTT_PORT
# load dotenv again because this is a seperate process
load_dotenv()

# example command for using koboldcpp
# python3 koboldcpp.py ~/Downloads/wizard-vicuna-13b-uncensored-superhot-8k.ggmlv3.q4_K_M.bin 8888 --stream --contextsize 8192 --unbantokens --threads 8 --usemlock



# wrapper for koboldcpp api
class KoboldApiLLM:
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
            "frmttriminc": True,
        }

        # Add the stop sequences to the data if they are provided
        if stop is not None:
            data["stop_sequence"] = stop

        # Send a POST request to the Kobold API with the data
        response = requests.post(f"{AI_API_URL}/api/v1/generate", json=data)

        # Raise an exception if the request failed
        response.raise_for_status()

        # Check for the expected keys in the response JSON
        json_response = response.json()
        if (
            "results" in json_response
            and len(json_response["results"]) > 0
            and "text" in json_response["results"][0]
        ):
            # Return the generated text
            text = json_response["results"][0]["text"].strip().replace("'''", "```")

            # Remove the stop sequence from the end of the text, if it's there
            if stop is not None:
                for sequence in stop:
                    if text.endswith(sequence):
                        text = text[: -len(sequence)].rstrip()

            return text
        else:
            raise ValueError("Unexpected response format from API")

    def __call__(self, prompt: str, stop: str = None) -> str:
        return self._call(prompt, stop)


class OllamaApiLLM:
    def _call(self, prompt: str, stop: str = None) -> str:
        data = {
            "model": AI_MODEL,
            "prompt": prompt,
        }

        # Add the stop sequences to the data if they are provided
        if stop is not None:
            data["stop_sequence"] = stop

        # Send a POST request to the Kobold API with the data
        response = requests.post(f"{AI_API_URL}/api/generate", json=data,stream=True)

        # Raise an exception if the request failed
        response.raise_for_status()
        # Buffer for partial lines
        response_text = ""
        buffer = ""

        # Iterate over the content in small chunks
        for chunk in response.iter_content(chunk_size=1024):
            # Decode the chunk and add it to the buffer
            buffer += chunk.decode('utf-8')

            # Split by newlines, but keep the last partial line in the buffer
            lines = buffer.split("\n")
            for line in lines[:-1]:
                # print(line)  # Or process the line in some other way
                # line to json
                json_line = json.loads(line)
                if "response" in json_line:
                    print(json_line['response'], end="")
                    response_text += json_line['response']
                else:
                    print(" ")

            # Keep the last, potentially incomplete line for the next iteration
            buffer = lines[-1]

        # Handle any remaining content in the buffer after all chunks are processed
        if buffer:
            print(buffer)  # Or process the line in some other way

        return response_text.strip().replace("'''", "```")

    def __call__(self, prompt: str, stop: str = None) -> str:
        return self._call(prompt, stop)

def run():
    selectedAI = Ai("luna")
    setproctitle.setproctitle("Orbit-Module AI")



    # Define callback function for MQTT client to process incoming messages
    def on_message(client, userdata, message):
        # Get the text from the incoming MQTT message
        text = message.payload.decode()
        if text.strip() == "":
            return

        print("User Input for AI: {}".format(text))

        # # Intercept commands here
        # from ludwig.api import LudwigModel
        #
        # # Load the trained model
        # model = LudwigModel.load("ludwig/results/experiment_run_26/model")
        #
        # # Make predictions
        # data_to_predict = {
        #     'utterance': [text],
        # }
        # predictions = model.predict(data_to_predict)
        #
        # print(predictions)
        #
        # predictions_df = predictions[0]
        # intent_predictions = predictions_df['intent_predictions'].tolist()
        # slots_predictions = predictions_df['slots_predictions'].tolist()
        #
        # for text, intent, slots in zip(data_to_predict['utterance'], intent_predictions, slots_predictions):
        #     slot_value = extract_slot_values(text, slots)
        #     print(f"Text: {text}\nIntent: {intent}\nSlot Value: {slot_value}\n")
        #
        # return
        from hyperdb import HyperDB
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

        additionalContext = ""
        results = db.query(text, top_k=5)
        print(results[0][0]["function"], results[0][1])  # trust over 0.88
        if results[0][1] > 0.88:
            print("call function", results[0][0]["function"])
            if results[0][0]["function"] == "getTime":
                additionalContext = "time is:" + datetime.now().strftime("%H:%M:%S")
            elif results[0][0]["function"] == "getDate":
                additionalContext = "date is:" + datetime.now().strftime("%d/%m/%Y")
        print("additionalContext", additionalContext)

        # TODO: allow chatgpt for ppl who dont need nsfw
        # TODO: ollama support
        # TODO: add parameter extraction and call functions from llm
        response = selectedAI.predict(text)
        print("luna response", response)

        mqtt_client.publish("assistant_response", response)
        # MQTT broker information


    # Initialize MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.subscribe("speech_transcribed")
    mqtt_client.on_message = on_message

    print("✅ AI waiting for recognized text")
    # Start MQTT client loop to listen for messages
    mqtt_client.loop_forever()


class Ai:
    userName = "USER"
    assistantName = "ASSISTANT"
    prompt_template = f"""{{memory}}
    {{history}}
    {userName}: {{text}}
    {assistantName}: {{preassistant}}"""
    history = []  # List of dictionaries containing the user and assistant messages
    memory = ""  # The memory of the AI with its personality

    def __init__(
        self, name="Assistant", preassistant="", memory="", history=[], stop=None
    ):
        self.agentName = name
        if AI_PROVIDER == "kobold":
            self.llm = KoboldApiLLM()
        if AI_PROVIDER == "ollama":
            self.llm = OllamaApiLLM()
        self.history = history
        self.memory = memory
        self.preassistant = preassistant
        self.stop = stop

        # check if character json exits in ./characters/name.json if not create it otherwise load it
        if not os.path.exists("./characters/" + name + ".json"):
            with open("./characters/" + name + ".json", "w") as f:
                json.dump(
                    {"name": name, "description": "", "memory": "", "history": []}, f
                )
        else:
            with open("./characters/" + name + ".json", "r") as f:
                data = json.load(f)
                self.memory = data["memory"]
                self.history = data["history"]

    def generate_prompt(self, text):
        max_items = 5  # Maximum number of items to take from prompt history
        items_to_take = min(max_items, len(self.history))
        items_taken = self.history[-items_to_take:]
        history = ""
        for i in items_taken:
            history += i["sender"] + ": " + i["text"] + "\n"

        prompt = self.prompt_template.replace("{memory}", self.memory)
        prompt = prompt.replace("{history}", history)
        prompt = prompt.replace("{text}", text)
        prompt = prompt.replace("{preassistant}", self.preassistant)
        return prompt

    def predict(self, text):
        response = self.llm(self.generate_prompt(text), self.stop)
        print("prepared prompt:", self.generate_prompt(text))
        self.history.append({"sender": self.userName, "text": text})
        self.history.append({"sender": self.assistantName, "text": response})
        # TODO: after each prediction, check if the history is too long maybe compact it
        # TODO: also persist the history to a file

        return response


if __name__ == "__main__":
    run()
