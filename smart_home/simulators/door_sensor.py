import time
import random

DOOR_CLOSED = 0
DOOR_OPEN = 1

def generate_door_states(initial_state=DOOR_CLOSED):
    state = initial_state
    while True:
        if random.random() < 0.3:
            state = DOOR_OPEN if state == DOOR_CLOSED else DOOR_CLOSED
        yield state

def run_door_sensor_simulator(delay, callback, stop_event, code):
    for state in generate_door_states():
        time.sleep(delay)
        callback(state, code)
        if stop_event.is_set():
            break

def door_sensor_console(data_code, description, state):
    print(f"[SIM] {description} ({data_code}) -> {state}")