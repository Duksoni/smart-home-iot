import json

from components.rgb_led import led_control
from mqtt_subscriber import MqttSubscriber

prefix = "[BRGB COORD]"


class BRGBCoordinator:
    def __init__(self, device_settings: dict):
        self.settings = device_settings

    def on_message(self, client, userdata, msg):
        print("Message received")
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            action = data.get("action")

            if action:
                print(f"{prefix} Received command for RGB LED: {action}")
                led_control(self.settings, action)
        except json.JSONDecodeError as exc:
            print(f"Invalid MQTT payload: {exc}")


def start_rgb_light_coordinator(broker_settings: dict, hardware_settings: dict):
    code = "BRGB"
    client_id = "rgb-light-coordinator"
    coordinator = BRGBCoordinator(hardware_settings.get(code))
    topic = f"{broker_settings.get('command_base_topic')}/{code}"
    subscriber = MqttSubscriber(
        broker_settings, coordinator.on_message, client_id, [topic]
    )
    subscriber.connect_and_start()

    print(f"{prefix} RGB Light Coordinator started")

    return subscriber
