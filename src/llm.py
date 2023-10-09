from ollama import OllamaApiLLM
from kobold import KoboldApiLLM
import os
import json
import app_config as env

class Ai:
    userName = "USER"
    assistantName = "ASSISTANT"
    prompt_template = f"""{{memory}}
    {{history}}
    {{context}}
    {userName}: {{text}}
    {assistantName}: {{preassistant}}"""
    history = []  # List of dictionaries containing the user and assistant messages
    memory = ""  # The memory of the AI with its personality

    def __init__(
        self, name="Assistant", preassistant="", memory="", history=[], stop=None
    ):
        self.agentName = name
        if env.AI_PROVIDER == "kobold":
            self.llm = KoboldApiLLM()
        if env.AI_PROVIDER == "ollama":
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
                if "prompt_template" in data:
                    self.prompt_template = data["prompt_template"]

    def generate_prompt(self, text, additional_context=""):
        max_items = 5  # Maximum number of items to take from prompt history
        items_to_take = min(max_items, len(self.history))
        items_taken = self.history[-items_to_take:]
        history = ""
        for i in items_taken:
            history += i["sender"] + ": " + i["text"] + "\n"

        prompt = self.prompt_template.replace("{memory}", self.memory)
        prompt = prompt.replace("{history}", history)
        prompt = prompt.replace("{text}", text)
        prompt = prompt.replace("{context}", additional_context)
        prompt = prompt.replace("{preassistant}", self.preassistant)
        return prompt

    def predict(self, text, additional_context=""):
        response = self.llm(self.generate_prompt(text), self.stop)
        print("prepared prompt:", self.generate_prompt(text, additional_context))
        self.history.append({"sender": self.userName, "text": text})
        self.history.append({"sender": self.assistantName, "text": response})
        # TODO: after each prediction, check if the history is too long maybe compact it
        # TODO: also persist the history to a file

        return response