import os

import app_config as env
import requests
import json


class OllamaApiLLM:
    model = ""
    stop = None
    def __init__(self, model=None, stop=None):
        if model is not None:
            self.model = model
        if stop is not None:
            self.stop = stop
    def _call(self, prompt: str) -> str:
        data = {
            "model": self.model,
            "prompt": prompt,
        }

        # Add the stop sequences to the data if they are provided (tested for nexus raven, not for mistral7b) was at just stop before
        if self.stop is not None:
            data['options'] = {"stop": self.stop}

        # Send a POST request to the Kobold API with the data
        response = requests.post(f"{env.AI_API_URL}/api/generate", json=data, stream=True)

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
                    # print(json_line['response'], end="")
                    response_text += json_line['response']
                # else:
                # print(" ")

            # Keep the last, potentially incomplete line for the next iteration
            buffer = lines[-1]

        # Handle any remaining content in the buffer after all chunks are processed
        # if buffer:
        #     print(buffer)  # Or process the line in some other way

        return response_text.strip().replace("'''", "```")

    def __call__(self, prompt: str ) -> str:
        return self._call(prompt=prompt)
