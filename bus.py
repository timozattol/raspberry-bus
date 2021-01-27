from datetime import datetime
from typing import Dict

import attr
import pytz as pytz
import requests

from config import STATION_ID, DIRECTION_B, DIRECTION_A, BUS_NUMBER

TRANSPORT_API = "http://transport.opendata.ch/v1/stationboard"


@attr.s
class Transport:
    number = attr.ib(type=str)
    destination = attr.ib(type=str)
    departure_dt = attr.ib(type=datetime)
    delay = attr.ib(type=str)


def parse_transport(transport_json: Dict) -> Transport:
    number = transport_json["number"]
    destination = transport_json["to"]
    stop = transport_json["stop"]
    departure = stop["departure"]
    delay = stop["delay"]
    departure_dt = datetime.fromisoformat(f"{departure[:22]}:{departure[22:]}")

    return Transport(number, destination, departure_dt, delay)


def in_the_future(transport: Transport, now: datetime):
    return transport.departure_dt >= now


def get_next_transports():
    parameters = dict(id=STATION_ID)
    response = requests.get(TRANSPORT_API, params=parameters)

    stationboard = response.json()["stationboard"]

    transports = [parse_transport(transport) for transport in stationboard]
    transports = [transport for transport in transports if transport.number == BUS_NUMBER]

    now = datetime.now(pytz.utc)

    transports = [transport for transport in transports if in_the_future(transport, now)]
    transports = sorted(transports, key=lambda t: t.departure_dt)

    transports_for_a = [transport for transport in transports if DIRECTION_A in transport.destination]
    transports_for_b = [transport for transport in transports if DIRECTION_B in transport.destination]

    next_for_a = transports_for_a[0] if len(transports_for_a) >= 1 else None
    next_for_b = transports_for_b[0] if len(transports_for_b) >= 1 else None

    return next_for_a, next_for_b


def send_next_transport_message(next_for_a, next_for_b):
    print(f"Next transport for {DIRECTION_A}: {next_for_a}")
    print(f"Next transport for {DIRECTION_B}: {next_for_b}")


def main():
    next_for_a, next_for_b = get_next_transports()
    send_next_transport_message(next_for_a, next_for_b)


if __name__ == "__main__":
    main()
