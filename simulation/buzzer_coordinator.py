"""
Buzzer actuator coordinator.

Listens on  smarthome/commands/DB  for {"action": "start"} / {"action": "stop"}
/ {"action": "short"} / {"action": "long"} and drives the buzzer accordingly.

The buzzer worker runs in a background thread so that blocking beep durations
never delay MQTT message processing.
"""

import json
import queue
import threading
import time

from components.buzzer import buzzer_control
from mqtt_subscriber import MqttSubscriber

_PREFIX = "[BUZZER COORD]"

_VALID_ACTIONS = {"start", "stop", "short", "long"}


class BuzzerCoordinator:
    def __init__(self, hardware_settings: dict, pause_between_double: float = 0.15):
        self.settings = hardware_settings
        self._queue: queue.Queue = queue.Queue()
        self._pause = pause_between_double
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(
            target=self._worker,
            name=f"buzzer-worker-{hardware_settings.get('code', 'DB')}",
            daemon=True,
        )
        self._worker_thread.start()

    def on_message(self, client, userdata, message):
        try:
            data = json.loads(message.payload.decode("utf-8"))
            action = data.get("action", "").lower()
            if action in _VALID_ACTIONS:
                print(f"{_PREFIX} Received command: {action}")
                self._queue.put(action)
            else:
                print(f"{_PREFIX} Unknown action: {action!r}")
        except json.JSONDecodeError as exc:
            print(f"{_PREFIX} Invalid payload: {exc}")

    def stop(self):
        self._stop_event.set()
        self._worker_thread.join(timeout=1)

    def _worker(self):
        while not self._stop_event.is_set():
            try:
                action = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            buzzer_control(self.settings, action)


def start_buzzer_coordinator(broker_settings: dict, hardware_settings: dict, code: str):
    """
    Start the MQTT subscriber + worker that drives the buzzer identified by `code`.
    Returns (coordinator, subscriber) so the caller can stop() both on shutdown.
    """
    settings = dict(hardware_settings.get(code, {}))
    settings.setdefault("code", code)

    coordinator = BuzzerCoordinator(settings)
    topic = f"{broker_settings['command_base_topic']}/{code}"
    subscriber = MqttSubscriber(
        broker_settings,
        coordinator.on_message,
        client_id=f"buzzer-coordinator-{code.lower()}",
        topics=[topic],
    )
    subscriber.connect_and_start()
    print(f"{_PREFIX} Buzzer coordinator started for {code}, topic: {topic}")
    return coordinator, subscriber
