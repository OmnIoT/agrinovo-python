"""Gives a sensor a new Modbus address, so several can share one RS485 line.

Connect only the sensor you want to change, set the two addresses below and
run the script once.

This script uses the pH probe. Change the class to match your sensor.

    python change_address.py /dev/ttyUSB0
"""

import sys

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
CURRENT_ADDRESS = 1
NEW_ADDRESS = 2

with agrinovo.Bus(PORT) as bus:
    probe = agrinovo.PH100(bus, address=CURRENT_ADDRESS)
    try:
        probe.change_address(NEW_ADDRESS)
        print(f"Done. The sensor now answers at address {probe.address}")
    except agrinovo.AgrinovoError as error:
        print(f"Address not changed: {error}")
