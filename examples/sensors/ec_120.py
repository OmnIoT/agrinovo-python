"""Agrinovo EC-120 conductivity probe.

Prints conductivity, resistivity, temperature, TDS and salinity every 5 seconds.

Sensor cable
  Red     supply +, 7-24 V DC
  Black   supply ground
  Yellow  RS485 A
  Green   RS485 B

The computer talks to the sensor through a USB to RS485 adapter: A to A,
B to B. Run this file with the adapter's port, for example:

    python ec_120.py /dev/ttyUSB0

https://agrinovo.io/products/sensors/aqua/ec/ec-120-probe/
"""

import sys
import time

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

with agrinovo.Bus(PORT, baudrate=9600) as bus:
    probe = agrinovo.EC120(bus)  # Modbus address 1
    while True:
        try:
            reading = probe.read()
            print(f"Conductivity: {reading.conductivity:.3f} mS/cm")
            print(f"Resistivity: {reading.resistivity:.1f} ohm cm")
            print(f"Temperature: {reading.temperature:.1f} °C")
            print(f"TDS: {reading.tds:.1f} ppm")
            print(f"Salinity: {reading.salinity:.1f} ppm")
        except agrinovo.AgrinovoError as error:
            print(error)
        time.sleep(5)
