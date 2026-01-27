import time
import random

DOOR_CLOSED = 0
DOOR_OPEN = 1


def generate_door_states(initial_state=DOOR_CLOSED, toggle_probability=0.3):
    state = initial_state
    while True:
        if random.random() < toggle_probability:
            state = DOOR_OPEN if state == DOOR_CLOSED else DOOR_CLOSED
        yield state


def run_door_sensor_simulator(
    delay,
    callback,
    stop_event,
    code,
    toggle_probability=0.3,
    initial_state=DOOR_CLOSED,
):
    for state in generate_door_states(initial_state, toggle_probability):
        time.sleep(delay)
        callback(state, code)
        if stop_event.is_set():
            break
