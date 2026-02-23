import threading

from mqtt_publisher import get_publisher


def _publish(settings, delta: float):
    code = settings.get("code", "GSG")
    simulated = settings.get("simulated", True)

    prefix = "[SIM]" if simulated else "[GPIO]"
    print(f"{prefix} GSG -> delta: {delta:.2f}")

    publisher = get_publisher()
    if not publisher:
        return

    payload = {
        "measurement": "gyroscope",
        "value": delta,
        "simulated": simulated,
        "device": publisher.device_name,
        "code": code,
    }

    topic = publisher.build_topic("sensors", code)
    publisher.enqueue_json(topic, payload)

def send_gyro_event(settings, delta: float):
    """
    Manual injection from console:
        gsg send <delta>
    """
    _publish(settings, delta)


def run_gsg(settings, threads, stop_event, code):
    sensor_code = code or settings.get("code", "GSG")

    def callback(gyro_val):
        _publish(settings, gyro_val)

    if settings.get("simulated", True):
        print(
            f"[SIM] {code} ready — use console:  gsg send <delta>"
        )

    else:
        from sensors.gyro import GSG, run_gsg_loop

        print(f"Starting real {sensor_code} loop")

        gsg = GSG()
        interval = settings.get("interval", 1)

        thread = threading.Thread(
            target=run_gsg_loop,
            args=(gsg, interval, callback, stop_event),
            name=f"sensor-{sensor_code.lower()}",
            daemon=True,
        )
        threads.append(thread)
        thread.start()
