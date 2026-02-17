import threading

from .rgb_led import actions as rgb_led_actions

from mqtt_publisher import get_publisher

_actions = {str(i): action for i, action in enumerate(rgb_led_actions)}


def send_key(settings, key):
    global _actions
    if key not in _actions.keys():
        print(f"Invalid key: {key}")
        return
    action = _actions.get(key)
    code = "IR"
    simulated = settings.get("simulated")
    prefix = "[SIM]" if simulated else "[GPIO]"
    print(f"{prefix} IR -> Key pressed: {key}, RGB LED Action: {action}")

    publisher = get_publisher()
    if publisher:
        key_payload = {
            "measurement": "ir_receiver",
            "value": key,
            "simulated": simulated,
            "device": publisher.device_name,
            "code": code,
        }
        key_topic = publisher.build_topic("sensors", code)

        publisher.enqueue_json(key_topic, key_payload)

        # Publish command to RGB LED coordinator
        rgb_led_code = settings.get("rgb_led_code")
        action_payload = {
            "action": action,
            "source": "ir_receiver",
            "simulated": simulated,
            "device": publisher.device_name,
            "code": rgb_led_code, # Use the RGB LED's code here
        }
        # The command topic for the RGB LED coordinator
        action_topic = publisher.build_topic("commands", rgb_led_code)
        publisher.enqueue_json(action_topic, action_payload)
        print(f"{prefix} IR -> Published RGB LED command '{action}' to topic: {action_topic}")


def run_ir_receiver(settings, threads, stop_event, code):
    if settings.get("simulated"):
        print("Control IR remote via console")
    else:
        print("Starting IR loop on GPIO")
        thread = threading.Thread(
            target=run_ir_receiver_gpio_loop,
            args=(settings, stop_event, code),
            name="sensor-ir",
            daemon=True,
        )
        threads.append(thread)
        thread.start()


def run_ir_receiver_gpio_loop(settings, stop_event, code):
    from sensors.ir_receiver import IRReceiver, run_ir_loop

    pin = settings.get("pin")
    ir = IRReceiver(pin)

    def callback(key, _code):
        send_key(settings, key)

    run_ir_loop(ir, callback, stop_event, code)

