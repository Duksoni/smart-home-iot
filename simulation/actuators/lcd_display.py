from drivers.pcf8574 import PCF8574_GPIO

from .lcd_display_adafrut import Adafruit_CharLCD

PCF8574_address = 0x27
PCF8574A_address = 0x3F


class LCD:
    def __init__(self):
        try:
            self.mcp = PCF8574_GPIO(PCF8574_address)
        except:
            try:
                self.mcp = PCF8574_GPIO(PCF8574A_address)
            except:
                print("I2C Address Error !")
                raise

        self.lcd = Adafruit_CharLCD(
            pin_rs=0, pin_e=2, pins_db=[4, 5, 6, 7], GPIO=self.mcp
        )
        self.mcp.output(3, 1)
        self.lcd.begin(16, 2)

    def display(self, first_row: str, second_row: str):
        self.lcd.set_cursor(0, 0)
        self.lcd.message(f"{first_row}\n")
        self.lcd.message(second_row)

    def clear(self):
        self.lcd.clear()
