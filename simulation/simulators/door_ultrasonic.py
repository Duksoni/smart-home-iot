import random
import time

def generate_distance(initial_distance=100):
    distance = initial_distance
    while True:
        distance += random.randint(-5, 5)
        if distance < 2: distance = 2
        if distance > 400: distance = 400
        yield distance

def run_dus_simulator(delay, callback, stop_event, code):
    for distance in generate_distance():
        time.sleep(delay)
        callback(distance, code)
        if stop_event.is_set():
            break