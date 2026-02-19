"""
Membrane switch (DMS) component.

Responsibilities on the PI side:
- Accept key presses (real GPIO or simulator/console)
- Accumulate digits until '#' is received
- Publish each key press as  measurement=membrane_key
- Publish the PIN attempt result as  measurement=membrane_attempt  (value=1/0)

All alarm logic (arming, disarming, triggering) lives on the SERVER, which
reacts to the membrane_attempt messages it receives over MQTT.
"""

import threading
import time

from mqtt_publisher import get_publisher
from simulators.membrane_switch import run_membrane_switch_simulator

_valid_keys = [str(i) for i in range(10)] + ["#"]
_password = "5279"
_current_attempt: list[str] = []
_auto_thread = None
_auto_stop_event = None


def set_password(new_password: str) -> None:
    global _password
    _password = new_password


def _consume_current() -> str:
    global _current_attempt
    attempted = "".join(_current_attempt)[:-1]  # strip the trailing '#'
    _current_attempt = []
    return attempted


def send_key(settings, key: str) -> None:
    global _current_attempt
    if key not in _valid_keys:
        print(f"Invalid key: {key!r}")
        _current_attempt = []
        return

    _current_attempt.append(key)
    code = settings.get("code", "DMS")
    simulated = settings.get("simulated", True)
    prefix = "[SIM]" if simulated else "[GPIO]"
    print(f"{prefix} DMS -> Key accepted: {key}")

    publisher = get_publisher()
    if publisher:
        key_value = 10 if key == "#" else int(key)
        publisher.enqueue_json(
            publisher.build_topic("sensors", code),
            {
                "measurement": "membrane_key",
                "value": key_value,
                "key": key,
                "simulated": simulated,
                "device": publisher.device_name,
                "code": code,
            },
        )

    if key != "#":
        return

    # Full sequence received — evaluate attempt
    attempt = _consume_current()
    success = attempt == _password
    print("Password accepted!" if success else "Wrong password! Try again.")

    if publisher:
        publisher.enqueue_json(
            publisher.build_topic("sensors", code),
            {
                "measurement": "membrane_attempt",
                "value": 1 if success else 0,
                "simulated": simulated,
                "device": publisher.device_name,
                "code": code,
            },
        )


def run_membrane_switch(settings, threads, stop_event, code):
    if settings.get("pin_code"):
        set_password(settings["pin_code"])

    if settings.get("simulated"):
        print("Control DMS via console or by running it on auto loop")
    else:
        print("Starting DMS loop on GPIO")
        thread = threading.Thread(
            target=_run_gpio_loop,
            args=(settings, stop_event, code),
            name="sensor-dms",
            daemon=True,
        )
        threads.append(thread)
        thread.start()


def _run_gpio_loop(settings, stop_event, code, delay=0.1):
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


def start_auto(settings, threads=None, delay=2) -> None:
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


def stop_auto() -> None:
    global _auto_thread, _auto_stop_event
    if not _auto_thread:
        print("DMS auto-simulator is not running")
        return
    _auto_stop_event.set()
    _auto_thread.join(timeout=1)
    _auto_thread = None
    _auto_stop_event = None
    print("DMS auto-simulator stopped")


def send_sequence(settings, sequence: str) -> None:
    seq = sequence.strip()
    if not seq.endswith("#"):
        seq += "#"
    for ch in seq:
        if ch not in _valid_keys:
            print(f"Invalid character in sequence: {ch!r}")
            return
    for ch in seq:
        send_key(settings, ch)
        time.sleep(settings.get("key_delay", 0.15))
