"""Agrinovo DO-110 dissolved oxygen probe.

Prints dissolved oxygen and temperature every 5 seconds.

Sensor cable
  Red              supply +, 12-24 V DC
  Black            supply ground
  Yellow or white  RS485 A
  Green            RS485 B

The computer talks to the sensor through a USB to RS485 adapter: A to A,
B to B. Run this file with the adapter's port, for example:

    python do_110.py /dev/ttyUSB0

https://agrinovo.io/products/sensors/aqua/do/do-110-titanium-probe/
"""

import sys
import time

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

with agrinovo.Bus(PORT, baudrate=9600) as bus:
    probe = agrinovo.DO110(bus)  # Modbus address 1
    while True:
        try:
            reading = probe.read()
            print(f"Dissolved oxygen: {reading.dissolved_oxygen:.2f} mg/L")
            print(f"Temperature: {reading.temperature:.2f} °C")
        except agrinovo.AgrinovoError as error:
            print(error)
        time.sleep(5)
