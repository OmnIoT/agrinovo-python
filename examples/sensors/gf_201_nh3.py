"""Agrinovo GF-201-NH3 ammonia gas detector.

Prints ammonia every 5 seconds.

Sensor terminals
  24V+  supply +, 12-30 V DC
  GND   supply ground
  A+    RS485 A
  B-    RS485 B

The computer talks to the sensor through a USB to RS485 adapter: A to A,
B to B. Run this file with the adapter's port, for example:

    python gf_201_nh3.py /dev/ttyUSB0

https://agrinovo.io/products/sensors/environmental/gf-201-nh3-ammonia-gas-sensor/
"""

import sys
import time

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

with agrinovo.Bus(PORT, baudrate=9600) as bus:
    sensor = agrinovo.GF201NH3(bus)  # Modbus address 1
    while True:
        try:
            reading = sensor.read()
            print(f"Ammonia: {reading.ammonia:.1f} ppm")
        except agrinovo.AgrinovoError as error:
            print(error)
        time.sleep(5)
