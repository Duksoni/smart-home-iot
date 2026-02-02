import RPi.GPIO as GPIO
import time


class DS:
    DOOR_CLOSED = 0
    DOOR_OPEN = 1

    def __init__(self, pin, debounce_ms=100):
        self.pin = pin
        self.debounce = debounce_ms / 1000
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read(self):
        first_reading = GPIO.input(self.pin)
        time.sleep(self.debounce)
        second_reading = GPIO.input(self.pin)

        if first_reading == second_reading:
            # LOW means door open (button pressed)
            if second_reading == GPIO.LOW:
                return self.DOOR_OPEN
            return self.DOOR_CLOSED

        # If readings disagree, wait a bit and try again
        time.sleep(self.debounce)
        return self.read()


def run_ds_loop(ds, delay, callback, stop_event, code):
    last_state = None
    while not stop_event.is_set():
        state = ds.read()
        if state != last_state:
            callback(state, code)
            last_state = state

        time.sleep(delay)
