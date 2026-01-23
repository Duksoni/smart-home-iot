import time
import threading
from simulators.door_button import run_door_sensor_simulator

def ds1_callback(state, code):
    t = time.localtime()
    state_str = "OPEN" if state == 1 else "CLOSED"
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Door state: {state_str}")

def run_ds1(settings, threads, stop_event, code):
    if settings["simulated"]:
        print("Starting simulated DS1")
        thread = threading.Thread(
            target=run_door_sensor_simulator,
            args=(5, ds1_callback, stop_event, code),
            name="simulator-ds1",
            daemon=True
        )
        threads.append(thread)
        thread.start()
    else:
        from sensors.door_button import run_ds_loop, DS
        print("Starting real DS1 loop")
        ds1 = DS(settings["pin"])
        thread = threading.Thread(
            target=run_ds_loop,
            args=(ds1, 5, ds1_callback, stop_event, code),
            name="sensor-ds1",
            daemon=True
        )
        threads.append(thread)
        thread.start()
        