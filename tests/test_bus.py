"""The bus itself and the base sensor class. The per-sensor tests are in
test_sensors.py and replay the datasheet frames."""

import math

import pytest

import agrinovo
from agrinovo import BadCRC, BadReply, BadRequest, Bus, NoReply, SensorRefused
from conftest import FakeSerial, hexbytes, with_crc

PH_REQUEST = hexbytes("01 03 00 00 00 01 84 0A")
PH_REPLY = hexbytes("01 03 02 02 AE 38 98")


def quick_bus(port, **options):
    options.setdefault("timeout", 0.02)
    options.setdefault("frame_gap", 0)
    return Bus(port, **options)


def test_crc():
    assert agrinovo.crc16(PH_REQUEST[:-2]) == 0x0A84
    assert with_crc(PH_REQUEST[:-2]) == PH_REQUEST


def test_read(serial_port):
    serial_port.reply(PH_REPLY)
    assert quick_bus(serial_port).read_registers(1, 0x03, 0, 1) == b"\x02\xAE"
    assert serial_port.written == PH_REQUEST


def test_defaults(serial_port):
    bus = Bus(serial_port)
    assert (bus.timeout, bus.retries) == (1.0, 1)


def test_silence_is_retried_once_then_reported(serial_port):
    with pytest.raises(NoReply, match="no reply from the sensor"):
        quick_bus(serial_port).read_registers(1, 0x03, 0, 1)
    assert serial_port.requests == 2
    assert serial_port.written == PH_REQUEST * 2


def test_timeout_is_waited_out(serial_port):
    import time

    started = time.monotonic()
    with pytest.raises(NoReply):
        quick_bus(serial_port, timeout=0.05, retries=0).read_registers(1, 0x03, 0, 1)
    assert 0.05 <= time.monotonic() - started < 0.5
    assert serial_port.requests == 1


def test_retries_setting(serial_port):
    with pytest.raises(NoReply):
        quick_bus(serial_port, retries=3).read_registers(1, 0x03, 0, 1)
    assert serial_port.requests == 4


def test_retry_succeeds(serial_port):
    serial_port.reply(b"")
    serial_port.reply(PH_REPLY)
    assert quick_bus(serial_port).read_registers(1, 0x03, 0, 1) == b"\x02\xAE"
    assert serial_port.requests == 2


def test_bad_crc(serial_port):
    damaged = bytearray(PH_REPLY)
    damaged[4] ^= 0x01
    serial_port.reply(damaged)
    with pytest.raises(BadCRC):
        quick_bus(serial_port, retries=0).read_registers(1, 0x03, 0, 1)


def test_bad_crc_is_retried(serial_port):
    damaged = bytearray(PH_REPLY)
    damaged[-1] ^= 0xFF
    serial_port.reply(damaged)
    serial_port.reply(PH_REPLY)
    assert quick_bus(serial_port).read_registers(1, 0x03, 0, 1) == b"\x02\xAE"
    assert serial_port.requests == 2


def test_reply_cut_short(serial_port):
    serial_port.reply("01 03 02 02")
    with pytest.raises(BadReply):
        quick_bus(serial_port, retries=0).read_registers(1, 0x03, 0, 1)


def test_reply_with_the_wrong_length_byte(serial_port):
    serial_port.reply(with_crc("01 03 04 02 AE"))
    with pytest.raises(BadReply):
        quick_bus(serial_port, retries=0).read_registers(1, 0x03, 0, 1)


def test_reply_to_another_function(serial_port):
    serial_port.reply(with_crc("01 04 02 02 AE"))
    with pytest.raises(BadReply):
        quick_bus(serial_port, retries=0).read_registers(1, 0x03, 0, 1)


def test_exception_reply_is_reported_with_its_code_and_not_retried(serial_port):
    serial_port.reply(with_crc("01 83 02"))
    with pytest.raises(SensorRefused) as caught:
        quick_bus(serial_port).read_registers(1, 0x03, 0, 1)
    assert caught.value.code == 2
    assert "the sensor refused the request" in str(caught.value)
    assert serial_port.requests == 1


def test_every_error_is_an_agrinovo_error():
    for error in (NoReply, BadCRC, BadReply, SensorRefused, BadRequest):
        assert issubclass(error, agrinovo.AgrinovoError)


def test_leading_noise_is_skipped(serial_port):
    serial_port.reply(hexbytes("00 FF") + PH_REPLY)
    assert quick_bus(serial_port, retries=0).read_registers(1, 0x03, 0, 1) == b"\x02\xAE"


def test_leftover_bytes_are_dropped_before_a_request(serial_port):
    serial_port._incoming = b"\x01\x03\x02"
    serial_port.reply(PH_REPLY)
    assert quick_bus(serial_port, retries=0).read_registers(1, 0x03, 0, 1) == b"\x02\xAE"


def test_broadcast_query_is_answered_from_the_sensors_own_address(serial_port):
    serial_port.reply(with_crc("03 03 02 00 03"))
    assert quick_bus(serial_port).read_registers(0xFF, 0x03, 0x2002, 1) == b"\x00\x03"


