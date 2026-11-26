"""Agrinovo EC-110 conductivity and salinity probe.

Prints conductivity, temperature, TDS and salinity every 5 seconds.

Sensor cable
  Red     supply +, 12-24 V DC
  Black   supply ground
  Yellow  RS485 A
  Green   RS485 B

The computer talks to the sensor through a USB to RS485 adapter: A to A,
B to B. Run this file with the adapter's port, for example:

    python ec_110.py /dev/ttyUSB0

https://agrinovo.io/products/sensors/aqua/ec/ec-110-probe/
"""

import sys
import time

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

with agrinovo.Bus(PORT, baudrate=9600) as bus:
    probe = agrinovo.EC110(bus)  # Modbus address 1
    while True:
        try:
            reading = probe.read()
            print(f"Conductivity: {reading.conductivity:.0f} µS/cm")
            print(f"Temperature: {reading.temperature:.1f} °C")
            print(f"TDS: {reading.tds:.0f} ppm")
            print(f"Salinity: {reading.salinity:.1f} ppt")
        except agrinovo.AgrinovoError as error:
            print(error)
        time.sleep(5)
