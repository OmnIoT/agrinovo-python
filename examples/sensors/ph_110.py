"""Agrinovo PH-110 industrial pH sensor.

Prints pH every 5 seconds.

Sensor cable
  Red     supply +, 12-24 V DC
  Black   supply ground
  Green   RS485 A
  Yellow  RS485 B

The computer talks to the sensor through a USB to RS485 adapter: A to A,
B to B. Run this file with the adapter's port, for example:

    python ph_110.py /dev/ttyUSB0

https://agrinovo.io/products/sensors/aqua/ph/ph-110-probe/
"""

import sys
import time

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

with agrinovo.Bus(PORT, baudrate=9600) as bus:
    sensor = agrinovo.PH110(bus)  # Modbus address 1
    while True:
        try:
            reading = sensor.read()
            print(f"pH: {reading.ph:.2f} pH")
        except agrinovo.AgrinovoError as error:
            print(error)
        time.sleep(5)
