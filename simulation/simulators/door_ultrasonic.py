import math
import random
import time


def generate_distance(initial_distance=80.0, min_distance=2.0, max_distance=120.0, step = 5):
    distance = float(initial_distance)
    while True:
        distance += float(random.randint(-step, step))
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
    initial_distance=0.0,
    min_distance=2.0,
    max_distance=120.0,
):
    for distance in generate_distance(initial_distance, min_distance, max_distance):
        time.sleep(delay)
        callback(distance, code)
        if stop_event.is_set():
            break
