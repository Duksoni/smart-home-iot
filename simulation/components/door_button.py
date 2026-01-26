import time
import threading
from mqtt_publisher import build_topic, get_base_topic, get_device_name, get_publisher
from simulators.door_button import run_door_sensor_simulator

def ds1_callback(state, code, simulated):
    t = time.localtime()
    state_str = "OPEN" if state == 1 else "CLOSED"
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Door state: {state_str}")
    publisher = get_publisher()
    if publisher:
        payload = {
            "measurement": "button",
            "value": state,
            "simulated": simulated,
            "device": get_device_name(),
            "code": code,
            "state": state_str,
        }
        topic = build_topic(get_base_topic(), "sensors", code)
        publisher.enqueue_json(topic, payload)

def run_ds1(settings, threads, stop_event, code):
    simulated = settings.get("simulated", True)

    def callback(state, code_value):
        ds1_callback(state, code_value, simulated)

    if settings.get("simulated"):
        print(f"Starting simulated {code}")
        thread = threading.Thread(
            target=run_door_sensor_simulator,
            args=(5, callback, stop_event, code),
            name=f"simulator-{code.lower()}",
            daemon=True
        )
        threads.append(thread)
        thread.start()
    else:
        from sensors.door_button import run_ds_loop, DS
        pin = settings.get("pin")
        print(f"Starting real {code} loop on pin {pin}")
        ds1 = DS(pin)
        thread = threading.Thread(
            target=run_ds_loop,
            args=(ds1, 5, callback, stop_event, code),
            name=f"sensor-{code.lower()}",
            daemon=True
        )
        threads.append(thread)
        thread.start()
        