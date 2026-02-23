import time
from typing import List

import RPi.GPIO as GPIO


class Display4Segment:
    def __init__(self, segment_pins: List[int], digit_pins: List[int]):
        self.segments = segment_pins
        self.digits = digit_pins
        
        GPIO.setmode(GPIO.BCM)
        for segment in segment_pins:
            GPIO.setup(segment, GPIO.OUT)
            GPIO.output(segment, 0)

        for digit in digit_pins:
            GPIO.setup(digit, GPIO.OUT)
            GPIO.output(digit, 1)
 
        self.num = {
            ' ':(0,0,0,0,0,0,0),
            '0':(1,1,1,1,1,1,0),
            '1':(0,1,1,0,0,0,0),
            '2':(1,1,0,1,1,0,1),
            '3':(1,1,1,1,0,0,1),
            '4':(0,1,1,0,0,1,1),
            '5':(1,0,1,1,0,1,1),
            '6':(1,0,1,1,1,1,1),
            '7':(1,1,1,0,0,0,0),
            '8':(1,1,1,1,1,1,1),
            '9':(1,1,1,1,0,1,1)
        }

    def display(self, digits: str):
        for digit in range(4):
            for loop in range(0,7):
                GPIO.output(self.segments[loop], self.num[digits[digit]][loop])
            GPIO.output(self.digits[digit], 0)
            time.sleep(0.001)
            GPIO.output(self.digits[digit], 1)

    def clear(self):
        for digit in range(4):
            GPIO.output(self.digits[digit], 1)
