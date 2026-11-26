"""Reads three sensors that share one RS485 line, each at its own address.

Give each sensor its address first with change_address.py, one at a time.

    python multiple_sensors.py /dev/ttyUSB0
"""

import sys
import time

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

with agrinovo.Bus(PORT) as bus:
    ph = agrinovo.PH100(bus, address=1)
    ec = agrinovo.EC120(bus, address=2)
    oxygen = agrinovo.DO100(bus, address=3)
    while True:
        try:
            print(f"pH: {ph.read().ph:.2f}")
            print(f"Conductivity: {ec.read().conductivity:.3f} mS/cm")
            print(f"Dissolved oxygen: {oxygen.read().dissolved_oxygen:.2f} mg/L")
        except agrinovo.AgrinovoError as error:
            print(error)
        time.sleep(5)
