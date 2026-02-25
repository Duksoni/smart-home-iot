import random
import time


def generate_values(initial_temp=25.0, initial_humidity=20.0, step=1):
    temperature = initial_temp
    humidity = initial_humidity
    while True:
        temperature = float(temperature + random.randint(-step, step))
        humidity = float(humidity + random.randint(-step, step))
        if humidity < 0.0:
            humidity = 0.0
        if humidity > 100.0:
            humidity = 100.0
        yield humidity, temperature


def run_dht_simulator(delay, callback, stop_event, code, initial_temp=25, initial_humidity=20, step=1):
    for h, t in generate_values(initial_temp, initial_humidity, step):
        time.sleep(delay)  # Delay between readings (adjust as needed)
        callback(h, t, code)
        if stop_event.is_set():
            break
