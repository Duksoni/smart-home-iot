import threading
import time

from mqtt_publisher import get_publisher


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


def send_distance_event(code: str, distance: float):
    print(f"[SIM] {code} distance -> {distance}cm")
    dus_callback(distance, code, True)


def run_dus(settings, threads, stop_event, code):
    simulated = settings.get("simulated", True)
    interval = settings.get("interval", 5)

    if simulated:
        print("Simulate distance via console")
    else:
        from sensors.door_ultrasonic import DUS, run_dus_loop

        def callback(distance, code_value):
            dus_callback(distance, code_value, simulated)

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
