import threading
import time

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

    if settings.get("simulated"):
        print(f"[SIM] DMS -> Key accepted: {key}")
    else:
        print(f"[GPIO] DMS -> Key accepted: {key}")

    if key != "#":
        return

    attempt = consume_current()
    print("Password accepted!" if attempt == _password else "Wrong password! Try again.")


def run_membrane_switch(settings, threads, stop_event, code):
    if settings.get("simulated"):
        print("Control DMS via console or by running it on auto loop")
    else:
        print("Starting DMS loop (GPIO support coming soon)")
        thread = threading.Thread(
            target=run_membrane_switch_gpio_loop,
            args=(settings, stop_event, code),
            name="sensor-dms",
            daemon=True,
        )
        threads.append(thread)
        thread.start()


def run_membrane_switch_gpio_loop(settings, stop_event, code, delay=5):
    pin = settings.get("pin")
    print(f"[GPIO] {code} -> Listening on pin {pin} (not implemented yet)")
    while not stop_event.is_set():
        time.sleep(delay)


def _auto_worker(delay, settings, stop_event):
    run_membrane_switch_simulator(delay, settings, send_key, stop_event)


def start_auto(settings, threads=None, delay=2):
    global _auto_thread, _auto_stop_event
    if _auto_thread and _auto_thread.is_alive():
        print("DMS auto-simulator already running")
        return

    _auto_stop_event = threading.Event()
    _auto_thread = threading.Thread(
        target=_auto_worker, args=(delay, settings, _auto_stop_event), name="simulator-dms-auto", daemon=True
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
        time.sleep(0.15)
