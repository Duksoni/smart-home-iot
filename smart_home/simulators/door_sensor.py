import time


def run_door_sensor_simulator(interval, callback, stop_event):
    state = False
    while not stop_event.is_set():
        state = not state
        callback("DS1", "Open" if state else "Closed", state)
        time.sleep(interval)

def door_sensor_console(data_code, description, state):
    print(f"[SIM] {description} ({data_code}) -> {state}")