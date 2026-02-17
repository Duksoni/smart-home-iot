import threading
import time

from components.buzzer import buzzer_control
from components.buzzer import cleanup_all as cleanup_buzzers
from components.door_button import run_ds1
from components.door_ultrasonic import run_dus1
from components.led import cleanup_all as cleanup_leds
from components.led import led_control
from components.membrane_switch import (
    run_membrane_switch,
    send_sequence,
    start_auto,
    stop_auto,
)
from components.motion import run_dpir
from door_coordinator import start_door_coordinator
from mqtt_publisher import init_mqtt_publisher
from settings import get_device_config

RUNNERS = {
    "DS1": run_ds1,
    "DMS": run_membrane_switch,
    "DPIR1": run_dpir,
    "DUS1": run_dus1,

}


def _get_hw_settings(hardware_config, code):
    params = hardware_config.get(code, {"simulated": True})
    if isinstance(params, dict):
        params.setdefault("code", code)
    return params


def _start_sensor_threads(device_config, hardware_config, threads, stop_event):
    for code in device_config.get("sensors", []):
        runner = RUNNERS.get(code)
        if not runner:
            continue
        params = _get_hw_settings(hardware_config, code)
        runner(params, threads, stop_event, code)


def _console_thread(hardware_config, stop_event):
    print("Type 'help' for commands, 'exit' or 'quit' to quit.")
    while not stop_event.is_set():
        try:
            cmd = input("> ").strip()
        except EOFError:
            print("Keyboard interrupt, exiting...")
            stop_event.set()
            return

        if not cmd:
            continue

        lower = cmd.lower()
        if lower in {"exit", "quit"}:
            stop_event.set()
            return
        if lower == "help":
            print("=" * 20)
            print("Commands:")
            print("led on/off")
            print("buzzer short/long/on/off")
            print("dms auto on/off")
            print("dms send <4 digits>")
            print("exit/quit")
            continue

        parts = cmd.split()

        if len(parts) == 2 and parts[0].lower() in {"led", "buzzer"}:
            target, action = parts[0].lower(), parts[1].lower()
            if target == "led":
                led_control(_get_hw_settings(hardware_config, "DL"), action)
            elif target == "buzzer":
                buzzer_control(_get_hw_settings(hardware_config, "DB"), action)
            continue

        if parts[0].lower() == "dms":
            if len(parts) >= 2 and parts[1].lower() == "auto":
                # toggle auto simulator
                if len(parts) == 3 and parts[2].lower() in {"on", "off"}:
                    if parts[2].lower() == "on":
                        start_auto(_get_hw_settings(hardware_config, "DMS"), threads=None, delay=2)
                    else:
                        stop_auto()
                else:
                    print("Usage: dms auto on|off")
                continue

            if len(parts) == 3 and parts[1].lower() == "send":
                seq = parts[2].strip()
                if len(seq) not in (4, 5):
                    print("Sequence must be 4 digits (optionally followed by '#')")
                    continue

                send_sequence(_get_hw_settings(hardware_config, "DMS"), seq)
                continue

        print("Unknown command, type 'help' to see the available commands.")


def run(settings):
    device_config, hardware_config = get_device_config(settings, device="PI1")
    for code, params in hardware_config.items():
        if isinstance(params, dict):
            params.setdefault("code", code)

    publisher = init_mqtt_publisher(settings)

    threads = []
    stop_event = threading.Event()

    start_door_coordinator(settings, device_config, hardware_config, threads, stop_event)
    _start_sensor_threads(device_config, hardware_config, threads, stop_event)

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

    publisher.stop()
    stop_event.set()
    for thread in threads:
        thread.join(timeout=1)

    try:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
    except ImportError:
        pass

    # Check later if this is no longer needed
    # cleanup_buzzers()
    # cleanup_leds()
