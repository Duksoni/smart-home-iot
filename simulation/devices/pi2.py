"""
PI2 device controller — Kitchen.

Sensors  : DS2, DUS2, DPIR2, BTN, DHT3, GSG
Actuators: none local (4SD is handled by a separate timer coordinator
           driven from the server/web-app — implemented in checkpoint 3 part 2)

PI2 publishes all sensor readings and the server handles alarm logic.
"""

import threading
import time

from components.dht import run_dht
from components.door_button import run_ds
from components.door_ultrasonic import run_dus
from components.gsg import run_gsg, send_gyro_event
from components.motion import run_dpir
from mqtt_publisher import init_mqtt_publisher
from settings import get_device_config

RUNNERS = {
    "DS2":   run_ds,
    "DUS2":  run_dus,
    "DPIR2": run_dpir,
    "BTN":   run_ds,      # BTN has the same button-press logic as a door sensor
    "DHT3":  run_dht,
    "GSG":   run_gsg,
}


def _get_hw(hardware_config, code):
    params = dict(hardware_config.get(code, {"simulated": True}))
    params.setdefault("code", code)
    return params


def _start_sensors(device_config, hardware_config, threads, stop_event):
    for code in device_config.get("sensors", []):
        runner = RUNNERS.get(code)
        if not runner:
            print(f"[PI2] No runner for sensor {code}, skipping.")
            continue
        runner(_get_hw(hardware_config, code), threads, stop_event, code)


def _console_thread(hardware_config, stop_event):
    print("PI2 console ready. Type 'help' for commands.")
    while not stop_event.is_set():
        try:
            cmd = input("> ").strip()
        except EOFError:
            stop_event.set()
            return

        if not cmd:
            continue
        lower = cmd.lower()

        if lower in {"exit", "quit"}:
            stop_event.set()
            return

        if lower == "help":
            print("Commands:")
            print("  gsg send <delta>   — publish a gyroscope delta reading")
            print("  exit | quit")
            continue

        parts = cmd.split()

        if len(parts) == 3 and parts[0].lower() == "gsg" and parts[1].lower() == "send":
            try:
                delta = float(parts[2])
                send_gyro_event(_get_hw(hardware_config, "GSG"), delta)
            except ValueError:
                print("delta must be a number, e.g.  gsg send 120.5")
            continue

        print("Unknown command. Type 'help'.")


def run(settings):
    device_config, hardware_config = get_device_config(settings, device="PI2")
    for code, params in hardware_config.items():
        if isinstance(params, dict):
            params.setdefault("code", code)

    publisher = init_mqtt_publisher(settings)

    threads = []
    stop_event = threading.Event()

    _start_sensors(device_config, hardware_config, threads, stop_event)

    console_t = threading.Thread(
        target=_console_thread, args=(hardware_config, stop_event), daemon=True
    )
    threads.append(console_t)
    console_t.start()

    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

    stop_event.set()
    publisher.stop()

    for t in threads:
        t.join(timeout=1)

    try:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
    except ImportError:
        pass
