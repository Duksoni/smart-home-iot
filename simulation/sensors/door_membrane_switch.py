import time

import RPi.GPIO as GPIO

DEFAULT_ROW_PINS = [25, 8, 7, 1]
DEFAULT_COL_PINS = [12, 16, 20, 21]
DEFAULT_KEYMAP = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"],
]


class DMS:
    def __init__(
        self,
        row_pins=None,
        col_pins=None,
        keymap=None,
        debounce=0.15,
        settle=0.001,
    ):
        self.row_pins = list(row_pins) if row_pins else list(DEFAULT_ROW_PINS)
        self.col_pins = list(col_pins) if col_pins else list(DEFAULT_COL_PINS)
        self.keymap = keymap or DEFAULT_KEYMAP
        if len(self.keymap) != len(self.row_pins):
            raise ValueError("Keymap rows do not match row pins")
        for row in self.keymap:
            if len(row) != len(self.col_pins):
                raise ValueError("Keymap columns do not match column pins")
        self.debounce = debounce
        self.settle = settle
        self._pressed_key = None
        self._last_key_time = 0.0

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        for row_pin in self.row_pins:
            GPIO.setup(row_pin, GPIO.OUT)
            GPIO.output(row_pin, GPIO.LOW)

        for col_pin in self.col_pins:
            GPIO.setup(col_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def _scan_row(self, row_pin, keys):
        GPIO.output(row_pin, GPIO.HIGH)
        if self.settle:
            time.sleep(self.settle)
        for col_pin, key in zip(self.col_pins, keys):
            if GPIO.input(col_pin) == 1:
                GPIO.output(row_pin, GPIO.LOW)
                return key
        GPIO.output(row_pin, GPIO.LOW)
        return None

    def scan(self):
        for row_pin, keys in zip(self.row_pins, self.keymap):
            key = self._scan_row(row_pin, keys)
            if key is not None:
                return key
        return None

    def read_key(self):
        key = self.scan()
        if key is None:
            self._pressed_key = None
            return None

        now = time.monotonic()
        if key == self._pressed_key:
            return None
        if self.debounce and (now - self._last_key_time) < self.debounce:
            return None
        self._pressed_key = key
        self._last_key_time = now
        return key

    def cleanup(self):
        for row_pin in self.row_pins:
            GPIO.output(row_pin, GPIO.LOW)


def run_dms_loop(dms, delay, callback, stop_event, code):
    while True:
        key = dms.read_key()
        if key is not None:
            callback(key, code)
        if stop_event.is_set():
            break
        time.sleep(delay)
