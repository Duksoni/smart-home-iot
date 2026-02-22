import json
import queue
import threading
from typing import Optional

from mqtt_subscriber import MqttSubscriber
import time


prefix = "[Kitchen Timer COORD]"


class KitchenTimerCoordinator:
    def __init__(self, device_settings: dict):
        segment_pins = device_settings.get("segment_pins")
        digit_pins = device_settings.get("digit_pins")
        self._command_queue  = queue.Queue()
        if device_settings.get("simulated"):
            self.display_4segment = None
        else:
            from actuators.display_4segment import Display4Segment

            self.display_4segment = Display4Segment(segment_pins, digit_pins)

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def on_message(self, client, userdata, message):
        try:
            data = json.loads(message.payload.decode("utf-8"))
            device_code = data.get("code")

            print(f"{prefix} Received MQTT message on topic {message.topic}: {data}")

            if device_code == "BTN":
                print(f"{prefix} Received button press")
                self._command_queue.put({
                    "type": "button_press",
                    "value": data.get("value") == 0
                })

            action = data.get("action")
            match action:
                case "set":
                    self._command_queue.put({
                        "type": "display_command",
                        "duration": int(data.get("duration", 0)),
                    })
                case "set_increment":
                    self._command_queue.put({
                        "type": "display_command",
                        "increment_interval": int(data.get("seconds", 30)),
                    })
                case "stop_blink":
                    self._command_queue.put({
                        "type": "display_command",
                        "stop": True,
                    })
                case "add":
                    self._command_queue.put({
                        "type": "display_command",
                        "add": int(data.get("seconds", 30)),
                    })

        except Exception as e:
            print(f"{prefix} Invalid MQTT payload: {e}")

    def start_cycle(self):
        self._thread = threading.Thread(
            target=self._display_worker,
            name="kitchen-timer-display",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=1)
        if self.display_4segment:
            self.display_4segment.clear()

    def _display(self, text: str):
        if self.display_4segment:
            self.display_4segment.display_text(text)
        else:
            print("=" * 20)
            print(f"Timer: {text[:2]}:{text[2:]}")
            print("=" * 20)

    def _display_worker(self):
        timer_seconds = 0
        increment_interval = 30
        is_blinking = False
        timer_cleared = True

        blink_visible = True
        last_blink_toggle = time.monotonic()
        last_tick = time.monotonic()

        while not self._stop_event.is_set():
            # Process all pending commands
            try:
                while True:
                    cmd = self._command_queue.get_nowait()

                    if cmd["type"] == "button_press":
                        if cmd["value"] and timer_cleared:
                            continue
                        if cmd["value"] and is_blinking:
                            is_blinking = False
                            timer_cleared = True
                        else:
                            timer_seconds += increment_interval

                    elif cmd["type"] == "display_command":
                        if cmd.get("duration"):
                            timer_seconds = cmd["duration"]
                            timer_cleared = False
                            is_blinking = False

                        elif cmd.get("increment_interval"):
                            increment_interval = cmd["increment_interval"]

                        elif cmd.get("stop"):
                            is_blinking = False
                            timer_cleared = True

                        elif cmd.get("add"):
                            timer_seconds += cmd["add"]

            except queue.Empty:
                pass

            # Timer logic
            now = time.monotonic()

            if not timer_cleared:

                if timer_seconds <= 0:
                    is_blinking = True

                if is_blinking:
                    if now - last_blink_toggle >= 0.5:
                        blink_visible = not blink_visible
                        last_blink_toggle = now

                    if blink_visible:
                        self._display("0000")
                    else:
                        self._display("    ")

                else:
                    if now - last_tick >= 1:
                        timer_seconds -= 1
                        last_tick = now

                    minutes = timer_seconds // 60
                    seconds = timer_seconds % 60
                    self._display(f"{minutes:02d}{seconds:02d}")

            time.sleep(0.999999)

def start_kitchen_timer_coordinator(broker_settings: dict, hardware_settings: dict):
    code = "4SD"
    client_id = "kitchen_timer_coordinator"
    device_settings = hardware_settings.get(code)
    command_topic = f"{broker_settings.get('command_base_topic')}/{code}"
    sensor_topic = f"{broker_settings.get('base_topic')}/sensors/BTN"
    coordinator = KitchenTimerCoordinator(device_settings)

    subscriber = MqttSubscriber(
        broker_settings, coordinator.on_message, client_id, [command_topic, sensor_topic]
    )

    subscriber.connect_and_start()

    coordinator.start_cycle()

    print(f"{prefix} Kitchen Timer Coordinator started")

    return coordinator, subscriber
