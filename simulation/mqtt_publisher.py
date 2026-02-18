import json
import queue
import threading
import time
from typing import Optional

import paho.mqtt.publish as publish


class MqttBatchPublisher:
    def __init__(self, settings):
        self.host = settings.get("host")
        self.port = settings.get("port")
        self.base_topic = settings.get("base_topic")
        self.batch_size = settings.get("publish_batch_size")
        self.flush_interval = settings.get("publish_flush_interval")
        self.device_name = settings.get("device")
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._worker,
            name="mqtt-publisher",
            daemon=True,
        )
        self._thread.start()

    def build_topic(self, category, code):
        base = self.base_topic.rstrip("/")
        return f"{base}/{category}/{code}"

    def enqueue_json(self, topic, payload, qos=0, retain=False):
        self._queue.put((topic, json.dumps(payload), qos, retain))

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=1)

    def _flush(self, batch):
        try:
            publish.multiple(batch, hostname=self.host, port=self.port)
        except Exception as exc:
            print(f"[MQTT] publish failed: {exc}")

    def _worker(self):
        batch = []
        last_flush = time.monotonic()
        while not self._stop_event.is_set():
            timeout = max(0.0, self.flush_interval - (time.monotonic() - last_flush))
            try:
                item = self._queue.get(timeout=timeout)
                batch.append(item)
                if len(batch) >= self.batch_size:
                    self._flush(batch)
                    batch = []
                    last_flush = time.monotonic()
            except queue.Empty:
                if batch:
                    self._flush(batch)
                    batch = []
                last_flush = time.monotonic()


_publisher: Optional["MqttBatchPublisher"] = None


def init_mqtt_publisher(settings: dict):
    global _publisher
    mqtt_settings = settings.get("mqtt")
    if not mqtt_settings:
        raise ValueError("MQTT settings are not configured")
    _publisher = MqttBatchPublisher(mqtt_settings)
    return _publisher


def get_publisher():
    return _publisher
