import time

import RPi.GPIO as GPIO


class DB:
    def __init__(self, pin, active_high=True, pwm=False, frequency=2000, duty_cycle=50):
        self.pin = pin
        self.active_high = active_high
        self.pwm_enabled = pwm
        self.frequency = frequency
        self.duty_cycle = duty_cycle
        self._pwm = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)

        if self.pwm_enabled:
            self._pwm = GPIO.PWM(pin, self.frequency)

        self._off()

    def _on(self):
        if self.pwm_enabled and self._pwm:
            self._pwm.start(self.duty_cycle)
        else:
            GPIO.output(self.pin, GPIO.HIGH if self.active_high else GPIO.LOW)

    def _off(self):
        if self.pwm_enabled and self._pwm:
            self._pwm.stop()
        GPIO.output(self.pin, GPIO.LOW if self.active_high else GPIO.HIGH)

    def start(self):
        self._on()

    def stop(self):
        self._off()

    def beep(self, duration):
        self._on()
        time.sleep(duration)
        self._off()

    def short_beep(self, duration=0.1):
        self.beep(duration)

    def long_beep(self, duration=0.5):
        self.beep(duration)

    def cleanup(self):
        self._off()
