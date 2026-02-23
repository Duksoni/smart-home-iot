import threading
import time

from components.dht import run_dht
from components.ir_receiver import run_ir_receiver, send_key
from components.motion import run_dpir, send_motion_event
from lcd_screen_coordinator import start_lcd_screen_coordinator
from mqtt_publisher import init_mqtt_publisher
from rgb_light_coordinator import start_rgb_light_coordinator
from settings import get_device_config

RUNNERS = {"DHT1": run_dht, "DHT2": run_dht, "DPIR3": run_dpir, "IR": run_ir_receiver}


def _get_hw_settings(hardware_config, code):
    params = hardware_config.get(code, {"simulated": True})
    if isinstance(params, dict):
        params.setdefault("code", code)
    return params


def _start_sensor_threads(device_config, hardware_config, threads, stop_event):
    for code in device_config.get("sensors", []):
        runner = RUNNERS.get(code)
        if not runner:
            continue
        params = _get_hw_settings(hardware_config, code)

        runner(params, threads, stop_event, code)


def _list_commands():
    print("=" * 26)
    print("Commands:")
    print("  ir send <digit in [0,7]>")
    print("  dpir trigger")
    print("  exit | quit")
    print("=" * 26)


def _console_thread(hardware_config, stop_event):
    print("Type 'help' for commands, 'exit' or 'quit' to quit.")
    while not stop_event.is_set():
        try:
            cmd = input("> ").strip()
        except EOFError:
            print("Keyboard interrupt, exiting...")
            stop_event.set()
            return

        if not cmd:
            continue

        lower = cmd.lower()
        if lower in {"exit", "quit"}:
            stop_event.set()
            return
        if lower == "help":
            _list_commands()
            continue

        parts = cmd.split()

        if len(parts) == 3:
            if parts[0] == "ir" and parts[1] == "send":
                send_key(_get_hw_settings(hardware_config, "IR"), parts[2])
                continue

        if len(parts) == 2 and parts[0].lower() == "dpir":
            send_motion_event("DPIR3")
            continue


def run(settings):
    device_name = "PI3"
    device_config, hardware_config = get_device_config(settings, device=device_name)
    for code, params in hardware_config.items():
        if isinstance(params, dict):
            params.setdefault("code", code)

    _list_commands()

    publisher = init_mqtt_publisher(settings)

    threads = []
    stop_event = threading.Event()

    broker_settings = settings.get("mqtt")

    brgb_subscriber = start_rgb_light_coordinator(broker_settings, hardware_config)
    lcd_screen_coordinator, lcd_screen_subscriber = start_lcd_screen_coordinator(
        broker_settings, hardware_config
    )

    _start_sensor_threads(device_config, hardware_config, threads, stop_event)

    console_t = threading.Thread(
        target=_console_thread, args=(hardware_config, stop_event), daemon=True
    )
    threads.append(console_t)
    console_t.start()

    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

    publisher.stop()
    brgb_subscriber.stop()
    lcd_screen_subscriber.stop()
    lcd_screen_coordinator.stop()

    stop_event.set()
    for thread in threads:
        thread.join(timeout=1)

    try:
        import RPi.GPIO as GPIO

        GPIO.cleanup()
    except ImportError:
        pass
