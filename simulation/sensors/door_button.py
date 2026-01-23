import RPi.GPIO as GPIO
import time

class DS(object):
    DOOR_CLOSED = 0
    DOOR_OPEN = 1

    def __init__(self, pin):
        self.pin = pin
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read(self):
        value = GPIO.input(self.pin)
        if value == GPIO.HIGH:
            return self.DOOR_OPEN
        return self.DOOR_CLOSED
    
def run_ds_loop(ds, delay, callback, stop_event, code):
    last_state = None
    while True:
        state = ds.read()
        if state != last_state:
            callback(state, code)
            last_state = state
        if  stop_event.is_set():
            break
        time.sleep(delay)