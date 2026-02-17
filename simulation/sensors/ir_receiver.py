import time
from datetime import datetime

import RPi.GPIO as GPIO


class IRReceiver:
    def __init__(self, pin):
        self.pin = pin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN)

    def get_binary(self):
        # Internal vars
        num1s = 0  # Number of consecutive 1s read
        binary = 1  # The binary value
        command = []  # The list to store pulse times in
        previous_value = 0  # The last value
        value = GPIO.input(self.pin)  # The current value

        # Waits for the sensor to pull pin low
        while value:
            time.sleep(0.0001)  # This sleep decreases CPU utilization immensely
            value = GPIO.input(self.pin)

        # Records start time
        start_time = datetime.now()

        while True:
            # If change detected in value
            if previous_value != value:
                now = datetime.now()
                pulse_time = now - start_time  # Calculate the time of pulse
                start_time = now  # Reset start time
                command.append(
                    (previous_value, pulse_time.microseconds)
                )  # Store recorded data

            # Updates consecutive 1s variable
            if value:
                num1s += 1
            else:
                num1s = 0

            # Breaks program when the amount of 1s surpasses 10000
            if num1s > 10000:
                break

            # Re-reads pin
            previous_value = value
            value = GPIO.input(self.pin)

        # Converts times to binary
        for typ, tme in command:
            if typ == 1:  # If looking at rest period
                if tme > 1000:  # If pulse greater than 1000us
                    binary = binary * 10 + 1  # Must be 1
                else:
                    binary *= 10  # Must be 0

        if len(str(binary)) > 34:  # Sometimes, there is some stray characters
            binary = int(str(binary)[:34])

        return binary

    # Convert value to hex
    @staticmethod
    def convert_hex(binary_value):
        return hex(int(str(binary_value), 2))


def run_ir_loop(ir: IRReceiver, callback, stop_event, code):
    while True:
        in_data = ir.convert_hex(ir.get_binary())
        for button in range(len(buttons)):  # Runs through every value in list
            if hex(buttons[button]) == in_data:  # Checks this against incoming
                callback(button_names[button], code)
        if stop_event.is_set():
            break


buttons = [
    0x300FF22DD,
    0x300FFC23D,
    0x300FF629D,
    0x300FFA857,
    0x300FF9867,
    0x300FFB04F,
    0x300FF6897,
    0x300FF02FD,
    0x300FF30CF,
    0x300FF18E7,
    0x300FF7A85,
    0x300FF10EF,
    0x300FF38C7,
    0x300FF5AA5,
    0x300FF42BD,
    0x300FF4AB5,
    0x300FF52AD,
]  # HEX code list

button_names = [
    "LEFT",
    "RIGHT",
    "UP",
    "DOWN",
    "2",
    "3",
    "1",
    "OK",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "*",
    "0",
    "#",
]  # String list in same order as HEX list
