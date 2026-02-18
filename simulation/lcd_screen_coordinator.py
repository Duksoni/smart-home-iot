import json
import threading
from threading import Thread
from typing import List, Optional

from mqtt_subscriber import MqttSubscriber

prefix = "[LCD COORD]"


class LCDScreenCoordinator:
    def __init__(self, device_settings: dict):
        self.readings_cycle = device_settings.get("readings_cycle_seconds")
        self.dht_codes = device_settings.get("dht_codes")
        self.sensor_locations = ["Bedroom", "Master Bedroom", "Kitchen"]
        measurement_codes = device_settings.get("measurement_codes")
        self.latest_readings = {
            code: {measurement: None for measurement in measurement_codes}
            for code in self.dht_codes
        }
        if device_settings.get("simulated"):
            self.lcd_screen = None
        else:
            from actuators.lcd_display import LCD

            self.lcd_screen = LCD()

        self._stop_event = threading.Event()
        self._thread: Optional[Thread] = None

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            device_code = data.get("code")
            measurement = data.get("measurement")
            value = data.get("value")
            if device_code in self.latest_readings and measurement:
                self.latest_readings[device_code][measurement] = value
        except json.JSONDecodeError as exc:
            print(f"Invalid MQTT payload: {exc}")

    def _display_text(self, code: str, location: str):
        reading = self.latest_readings.get(code, {})
        temp = reading.get("temperature", "—")
        hum = reading.get("humidity", "—")
        first_row = f"{location}"
        if temp and hum:
            second_row = f"Temp: {temp}°C Hum: {hum}%"
        else:
            second_row = "No data"
        if self.lcd_screen:
            self.lcd_screen.display(first_row, second_row)
        else:
            print("=" * 20)
            print(f"{first_row} {code}\n{second_row}")
            print("=" * 20)

    def _display_cycle_worker(self):
        idx = 0
        while not self._stop_event.is_set():
            code = self.dht_codes[idx % len(self.dht_codes)]
            location = self.sensor_locations[idx % len(self.sensor_locations)]
            self._display_text(code, location)
            idx += 1
            self._stop_event.wait(self.readings_cycle)

    def start_cycle(self):
        self._thread = threading.Thread(
            target=self._display_cycle_worker,
            name="lcd-display-cycle",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=1)
        if self.lcd_screen:
            self.lcd_screen.clear()


def start_lcd_screen_coordinator(broker_settings: dict, hardware_settings: dict):
    code = "LCD"
    client_id = "lcd-screen-coordinator"
    device_settings = hardware_settings.get(code)
    dht_codes: List[str] = device_settings.get("dht_codes")
    base_topic = f"{broker_settings.get('base_topic')}/sensors"
    topics = [f"{base_topic}/{code}" for code in dht_codes]

    coordinator = LCDScreenCoordinator(device_settings)
    subscriber = MqttSubscriber(
        broker_settings, coordinator.on_message, client_id, topics
    )
    subscriber.connect_and_start()

    coordinator.start_cycle()

    print(f"{prefix} LCD Screen Coordinator started")

    return coordinator, subscriber
