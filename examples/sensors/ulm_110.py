"""Agrinovo ULM-110 explosion-proof ultrasonic level meter.

Prints level or distance every 5 seconds.

Sensor terminals
  1  supply +, 24 V DC
  2  supply ground
  5  RS485 A
  6  RS485 B

The computer talks to the sensor through a USB to RS485 adapter: A to A,
B to B. Run this file with the adapter's port, for example:

    python ulm_110.py /dev/ttyUSB0

https://agrinovo.io/products/sensors/sillo/ulm-110-explosion-proof-ultrasonic-level-meter/
"""

import sys
import time

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

with agrinovo.Bus(PORT, baudrate=9600) as bus:
    sensor = agrinovo.ULM110(bus)  # Modbus address 1
    while True:
        try:
            reading = sensor.read()
            print(f"Level or distance: {reading.level:.0f} cm")
        except agrinovo.AgrinovoError as error:
            print(error)
        time.sleep(5)
