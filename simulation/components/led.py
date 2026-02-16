from mqtt_publisher import get_publisher

ACTION_VALUES = {
    "on": 1,
    "off": 0,
    "toggle": 2,
}

_LEDS = {}

def _get_led(settings):
    from actuators.led import DL

    code = settings.get("code", "DL")
    led = _LEDS.get(code)
    if led:
        return led
    pin = settings.get("pin")
    if pin is None:
        raise ValueError("Led pin is not configured")
    led = DL(
        pin,
        active_high=settings.get("active_high", True)
    )
    _LEDS[code] = led
    return led

def led_control(settings, command):
    cmd = (command or "").lower()

    # normalize commands
    if cmd == "start":
        cmd = "on"
    if cmd == "stop":
        cmd = "off"

    if settings.get("simulated"):
        if cmd == "on":
            print("[SIM] LED -> on")
        elif cmd == "off":
            print("[SIM] LED -> off")
        elif cmd == "toggle":
            print("[SIM] LED -> toggle")
        else:
            print("[SIM] LED -> unknown command: {command}")
    else:
        led = _get_led(settings)
        if cmd == "on":
            led.on()
        elif cmd == "off":
            led.off()
        elif cmd == "toggle":
            led.toggle()
        else:
            print(f"[GPIO] LED -> unknown command: {command}")

    if cmd in ACTION_VALUES:
        publisher = get_publisher()
        if publisher:
            code = settings.get("code", "DL")
            payload = {
                "measurement": "led",
                "value": ACTION_VALUES[cmd],
                "action": cmd,
                "simulated": settings.get("simulated", True),
                "device": publisher.device_name,
                "code": code
            }
            topic = publisher.build_topic("actuators", code)
            publisher.enqueue_json(topic, payload)

def cleanup_all():
    for led in _LEDS.values():
        try:
            led.cleanup()
        except Exception:
            pass
    _LEDS.clear()