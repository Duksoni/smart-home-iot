from mqtt_publisher import get_publisher

actions = [
    "light_off",
    "light_red",
    "light_green",
    "light_blue",
    "light_cyan",
    "light_magenta",
    "light_yellow",
    "light_white",
]

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

    if action not in actions:
        print(f"{prefix} RGB LED -> Invalid action: {action}")
        return

    print(f"{prefix} RGB LED -> Action: {action}")

    if simulated:
        do_action(prefix, action)
    else:
        led = _get_led(settings)
        do_action(prefix, action, led)

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
        topic = publisher.build_topic( "actuators", code)
        publisher.enqueue_json(topic, payload)


def do_action(prefix, action, led=None):
    match action:
        case "light_off":
            print(f"{prefix} RGB LED -> Turning off")
            if led:
                led.turn_off()

        case "light_red":
            print(f"{prefix} RGB LED -> Switching to red")
            if led:
                led.red_light()

        case "light_green":
            print(f"{prefix} RGB LED -> Switching to green")
            if led:
                led.green_light()

        case "light_blue":
            print(f"{prefix} RGB LED -> Switching to blue")
            if led:
                led.blue_light()

        case "light_cyan":
            print(f"{prefix} RGB LED -> Switching to cyan")
            if led:
                led.cyan_light()

        case "light_magenta":
            print(f"{prefix} RGB LED -> Switching to magenta")
            if led:
                led.magenta_light()

        case "light_yellow":
            print(f"{prefix} RGB LED -> Switching to yellow")
            if led:
                led.yellow_light()

        case "light_white":
            print(f"{prefix} RGB LED -> Switching to white")
            if led:
                led.white_light()
