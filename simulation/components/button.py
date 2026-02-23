import threading
import time

from mqtt_publisher import get_publisher


def ds_callback(state, code, simulated):
    t = time.localtime()
    state_str = "OPEN" if state == 1 else "CLOSED"
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Door state: {state_str}")

    publisher = get_publisher()
    if publisher:
        payload = {
            "measurement": "button",
            "value": state,
            "simulated": simulated,
            "device": publisher.device_name,
            "code": code,
            "state": state_str,
        }
        topic = publisher.build_topic("sensors", code)
        publisher.enqueue_json(topic, payload)


def btn_callback(state, code, simulated):
    t = time.localtime()
    if state == 1:
        return  # Only log releases
    state_str = "PRESSED"
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Button state: {state_str}")

    publisher = get_publisher()
    if publisher:
        payload = {
            "measurement": "timer_event",
            "value": state,
            "simulated": simulated,
            "device": publisher.device_name,
            "code": code,
            "state": state_str,
        }
        topic = publisher.build_topic("sensors", code)
        publisher.enqueue_json(topic, payload)


def press_button(code):
    print("[SIM] BTN button -> pressed")
    btn_callback(0, code, True)


def switch_door_state(code, new_state: str):
    print(f"[SIM] {code} door state change -> {new_state}")
    ds_callback(1 if new_state.lower() == "open" else 0, code, True)


def run_btn(settings, threads, stop_event, code):
    simulated = settings.get("simulated", True)

    if simulated:
        print("Simulate door opening and closing via console")
    else:
        from sensors.button import BTN, run_button_loop

        interval = settings.get("interval")

        def callback(state, code_value):
            btn_callback(state, code_value, simulated)

        pin = settings.get("pin")
        debounce = settings.get("debounce_ms", 100)
        print(f"Starting real {code} loop on pin {pin}")
        ds = BTN(pin, debounce)
        thread = threading.Thread(
            target=run_button_loop,
            args=(ds, interval, callback, stop_event, code),
            name=f"sensor-{code.lower()}",
            daemon=True,
        )
        threads.append(thread)
        thread.start()


def run_ds(settings, threads, stop_event, code):
    simulated = settings.get("simulated", True)
    interval = settings.get("interval", 5)

    def callback(state, code_value):
        ds_callback(state, code_value, simulated)

    if simulated:
        print("Simulate door state change via console")
    else:
        from sensors.button import BTN, run_button_loop

        pin = settings.get("pin")
        debounce = settings.get("debounce_ms", 100)
        print(f"Starting real {code} loop on pin {pin}")
        ds = BTN(pin, debounce)
        thread = threading.Thread(
            target=run_button_loop,
            args=(ds, interval, callback, stop_event, code),
            name=f"sensor-{code.lower()}",
            daemon=True,
        )
        threads.append(thread)
        thread.start()
