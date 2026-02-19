import time
import threading

from mqtt_publisher import get_publisher
from simulators.door_button import run_door_sensor_simulator


def ds_callback(state, code, simulated):
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
            "device": publisher.device_name,
            "code": code,
            "state": state_str,
        }
        topic = publisher.build_topic("sensors", code)
        publisher.enqueue_json(topic, payload)


def run_ds(settings, threads, stop_event, code):
    """Generic door-button runner — works for DS1 and DS2."""
    simulated = settings.get("simulated", True)
    interval = settings.get("interval", 5)

    def callback(state, code_value):
        ds_callback(state, code_value, simulated)

    if simulated:
        print(f"Starting simulated {code}")
        sim_cfg = settings.get("simulator", {})
        thread = threading.Thread(
            target=run_door_sensor_simulator,
            args=(
                interval,
                callback,
                stop_event,
                code,
                sim_cfg.get("toggle_probability", 0.3),
                sim_cfg.get("initial_state", 0),
            ),
            name=f"simulator-{code.lower()}",
            daemon=True,
        )
        threads.append(thread)
        thread.start()
    else:
        from sensors.door_button import run_ds_loop, DS
        pin = settings.get("pin")
        debounce = settings.get("debounce_ms", 100)
        print(f"Starting real {code} loop on pin {pin}")
        ds = DS(pin, debounce)
        thread = threading.Thread(
            target=run_ds_loop,
            args=(ds, interval, callback, stop_event, code),
            name=f"sensor-{code.lower()}",
            daemon=True,
        )
        threads.append(thread)
        thread.start()


# Keep old name as alias so existing imports in pi1.py keep working
run_ds1 = run_ds
