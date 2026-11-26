"""Checks a sensor from the command line.

    python -m agrinovo list
    python -m agrinovo scan /dev/ttyUSB0
    python -m agrinovo read NO3-100 /dev/ttyUSB0 --address 3 --debug
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import SENSORS, AgrinovoError, Bus, __version__, scan


def _bus_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("port", help="serial port of the RS485 adapter, for example /dev/ttyUSB0 or COM3")
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--debug", action="store_true", help="print every frame sent and received")


def main(argv: Optional[List[str]] = None, port: object = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m agrinovo", description="Check an Agrinovo sensor.")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="the supported models")
    scanner = commands.add_parser("scan", help="find the address of whatever is connected")
    _bus_options(scanner)
    reader = commands.add_parser("read", help="read a sensor once")
    reader.add_argument("model", help="for example NO3-100")
    _bus_options(reader)
    reader.add_argument("--address", type=int, help="Modbus address, when it is not the factory one")
    args = parser.parse_args(argv)

    if args.command == "list":
        for model, cls in SENSORS.items():
            print("%-12s %s" % (model, cls.NAME))
        return 0

    if args.command == "read":
        cls = SENSORS.get(args.model.upper())
        if cls is None:
            print("Unknown model %s. Run: python -m agrinovo list" % args.model, file=sys.stderr)
            return 2

    # `port` lets the tests hand in a stand-in serial port.
    with Bus(port or args.port, baudrate=args.baudrate, debug=args.debug) as bus:
        if args.command == "scan":
            print("Scanning addresses 1 to 247...")
            found = scan(bus, found=lambda address: print("Sensor at address %d" % address))
            print("%d found." % len(found))
            return 0
        sensor = cls(bus, args.address)
        try:
            reading = sensor.read()
        except AgrinovoError as error:
            print("%s at address %d: %s" % (cls.MODEL, sensor.address, error), file=sys.stderr)
            return 1
        for field, value in zip(cls.FIELDS, reading):
            print("%s: %.*f %s" % (field.label, field.decimals, value, field.unit))
        return 0


if __name__ == "__main__":
    sys.exit(main())
