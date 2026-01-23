from simulators.dht import run_dht_simulator
import threading
import time

def dht_callback(humidity, temperature, code):
    t = time.localtime()
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Humidity: {humidity:.1f}%")
    print(f"Temperature: {temperature:.1f}°C")

def run_dht(settings, threads, stop_event, code):
    if settings["simulated"]:
        print("Starting simulated DHT1")
        thread = threading.Thread(
            target=run_dht_simulator,
            args=(5, dht_callback, stop_event, code),
            name="simulator-dht",
            daemon=True,
        )
        threads.append(thread)
        thread.start()
    else:
        from simulation.sensors.dht import run_dht_loop, DHT
        print("Starting real DHT1 loop")
        dht = DHT(settings["pin"])
        thread = threading.Thread(
            target=run_dht_loop,
            args=(dht, 5, dht_callback, stop_event, code),
            name="sensor-dht",
            daemon=True,
        )
        threads.append(thread)
        thread.start()
