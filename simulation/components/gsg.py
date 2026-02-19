"""
Gyroscope (GSG) component.

On real hardware this would read an MPU-6050 or similar over I2C and publish
the magnitude of the angular velocity vector.  Since there is no GPIO
implementation yet, the simulated path only accepts console triggers.

The server watches for  measurement=gyroscope  and fires the alarm when
|value| >= GYRO_THRESHOLD (configured in server/app/alarm_logic.py).
"""

import threading

from mqtt_publisher import get_publisher


def _publish(settings, delta: float) -> None:
    code = settings.get("code", "GSG")
    simulated = settings.get("simulated", True)
    prefix = "[SIM]" if simulated else "[GPIO]"
    print(f"{prefix} GSG -> delta: {delta}")

    publisher = get_publisher()
    if publisher:
        publisher.enqueue_json(
            publisher.build_topic("sensors", code),
            {
                "measurement": "gyroscope",
                "value": delta,
                "simulated": simulated,
                "device": publisher.device_name,
                "code": code,
            },
        )


def send_gyro_event(settings, delta: float) -> None:
    """Manually publish a gyroscope delta (for console simulation)."""
    _publish(settings, delta)


def run_gsg(settings, threads, stop_event, code):
    """
    Start the GSG component.

    Simulated: does nothing automatically — use 'gsg send <delta>' in the
               PI2 console to inject events.
    Real HW:   would start an I2C polling loop (not implemented yet).
    """
    settings.setdefault("code", code)

    if settings.get("simulated", True):
        print(f"[SIM] GSG ready — use console 'gsg send <value>' to inject events.")
    else:
        print("[GPIO] GSG -> Starting I2C loop (not yet implemented, falling back to console mode).")
