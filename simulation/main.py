from mqtt_publisher import init_mqtt
from settings import load_settings

if __name__ == "__main__":
    settings = load_settings()
    init_mqtt(settings)
    device_name = settings.get("device", "PI1")

    if device_name == "PI1":
        from devices.pi1 import run

        print("Starting PI1 controller")
        run(settings)
    elif device_name == "PI2":
        print("Starting PI2 controller")
    elif device_name == "PI3":
        print("Starting PI3 controller")
    else:
        print(f"No device implementation for {device_name}")
