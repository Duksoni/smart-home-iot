"""
Generic actuator coordinator for simple on/off/start/stop actuators.

The server publishes commands to  smarthome/commands/<CODE>
with payload  {"action": "<action>"}.
This coordinator subscribes to that topic and calls the correct
component function so the physical (or simulated) device reacts.

Usage
-----
    from actuator_coordinator import start_actuator_coordinator
    from components.led import led_control
    from components.buzzer import buzzer_control

    dl_sub = start_actuator_coordinator(broker, hardware["DL"], led_control, "DL")
    db_sub = start_actuator_coordinator(broker, hardware["DB"], buzzer_control, "DB")

    # On shutdown:
    dl_sub.stop()
    db_sub.stop()
"""

import json

from mqtt_subscriber import MqttSubscriber


class ActuatorCoordinator:
    """
    Receives MQTT command messages for one actuator and calls the
    supplied control function with (settings, action).

    Expected message schema:  {"action": "<string>"}
    """

    def __init__(self, settings: dict, control_fn, code: str):
        self.settings = settings
        self.control_fn = control_fn
        self.code = code

    def on_message(self, client, userdata, message):
        try:
            data = json.loads(message.payload.decode("utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[{self.code} COORD] Invalid payload: {exc}")
            return

        action = data.get("action")
        if not action:
            return

        print(f"[{self.code} COORD] Received command: {action}")
        self.control_fn(self.settings, action)


def start_actuator_coordinator(
    broker_settings: dict,
    hardware_settings: dict,
    control_fn,
    code: str,
) -> MqttSubscriber:
    """
    Start a subscriber that drives `code`'s actuator from server commands.

    :param broker_settings:  The "mqtt" block from settings.json.
    :param hardware_settings: The hardware block for this actuator (e.g. hardware["DL"]).
    :param control_fn:       Component control function, e.g. led_control or buzzer_control.
    :param code:             Actuator code, e.g. "DL" or "DB".
    :returns:                The running MqttSubscriber (call .stop() on shutdown).
    """
    command_base = broker_settings.get("command_base_topic", "smarthome/commands")
    topic = f"{command_base}/{code}"
    client_id = f"actuator-coordinator-{code.lower()}"

    coordinator = ActuatorCoordinator(hardware_settings, control_fn, code)
    subscriber = MqttSubscriber(
        broker_settings,
        coordinator.on_message,
        client_id,
        [topic],
    )
    subscriber.connect_and_start()
    print(f"[{code} COORD] Actuator coordinator started, listening on {topic}")
    return subscriber
