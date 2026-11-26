# TVOC-100: TVOC air quality sensor

Class `agrinovo.TVOC100`. [Product page](https://agrinovo.io/products/sensors/environmental/tvoc-100-rs485-air-quality-sensor/) · [Datasheet](https://agrinovo.io/datasheets/sensors/AGRINOVO-TVOC-100_Datasheet.pdf)

## Wiring

| Terminal | Connect to |
|:--|:--|
| V+ | Supply + (5-12 V DC) |
| GND | Supply ground |
| A+ | RS485 A |
| B- | RS485 B |

A and B go to the A and B terminals of the RS485 adapter. When the adapter has a ground terminal, join it to the supply ground.

## Values

`read()` returns these, by name:

| Name | Value | Unit | Register | Stored as |
|:--|:--|:--|:--|:--|
| `tvoc` | TVOC | ppb | 0x0003 | unsigned 16-bit |
| `co2_equivalent` | CO2 equivalent | ppm | 0x0004 | unsigned 16-bit |

The sensor is read with function 0x03, 2 registers from 0x0003, at 9600 baud 8N1. Factory address: 1.

## Settings and calibration

| Method | What it does |
|:--|:--|
| `change_address(new_address)` | Gives the sensor a new Modbus address and keeps talking to it there. |

A method returns once the sensor has confirmed the command and raises `agrinovo.AgrinovoError` when it has not.

## Example

```python
"""Agrinovo TVOC-100 TVOC air quality sensor.

Prints TVOC and CO2 equivalent every 5 seconds.

Sensor terminals
  V+   supply +, 5-12 V DC
  GND  supply ground
  A+   RS485 A
  B-   RS485 B

The computer talks to the sensor through a USB to RS485 adapter: A to A,
B to B. Run this file with the adapter's port, for example:

    python tvoc_100.py /dev/ttyUSB0

https://agrinovo.io/products/sensors/environmental/tvoc-100-rs485-air-quality-sensor/
"""

import sys
import time

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

with agrinovo.Bus(PORT, baudrate=9600) as bus:
    sensor = agrinovo.TVOC100(bus)  # Modbus address 1
    while True:
        try:
            reading = sensor.read()
            print(f"TVOC: {reading.tvoc:.0f} ppb")
            print(f"CO2 equivalent: {reading.co2_equivalent:.0f} ppm")
        except agrinovo.AgrinovoError as error:
            print(error)
        time.sleep(5)
```
