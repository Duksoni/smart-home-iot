import threading
import time

from door_coordinator import update_attempt, update_key
from mqtt_publisher import get_publisher
from simulators.membrane_switch import run_membrane_switch_simulator

_valid_keys = [str(i) for i in range(10)] + ["#"]
_password = "5279"
_current_attempt = []
_auto_thread = None
_auto_stop_event = None


def set_password(new_password):
    global _password
    _password = new_password


def consume_current():
    global _current_attempt
    attempted_password = "".join(_current_attempt)[:-1]
    _current_attempt = []
    return attempted_password


def send_key(settings, key):
    global _current_attempt, _valid_keys
    if key not in _valid_keys:
        print(f"Invalid key: {key}")
        _current_attempt = []
        return
    _current_attempt.append(key)
    code = settings.get("code", "DMS")
    update_key(code, key)

    if settings.get("simulated"):
        print(f"[SIM] DMS -> Key accepted: {key}")
    else:
        print(f"[GPIO] DMS -> Key accepted: {key}")

    publisher = get_publisher()
    if publisher:
        key_value = 10 if key == "#" else int(key)
        key_payload = {
            "measurement": "membrane_key",
            "value": key_value,
            "key": key,
            "simulated": settings.get("simulated", True),
            "device": publisher.device_name,
            "code": code,
        }
        key_topic = publisher.build_topic("sensors", code)
        publisher.enqueue_json(key_topic, key_payload)

    if key != "#":
        return

    attempt = consume_current()
    success = attempt == _password
    print("Password accepted!" if success else "Wrong password! Try again.")
    update_attempt(code, success)
    if publisher:
        attempt_payload = {
            "measurement": "membrane_attempt",
            "value": 1 if success else 0,
            "simulated": settings.get("simulated", True),
            "device": publisher.device_name,
            "code": code,
        }
        attempt_topic = publisher.build_topic("sensors", code)
        publisher.enqueue_json(attempt_topic, attempt_payload)


def run_membrane_switch(settings, threads, stop_event, code):
    if settings.get("password"):
        set_password(settings["password"])
    if settings.get("simulated"):
        print("Control DMS via console or by running it on auto loop")
    else:
        print("Starting DMS loop on GPIO")
        thread = threading.Thread(
            target=run_membrane_switch_gpio_loop,
            args=(settings, stop_event, code),
            name="sensor-dms",
            daemon=True,
        )
        threads.append(thread)
        thread.start()


def run_membrane_switch_gpio_loop(settings, stop_event, code, delay=0.1):
    from sensors.door_membrane_switch import DMS, run_dms_loop

    row_pins = settings.get("row_pins") or settings.get("rows")
    col_pins = settings.get("col_pins") or settings.get("cols")
    keymap = settings.get("keymap")
    debounce = settings.get("debounce", 0.15)
    settle = settings.get("settle", 0.001)
    interval = settings.get("interval", delay)

    if row_pins and col_pins:
        print(f"[GPIO] {code} -> Rows: {row_pins} Cols: {col_pins}")
    else:
        print(f"[GPIO] {code} -> Using default keypad pinout")

    dms = DMS(
        row_pins=row_pins,
        col_pins=col_pins,
        keymap=keymap,
        debounce=debounce,
        settle=settle,
    )

    def callback(key, _code):
        send_key(settings, key)

    run_dms_loop(dms, interval, callback, stop_event, code)


def _auto_worker(delay, settings, stop_event):
    run_membrane_switch_simulator(delay, settings, send_key, stop_event)


def start_auto(settings, threads=None, delay=2):
    global _auto_thread, _auto_stop_event
    if _auto_thread and _auto_thread.is_alive():
        print("DMS auto-simulator already running")
        return

    _auto_stop_event = threading.Event()
    auto_delay = settings.get("auto_delay", delay)
    _auto_thread = threading.Thread(
        target=_auto_worker,
        args=(auto_delay, settings, _auto_stop_event),
        name="simulator-dms-auto",
        daemon=True,
    )
    if threads is not None:
        threads.append(_auto_thread)
    _auto_thread.start()
    print("DMS auto-simulator started")


def stop_auto():
    global _auto_thread, _auto_stop_event
    if not _auto_thread:
        print("DMS auto-simulator is not running")
        return
    _auto_stop_event.set()
    _auto_thread.join(timeout=1)
    _auto_thread = None
    _auto_stop_event = None
    print("DMS auto-simulator stopped")


def send_sequence(settings, sequence):
    if not sequence:
        print("Empty sequence")
        return
    seq = sequence.strip()
    if not seq.endswith("#"):
        seq = seq + "#"

    for ch in seq:
        if ch not in _valid_keys:
            print(f"Invalid character in sequence: {ch}")
            return

    for ch in seq:
        send_key(settings, ch)
        time.sleep(settings.get("key_delay", 0.15))
