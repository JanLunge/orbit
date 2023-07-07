import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv
load_dotenv()

class BaseMqttClient:
    def __init__(self):
        self.mqtt_broker = os.getenv('MQTT_BROKER')
        self.mqtt_port = int(os.getenv('MQTT_PORT'))
        self.client = mqtt.Client()
        self.client.on_disconnect = self.on_disconnect
        self.connect()

    def connect(self):
        self.client.connect(self.mqtt_broker, self.mqtt_port)
        self.client.loop_start()

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print("Unexpected disconnection from MQTT broker.")
            # Add any desired reconnection logic here

    def on_log(self, client, userdata, level, buf):
        # Add your desired logging logic here
        print(buf)

    def subscribe(self, topic, qos=0):
        self.client.subscribe(topic, qos=qos)

    def publish(self, topic, message, qos=0, retain=False):
        self.client.publish(topic, message, qos=qos, retain=retain)

    def on_message(self, callback):
        self.client.on_message = callback

    def loop_forever(self):
        self.client.loop_forever()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()