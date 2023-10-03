import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fetch environment variables with default values if not set
AI_PROVIDER = os.getenv('AI_PROVIDER', 'ollama')
AI_MODEL = os.getenv('AI_MODEL', 'llama2-uncensored:7b')
AI_API_URL = os.getenv('AI_API_URL', 'http://localhost:11434')
if AI_PROVIDER == 'kobold':
    AI_API_URL = os.getenv('AI_API_URL', 'http://localhost:5001')
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))