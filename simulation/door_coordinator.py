import queue
import threading
import time
from queue import Queue
from typing import Optional


class DoorState:
    def __init__(self, codes):
        self._lock = threading.Lock()
        self._codes = codes
        self.motion_state = 0
        self.motion_at = 0.0
        self.distance_cm = None
        self.distance_at = 0.0
        self.door_open = False
        self.door_at = 0.0
        self.last_key = None
        self.key_at = 0.0
        self.attempt_success = None
        self.attempt_at = 0.0

    def _matches(self, kind, code):
        expected = self._codes.get(kind)
        return expected is None or expected == code

    def update_motion(self, code, state):
        if not self._matches("dpir", code):
            return
        now = time.monotonic()
        with self._lock:
            self.motion_state = state
            self.motion_at = now

    def update_distance(self, code, distance_cm):
        if not self._matches("dus", code):
            return
        now = time.monotonic()
        with self._lock:
            self.distance_cm = distance_cm
            self.distance_at = now

    def update_door(self, code, is_open):
        if not self._matches("ds", code):
            return
        now = time.monotonic()
        new_state = bool(is_open)
        with self._lock:
            if new_state == self.door_open:
                return
            self.door_open = new_state
            self.door_at = now

    def update_key(self, code, key):
        if not self._matches("dms", code):
            return
        now = time.monotonic()
        with self._lock:
            self.last_key = key
            self.key_at = now

    def update_attempt(self, code, success):
        if not self._matches("dms", code):
            return
        now = time.monotonic()
        with self._lock:
            self.attempt_success = bool(success)
            self.attempt_at = now

    def snapshot(self):
        with self._lock:
            return {
                "motion_state": self.motion_state,
                "motion_at": self.motion_at,
                "distance_cm": self.distance_cm,
                "distance_at": self.distance_at,
                "door_open": self.door_open,
                "door_at": self.door_at,
                "last_key": self.last_key,
                "key_at": self.key_at,
                "attempt_success": self.attempt_success,
                "attempt_at": self.attempt_at,
            }


_STATE: Optional[DoorState] = None
_BUZZER_QUEUE: Optional[Queue] = None


def update_motion(code, state):
    if _STATE:
        _STATE.update_motion(code, state)


def update_distance(code, distance_cm):
    if _STATE:
        _STATE.update_distance(code, distance_cm)


def update_door(code, is_open):
    if _STATE:
        _STATE.update_door(code, is_open)


def update_key(code, key):
    if _STATE:
        _STATE.update_key(code, key)


def update_attempt(code, success):
    if _STATE:
        _STATE.update_attempt(code, success)


def _enqueue_buzzer(pattern):
    if _BUZZER_QUEUE is not None:
        _BUZZER_QUEUE.put(pattern)


def _buzzer_worker(buzzer_settings, stop_event, pause_seconds):
    from components.buzzer import buzzer_control

    while not stop_event.is_set():
        try:
            pattern = _BUZZER_QUEUE.get(timeout=0.2)
        except queue.Empty:
            continue

        if pattern == "double_short":
            buzzer_control(buzzer_settings, "short")
            time.sleep(pause_seconds)
            buzzer_control(buzzer_settings, "short")
        elif pattern in {"short", "long", "start", "stop"}:
            buzzer_control(buzzer_settings, pattern)


def _coordinator_loop(state, config, hardware_config, codes, stop_event):
    from components.led import led_control

    led_settings = dict(hardware_config.get(codes.get("dl"), {"simulated": True}))
    buzzer_settings = dict(hardware_config.get(codes.get("db"), {"simulated": True}))
    if codes.get("dl"):
        led_settings.setdefault("code", codes.get("dl"))
    if codes.get("db"):
        buzzer_settings.setdefault("code", codes.get("db"))

    led_on = False
    last_key_at = 0.0
    last_attempt_at = 0.0

    interval = config.get("coordinator_interval", 0.2)

    key_beep = config.get("key_beep", "short")
    success_beep = config.get("success_beep", "long")
    failure_beep = config.get("failure_beep", "double_short")

    while not stop_event.is_set():
        snapshot = state.snapshot()

        # key press beep
        if snapshot["key_at"] > last_key_at:
            _enqueue_buzzer(key_beep)
            last_key_at = snapshot["key_at"]

        # password attempt result
        if snapshot["attempt_at"] > last_attempt_at:
            if snapshot["attempt_success"]:
                _enqueue_buzzer(success_beep)
            else:
                _enqueue_buzzer(failure_beep)
            last_attempt_at = snapshot["attempt_at"]

        door_open = bool(snapshot["door_open"])

        if door_open != led_on:
            led_control(led_settings, "on" if door_open else "off")
            led_on = door_open

        time.sleep(interval)


def start_door_coordinator(
    settings, device_config, hardware_config, threads, stop_event
):
    global _STATE, _BUZZER_QUEUE

    config = settings.get("door_logic", {})
    if not config.get("enabled", True):
        return False

    codes = config.get("codes", {})

    sensors = set(device_config.get("sensors", []))
    actuators = set(device_config.get("actuators", []))
    required = {
        codes.get("ds"),
        codes.get("dpir"),
        codes.get("dus"),
        codes.get("dms"),
        codes.get("dl"),
        codes.get("db"),
    }
    missing = [
        code
        for code in required
        if code and code not in sensors and code not in actuators
    ]
    if missing:
        return False

    _STATE = DoorState(codes)
    _BUZZER_QUEUE = queue.Queue()

    pause_seconds = config.get("failure_beep_pause_seconds", 0.15)
    buzzer_settings = dict(hardware_config.get(codes.get("db"), {"simulated": True}))
    if codes.get("db"):
        buzzer_settings.setdefault("code", codes.get("db"))
    buzzer_thread = threading.Thread(
        target=_buzzer_worker,
        args=(buzzer_settings, stop_event, pause_seconds),
        name="door-buzzer-worker",
        daemon=True,
    )
    threads.append(buzzer_thread)
    buzzer_thread.start()

    coordinator_thread = threading.Thread(
        target=_coordinator_loop,
        args=(_STATE, config, hardware_config, codes, stop_event),
        name="door-coordinator",
        daemon=True,
    )
    threads.append(coordinator_thread)
    coordinator_thread.start()
    return True
