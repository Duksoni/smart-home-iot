import threading
import time

from components.button import press_button, run_btn, run_ds, switch_door_state
from components.dht import run_dht
from components.door_ultrasonic import run_dus, send_distance_event
from components.gsg import run_gsg, send_gyro_event
from components.motion import run_dpir, send_motion_event
from kitchen_timer_coordinator import start_kitchen_timer_coordinator
from mqtt_publisher import init_mqtt_publisher
from settings import get_device_config

RUNNERS = {
    "DS2": run_ds,
    "DUS2": run_dus,
    "DPIR2": run_dpir,
    "BTN": run_btn,
    "DHT3": run_dht,
    "GSG": run_gsg,
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


def _list_commands():
    print("=" * 54)
    print("Commands:")
    print("  gsg send <delta> — publish a gyroscope delta reading")
    print("  btn press — press timer button")
    print("  door open|close")
    print("  dpir trigger")
    print("  dus trigger <distance_cm>")
    print("  exit | quit")
    print("=" * 54)    


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
            _list_commands()
            continue

        parts = cmd.split()

        if len(parts) == 3 and parts[0].lower() == "gsg" and parts[1].lower() == "send":
            try:
                delta = float(parts[2])
                send_gyro_event(_get_hw(hardware_config, "GSG"), delta)
            except ValueError:
                print("delta must be a number, e.g.  gsg send 120.5")
            continue
        if (
            len(parts) == 2
            and parts[0].lower() == "btn"
            and parts[1].lower() == "press"
        ):
            press_button("BTN")
            continue

        if len(parts) == 2 and parts[0].lower() == "door":
            command = parts[1].lower()
            if command not in ("open", "close"):
                print("Invalid door command. Use 'open' or 'close'.")
                continue
            switch_door_state("DS2", command)
            continue

        if len(parts) == 2 and parts[0].lower() == "dpir":
            send_motion_event("DPIR2")
            continue

        if (
            len(parts) == 3
            and parts[0].lower() == "dus"
            and parts[1].lower() == "trigger"
        ):
            try:
                distance = float(parts[2])
                send_distance_event("DUS2", distance)
            except ValueError:
                print("Invalid distance value. Must be a number.")
            continue

        print("Unknown command. Type 'help'.")


def run(settings):
    device_config, hardware_config = get_device_config(settings, device="PI2")
    for code, params in hardware_config.items():
        if isinstance(params, dict):
            params.setdefault("code", code)

    _list_commands()

    publisher = init_mqtt_publisher(settings)

    threads = []
    stop_event = threading.Event()

    broker_settings = settings.get("mqtt")

    kitchen_timer_coordinator, kitchen_timer_subscriber = (
        start_kitchen_timer_coordinator(broker_settings, hardware_config)
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

    publisher.stop()
    kitchen_timer_subscriber.stop()
    kitchen_timer_coordinator.stop()

    stop_event.set()
    for t in threads:
        t.join(timeout=1)

    try:
        import RPi.GPIO as GPIO

        GPIO.cleanup()
    except ImportError:
        pass
