import random
import time


def generate_motion_events(quiet_range=(3, 10), burst_range=(2, 6)):
    while True:
        quiet_len = random.randint(quiet_range[0], quiet_range[1])
        for _ in range(quiet_len):
            yield 0
        burst_len = random.randint(burst_range[0], burst_range[1])
        for _ in range(burst_len):
            yield 1


def run_dpir_simulator(delay, callback, stop_event, code, quiet_range=(3, 10), burst_range=(2, 6)):
    for state in generate_motion_events(quiet_range, burst_range):
        time.sleep(delay)
        callback(state, code)
        if stop_event.is_set():
            break
