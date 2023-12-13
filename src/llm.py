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
    model = ""

    def __init__(
            self, name="Assistant", preassistant="", memory="", history=[], stop=None, model=None, prompt_template=None
    ):
        if model is not None:
            self.model = model
        else:
            self.model = os.getenv("AI_MODEL")
        self.agentName = name
        self.stop = stop
        if env.AI_PROVIDER == "kobold":
            self.llm = KoboldApiLLM()
        if env.AI_PROVIDER == "ollama":
            self.llm = OllamaApiLLM(model=self.model, stop=self.stop)
        self.history = history
        self.memory = memory
        self.preassistant = preassistant
        if prompt_template is not None:
            self.prompt_template = prompt_template


        # check if character json exits in ./characters/name.json if not create it otherwise load it
        if not os.path.exists("./characters/" + name + ".json"):
            self.prompt_template = "{text}"
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

        # prompt = self.prompt_template.replace("{memory}", self.memory)
        # prompt = prompt.replace("{history}", history)
        # prompt = prompt.replace("{text}", text)
        # prompt = prompt.replace("{context}", additional_context)
        # prompt = prompt.replace("{preassistant}", self.preassistant)

        return text

    def predict(self, text, additional_context=""):
        response = self.llm(prompt=self.generate_prompt(text))
        if int(os.getenv("DEBUG_LEVEL")) >= 2:
            print("prepared prompt:", self.generate_prompt(text, additional_context))
        # self.history.append({"sender": self.userName, "text": text})
        # self.history.append({"sender": self.assistantName, "text": response})
        # TODO: after each prediction, check if the history is too long maybe compact it
        # TODO: also persist the history to a file

        return response
