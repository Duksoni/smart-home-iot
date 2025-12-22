import time
import threading
from simulators.door_ultrasonic import run_dus_simulator

def dus1_callback(distance, code):
    t = time.localtime()
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    if distance is None:
        print("Distance: TIMEOUT")
    else:
        print(f"Distance: {distance} cm")

def run_dus1(settings, threads, stop_event, code):
    if settings["simulated"]:
        print("Starting simulated DUS1")
        thread = threading.Thread(
            target=run_dus_simulator,
            args=(5, dus1_callback, stop_event, code),
            name="simulator-dus1",
            daemon=True
        )
        threads.append(thread)
        thread.start()
    else:
        from sensors.door_ultrasonic import run_dus_loop, DUS
        print("Starting real DUS1 loop")
        dus1 = DUS(settings["trigger_pin"], settings["echo_pin"])
        thread = threading.Thread(
            target=run_dus_loop,
            args=(dus1, 5, dus1_callback, stop_event, code),
            name="sensor-dus1",
            daemon=True
        )
        threads.append(thread)
        thread.start()