def test_requests_the_bus_cannot_send(serial_port):
    bus = quick_bus(serial_port)
    for arguments in ((1, 0x03, 0, 0), (1, 0x03, 0, agrinovo.MAX_REGISTERS + 1), (1, 0x05, 0, 1), (300, 0x03, 0, 1)):
        with pytest.raises(BadRequest):
            bus.read_registers(*arguments)
    with pytest.raises(BadRequest):
        bus.write_register(1, 0, 0, function=0x05)
    with pytest.raises(BadRequest):
        bus.write_register(1, 0, 0x10000)
    assert serial_port.requests == 0
    assert issubclass(BadRequest, ValueError)


def test_write_with_function_06(serial_port):
    serial_port.confirm_writes = True
    quick_bus(serial_port).write_register(1, 0x0050, 2)
    assert serial_port.written == with_crc("01 06 00 50 00 02")


def test_write_with_function_10(serial_port):
    serial_port.confirm_writes = True
    quick_bus(serial_port).write_register(1, 0x0010, 0x0200, function=0x10)
    assert serial_port.written == with_crc("01 10 00 10 00 01 02 02 00")


def test_write_confirmed_for_another_register(serial_port):
    serial_port.reply(with_crc("01 06 00 51 00 02"))
    with pytest.raises(BadReply):
        quick_bus(serial_port, retries=0).write_register(1, 0x0050, 2)


def test_ping_sees_a_refusal_as_present_and_silence_as_absent(serial_port):
    serial_port.reply(with_crc("05 83 02"))
    bus = quick_bus(serial_port, retries=0)
    assert bus.ping(5)
    assert not bus.ping(6)


def test_scan(serial_port):
    class Line(FakeSerial):
        def flush(self):
            address = self._pending[0]
            if address == 3:
                self.reply(with_crc(bytes((address, 0x03, 0x02, 0x00, 0x00))))
            if address == 9:
                self.reply(with_crc(bytes((address, 0x83, 0x02))))
            super().flush()

    port = Line()
    bus = Bus(port, timeout=0.5, retries=2, frame_gap=0)
    seen = []
    assert agrinovo.scan(bus, range(1, 12), timeout=0.001, found=seen.append) == [3, 9]
    assert seen == [3, 9]
    assert port.requests == 11  # no retries while scanning
    assert (bus.timeout, bus.retries) == (0.5, 2)  # and the settings come back


def test_debug_output(serial_port, capsys):
    serial_port.reply(PH_REPLY)
    quick_bus(serial_port, debug=True).read_registers(1, 0x03, 0, 1)
    assert capsys.readouterr().err == "> 01 03 00 00 00 01 84 0A\n< 01 03 02 02 AE 38 98\n"


def test_debug_hook(serial_port):
    lines = []
    serial_port.reply(PH_REPLY)
    quick_bus(serial_port, debug=lines.append).read_registers(1, 0x03, 0, 1)
    assert lines == ["> 01 03 00 00 00 01 84 0A", "< 01 03 02 02 AE 38 98"]


def test_frame_gap_is_kept_between_frames(serial_port):
    import time

    serial_port.reply(PH_REPLY)
    serial_port.reply(PH_REPLY)
    bus = Bus(serial_port, frame_gap=0.05)
    bus.read_registers(1, 0x03, 0, 1)
    started = time.monotonic()
    bus.read_registers(1, 0x03, 0, 1)
    assert time.monotonic() - started >= 0.045


def test_a_port_handed_in_is_left_open(serial_port):
    with Bus(serial_port):
        pass
    assert not serial_port.closed


def test_a_port_named_by_path_is_opened_8n1_and_closed(monkeypatch):
    import serial

    opened = {}

    class Port(FakeSerial):
        def __init__(self, port, **settings):
            super().__init__()
            opened.update(settings, port=port)

    monkeypatch.setattr(serial, "Serial", Port)
    with Bus("/dev/ttyUSB7", baudrate=4800) as bus:
        port = bus._serial
    assert opened == {"port": "/dev/ttyUSB7", "baudrate": 4800, "bytesize": 8, "parity": "N", "stopbits": 1}
    assert port.closed


# ------------------------------------------------------------ base sensor


def test_address_change_answered_from_the_new_address(serial_port):
    serial_port.reply(with_crc("02 06 00 50 00 02"))
    probe = agrinovo.PH100(quick_bus(serial_port))
    probe.change_address(2)
    assert probe.address == 2


def test_failed_address_change_leaves_the_object_where_it_was(serial_port):
    probe = agrinovo.PH100(quick_bus(serial_port))
    with pytest.raises(NoReply):
        probe.change_address(2)
    assert probe.address == 1


def test_sensor_read_and_failure(serial_port):
    serial_port.reply(PH_REPLY)
    probe = agrinovo.PH100(quick_bus(serial_port, retries=0))
    reading = probe.read()
    assert reading.ph == 6.86
    assert reading == (6.86,)
    assert reading._asdict() == {"ph": 6.86}
    assert probe.units() == {"ph": "pH"}
    with pytest.raises(NoReply):
        probe.read()


