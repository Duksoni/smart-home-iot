import RPi.GPIO as GPIO
import time

class DUS:
    def __init__(self, trig_pin, echo_pin):
        self.trig = trig_pin
        self.echo = echo_pin

        GPIO.setup(self.trig, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)

        GPIO.output(self.trig, False)
        time.sleep(0.5)

    def read_distance(self):
        GPIO.output(self.trig, True)
        time.sleep(0.00001)
        GPIO.output(self.trig, False)

        start_time = time.time()
        timeout = start_time + 0.04

        while GPIO.input(self.echo) == 0:
            start_time = time.time()
            if start_time > timeout:
                return None
            
        stop_time = time.time()
        while GPIO.input(self.echo) == 1:
            stop_time = time.time()
            if stop_time > timeout:
                return None
            
        pulse_duration = stop_time - start_time
        distance = (pulse_duration * 34300) / 2
        return round(distance, 2)
    
def run_dus_loop(dus, delay, callback, stop_event, code):
    while True:
        distance = dus.read_distance()
        callback(distance, code)
        if stop_event.is_set():
            break
        time.sleep(delay)