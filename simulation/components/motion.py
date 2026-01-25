import threading
import time

from mqtt_publisher import build_topic, get_base_topic, get_device_name, get_publisher
from simulators.motion import run_dpir_simulator


def dpir_callback(state, code, simulated):
    t = time.localtime()
    state_str = "MOTION" if state == 1 else "NO_MOTION"
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Motion state: {state_str}")
    publisher = get_publisher()
    if publisher:
        payload = {
            "measurement": "motion",
            "value": state,
            "simulated": simulated,
            "device": get_device_name(),
            "code": code,
            "state": state_str,
        }
        topic = build_topic(get_base_topic(), "sensors", code)
        publisher.enqueue_json(topic, payload)


def run_dpir(settings, threads, stop_event, code):
    simulated = settings.get("simulated", True)

    def callback(state, code_value):
        dpir_callback(state, code_value, simulated)

    if settings.get("simulated"):
        print(f"Starting simulated {code}")
        thread = threading.Thread(
            target=run_dpir_simulator,
            args=(3, callback, stop_event, code),
            name=f"simulator-{code.lower()}",
            daemon=True,
        )
        threads.append(thread)
        thread.start()
    else:
        from sensors.motion_sensor import DPIR

        pin = settings.get("pin")
        print(f"Starting real {code} loop on pin {pin}")
        dpir = DPIR(pin)

        def loop():
            last_state = None
            delay = 1.0  # sampling interval (seconds)
            while not stop_event.is_set():
                state = dpir.read()
                if state != last_state:
                    callback(state, code)
                    last_state = state
                time.sleep(delay)

        thread = threading.Thread(
            target=loop,
            name=f"sensor-{code.lower()}",
            daemon=True,
        )
        threads.append(thread)
        thread.start()
