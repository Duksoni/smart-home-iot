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
