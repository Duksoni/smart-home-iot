import random
import time


def generate_distance(initial_distance=100, min_distance=2, max_distance=400, step=5):
    distance = initial_distance
    while True:
        distance += random.randint(-step, step)
        if distance < min_distance:
            distance = min_distance
        if distance > max_distance:
            distance = max_distance
        yield distance


def run_dus_simulator(
    delay,
    callback,
    stop_event,
    code,
    initial_distance=100,
    min_distance=2,
    max_distance=400,
    step=5,
):
    for distance in generate_distance(initial_distance, min_distance, max_distance, step):
        time.sleep(delay)
        callback(distance, code)
        if stop_event.is_set():
            break
