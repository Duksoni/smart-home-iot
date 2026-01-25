import threading
import time

from mqtt_publisher import build_topic, get_base_topic, get_device_name, get_publisher
from simulators.dht import run_dht_simulator


def dht_callback(humidity, temperature, status, dht_settings, code, verbose=False):
    if verbose:
        t = time.localtime()
        print("=" * 20)
        print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print(f"Status: {status}")
        print(f"Humidity: {humidity}%")
        print(f"Temperature: {temperature}°C")

    publisher = get_publisher()
    if not publisher:
        return

    topic = build_topic(get_base_topic(), "sensors", code)
    base_payload = {
        "simulated": dht_settings.get("simulated", True),
        "device": get_device_name(),
        "code": code,
    }
    temp_payload = {
        "measurement": "Temperature",
        "value": temperature,
        **base_payload,
    }
    humidity_payload = {
        "measurement": "Humidity",
        "value": humidity,
        **base_payload,
    }
    publisher.enqueue_json(topic, temp_payload)
    publisher.enqueue_json(topic, humidity_payload)


def run_dht(settings, threads, stop_event, code):
    sensor_code = code or settings.get("code", "DHT1")

    def callback(humidity, temperature, status):
        dht_callback(humidity, temperature, status, settings, sensor_code)

    if settings.get("simulated", True):
        print(f"Starting simulated {sensor_code}")
        thread = threading.Thread(
            target=run_dht_simulator,
            args=(2, callback, stop_event, "DHTLIB_OK"),
            name=f"simulator-{sensor_code.lower()}",
            daemon=True,
        )
        threads.append(thread)
        thread.start()
    else:
        from sensors.dht import DHT, run_dht_loop

        print(f"Starting real {sensor_code} loop")
        dht = DHT(settings["pin"])
        thread = threading.Thread(
            target=run_dht_loop,
            args=(dht, 2, callback, stop_event),
            name=f"sensor-{sensor_code.lower()}",
            daemon=True,
        )
        threads.append(thread)
        thread.start()
