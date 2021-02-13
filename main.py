import time
from datetime import datetime
from queue import Empty, Queue
from threading import Thread
from typing import Optional, Tuple

import attr

from bus import get_next_transports, Transport
# How much time to wait between each request to the transport API
from four_digits_lcd import FourDigitsLCDController, Digit

TRANSPORT_UPDATE_TIME = 30


@attr.s
class TransportMessage:
    """Message from the transport thread to the display thread"""
    next_transport_for_a = attr.ib(type=Transport)
    next_transport_for_b = attr.ib(type=Transport)


class TransportThread:
    def __init__(self, communication_queue: Queue):
        self.thread = Thread(target=self.transport_loop)
        self.communication_queue = communication_queue

    def transport_loop(self):
        while True:
            next_for_a, next_for_b = get_next_transports()

            print(f"Next transports found. A:{next_for_a} B:{next_for_b}")

            self.communication_queue.put(TransportMessage(next_for_a, next_for_b))
            time.sleep(TRANSPORT_UPDATE_TIME)

    def start(self):
        self.thread.start()


class DisplayThread:
    def __init__(self, communication_queue: Queue):
        self.thread = Thread(target=self.display_loop)
        self.communication_queue = communication_queue

        self.display_controller = FourDigitsLCDController()

    def display_loop(self):
        while True:
            try:
                transport_message = self.communication_queue.get_nowait()
                self.update_digits(transport_message)
            except Empty:
                pass

            self.display_controller.update_display()

    @staticmethod
    def transport_to_digits(transport: Optional[Transport]) -> Tuple[Digit, Digit]:
        now = datetime.now()

        digits = (Digit(digit=None, contains_dot=True), Digit(digit=None, contains_dot=True))

        if transport:
            a_departs_in = (now - transport.departure_dt)

            hours_left = a_departs_in.seconds // 3600
            minutes_left = (a_departs_in.seconds // 60) % 60

            # If departure is in more than an hour, don't display minutes left
            if hours_left == 0:
                minutes_str = str(minutes_left)
                digits = (
                    Digit(digit=minutes_str[0], contains_dot=False),
                    Digit(digit=minutes_str[1], contains_dot=False),
                )

        return digits

    def update_digits(self, transport_message: TransportMessage):
        a_digits = self.transport_to_digits(transport_message.next_transport_for_a)
        b_digits = self.transport_to_digits(transport_message.next_transport_for_b)
        four_digits = a_digits + b_digits
        self.display_controller.set_digits(four_digits)

    def start(self):
        self.thread.start()


def main():
    communication_queue = Queue()
    transport_thread = TransportThread(communication_queue)
    display_thread = DisplayThread(communication_queue)

    transport_thread.start()
    display_thread.start()

    # TODO maybe handle SIGTERM / SIGINT and exit gracefully


if __name__ == '__main__':
    main()
