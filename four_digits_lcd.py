# Adapted from https://peppe8o.com/how-to-control-a-4-digit-7-segment-display-from-raspberry-pi-with-python/

import time
from typing import Optional

import RPi.GPIO as GPIO
import attr
import yaml

GPIO_YAML = "gpio.yaml"
SLEEP_TIME = 0.005


@attr.s
class Digit:
    # None if nothing should be displayed
    digit = attr.ib(type=Optional[int])
    contains_dot = attr.ib(type=bool)


# Rows = digits from 0 to 9
# Columns = signal to send to each bar
digit_to_bar_matrix = [
    [1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 0, 0, 0, 0],
    [1, 1, 0, 1, 1, 0, 1],
    [1, 1, 1, 1, 0, 0, 1],
    [0, 1, 1, 0, 0, 1, 1],
    [1, 0, 1, 1, 0, 1, 1],
    [1, 0, 1, 1, 1, 1, 1],
    [1, 1, 1, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 0, 1, 1],
]


class FourDigitsLCDController:
    def __init__(self):
        with open(GPIO_YAML, "r") as f:
            self.gpio_config = yaml.load(f, Loader=yaml.Loader)
            self.digits = [Digit(0, False)] * 4

        self.initialize_gpio()

    def initialize_gpio(self):
        # Use BCM GPIO referencing
        GPIO.setmode(GPIO.BCM)

        for pin in self.gpio_config["digit_selection"] + self.gpio_config["bars"] + [self.gpio_config["dot"]]:
            GPIO.setup(pin, GPIO.OUT)

    def activate_digit_index(self, digit_index):
        # The selected digit is indicated with a low signal (0)
        selection_mask = [1, 1, 1, 1]
        selection_mask[digit_index] = 0

        GPIO.output(self.gpio_config["digit_selection"], selection_mask)

    def display_black_digit(self):
        GPIO.output(self.gpio_config["bars"], 0)

    def display_digit(self, digit: int):
        GPIO.output(self.gpio_config["bars"], digit_to_bar_matrix[digit])

    def display_dot(self):
        GPIO.output(self.gpio_config["dot"], 1)

    def display_black_dot(self):
        GPIO.output(self.gpio_config["dot"], 0)

    def update_display(self):
        for digit_index, digit in enumerate(self.digits):
            self.activate_digit_index(digit_index)

            if digit.digit is None:
                self.display_black_digit()
            else:
                self.display_digit(digit.digit)

            if digit.contains_dot:
                self.display_dot()
            else:
                self.display_black_dot()

            time.sleep(SLEEP_TIME)

    @staticmethod
    def exit():
        GPIO.cleanup()


def main():
    controller = FourDigitsLCDController()

    try:
        while True:
            controller.update_display()
    except KeyboardInterrupt:
        print("Cleaning up and exiting")
        controller.exit()


if __name__ == "__main__":
    main()
