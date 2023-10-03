import requests
import json
from src import env
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
        response = requests.post(f"{env.AI_API_URL}/api/v1/generate", json=data)

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

