import threading
import time

from mqtt_publisher import get_publisher


def dpir_callback(code, simulated):
    t = time.localtime()
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print("Motion detected")

    publisher = get_publisher()
    if publisher:
        payload = {
            "measurement": "motion",
            "value": 1,
            "simulated": simulated,
            "device": publisher.device_name,
            "code": code,
        }
        topic = publisher.build_topic("sensors", code)
        publisher.enqueue_json(topic, payload)


def send_motion_event(code: str):
    print(f"[SIM] {code} -> motion")
    dpir_callback( code, True)
    

def run_dpir(settings, threads, stop_event, code):
    simulated = settings.get("simulated", True)

    if simulated:
        print("Simulate motion via console")
    else:
        def callback(code_value):
            dpir_callback(code_value, False)

        from sensors.motion_sensor import DPIR, run_dpir_loop

        pin = settings.get("pin")
        print(f"Starting real {code} loop on pin {pin}")
        dpir = DPIR(pin)
        delay = settings.get("interval", 1.0)

        thread = threading.Thread(
            target=run_dpir_loop,
            args=(dpir, delay, code, callback, stop_event),
            name=f"sensor-{code.lower()}",
            daemon=True,
        )
        threads.append(thread)
        thread.start()
