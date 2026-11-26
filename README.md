# Agrinovo sensor library for Python

Read [Agrinovo](https://agrinovo.io) water, soil and air sensors from a Raspberry Pi or any computer with a USB to RS485 adapter. One class per sensor, values in engineering units, and an example for every model.

```python
import agrinovo

with agrinovo.Bus("/dev/ttyUSB0") as bus:    # the RS485 adapter's serial port
    probe = agrinovo.NO3100(bus)             # nitrate probe at Modbus address 1
    reading = probe.read()
    print(reading.nitrate)                   # mg/L
    print(reading.temperature)               # °C
```

## Supported sensors

<!-- sensors:start -->
| Model | Sensor | Class | Values |
|:--|:--|:--|:--|
| [AG-100](docs/sensors/ag-100.md) | Silver ion probe | `AG100` | silver, electrode signal, temperature |
| [CA-100](docs/sensors/ca-100.md) | Calcium probe | `CA100` | calcium, electrode signal, temperature |
| [CHL-100](docs/sensors/chl-100.md) | Chlorophyll probe | `CHL100` | chlorophyll, temperature |
| [CL-100](docs/sensors/cl-100.md) | Chloride probe | `CL100` | chloride, electrode signal, temperature |
| [CLO2-100](docs/sensors/clo2-100.md) | Chlorine dioxide probe | `CLO2100` | chlorine dioxide, electrode signal, temperature |
| [CO2-100](docs/sensors/co2-100.md) | Dissolved carbon dioxide probe | `CO2100` | dissolved CO2, electrode signal, temperature |
| [CU-100](docs/sensors/cu-100.md) | Copper probe | `CU100` | copper, electrode signal, temperature |
| [DO-100](docs/sensors/do-100.md) | Dissolved oxygen probe | `DO100` | dissolved oxygen, temperature |
| [DO-110](docs/sensors/do-110.md) | Dissolved oxygen probe | `DO110` | dissolved oxygen, temperature |
| [DO-130](docs/sensors/do-130.md) | Self-cleaning dissolved oxygen probe | `DO130` | dissolved oxygen, temperature |
| [EC-100](docs/sensors/ec-100.md) | Conductivity probe | `EC100` | conductivity, temperature |
| [EC-110](docs/sensors/ec-110.md) | Conductivity and salinity probe | `EC110` | conductivity, temperature, TDS, salinity |
| [EC-120](docs/sensors/ec-120.md) | Conductivity probe | `EC120` | conductivity, resistivity, temperature, TDS, salinity |
| [F-100](docs/sensors/f-100.md) | Fluoride probe | `F100` | fluoride, electrode signal, temperature |
| [GF-201-CH4](docs/sensors/gf-201-ch4.md) | Combustible gas detector | `GF201CH4` | combustible gas |
| [GF-201-CO2](docs/sensors/gf-201-co2.md) | Carbon dioxide gas detector | `GF201CO2` | carbon dioxide |
| [GF-201-NH3](docs/sensors/gf-201-nh3.md) | Ammonia gas detector | `GF201NH3` | ammonia |
| [GF-201-O2](docs/sensors/gf-201-o2.md) | Oxygen gas detector | `GF201O2` | oxygen |
| [GF-201](docs/sensors/gf-201.md) | Hydrogen sulfide gas detector | `GF201` | hydrogen sulfide |
| [K-100](docs/sensors/k-100.md) | Potassium probe | `K100` | potassium, electrode signal, temperature |
| [NH3-100](docs/sensors/nh3-100.md) | Ammonia nitrogen probe | `NH3100` | ammonia nitrogen, electrode signal, temperature |
| [NH4-100](docs/sensors/nh4-100.md) | Ammonium probe | `NH4100` | ammonium, electrode signal, temperature |
| [NO2-100](docs/sensors/no2-100.md) | Nitrite probe | `NO2100` | nitrite, electrode signal, temperature |
| [NO3-100](docs/sensors/no3-100.md) | Nitrate probe | `NO3100` | nitrate, electrode signal, temperature |
| [O2-100](docs/sensors/o2-100.md) | Soil oxygen sensor | `O2100` | oxygen |
| [O3-100](docs/sensors/o3-100.md) | Dissolved ozone probe | `O3100` | ozone, electrode signal, temperature |
| [ORP-100](docs/sensors/orp-100.md) | ORP probe | `ORP100` | ORP |
| [PB-100](docs/sensors/pb-100.md) | Lead probe | `PB100` | lead, electrode signal, temperature |
| [PH-100](docs/sensors/ph-100.md) | pH probe | `PH100` | pH |
| [PH-110](docs/sensors/ph-110.md) | Industrial pH sensor | `PH110` | pH |
| [THS-100](docs/sensors/ths-100.md) | Temperature and humidity sensor | `THS100` | temperature, humidity |
| [TUR-100](docs/sensors/tur-100.md) | Turbidity sensor | `TUR100` | turbidity |
| [TVOC-100](docs/sensors/tvoc-100.md) | TVOC air quality sensor | `TVOC100` | TVOC, CO2 equivalent |
| [ULM-100](docs/sensors/ulm-100.md) | Ultrasonic level meter | `ULM100` | level or distance |
| [ULM-110](docs/sensors/ulm-110.md) | Explosion-proof ultrasonic level meter | `ULM110` | level or distance |
<!-- sensors:end -->

Each model has a page under [docs/sensors](docs/sensors) with its wiring, values, settings and a complete script, and a ready-to-run file under [examples/sensors](examples/sensors).

A sensor that is not in the table yet can be read with `agrinovo.GenericSensor` and the register table from its datasheet. See [examples/generic_sensor.py](examples/generic_sensor.py).

## Install

```
pip install agrinovo
```

Python 3.9 or newer. The only dependency is [pyserial](https://pypi.org/project/pyserial/).

## What you need

- A Raspberry Pi, or a PC running Linux, macOS or Windows.
- A USB to RS485 adapter, or an RS485 HAT on the Pi's serial port.
- A DC supply for the sensor. Most models take 12 to 24 V; the sensor's page gives the range.

## Wiring

| Adapter | Connect to |
|:--|:--|
| A (sometimes marked D+) | The sensor's RS485 A wire |
| B (sometimes marked D-) | The sensor's RS485 B wire |
| GND, when the adapter has one | The sensor supply's ground |

Power the sensor from its own supply. The wire colours of each model are on its page under [docs/sensors](docs/sensors).

The adapter shows up as a serial port:

| System | Port |
|:--|:--|
| Raspberry Pi, Linux | `/dev/ttyUSB0`, or `/dev/serial0` for a HAT |
| macOS | `/dev/tty.usbserial-...` |
| Windows | `COM3` or another COM number, shown in Device Manager |

`python -m serial.tools.list_ports` lists the ports the computer has. On Linux your user has to be in the `dialout` group to open one: `sudo usermod -a -G dialout $USER`, then log out and in again.

## Reading

`read()` returns the values by name. The result is a named tuple, so it also unpacks, and `_asdict()` turns it into a dict for a CSV file or a data frame.

```python
reading = probe.read()
reading.nitrate                    # 10.0
nitrate, signal, temperature = reading
reading._asdict()                  # {'nitrate': 10.0, 'electrode_signal': 100.1, 'temperature': 24.99}, shown rounded
probe.units()                      # {'nitrate': 'mg/L', 'electrode_signal': 'mV', 'temperature': '°C'}
```

A sensor that does not answer raises an error instead of returning a value. Every error is an `agrinovo.AgrinovoError`:

```python
try:
    reading = probe.read()
except agrinovo.AgrinovoError as error:
    print(error)                   # for example: no reply from the sensor
```

[examples/log_to_csv.py](examples/log_to_csv.py) logs a sensor to a file with a timestamp.

## Several sensors on one line

Sensors share the two RS485 wires as long as each has its own address. They all leave the factory at the same address, so connect one at a time and move it with `change_address()`. See [examples/change_address.py](examples/change_address.py) and [examples/multiple_sensors.py](examples/multiple_sensors.py).

```python
with agrinovo.Bus("/dev/ttyUSB0") as bus:
    ph = agrinovo.PH100(bus, address=1)
    ec = agrinovo.EC120(bus, address=2)
    oxygen = agrinovo.DO100(bus, address=3)
```

## Reference

**agrinovo.Bus**

| Call | What it does |
|:--|:--|
| `Bus(port, baudrate=9600, timeout=1.0, retries=1)` | Opens the serial port at 8N1. `timeout` is the time to wait for a reply, in seconds; `retries` is how many times a failed request is sent again |
| `Bus(port, debug=True)` | Prints every frame sent and received. Pass a function to receive the lines instead |
| `bus.ping(address)` | True when a device answers at that address |
| `bus.read_registers(address, function, start, count)` | The raw register bytes |
| `bus.write_register(address, register, value)` | Writes one register |
| `bus.close()` | Closes the port. A `with` block does it for you |
| `agrinovo.scan(bus)` | The addresses that answer, as a list |

`port` can also be a serial port you opened yourself with pyserial, for a HAT that needs its own settings.

**Every sensor**

| Call | What it does |
|:--|:--|
| `Sensor(bus, address=1)` | `agrinovo.NO3100(bus)`, `agrinovo.PH100(bus, address=4)` and so on |
| `read()` | Reads the sensor and returns its values |
| `units()` | The unit of each value |
| `address` | The address this object talks to |
| `read_register(register)`, `write_register(register, value)` | Direct register access |

Address change, calibration and brush commands are methods of the sensors that have them, listed on each sensor's page.

**Errors**

| Error | Meaning |
|:--|:--|
| `agrinovo.NoReply` | Nothing came back before the timeout |
| `agrinovo.BadCRC` | The reply failed its checksum |
| `agrinovo.BadReply` | The reply was cut short or does not match the request |
| `agrinovo.SensorRefused` | The sensor refused the request; `error.code` is the Modbus exception code |
| `agrinovo.BadRequest` | The request is not valid, so nothing was sent |

## Command line

The package can check a sensor without a script:

```
python -m agrinovo list                          # the supported models
python -m agrinovo scan /dev/ttyUSB0             # find the address of whatever is connected
python -m agrinovo read NO3-100 /dev/ttyUSB0     # read a sensor once
python -m agrinovo read NO3-100 /dev/ttyUSB0 --address 3 --debug
```

## Troubleshooting

`no reply from the sensor` is nearly always one of four things: A and B swapped, the sensor not powered, the wrong serial port, or a different address. Run `python -m agrinovo scan` with your port to find the address, and add `--debug` (or `debug=True` in a script) to see the frames.

When you open an issue, include the computer, the RS485 adapter, the wiring and the frames printed with `debug=True`.

## Development

The sensor classes, examples and sensor pages are generated from the same definitions as the [Agrinovo Arduino library](https://github.com/OmnIoT/agrinovo-arduino). Each definition carries the example frames from the sensor's datasheet, and the tests replay them through the package with a stand-in serial port.

```
pip install -e ".[dev]"
python tools/generate.py     # after a definition changes, needs the Arduino library next to this folder
pytest
```

## Licence

MIT. See [LICENSE](LICENSE).
