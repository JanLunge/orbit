![header](./assets/orbit-header.png)
<h1 align="center">Orbit
</h1>
<h4 align="center">
a modular platform for building a voice based LLM assistant</h4>
<p align="center">
    <a href="https://github.com/JanLunge/orbit/stargazers"><img src="https://img.shields.io/github/stars/JanLunge/orbit" alt="Stars Badge"/></a>
    <a href="https://github.com/JanLunge/orbit/network/members"><img src="https://img.shields.io/github/forks/JanLunge/orbit" alt="Forks Badge"/></a>
</p>

# services
* 🎤 audio streaming via mqtt (audio_satelite)
* ❗️ Hotword detection with porcupine
* 🎧 whisper speech recognition
* ⚙️ Command service for custom executable commands
* 🧠 LLM AI integration with OpenAi or local inference (llama.cpp, kobold.cpp, mistral via ollama)
* 💬 TTS via elevenlabs, pyttsx3 or macos say

![demo](./assets/usage.gif)

## what is this?
Build your own jarvis or alexa/siri/google assistant with this modular platform. 
it will listen for audio with a microphone streamer via mqtt, 
then a hotword module will trigger the hotword event if you say the hotword/wakeword atlas
then the audio will be streamed to a whisper speech recognition module that will return the text
then the text will be sent to an AI module that will return a response
then the text will be sent to a command module that will execute the command
then the response will be sent to a TTS module that will speak the response

This tool is mainly built for use on mac and linux but it should work on windows too with a bit of configuration.


## TODOs:
- [ ] use https://github.com/coqui-ai/TTS for voice clonable output
- [ ] implement function calling in the ai module so the ai can trigger commands
- [ ] create a management interface for the function calling
- [x] support local inference with custom models
- [ ] support large context models
- [ ] switch wake word to something fully opensource eg. snowboy
- [ ] saving context in interactions for the ai
- [ ] vector store for permanent information?
- [ ] already speak chunks of responses when streaming inference content to speed up response time
- [ ] ignore the hotword if the ai is speaking or the user is speaking
- [ ] test if instruct models work better as agents
- [ ] figure out a way for the agent to still preserve character and answer normal questions casually

current token limitations make the function calling not really feasible but in the close future you will be able to use your computer or other api apps just with your voice,
AI will be the interface between you and your computer. get in now and be ready for the future!

# requirements
- a Mqtt server

on OSX install one with `brew install mosquitto` then manage it with `brew services start mosquitto`
and 
`brew services stop mosquitto`
* `ffmpeg` for the whisper speech recognition
* a working `pyaudio` installation

# optional
- openai api key into .env named OPENAI_API_KEY (if you use chatgpt in the ai.py file)
- a porcupine hotword model and access key
- an elevenlabs api key for tts



# Setup
for the first run use `sh run.sh --setup`
after that just run `sh run.sh`
-- poetry
1. get a poetry shell with `poetry shell`
2. install the dependencies with `poetry install`
3. then run `python3 main.py` to start the program

on mac os install pyaudo support with 
```
xcode-select --install
brew remove portaudio
brew install portaudio
pip3 install pyaudio
```

# Notes
using local models works best in simple mode as most ai models do not work well with the reasoning chains in langchain and will produce nonsense
using openai works very well as agent in the advanced mode


# training an intent model:
in the ludwig folder do `ludwig train --dataset sequence_tags.csv --config config.yaml`


## Project Structure

### AI Providers
- Ollama (recommended)

start the ollama app and set the AI_PROVIDER to 'ollama' in the .env file

- Kobold.cpp

compile the kobold.cpp based on the instructions then run a model of your choice with the following command:
`python3 koboldcpp.py ~/Downloads/wizard-vicuna-13b-uncensored-superhot-8k.ggmlv3.q4_K_M.bin 8888 --stream --contextsize 8192 --unbantokens --threads 8 --usemlock`
set the AI_PROVIDER to 'kobold' in the .env file and the AI_API_URL to the ip of the kobold server with the port (in this case https://localhost:8888)


# TODO:
1. pull
2. install pyaudio via these commands:

xcode-select --install
brew remove portaudio
brew install portaudio
pip3 install pyaudio

3. install mosquitto via brew and start it
4. set .env key for PORCUPINE_ACCESS_KEY https://picovoice.ai/platform/porcupine/
5. make sure to select your favorite wakeword in the wakewords folder or create one yourself at : link here
5. if you are using macOS system python instead of homebrew, refer to this: https://github.com/urllib3/urllib3/issues/3020
5. make sure to install https://github.com/jmorganca/ollama
6. run sh run.sh --setup