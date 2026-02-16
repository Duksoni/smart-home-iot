import time

import smbus


class PCF8574_I2C:
    OUPUT = 0
    INPUT = 1

    def __init__(self, address):
        # Note you need to change the bus number to 0 if running on a revision 1 Raspberry Pi.
        self.bus = smbus.SMBus(1)
        self.address = address
        self.currentValue = 0
        self.write_byte(0)  # I2C test.

    def read_byte(self):  # Read PCF8574 all port of the data
        # value = self.bus.read_byte(self.address)
        return self.currentValue  # value

    def write_byte(self, value):  # Write data to PCF8574 port
        self.currentValue = value
        self.bus.write_byte(self.address, value)

    def digital_read(self, pin):  # Read PCF8574 one port of the data
        value = self.read_byte()
        return (value & (1 << pin) == (1 << pin)) and 1 or 0

    def digital_write(self, pin, newvalue):  # Write data to PCF8574 one port
        value = self.currentValue  # bus.read_byte(address)
        if newvalue == 1:
            value |= 1 << pin
        elif newvalue == 0:
            value &= ~(1 << pin)
        self.write_byte(value)

    def destroy(self):
        self.bus.close()


def loop():
    mcp = PCF8574_I2C(0x27)
    try:
        while True:
            # mcp.writeByte(0xff)
            mcp.digital_write(3, 1)
            print("Is 0xff? %x" % (mcp.read_byte()))
            time.sleep(1)
            mcp.write_byte(0x00)
            # mcp.digitalWrite(7,1)
            print("Is 0x00? %x" % (mcp.read_byte()))
            time.sleep(1)
    finally:
        mcp.destroy()


class PCF8574_GPIO:  # Standardization function interface
    OUT = 0
    IN = 1
    BCM = 0
    BOARD = 0

    def __init__(self, address):
        self.chip = PCF8574_I2C(address)
        self.address = address

    def setmode(
        self, mode
    ):  # PCF8574 port belongs to two-way IO, do not need to set the input and output model
        pass

    def setup(self, pin, mode):
        pass

    def input(self, pin):  # Read PCF8574 one port of the data
        return self.chip.digital_read(pin)

    def output(self, pin, value):  # Write data to PCF8574 one port
        self.chip.digital_write(pin, value)


if __name__ == "__main__":
    print("Program is starting ... ")
    loop()
