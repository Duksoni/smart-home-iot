import threading
import time

from buzzer_coordinator import start_buzzer_coordinator
from components.door_button import run_ds
from components.door_ultrasonic import run_dus
from components.led import led_control
from components.buzzer import buzzer_control
from components.membrane_switch import (
    run_membrane_switch,
    send_sequence,
    start_auto,
    stop_auto,
)
from components.motion import run_dpir
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
            print("Commands:")
            print("  led on|off")
            print("  buzzer short|long|start|stop")
            print("  dms auto on|off")
            print("  dms send <4 digits>")
            print("  exit | quit")
            continue

        parts = cmd.split()

        if len(parts) == 2 and parts[0].lower() == "led":
            led_control(_get_hw(hardware_config, "DL"), parts[1].lower())
            continue

        if len(parts) == 2 and parts[0].lower() == "buzzer":
            buzzer_control(_get_hw(hardware_config, "DB"), parts[1].lower())
            continue

        if parts[0].lower() == "dms":
            if len(parts) == 3 and parts[1].lower() == "auto":
                if parts[2].lower() == "on":
                    start_auto(_get_hw(hardware_config, "DMS"), threads=None)
                elif parts[2].lower() == "off":
                    stop_auto()
                else:
                    print("Usage: dms auto on|off")
                continue

            if len(parts) == 3 and parts[1].lower() == "send":
                send_sequence(_get_hw(hardware_config, "DMS"), parts[2])
                continue

        print("Unknown command. Type 'help'.")


def run(settings):
    device_config, hardware_config = get_device_config(settings, device="PI1")
    for code, params in hardware_config.items():
        if isinstance(params, dict):
            params.setdefault("code", code)

    broker_settings = settings.get("mqtt")
    publisher = init_mqtt_publisher(settings)

    threads = []
    stop_event = threading.Event()

    # ── Actuator coordinators (subscribe to server commands) ──────────────────
    dl_subscriber = start_led_coordinator(broker_settings, hardware_config, "DL")
    buzzer_coordinator, db_subscriber = start_buzzer_coordinator(
        broker_settings, hardware_config, "DB"
    )

    # ── Sensor threads (publish readings) ─────────────────────────────────────
    _start_sensors(device_config, hardware_config, threads, stop_event)

    # ── Console ───────────────────────────────────────────────────────────────
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
