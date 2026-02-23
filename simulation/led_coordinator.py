import json

from components.led import led_control
from mqtt_subscriber import MqttSubscriber

_PREFIX = "[LED COORD]"


class LEDCoordinator:
    def __init__(self, hardware_settings: dict):
        self.settings = hardware_settings

    def on_message(self, client, userdata, message):
        try:
            data = json.loads(message.payload.decode("utf-8"))
            action = data.get("action", "").lower()
            if action in {"on", "off", "toggle"}:
                print(f"{_PREFIX} Received command: {action}")
                led_control(self.settings, action)
            else:
                print(f"{_PREFIX} Unknown action: {action!r}")
        except json.JSONDecodeError as exc:
            print(f"{_PREFIX} Invalid payload: {exc}")


def start_led_coordinator(broker_settings: dict, hardware_settings: dict, code: str):
    settings = dict(hardware_settings.get(code, {}))
    settings.setdefault("code", code)

    coordinator = LEDCoordinator(settings)
    topic = f"{broker_settings['command_base_topic']}/{code}"
    subscriber = MqttSubscriber(
        broker_settings,
        coordinator.on_message,
        client_id=f"led-coordinator-{code.lower()}",
        topics=[topic],
    )
    subscriber.connect_and_start()
    print(f"{_PREFIX} LED coordinator started for {code}, topic: {topic}")
    return subscriber
