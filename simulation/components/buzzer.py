def buzzer_control(settings, command):
    cmd = (command or "").lower()

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
        if cmd == "short":
            print("[GPIO] Buzzer -> short pulse")
        elif cmd == "long":
            print("[GPIO] Buzzer -> long pulse")
        elif cmd == "start":
            print("[GPIO] Buzzer -> start continuous")
        elif cmd == "stop":
            print("[GPIO] Buzzer -> stop")
        else:
            print(f"[GPIO] Buzzer -> unknown command: {command}")
