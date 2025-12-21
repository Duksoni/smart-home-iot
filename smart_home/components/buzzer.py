def buzzer_control(settings, command):
    if settings["simulated"]:
        print(f"[SIM] Buzzer -> {command}")
    else:
        print(f"[GPIO] Buzzer -> {command}")