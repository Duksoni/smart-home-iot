import time
import threading
from mqtt_publisher import build_topic, get_base_topic, get_device_name, get_publisher

from simulators.door_ultrasonic import run_dus_simulator

def dus1_callback(distance, code, simulated):
    t = time.localtime()
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    if distance is None:
        print("Distance: TIMEOUT")
    else:
        print(f"Distance: {distance} cm")

    publisher = get_publisher()
    if publisher:
        payload = {
            "measurement": "ultrasonic",
            "value": distance,
            "simulated": simulated,
            "device": get_device_name(),
            "code": code,
        }
        topic = build_topic(get_base_topic(), "sensors", code)
        publisher.enqueue_json(topic, payload)

def run_dus1(settings, threads, stop_event, code):
    simulated = settings.get("simulated", True)

    def callback(state, code_value):
        dus1_callback(state, code_value, simulated)

    if settings.get("simulated"):
        print(f"Starting simulated {code}")
        thread = threading.Thread(
            target=run_dus_simulator,
            args=(5, callback, stop_event, code),
            name=f"simulator-{code.lower()}",
            daemon=True
        )
        threads.append(thread)
        thread.start()
    else:
        from sensors.door_ultrasonic import run_dus_loop, DUS
        trigger_pin = settings.get("trigger_pin")
        echo_pin = settings.get("echo_pin")
        print(f"Starting real {code} loop on trigger pin {trigger_pin} and on echo pin {echo_pin}")
        dus1 = DUS(trigger_pin, echo_pin)
        thread = threading.Thread(
            target=run_dus_loop,
            args=(dus1, 5, callback, stop_event, code),
            name=f"sensor-{code.lower()}",
            daemon=True
        )
        threads.append(thread)
        thread.start()
