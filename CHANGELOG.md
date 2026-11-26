# Changelog

## 0.9.0

- RS485 Modbus RTU bus over a serial port, with retries, timeout and frame debugging.
- Sensor classes for 35 models, the same ones as the Agrinovo Arduino library 0.9.0.
- Address change, calibration and brush commands where the sensor has them.
- `GenericSensor` for a register table of your own, and `scan()` to find addresses.
- `python -m agrinovo` to list models, scan a line and read a sensor from the command line.
- Examples: one per sensor, scan, change address, multiple sensors, generic sensor, CSV logging.
