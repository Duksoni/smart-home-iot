import threading
import time

from simulators.motion import run_dpir_simulator


def dpir_callback(state, code):
    t = time.localtime()
    state_str = "MOTION" if state == 1 else "NO_MOTION"
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Motion state: {state_str}")


def run_dpir(settings, threads, stop_event, code):
    if settings.get("simulated"):
        print(f"Starting simulated {code}")
        thread = threading.Thread(
            target=run_dpir_simulator,
            args=(3, dpir_callback, stop_event, code),
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
                    dpir_callback(state, code)
                    last_state = state
                time.sleep(delay)
        thread = threading.Thread(
            target=loop,
            name=f"sensor-{code.lower()}",
            daemon=True,
        )
        threads.append(thread)
        thread.start()