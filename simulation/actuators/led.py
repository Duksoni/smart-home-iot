import RPi.GPIO as GPIO


class DL:
    def __init__(self, pin, active_high=True):
        self.pin = pin
        self.active_high = active_high
        self._state = False

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)

        self.off()

    def on(self):
        self._state = True
        GPIO.output(self.pin, GPIO.HIGH if self.active_high else GPIO.LOW)

    def off(self):
        self._state = False
        GPIO.output(self.pin, GPIO.LOW if self.active_high else GPIO.HIGH)

    def toggle(self):
        if self._state: self.off()
        else: self.on()

    def cleanup(self):
        self.off()