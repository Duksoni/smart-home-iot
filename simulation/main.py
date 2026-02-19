from settings import load_settings

if __name__ == "__main__":
    settings = load_settings()
    device_name = settings.get("device", "PI1")

    if device_name == "PI1":
        from devices.pi1 import run

        print("Starting PI1 controller")
        run(settings)
    elif device_name == "PI2":
        from devices.pi2 import run
        print("Starting PI2 controller")
        run(settings)
    elif device_name == "PI3":
        from devices.pi3 import run
        print("Starting PI3 controller")
        run(settings)
    else:
        print(f"No device implementation for {device_name}")
