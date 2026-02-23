import RPi.GPIO as GPIO


class DPIR:
    MOTION = 1
    NO_MOTION = 0

    def __init__(self, pin):
        self.pin = pin
        if GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.IN)

    def read(self):
        value = GPIO.input(self.pin)
        return self.MOTION if value == GPIO.HIGH else self.NO_MOTION


def run_dpir_loop(dpir: DPIR, delay, code, callback, stop_event):
    last_state = None
    while not stop_event.is_set():
        state = dpir.read()
        if state != last_state:
            last_state = state
            if state == DPIR.MOTION:
                callback(code)
        stop_event.wait(delay)
