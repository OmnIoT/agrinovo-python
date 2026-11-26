"""Finds every sensor on the RS485 line and prints its Modbus address.

Use it when a sensor does not answer at the address you expect.

    python scan_bus.py /dev/ttyUSB0
"""

import sys

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

with agrinovo.Bus(PORT) as bus:
    print("Scanning addresses 1 to 247...")
    found = agrinovo.scan(bus, found=lambda address: print(f"Sensor at address {address}"))
    print(f"{len(found)} found.")
