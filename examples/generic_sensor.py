"""Reads a sensor this package has no class for yet, from the register table
in its datasheet.

The example sensor keeps temperature in register 0 (signed, tenths of a
degree) and humidity in register 1 (tenths of a percent), read with
function 0x03 at address 1. Replace the table with your sensor's.

    python generic_sensor.py /dev/ttyUSB0
"""

import sys
import time

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

# Name, register offset, how the value is stored, and what to multiply it by.
# The storage types are listed in agrinovo.TYPES.
FIELDS = [
    ("temperature", 0, "i16", 0.1),
    ("humidity", 1, "u16", 0.1),
]

with agrinovo.Bus(PORT) as bus:
    # address, function, first register, number of registers, table
    sensor = agrinovo.GenericSensor(bus, 1, 0x03, 0x0000, 2, FIELDS)
    while True:
        try:
            reading = sensor.read()
            print(f"Temperature: {reading['temperature']:.1f} °C")
            print(f"Humidity: {reading['humidity']:.1f} %")
        except agrinovo.AgrinovoError as error:
            print(error)
        time.sleep(5)
