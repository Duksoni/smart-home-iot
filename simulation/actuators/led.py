import RPi.GPIO as GPIO


class DL:
    def __init__(self, pin):
        self.pin = pin
        self.current_mode = GPIO.LOW
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)

    def toggle(self):
        self.current_mode = GPIO.HIGH if self.current_mode == GPIO.LOW else GPIO.LOW