import json
import queue
import threading
import time

import paho.mqtt.publish as publish


DEFAULT_BASE_TOPIC = "smarthome"
DEFAULT_BATCH_SIZE = 10
DEFAULT_FLUSH_INTERVAL = 2.0
HOSTNAME = "localhost"
PORT = 1883

_publisher = None
_base_topic = DEFAULT_BASE_TOPIC
_device_name = "unknown"


class MqttBatchPublisher:
    def __init__(self, host, port, batch_size=DEFAULT_BATCH_SIZE, flush_interval=DEFAULT_FLUSH_INTERVAL):
        self.host = host
        self.port = port
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._worker,
            name="mqtt-batcher",
            daemon=True,
        )
        self._thread.start()

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


def init_mqtt(settings):
    global _publisher, _base_topic, _device_name
    mqtt_settings = settings.get("mqtt", {})
    host = mqtt_settings.get("host", HOSTNAME)
    port = mqtt_settings.get("port", PORT)
    _base_topic = mqtt_settings.get("base_topic", DEFAULT_BASE_TOPIC)
    batch_size = mqtt_settings.get("batch_size", DEFAULT_BATCH_SIZE)
    flush_interval = mqtt_settings.get("flush_interval", DEFAULT_FLUSH_INTERVAL)
    _device_name = settings.get("device", "unknown")
    _publisher = MqttBatchPublisher(host, port, batch_size=batch_size, flush_interval=flush_interval)
    return _publisher


def get_publisher():
    return _publisher


def get_base_topic():
    return _base_topic


def get_device_name():
    return _device_name


def build_topic(base_topic, category, code):
    base = (base_topic or DEFAULT_BASE_TOPIC).rstrip("/")
    return f"{base}/{category}/{code}"
