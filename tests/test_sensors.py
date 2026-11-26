"""Every sensor against the frames in its datasheet: the request it sends is
byte for byte the datasheet's, and the values it decodes are the datasheet's
values. Same for every setting and calibration command.

This proves the code against the documented protocol. It is not a test on a
physical sensor.
"""

import math

import pytest

import agrinovo
from agrinovo import Bus
from conftest import DEFINITIONS, FakeSerial, hexbytes

FRAMES = [
    pytest.param(s, frame, id="%s frame %d" % (s["model"], i + 1))
    for s in DEFINITIONS
    for i, frame in enumerate(s["frames"])
]
COMMANDS = [
    pytest.param(s, command, id="%s %s()" % (s["model"], command["method"]))
    for s in DEFINITIONS
    for command in s["commands"]
]


def test_every_model_has_a_class():
    assert len(DEFINITIONS) == 35
    assert list(agrinovo.SENSORS) == [s["model"] for s in DEFINITIONS]
    for s in DEFINITIONS:
        cls = getattr(agrinovo, s["class"])
        assert agrinovo.SENSORS[s["model"]] is cls
        assert issubclass(cls, agrinovo.Sensor)
        assert s["class"] in agrinovo.__all__
        assert cls.MODEL == s["model"]
        assert cls.Reading._fields == tuple(s["values"]) == tuple(f.name for f in cls.FIELDS)
        assert cls(Bus(FakeSerial())).address == s["address"] == cls.DEFAULT_ADDRESS
        assert s["frames"], "a sensor without a datasheet frame is not tested"


@pytest.mark.parametrize("s, frame", FRAMES)
def test_datasheet_frame(s, frame):
    request = hexbytes(frame["request"])
    port = FakeSerial()
    port.reply(frame["response"])
    sensor = getattr(agrinovo, s["class"])(Bus(port, frame_gap=0), address=request[0])
    reading = sensor.read()
    assert port.written == request
    assert reading._fields == tuple(frame["expect"])
    for name, expected in frame["expect"].items():
        value = getattr(reading, name)
        assert not math.isnan(value)
        assert value == pytest.approx(expected, abs=frame["tolerance"]), name


@pytest.mark.parametrize("s, command", COMMANDS)
def test_command(s, command):
    request = hexbytes(command["request"])
    port = FakeSerial(confirm_writes=not command["read"])
    if command["read"]:
        port.reply(command["response"])
    sensor = getattr(agrinovo, s["class"])(Bus(port, frame_gap=0), address=request[0])
    result = getattr(sensor, command["method"])(*command["args"])
    assert port.written == request
    if command["read"]:
        assert result == command["expect"]
    else:
        assert result is None
    assert sensor.address == (command["args"][0] if command["sets_address"] else request[0])


@pytest.mark.parametrize("s, command", [c for c in COMMANDS if not c.values[1]["read"]])
def test_command_without_an_answer_raises(s, command):
    port = FakeSerial()
    sensor = getattr(agrinovo, s["class"])(Bus(port, timeout=0.002, retries=0, frame_gap=0))
    with pytest.raises(agrinovo.NoReply):
        getattr(sensor, command["method"])(*command["args"])
    assert sensor.address == s["address"]
