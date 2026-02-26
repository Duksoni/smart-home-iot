"""
Server-side alarm logic

All time-sensitive decisions (motion light, door-open timeout, arm grace,
door-entry grace) use threading.Timer so the MQTT callback thread is never
blocked.  All shared mutable state is protected by a single Lock.

Obtain the singleton with AlarmLogic().  Call configure() once at startup.

"""

import threading
import time
from collections import defaultdict, deque
from typing import Optional

from influxdb_client import Point

from .config import get_settings
from .dependencies import AppDependencies
from .state import HouseState


UNLOCK_ALARM_SECONDS: float = 5.0  # door open this long -> alarm
MOTION_LIGHT_SECONDS: float = 10.0  # DL stays on this long
ARM_GRACE_SECONDS: float = 10.0  # delay before arming completes
DOOR_ENTRY_GRACE_SECONDS: float = 10.0  # req 4b: window to enter PIN after door
OCCUPANCY_WINDOW_SECONDS: float = 5.0  # req 2: recent DUS window size
GYRO_THRESHOLD: float = 20.0  # req 6: minimum |delta| to trigger alarm

# Door PIR -> paired distance sensor
_DPIR_TO_DUS: dict[str, str] = {"DPIR1": "DUS1", "DPIR2": "DUS2"}

# Door sensors relevant to points 3 & 4b
_DOOR_CODES: frozenset[str] = frozenset({"DS1", "DS2"})


# MQTT command topic prefix (must match broker settings)
_CMD_PREFIX = "smarthome/commands"


