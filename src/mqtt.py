import paho.mqtt.client as mqtt
import app_config as env


class MqttClient:
    client = None
    def __init__(
            self, subscribeTopics=[], onMessage=None
    ):
        self.client = mqtt.Client()
        self.client.connect(env.MQTT_BROKER, env.MQTT_PORT)
        for topic in subscribeTopics:
            self.client.subscribe(topic)
        self.client.on_message = onMessage

    def publish(self, topic, payload):
        self.client.publish(topic, payload)

    def run(self):
        self.client.loop_forever()
