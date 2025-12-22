import random
import time

DIGITS = [str(i) for i in range(10)]
VALID_KEYS = DIGITS + ["#"]


def generate_key_stream():
    while True:
        for _ in range(4):
            yield random.choice(DIGITS)
        yield "#"


def run_membrane_switch_simulator(delay, settings, callback, stop_event):
    for key in generate_key_stream():
        if stop_event.is_set():
            break
        time.sleep(delay)
        callback(settings, key)
