from mqtt_publisher import get_publisher

actions = {
    "light_off": ("Turning off", "turn_off"),
    "light_red": ("Switching to red", "red_light"),
    "light_green": ("Switching to green", "green_light"),
    "light_blue": ("Switching to blue", "blue_light"),
    "light_cyan": ("Switching to cyan", "cyan_light"),
    "light_magenta": ("Switching to magenta", "magenta_light"),
    "light_yellow": ("Switching to yellow", "yellow_light"),
    "light_white": ("Switching to white", "white_light"),
}

_LEDS = {}


def _get_led(settings):
    from actuators.rgb_led import BRGB

    code = settings.get("code", "BRGB")
    led = _LEDS.get(code)
    if led:
        return led
    red_pin = settings.get("red_pin")
    if red_pin is None:
        raise ValueError("RGB Led red pin is not configured")
    blue_pin = settings.get("blue_pin")
    if blue_pin is None:
        raise ValueError("RGB Led blue pin is not configured")
    green_pin = settings.get("green_pin")
    if green_pin is None:
        raise ValueError("RGB Led green pin is not configured")
    led = BRGB(red_pin, green_pin, blue_pin)
    _LEDS[code] = led
    return led


def led_control(settings, action):
    simulated = settings.get("simulated")
    prefix = "[SIM]" if simulated else "[GPIO]"

    if action not in actions.keys():
        print(f"{prefix} RGB LED -> Invalid action: {action}")
        return

    print(f"{prefix} RGB LED -> Action: {action}")

    message, method_name = actions[action]
    print(f"{prefix} RGB LED -> {message}")

    if not simulated:
        print(f"{prefix} RGB LED -> {method_name}()")
        led = _get_led(settings)
        getattr(led, method_name)()

    publisher = get_publisher()
    if publisher:
        code = settings.get("code", "BRGB")
        payload = {
            "measurement": "rgb_led",
            "value": action,
            "simulated": simulated,
            "device": publisher.device_name,
            "code": code,
        }
        topic = publisher.build_topic("actuators", code)
        publisher.enqueue_json(topic, payload)