def test_sensor_at_another_address(serial_port):
    serial_port.reply(with_crc("07 03 02 02 AE"))
    probe = agrinovo.PH100(quick_bus(serial_port), address=7)
    assert probe.read().ph == 6.86
    assert serial_port.written == with_crc("07 03 00 00 00 01")
    assert repr(probe) == "PH100(address=7)"


def test_direct_register_access(serial_port):
    serial_port.reply(with_crc("01 04 02 12 34"))
    serial_port.confirm_writes = True
    probe = agrinovo.PH100(quick_bus(serial_port))
    assert probe.read_register(0x0011, function=0x04) == 0x1234
    probe.write_register(0x0020, 0xBEEF)
    assert serial_port.written == with_crc("01 04 00 11 00 01") + with_crc("01 06 00 20 BE EF")


def test_command_arguments_are_checked_before_anything_is_sent(serial_port):
    bus = quick_bus(serial_port)
    with pytest.raises(BadRequest):
        agrinovo.PH100(bus).change_address(256)
    with pytest.raises(BadRequest):
        agrinovo.DO130(bus).set_brush_interval(-1)
    with pytest.raises(BadRequest):
        agrinovo.DO130(bus).set_brush_interval(1.5)
    with pytest.raises(BadRequest):
        agrinovo.THS100(bus).set_temperature_offset(5000)
    with pytest.raises(BadRequest):
        agrinovo.ORP100(bus).set_offset(40000)
    assert serial_port.requests == 0


def test_scaled_arguments_round_to_the_nearest_step(serial_port):
    serial_port.confirm_writes = True
    sensor = agrinovo.THS100(quick_bus(serial_port))
    sensor.set_temperature_offset(1.26)
    sensor.set_temperature_offset(-1.26)
    assert serial_port.written == with_crc("01 06 01 04 00 0D") + with_crc("01 06 01 04 FF F3")


def test_generic_sensor(serial_port):
    fields = [
        ("signed", 0, "i16", 0.1),
        ("unsigned", 1, "u16"),
        ("low_word_first", 2, "u32_cdab"),
        ("wide", 4, "u32_abcd"),
        agrinovo.Field("float", 6, "f32_abcd", unit="mg/L"),
        ("outside", 9, "u16"),
    ]
    serial_port.reply(with_crc("01 04 10 FF 9C 01 F4 1D 02 00 00 00 01 86 A0 41 0A E1 48"))
    sensor = agrinovo.GenericSensor(quick_bus(serial_port), 1, 0x04, 0x0100, 8, fields)
    reading = sensor.read()
    assert serial_port.written == with_crc("01 04 01 00 00 08")
    assert list(reading) == ["signed", "unsigned", "low_word_first", "wide", "float", "outside"]
    assert reading["signed"] == -10.0
    assert reading["unsigned"] == 500
    assert reading["low_word_first"] == 7426
    assert reading["wide"] == 100000
    assert reading["float"] == pytest.approx(8.68, abs=0.001)
    assert math.isnan(reading["outside"])
    assert sensor.units()["float"] == "mg/L"


@pytest.mark.parametrize(
    "kind, data, expected",
    [
        ("u16", "FF 9C", 65436),
        ("i16", "FF 9C", -100),
        ("sm16", "80 64", -100),
        ("sm16", "00 64", 100),
        ("u16_dec", "03 64 00 02", 8.68),
        ("u32_abcd", "00 01 86 A0", 100000),
        ("u32_cdab", "86 A0 00 01", 100000),
        ("f32_abcd", "41 0A E1 48", 8.68),
        ("f32_cdab", "E1 48 41 0A", 8.68),
        ("f32_dcba", "48 E1 0A 41", 8.68),
    ],
)
def test_every_storage_type(serial_port, kind, data, expected):
    payload = hexbytes(data)
    count = len(payload) // 2
    serial_port.reply(with_crc(bytes((1, 3, len(payload))) + payload))
    sensor = agrinovo.GenericSensor(quick_bus(serial_port), 1, 0x03, 0, count, [("value", 0, kind)])
    assert sensor.read()["value"] == pytest.approx(expected, abs=1e-5)
    assert set(agrinovo.TYPES) >= {kind}


def test_decimal_places_that_make_no_sense_give_nan(serial_port):
    serial_port.reply(with_crc("01 03 04 03 64 00 0A"))
    sensor = agrinovo.GenericSensor(quick_bus(serial_port), 1, 0x03, 0, 2, [("value", 0, "u16_dec")])
    assert math.isnan(sensor.read()["value"])


def test_generic_sensor_rejects_a_bad_table(serial_port):
    bus = quick_bus(serial_port)
    with pytest.raises(BadRequest):
        agrinovo.GenericSensor(bus, 1, 0x03, 0, 2, [("a", 0, "u8")])
    with pytest.raises(BadRequest):
        agrinovo.GenericSensor(bus, 1, 0x03, 0, 2, [("a", 0, "u16"), ("a", 1, "u16")])
