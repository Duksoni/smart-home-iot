import threading
import time

from components.buzzer import buzzer_control
from components.motion import run_dpir
from components.door_ultrasonic import run_ds1
from components.led import led_control
from components.membrane_switch import (
    run_membrane_switch,
    send_sequence,
    start_auto,
    stop_auto,
)
from settings import get_device_config, load_settings

RUNNERS = {
    # "DHT1": run_dht,
    "DS1": run_ds1,
    "DMS": run_membrane_switch,
    "DPIR1": run_dpir,
    # ...
}


def console_thread(settings, stop_event):
    print("Type 'help' for commands, 'exit' or 'quit' to quit.")
    while not stop_event.is_set():
        try:
            cmd = input("> ").strip()
        except EOFError:
            print("Keyboard interrupt, exiting...")
            stop_event.set()
            break

        if not cmd:
            continue

        lower = cmd.lower()
        if lower in {"exit", "quit"}:
            stop_event.set()
            break
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
                led_control(settings["DL"], action)
            elif target == "buzzer":
                buzzer_control(settings["DB"], action)
            continue

        if parts[0].lower() == "dms":
            if len(parts) >= 2 and parts[1].lower() == "auto":
                # toggle auto simulator
                if len(parts) == 3 and parts[2].lower() in {"on", "off"}:
                    if parts[2].lower() == "on":
                        start_auto(settings["DMS"], threads=None, delay=2)
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

                send_sequence(settings["DMS"], seq)
                continue

        print("Unknown command, type 'help' to see the available commands.")


if __name__ == "__main__":
    print("Starting PI1 controller")
    settings = load_settings()
    device_config, hardware_config = get_device_config(settings)

    threads = []
    stop_event = threading.Event()
    for code in device_config.get("sensors", []):
        runner = RUNNERS.get(code)
        if not runner:
            continue
        params = hardware_config.get(code, {"simulated": True})
        runner(params, threads, stop_event, code)

    console_t = threading.Thread(
        target=console_thread, args=(hardware_config, stop_event), daemon=True
    )
    threads.append(console_t)
    console_t.start()

    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_event.set()

    stop_event.set()
    for thread in threads:
        thread.join(timeout=1)
