import threading
import time

from mqtt_publisher import get_publisher

_valid_keys = [str(i) for i in range(10)] + ["#"]
_current_attempt: list[str] = []


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

    if key != "#":
        return

    # Full sequence received — evaluate attempt
    attempt = _consume_current()
    print(f"Sending DMS attempt: {attempt!r}")

    publisher = get_publisher()
    if publisher:
        publisher.enqueue_json(
            publisher.build_topic("sensors", code),
            {
                "measurement": "membrane_attempt",
                "value": 1,
                "simulated": simulated,
                "device": publisher.device_name,
                "code": code,
            },
        )


def run_membrane_switch(settings, threads, stop_event, code):
    if settings.get("simulated"):
        print("Control DMS via console")
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
