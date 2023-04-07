# setup
- Mqtt server
`brew services start mosquitto`
and 
`brew services stop mosquitto`
- openai api key into .env named OPENAI_API_KEY

# services
- audio_satelite streams audio via mqtt
- hotword_detect listens for hotword with porcupine and sends this event via mqtt
- speech uses whisper to recognize speech
- ai uses chatgpt api to respond to the user
- tts
    - using elevenlabs for best quality
    - maybe using python coqui-ai/TTS for price
    - pyttsx3 for simplicity


# dependencies
- audio_satelite
`pip install paho-mqtt`
- ai
`pip install python-dotenv openai paho-mqtt`
- hotword
`pip install pvporcupine`
- speech
`speech_recognition whisper`
- tts 
`pip install pygame`

some setup steps for pyaudio for mac are still missing