import RPi.GPIO as GPIO


class BRGB:
    def __init__(self, red_pin, green_pin, blue_pin):
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.red_pin, GPIO.OUT)
        GPIO.setup(self.green_pin, GPIO.OUT)
        GPIO.setup(self.blue_pin, GPIO.OUT)

        self.turn_off()

    def turn_off(self):
        GPIO.output(self.red_pin, GPIO.LOW)
        GPIO.output(self.green_pin, GPIO.LOW)
        GPIO.output(self.blue_pin, GPIO.LOW)

    def white_light(self):
        GPIO.output(self.red_pin, GPIO.HIGH)
        GPIO.output(self.green_pin, GPIO.HIGH)
        GPIO.output(self.blue_pin, GPIO.HIGH)

    def red_light(self):
        GPIO.output(self.red_pin, GPIO.HIGH)
        GPIO.output(self.green_pin, GPIO.LOW)
        GPIO.output(self.blue_pin, GPIO.LOW)

    def green_light(self):
        GPIO.output(self.red_pin, GPIO.LOW)
        GPIO.output(self.green_pin, GPIO.HIGH)
        GPIO.output(self.blue_pin, GPIO.LOW)

    def blue_light(self):
        GPIO.output(self.red_pin, GPIO.LOW)
        GPIO.output(self.green_pin, GPIO.LOW)
        GPIO.output(self.blue_pin, GPIO.HIGH)

    def cyan_light(self):
        GPIO.output(self.red_pin, GPIO.LOW)
        GPIO.output(self.green_pin, GPIO.HIGH)
        GPIO.output(self.blue_pin, GPIO.HIGH)

    def magenta_light(self):
        GPIO.output(self.red_pin, GPIO.HIGH)
        GPIO.output(self.green_pin, GPIO.LOW)
        GPIO.output(self.blue_pin, GPIO.HIGH)

    def yellow_light(self):
        GPIO.output(self.red_pin, GPIO.HIGH)
        GPIO.output(self.green_pin, GPIO.HIGH)
        GPIO.output(self.blue_pin, GPIO.LOW)