class AlarmLogic:
    """Process-wide singleton for all alarm-related state machine logic."""

    _instance: Optional["AlarmLogic"] = None

    def __new__(cls) -> "AlarmLogic":
        if cls._instance is None:
            inst = super().__new__(cls)
            inst._init()
            cls._instance = inst
        return cls._instance

    # ── One-time initialisation ───────────────────────────────────────────────

    def _init(self) -> None:
        self._lock = threading.Lock()

        # DUS distance history: code -> deque of (monotonic_ts, distance_cm)
        self._distance_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=30))

        # Timestamp (monotonic) of last successful PIN entry on any DMS
        self._last_correct_pin_at: float = 0.0

        # --- Active timers (cancel before replacing) ---
        # req 3: door open too long -> alarm
        self._unlock_timers: dict[str, threading.Timer] = {}
        # req 4b: armed + door opened -> alarm unless PIN entered in time
        self._armed_door_timers: dict[str, threading.Timer] = {}
        # req 1: DL off after motion light timeout
        self._dl_off_timer: Optional[threading.Timer] = None
        # req 4a: arm after PIN grace
        self._arm_timer: Optional[threading.Timer] = None

        # Track which door sensor(s) caused the current unlocked-door alarm
        # so we know when the right door closing should clear it.
        self._unlock_alarm_doors: set[str] = set()

    # ── Public event handlers (called from main._update_state) ───────────────

    def on_motion(self, code: str, value: int) -> None:
        """Called for every motion/clear reading from any DPIR sensor."""
        if value != 1:
            return  # only care about motion-detected events

        house = HouseState()

        # Req 5: nobody home + any motion -> alarm
        if house.get_people_count() == 0:
            self._trigger_alarm(f"motion_no_occupants:{code}")
            # Still continue so req 1 fires for DPIR1

        # Req 1: DPIR1 specifically -> turn on DL for MOTION_LIGHT_SECONDS
        if code == "DPIR1":
            self._publish_command("DL", "on")
            self._reset_dl_off_timer()

        # Req 2: door PIRs -> update occupancy based on distance trend
        if code in _DPIR_TO_DUS:
            self._update_occupancy(code)

    def on_distance(self, code: str, value) -> None:
        """Called for every ultrasonic distance reading."""
        if value is None:
            return
        with self._lock:
            self._distance_history[code].append((time.monotonic(), float(value)))

    def on_door(self, code: str, value: int) -> None:
        """Called when a door button (DS1/DS2) changes state."""
        if code not in _DOOR_CODES:
            return
        is_open = bool(value)
        house = HouseState()

        if is_open:
            # Req 3: start unlock-alarm timer
            self._start_unlock_timer(code)

            # Req 4b: if armed + no recent valid PIN -> start entry grace timer
            alarm_state = house.get_alarm()
            if alarm_state["armed"] and not alarm_state["active"]:
                now = time.monotonic()
                with self._lock:
                    recent_pin = (
                        now - self._last_correct_pin_at
                    ) < DOOR_ENTRY_GRACE_SECONDS
                if not recent_pin:
                    self._start_armed_door_timer(code)
        else:
            # Door closed
            self._cancel_unlock_timer(code)
            self._cancel_armed_door_timer(code)

            # Req 3: if this door being left open caused the current alarm -> clear
            with self._lock:
                caused_alarm = code in self._unlock_alarm_doors
            if caused_alarm:
                with self._lock:
                    self._unlock_alarm_doors.discard(code)
                # Only auto-clear if no other unlock-alarm door is still open
                with self._lock:
                    any_remaining = bool(self._unlock_alarm_doors)
                if not any_remaining:
                    alarm_state = house.get_alarm()
                    if not alarm_state["active"]:
                        reason = alarm_state.get("reason", "")
                        if reason and reason.startswith("unlocked_door:"):
                            self._deactivate_alarm()

    def on_membrane_attempt(self, input: str) -> None:
        """Called when a complete 4-digit+# sequence is entered on DMS."""
        settings = get_settings()
        print(input)
        if input != settings.alarm_pin:
            print("Wrong code")
            return

        now = time.monotonic()
        with self._lock:
            self._last_correct_pin_at = now

        house = HouseState()
        alarm_state = house.get_alarm()

        if alarm_state["active"] or alarm_state["armed"]:
            # Req 4c: correct PIN while active/armed -> deactivate everything
            self._cancel_armed_door_timers_all()
            self._cancel_unlock_timers_all()
            self._deactivate_alarm()
        elif not alarm_state["arm_pending"]:
            # Req 4a: correct PIN while disarmed and not already pending -> arm after grace
            self._start_arm_timer()

    def on_gyroscope(self, code: str, value) -> None:
        """Called for every gyroscope reading from GSG."""
        try:
            delta = float(value)
        except (TypeError, ValueError):
            return
        if abs(delta) >= GYRO_THRESHOLD:
            self._trigger_alarm(f"gyroscope:{code} - {value}cm")

    # ── Alarm state changes ───────────────────────────────────────────────────

    def _trigger_alarm(self, reason: str) -> None:
        with self._lock:
            house = HouseState()
            if house.get_alarm()["active"]:
                return

            house.set_alarm(active=True, reason=reason)
            house.set_arm_pending(False)

            if self._arm_timer:
                self._arm_timer.cancel()
                self._arm_timer = None

        print(f"[ALARM] Activated — reason: {reason}")
        self._publish_command("DB", "start")  # turn buzzer on
        self._write_alarm_event("activated", reason)

    def _deactivate_alarm(self) -> None:
        house = HouseState()
        house.set_alarm(active=False)
        house.set_armed(False)
        house.set_arm_pending(False)

        with self._lock:
            if self._arm_timer:
                self._arm_timer.cancel()
                self._arm_timer = None

        print("[ALARM] Deactivated")
        self._publish_command("DB", "stop")  # turn buzzer off
        self._write_alarm_event("deactivated", None)

    # ── Occupancy (req 2) ─────────────────────────────────────────────────────

    def _update_occupancy(self, dpir_code: str) -> None:
        dus_code = _DPIR_TO_DUS[dpir_code]
        now = time.monotonic()

        with self._lock:
            history = list(self._distance_history[dus_code])

        if not history:
            return

        # Split into "recent" (last WINDOW seconds) and "older" (1–2 WINDOWs ago)
        recent = [d for ts, d in history if now - ts < OCCUPANCY_WINDOW_SECONDS]
        older = [
            d
            for ts, d in history
            if OCCUPANCY_WINDOW_SECONDS <= (now - ts) < OCCUPANCY_WINDOW_SECONDS * 2
        ]

        if not recent:
            return

        avg_recent = sum(recent) / len(recent)

        if older:
            avg_older = sum(older) / len(older)
            if avg_recent < avg_older - 5:  # approaching (entering)
                delta = 1
            elif avg_recent > avg_older + 5:  # departing (leaving)
                delta = -1
            else:
                return  # no clear direction
        else:
            # No older window yet — use absolute threshold as fallback
            # (close to door = entering, far = leaving)
            # Default threshold: 80 cm
            delta = 1 if avg_recent < 80.0 else -1

        house = HouseState()
        house.delta_people(delta)
        current_count = house.get_people_count()
        self._write_occupancy_event(delta)
        self._write_people_count(current_count)
        action = "entered" if delta > 0 else "left"
        print(
            f"[OCCUPANCY] Person {action} via {dpir_code} — "
            f"count={current_count}"
        )

    # ── Timer management ──────────────────────────────────────────────────────

    def _start_unlock_timer(self, door_code: str) -> None:
        """Req 3: door open for UNLOCK_ALARM_SECONDS -> alarm."""
        with self._lock:
            existing = self._unlock_timers.get(door_code)
            if existing:
                existing.cancel()
            t = threading.Timer(
                UNLOCK_ALARM_SECONDS,
                self._on_unlock_alarm_fired,
                args=(door_code,),
            )
            self._unlock_timers[door_code] = t
        t.start()

    def _on_unlock_alarm_fired(self, door_code: str) -> None:
        with self._lock:
            self._unlock_alarm_doors.add(door_code)
            self._unlock_timers.pop(door_code, None)
        self._trigger_alarm(f"unlocked_door:{door_code}")

    def _cancel_unlock_timer(self, door_code: str) -> None:
        with self._lock:
            t = self._unlock_timers.pop(door_code, None)
        if t:
            t.cancel()

    def _cancel_unlock_timers_all(self) -> None:
        with self._lock:
            timers = list(self._unlock_timers.values())
            self._unlock_timers.clear()
            self._unlock_alarm_doors.clear()
        for t in timers:
            t.cancel()

    def _start_armed_door_timer(self, door_code: str) -> None:
        """Req 4b: armed + door opened; alarm if no PIN within grace."""
        with self._lock:
            existing = self._armed_door_timers.get(door_code)
            if existing:
                existing.cancel()
            t = threading.Timer(
                DOOR_ENTRY_GRACE_SECONDS,
                self._on_armed_door_fired,
                args=(door_code,),
            )
            self._armed_door_timers[door_code] = t
        t.start()

    def _on_armed_door_fired(self, door_code: str) -> None:
        with self._lock:
            self._armed_door_timers.pop(door_code, None)
        self._trigger_alarm(f"armed_door_breach:{door_code}")

    def _cancel_armed_door_timer(self, door_code: str) -> None:
        with self._lock:
            t = self._armed_door_timers.pop(door_code, None)
        if t:
            t.cancel()

    def _cancel_armed_door_timers_all(self) -> None:
        with self._lock:
            timers = list(self._armed_door_timers.values())
            self._armed_door_timers.clear()
        for t in timers:
            t.cancel()

    def _reset_dl_off_timer(self) -> None:
        """Req 1: reset the DL-off timer every time DPIR1 fires while light is on."""
        with self._lock:
            if self._dl_off_timer:
                self._dl_off_timer.cancel()
            t = threading.Timer(MOTION_LIGHT_SECONDS, self._on_dl_off_fired)
            self._dl_off_timer = t
        t.start()

    def _on_dl_off_fired(self) -> None:
        with self._lock:
            self._dl_off_timer = None
        self._publish_command("DL", "off")

    def _start_arm_timer(self) -> None:
        """Req 4a: arm the system after ARM_GRACE_SECONDS."""
        HouseState().set_arm_pending(True)
        print(f"[ALARM] System arming in {ARM_GRACE_SECONDS:.0f} s…")
        with self._lock:
            if self._arm_timer:
                self._arm_timer.cancel()
            t = threading.Timer(ARM_GRACE_SECONDS, self._on_arm_fired)
            self._arm_timer = t
        t.start()

    def _on_arm_fired(self) -> None:
        with self._lock:
            self._arm_timer = None
        house = HouseState()
        # Only arm if the pending flag is still set (not cancelled by deactivate)
        if house.is_arm_pending():
            house.set_arm_pending(False)
            house.set_armed(True)
            print("[ALARM] System armed.")
            self._write_alarm_event("armed", None)

    # ── MQTT publishing ───────────────────────────────────────────────────────

    def _publish_command(self, actuator_code: str, action: str) -> None:
        import json

        mqtt = AppDependencies().get_mqtt_client()
        if mqtt is None:
            return
        topic = f"{_CMD_PREFIX}/{actuator_code}"
        print(f"[MQTT] Publishing command to {topic}: {action}")
        mqtt.publish(topic, json.dumps({"action": action}))

    # ── InfluxDB writes ───────────────────────────────────────────────────────

    def _write_alarm_event(self, action: str, reason: Optional[str]) -> None:
        write_api = AppDependencies().get_write_api()
        if write_api is None:
            return
        from .config import get_settings
        settings = get_settings()        
        point = (
            Point("alarm_event")
            .tag("action", action)
            .tag("reason", reason or "")
            .field("value", 1)
        )
        try:
            write_api.write(
                bucket=settings.influxdb_bucket,
                org=settings.influxdb_org,
                record=point,
            )
        except Exception as exc:
            print(f"[ALARM] InfluxDB write failed: {exc}")

    def _write_occupancy_event(self, delta: int) -> None:
        write_api = AppDependencies().get_write_api()
        if write_api is None:
            return
        from .config import get_settings
        settings = get_settings()

        point = Point("occupancy").tag("code", "occupancy").field("value", delta)
        try:
            write_api.write(
                bucket=settings.influxdb_bucket,
                org=settings.influxdb_org,
                record=point,
            )
        except Exception as exc:
            print(f"[ALARM] InfluxDB occupancy write failed: {exc}")

    def _write_people_count(self, count: int) -> None:
        write_api = AppDependencies().get_write_api()
        if write_api is None:
            return

        from .config import get_settings
        settings = get_settings()

        point = (
            Point("people_count")
            .tag("code", "occupancy")
            .field("value", int(count))
        )

        try:
            write_api.write(
                bucket=settings.influxdb_bucket,
                org=settings.influxdb_org,
                record=point,
            )
        except Exception as exc:
            print(f"[OCCUPANCY] InfluxDB count write failed: {exc}")
