import threading
from typing import Optional

from paho.mqtt import client as mqtt_client
from paho.mqtt.client import CallbackOnMessage


class MqttSubscriber:
    def __init__(
        self,
        mqtt_settings: dict,
        on_message: CallbackOnMessage,
        code: str,
        client_id: Optional[str] = None,
    ):
        self.host = mqtt_settings.get("host")
        self.port = mqtt_settings.get("port")
        self.base_topic = mqtt_settings.get("command_base_topic")
        self.code = code
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
            print(f"[MQTT SUB {self.code}] Connected to broker.")
            self._subscribe()
        else:
            print(f"[MQTT SUB {self.code}] Connection failed with rc={rc}")

    def _subscribe(self, qos: int = 0):
        topic = self._build_topic()
        self._client.subscribe(topic, qos=qos)
        print(f"[MQTT SUB {self.code}] Subscribied to topic {topic}")

    def connect_and_start(self):
        self._client.connect(self.host, self.port)
        self._thread.start()

    def _build_topic(self) -> str:
        return f"{self.base_topic}/{self.code}"

    def _run_loop(self):
        self._client.loop_start()
        self._stop_event.wait()
        self._client.loop_stop()
