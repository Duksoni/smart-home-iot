import threading
import time

from mqtt_publisher import get_publisher
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
            "device": publisher.device_name,
            "code": code,
            "state": state_str,
        }
        topic = publisher.build_topic("sensors", code)
        publisher.enqueue_json(topic, payload)


def run_dpir(settings, threads, stop_event, code):
    """Generic PIR runner — works for DPIR1, DPIR2, DPIR3."""
    simulated = settings.get("simulated", True)

    def callback(state, code_value):
        dpir_callback(state, code_value, simulated)

    if simulated:
        print(f"Starting simulated {code}")
        interval = settings.get("interval", 3)
        sim_cfg = settings.get("simulator", {})
        quiet_range = sim_cfg.get("quiet_range") or (3, 10)
        burst_range = sim_cfg.get("burst_range") or (2, 6)
        thread = threading.Thread(
            target=run_dpir_simulator,
            args=(interval, callback, stop_event, code, quiet_range, burst_range),
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
        delay = settings.get("interval", 1.0)

        def loop():
            last_state = None
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
