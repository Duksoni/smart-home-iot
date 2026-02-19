import time
import threading

from mqtt_publisher import get_publisher
from simulators.door_ultrasonic import run_dus_simulator


def dus_callback(distance, code, simulated):
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
            "device": publisher.device_name,
            "code": code,
        }
        topic = publisher.build_topic("sensors", code)
        publisher.enqueue_json(topic, payload)


def run_dus(settings, threads, stop_event, code):
    """Generic ultrasonic runner — works for DUS1 and DUS2."""
    simulated = settings.get("simulated", True)
    interval = settings.get("interval", 5)

    def callback(distance, code_value):
        dus_callback(distance, code_value, simulated)

    if simulated:
        print(f"Starting simulated {code}")
        sim_cfg = settings.get("simulator", {})
        thread = threading.Thread(
            target=run_dus_simulator,
            args=(
                interval,
                callback,
                stop_event,
                code,
                sim_cfg.get("initial_distance", 80.0),
                sim_cfg.get("min_distance", 2.0),
                sim_cfg.get("max_distance", 120.0),
            ),
            name=f"simulator-{code.lower()}",
            daemon=True,
        )
        threads.append(thread)
        thread.start()
    else:
        from sensors.door_ultrasonic import run_dus_loop, DUS
        trigger_pin = settings.get("trigger_pin")
        echo_pin = settings.get("echo_pin")
        print(f"Starting real {code} loop on trigger={trigger_pin} echo={echo_pin}")
        dus = DUS(trigger_pin, echo_pin)
        thread = threading.Thread(
            target=run_dus_loop,
            args=(dus, interval, callback, stop_event, code),
            name=f"sensor-{code.lower()}",
            daemon=True,
        )
        threads.append(thread)
        thread.start()


# Keep old name as alias
run_dus1 = run_dus
