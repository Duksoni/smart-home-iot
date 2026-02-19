"""
Single source of truth for all runtime house state.

One singleton instance (HouseState) is shared across the entire process.
All mutations are protected by a single RLock.
Obtain the instance simply with:  HouseState()
"""

import threading
import time
from dataclasses import dataclass
from typing import Literal, Optional


RgbMode = Literal[
    "light_off",
    "light_red",
    "light_green",
    "light_blue",
    "light_cyan",
    "light_magenta",
    "light_yellow",
    "light_white",
]

RGB_MODES: list[RgbMode] = [
    "light_off",
    "light_red",
    "light_green",
    "light_blue",
    "light_cyan",
    "light_magenta",
    "light_yellow",
    "light_white",
]

# CSS colour for each mode – used by the API so the frontend can render a
# preview without maintaining its own mapping.
MODE_CSS_COLOR: dict[str, str] = {
    "light_off":     "#000000",
    "light_red":     "#ff0000",
    "light_green":   "#00ff00",
    "light_blue":    "#0000ff",
    "light_cyan":    "#00ffff",
    "light_magenta": "#ff00ff",
    "light_yellow":  "#ffff00",
    "light_white":   "#ffffff",
}


@dataclass
class AlarmData:
    active: bool = False
    armed: bool = False
    triggered_at: Optional[float] = None
    reason: Optional[str] = None


@dataclass
class TimerData:
    duration_seconds: int = 0
    started_at: Optional[float] = None   # monotonic
    running: bool = False
    blink_mode: bool = False
    add_seconds_increment: int = 30


@dataclass
class RgbData:
    mode: str = "light_off"


class HouseState:
    """Process-wide singleton holding all mutable runtime state."""

    _instance: Optional["HouseState"] = None

    def __new__(cls) -> "HouseState":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._init()
            cls._instance = instance
        return cls._instance

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init(self) -> None:
        self._lock = threading.RLock()
        self._alarm = AlarmData()
        self._arm_pending: bool = False  # PIN entered, waiting for 10-s grace to complete
        self._people_count: int = 0
        self._sensor_readings: dict[str, dict] = {}
        self._actuator_states: dict[str, dict] = {}
        self._timer = TimerData()
        self._rgb = RgbData()

    # ── Alarm ─────────────────────────────────────────────────────────────────

    def get_alarm(self) -> dict:
        with self._lock:
            return {
                "active": self._alarm.active,
                "armed": self._alarm.armed,
                "arm_pending": self._arm_pending,
                "triggered_at": self._alarm.triggered_at,
                "reason": self._alarm.reason,
            }

    def set_alarm(self, active: bool, reason: Optional[str] = None) -> None:
        with self._lock:
            self._alarm.active = active
            if active:
                self._alarm.triggered_at = time.time()
                self._alarm.reason = reason
            else:
                self._alarm.triggered_at = None
                self._alarm.reason = None

    def set_armed(self, armed: bool) -> None:
        with self._lock:
            self._alarm.armed = armed

    def set_arm_pending(self, pending: bool) -> None:
        with self._lock:
            self._arm_pending = pending

    def is_arm_pending(self) -> bool:
        with self._lock:
            return self._arm_pending

    # ── Occupancy ─────────────────────────────────────────────────────────────

    def get_people_count(self) -> int:
        with self._lock:
            return self._people_count

    def set_people_count(self, count: int) -> None:
        with self._lock:
            self._people_count = max(0, count)

    def delta_people(self, delta: int) -> None:
        with self._lock:
            self._people_count = max(0, self._people_count + delta)

    # ── Sensor readings ───────────────────────────────────────────────────────

    def update_sensor(self, code: str, payload: dict) -> None:
        # Key includes the measurement so DHT temperature and humidity
        # are stored independently and neither overwrites the other.
        measurement = payload.get("measurement", "")
        key = f"{code}_{measurement}" if measurement else code
        with self._lock:
            # Preserve a timestamp already present in the payload (e.g. from
            # boot-time hydration where it carries the original InfluxDB time).
            received_at = payload.get("received_at") or time.time()
            self._sensor_readings[key] = {**payload, "received_at": received_at}

    def get_sensor(self, code: str) -> Optional[dict]:
        """Return the first reading whose key starts with `code`."""
        with self._lock:
            for key, reading in self._sensor_readings.items():
                if key == code or key.startswith(f"{code}_"):
                    return reading
            return None

    def get_all_sensors(self) -> dict[str, dict]:
        with self._lock:
            return dict(self._sensor_readings)

    # ── Actuator states ───────────────────────────────────────────────────────

    def update_actuator(self, code: str, payload: dict) -> None:
        with self._lock:
            # Preserve a timestamp already present in the payload (e.g. from
            # boot-time hydration where it carries the original InfluxDB time).
            updated_at = payload.get("updated_at") or payload.get("received_at") or time.time()
            self._actuator_states[code] = {**payload, "updated_at": updated_at}

    def get_actuator(self, code: str) -> Optional[dict]:
        with self._lock:
            return self._actuator_states.get(code)

    def get_all_actuators(self) -> dict[str, dict]:
        with self._lock:
            return dict(self._actuator_states)

    # ── Kitchen timer ─────────────────────────────────────────────────────────

    def get_timer(self) -> dict:
        with self._lock:
            remaining = 0
            if self._timer.running and self._timer.started_at is not None:
                elapsed = time.monotonic() - self._timer.started_at
                remaining = max(0, self._timer.duration_seconds - int(elapsed))
            return {
                "duration_seconds": self._timer.duration_seconds,
                "remaining_seconds": remaining,
                "running": self._timer.running,
                "blink_mode": self._timer.blink_mode,
                "add_seconds_increment": self._timer.add_seconds_increment,
            }

    def set_timer(self, duration_seconds: int, add_seconds_increment: Optional[int] = None) -> None:
        with self._lock:
            self._timer.duration_seconds = duration_seconds
            self._timer.started_at = time.monotonic()
            self._timer.running = True
            self._timer.blink_mode = False
            if add_seconds_increment is not None:
                self._timer.add_seconds_increment = add_seconds_increment

    def stop_timer_blink(self) -> None:
        with self._lock:
            self._timer.blink_mode = False
            self._timer.running = False

    def set_timer_blink(self, blink: bool) -> None:
        with self._lock:
            self._timer.blink_mode = blink
            if blink:
                self._timer.running = False

    def set_add_seconds_increment(self, n: int) -> None:
        with self._lock:
            self._timer.add_seconds_increment = n

    # ── RGB bulb ──────────────────────────────────────────────────────────────

    def get_rgb(self) -> dict:
        with self._lock:
            mode = self._rgb.mode
            return {
                "mode": mode,
                "color": MODE_CSS_COLOR[mode],
                "available_modes": RGB_MODES,
            }

    def set_rgb_mode(self, mode: str) -> None:
        if mode not in RGB_MODES:
            raise ValueError(f"Unknown RGB mode: {mode!r}")
        with self._lock:
            self._rgb.mode = mode


# ── Measurement classification ────────────────────────────────────────────────
# Defined here (not in main.py) so boot.py and main.py share one source of truth.

_SENSOR_MEASUREMENTS: frozenset[str] = frozenset({
    "button", "ultrasonic", "motion",
    "temperature", "humidity",
    "membrane_key", "membrane_attempt", "ir_receiver", "gyroscope",
})

_ACTUATOR_MEASUREMENTS: frozenset[str] = frozenset({
    "led", "buzzer", "rgb_led", "lcd_display", "segment_display",
})
