import random
import time


def generate_motion_events():
    while True:
        quiet_len = random.randint(3, 10)
        for _ in range(quiet_len):
            yield 0
        burst_len = random.randint(2, 6)
        for _ in range(burst_len):
            yield 1


def run_dpir_simulator(delay, callback, stop_event, code):
    for state in generate_motion_events():
        time.sleep(delay)
        callback(state, code)
        if stop_event.is_set():
            break
