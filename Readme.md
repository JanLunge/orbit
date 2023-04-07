# Mqtt server
`brew services start mosquitto`
and 
`brew services stop mosquitto`


# services
- audio_satelite streams audio via mqtt
- hotword_detect listens for hotword with porcupine and sends this event via mqtt
- speech uses whisper to recognize speech
- ai uses chatgpt api to respond to the user


# dependencies
pip install python-dotenv