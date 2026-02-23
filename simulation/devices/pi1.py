import threading
import time

from buzzer_coordinator import start_buzzer_coordinator
from components.button import run_ds, switch_door_state
from components.buzzer import buzzer_control
from components.door_ultrasonic import run_dus, send_distance_event
from components.led import led_control
from components.membrane_switch import run_membrane_switch, send_sequence
from components.motion import run_dpir, send_motion_event
from led_coordinator import start_led_coordinator
from mqtt_publisher import init_mqtt_publisher
from settings import get_device_config

RUNNERS = {
    "DS1": run_ds,
    "DUS1": run_dus,
    "DPIR1": run_dpir,
    "DMS": run_membrane_switch,
}


def _get_hw(hardware_config, code):
    params = dict(hardware_config.get(code, {"simulated": True}))
    params.setdefault("code", code)
    return params


def _start_sensors(device_config, hardware_config, threads, stop_event):
    for code in device_config.get("sensors", []):
        runner = RUNNERS.get(code)
        if not runner:
            print(f"[PI1] No runner for sensor {code}, skipping.")
            continue
        runner(_get_hw(hardware_config, code), threads, stop_event, code)


def _list_commands():
    print("=" * 32)
    print("Commands:")
    print("  led on|off")
    print("  buzzer short|long|start|stop")
    print("  door open|close")
    print("  dpir trigger")
    print("  dus trigger float<distance_cm>")
    print("  dms send <4 digits>")
    print("  exit | quit")
    print("=" * 32)


def _console_thread(hardware_config, stop_event):
    print("PI1 console ready. Type 'help' for commands.")
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
            _list_commands()
            continue

        parts = cmd.split()

        if len(parts) == 2 and parts[0].lower() == "led":
            led_control(_get_hw(hardware_config, "DL"), parts[1].lower())
            continue

        if len(parts) == 2 and parts[0].lower() == "buzzer":
            buzzer_control(_get_hw(hardware_config, "DB"), parts[1].lower())
            continue

        if len(parts) == 2 and parts[0].lower() == "door":
            command = parts[1].lower()
            if command not in ("open", "close"):
                print("Invalid door command. Use 'open' or 'close'.")
                continue
            switch_door_state("DS1", command)
            continue

        if (
            len(parts) == 2
            and parts[0].lower() == "dpir"
            and parts[1].lower() == "trigger"
        ):
            send_motion_event("DPIR1")
            continue

        if (
            len(parts) == 3
            and parts[0].lower() == "dus"
            and parts[1].lower() == "trigger"
        ):
            try:
                distance = float(parts[2])
                send_distance_event("DUS1", distance)
            except ValueError:
                print("Invalid distance value. Must be a number.")
            continue

        if parts[0].lower() == "dms":
            if len(parts) == 3 and parts[1].lower() == "send":
                send_sequence(_get_hw(hardware_config, "DMS"), parts[2])
                continue

        print("Unknown command. Type 'help'.")


def run(settings):
    device_config, hardware_config = get_device_config(settings, device="PI1")
    for code, params in hardware_config.items():
        if isinstance(params, dict):
            params.setdefault("code", code)

    _list_commands()

    broker_settings = settings.get("mqtt")
    publisher = init_mqtt_publisher(settings)

    threads = []
    stop_event = threading.Event()

    dl_subscriber = start_led_coordinator(broker_settings, hardware_config, "DL")
    buzzer_coordinator, db_subscriber = start_buzzer_coordinator(
        broker_settings, hardware_config, "DB"
    )

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
    dl_subscriber.stop()
    db_subscriber.stop()
    buzzer_coordinator.stop()

    for t in threads:
        t.join(timeout=1)

    try:
        import RPi.GPIO as GPIO

        GPIO.cleanup()
    except ImportError:
        pass
