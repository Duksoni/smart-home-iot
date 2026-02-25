#!/usr/bin/env python3
import math

from helper.MPU6050 import MPU6050
import time
import os

class GSG:
    """
    Gyroscope sensor wrapper for MPU-6050.
    Produces magnitude of angular velocity vector (deg/s).
    """

    def __init__(self):
        self.mpu = MPU6050()
        self.mpu.dmp_initialize()

    def read(self) -> float:
        """
        Read gyroscope and return angular velocity magnitude (deg/s).
        """
        gyro = self.mpu.get_rotation()

        # convert to deg/s
        gx = gyro[0] / 131.0
        gy = gyro[1] / 131.0
        gz = gyro[2] / 131.0

        magnitude = math.sqrt(gx * gx + gy * gy + gz * gz)
        # filter noise
        if magnitude < 0.5:
            magnitude = 0.0 

        return magnitude
    
def run_gsg_loop(gsg: GSG, delay: float, callback, stop_event):
    """
    Continuous polling loop (same pattern as DHT).
    """
    while not stop_event.is_set():
        try:
            value = gsg.read()
            callback(value)
        except Exception as e:
            print(f"[GPIO] GSG read error: {e}")

        time.sleep(delay)
