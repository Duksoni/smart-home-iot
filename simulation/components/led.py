def led_control(settings, command):
    if settings["simulated"]:
        print(f"[SIM] LED -> {command}")
    else:
        # actual GPIO toggling would go here
        print(f"[GPIO] LED -> {command}")
