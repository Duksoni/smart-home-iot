import threading
import time

from settings import load_settings, get_device_config
from smart_home.components.buzzer import buzzer_control
from smart_home.components.dht import run_dht
from smart_home.components.led import led_control

RUNNERS = {
    "DHT1": run_dht,
    # "DS1": run_door_sensor,
    # ...
}


def actuator_console(settings, stop_event):
    print("Type 'help' for commands, 'exit' to quit.")
    while not stop_event.is_set():
        try:
            cmd = input("> ").strip().lower()
        except EOFError:
            stop_event.set()
            break

        if cmd in {"exit", "quit"}:
            stop_event.set()
            break
        if cmd == "help":
            print("Commands: led on/off, buzzer on/off, exit")
            continue

        parts = cmd.split()
        if len(parts) != 2:
            print("Invalid command, try 'led on'")
            continue

        target, action = parts
        if target == "led":
            led_control(settings["DL"], action)
        elif target == "buzzer":
            buzzer_control(settings["DB"], action)
        else:
            print("Unknown actuator:", target)


if __name__ == "__main__":
    print("Starting PI1 controller")
    settings = load_settings()
    device_config, hardware_config = get_device_config(settings)

    # Each simulator should accept a callback for console printing.

    threads = []
    stop_event = threading.Event()
    for code in device_config.get("sensors", []):
        runner = RUNNERS.get(code)
        if not runner:
            continue
        params = hardware_config.get(code, {"simulated": True})
        runner(params, threads, stop_event, code)

    actuator_thread = threading.Thread(
        target=actuator_console, args=(hardware_config, stop_event), daemon=True
    )
    threads.append(actuator_thread)
    actuator_thread.start()

    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_event.set()

    stop_event.set()
    for thread in threads:
        thread.join(timeout=1)
