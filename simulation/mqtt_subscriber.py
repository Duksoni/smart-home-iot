import threading
from typing import List

from paho.mqtt import client as mqtt_client
from paho.mqtt.client import CallbackOnMessage


class MqttSubscriber:
    def __init__(
        self,
        mqtt_settings: dict,
        on_message: CallbackOnMessage,
        client_id: str,
        topics: List[str],
        qos: int = 0,
    ):
        self.host = mqtt_settings.get("host")
        self.port = mqtt_settings.get("port")
        self.client_id = client_id
        self.topics = topics
        self.qos = qos

        self._client = mqtt_client.Client(client_id=client_id)
        self._client.on_connect = self._handle_connect
        self._client.on_message = on_message
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run_loop, name=f"mqtt-subscriber-{client_id}", daemon=True
        )

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=1)
        self._client.disconnect()

    def _handle_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT SUB {self.client_id}] Connected to broker.")
            self._subscribe_all()
        else:
            print(f"[MQTT SUB {self.client_id}] Connection failed with rc={rc}")

    def _subscribe_all(self):
        for topic in self.topics:
            self._client.subscribe(topic, qos=self.qos)
            print(f"[MQTT SUB {self.client_id}] Subscribed to topic {topic}")

    def connect_and_start(self):
        self._client.connect(self.host, self.port)
        self._thread.start()

    def _run_loop(self):
        self._client.loop_start()
        self._stop_event.wait()
        self._client.loop_stop()
