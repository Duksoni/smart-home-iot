from mqtt_publisher import get_publisher

ACTION_VALUES = {
    "short": 1,
    "long": 2,
    "start": 3,
    "stop": 0,
}

_BUZZERS = {}


def _get_buzzer(settings):
    from actuators.buzzer import DB

    code = settings.get("code", "DB")
    buzzer = _BUZZERS.get(code)
    if buzzer:
        return buzzer
    pin = settings.get("pin")
    if pin is None:
        raise ValueError("Buzzer pin is not configured")
    buzzer = DB(
        pin,
        active_high=settings.get("active_high", True),
        pwm=settings.get("pwm", False),
        frequency=settings.get("frequency", 2000),
        duty_cycle=settings.get("duty_cycle", 50),
    )
    _BUZZERS[code] = buzzer
    return buzzer


def buzzer_control(settings, command):
    cmd = (command or "").lower()
    short_duration = settings.get("short_duration", 0.1)
    long_duration = settings.get("long_duration", 0.5)

    if cmd == "beep":
        cmd = "short"
    if cmd == "on":
        cmd = "start"
    if cmd == "off":
        cmd = "stop"

    if settings.get("simulated"):
        if cmd == "short":
            print("[SIM] Buzzer -> short beep \a")
        elif cmd == "long":
            print("[SIM] Buzzer -> long beep \a")
        elif cmd == "start":
            print("[SIM] Buzzer -> start (continuous) \a")
        elif cmd == "stop":
            print("[SIM] Buzzer -> stop")
        else:
            print(f"[SIM] Buzzer -> unknown command: {command}")
    else:
        buzzer = _get_buzzer(settings)
        if cmd == "short":
            buzzer.short_beep(duration=short_duration)
        elif cmd == "long":
            buzzer.long_beep(duration=long_duration)
        elif cmd == "start":
            buzzer.start()
        elif cmd == "stop":
            buzzer.stop()
        else:
            print(f"[GPIO] Buzzer -> unknown command: {command}")

    if cmd in ACTION_VALUES:
        publisher = get_publisher()
        if publisher:
            code = settings.get("code", "DB")
            payload = {
                "measurement": "buzzer",
                "value": ACTION_VALUES[cmd],
                "action": cmd,
                "simulated": settings.get("simulated", True),
                "device": publisher.device_name,
                "code": code,
            }
            topic = publisher.build_topic("actuators", code)
            publisher.enqueue_json(topic, payload)

def cleanup_all():
    for buzzer in _BUZZERS.values():
        try:
            buzzer.cleanup()
        except Exception:
            pass
    _BUZZERS.clear()