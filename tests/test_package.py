"""The command line, the examples, the generated files and the packaging."""

import ast
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

import agrinovo
from agrinovo.__main__ import main
from conftest import DEFINITIONS, FakeSerial, with_crc

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = sorted((ROOT / "examples").rglob("*.py"))


def test_version_matches_pyproject():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r'^version = "(.+)"$', text, re.M).group(1) == agrinovo.__version__


def test_cli_list(capsys):
    assert main(["list"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 35
    assert "NO3-100      Nitrate probe" in lines


def test_cli_read(capsys):
    port = FakeSerial()
    port.reply(with_crc("03 03 04 01 E6 FF 9F"))
    assert main(["read", "ths-100", "fake", "--address", "3"], port=port) == 0
    assert capsys.readouterr().out == "Temperature: -9.7 °C\nHumidity: 48.6 % RH\n"


def test_cli_read_failure(capsys, monkeypatch):
    monkeypatch.setattr(agrinovo.Bus, "__init__", _quick_init)
    assert main(["read", "PH-100", "fake"], port=FakeSerial()) == 1
    assert capsys.readouterr().err == "PH-100 at address 1: no reply from the sensor\n"
    assert main(["read", "PH-999", "fake"], port=FakeSerial()) == 2


_init = agrinovo.Bus.__init__


def _quick_init(self, port, **options):
    _init(self, port, timeout=0.002, retries=0, frame_gap=0, debug=options.get("debug"))


def test_cli_scan(capsys, monkeypatch):
    monkeypatch.setattr(agrinovo, "scan", lambda bus, **options: agrinovo.bus.scan(bus, timeout=0.0005, **options))
    monkeypatch.setattr("agrinovo.__main__.scan", agrinovo.scan)
    port = FakeSerial()
    for _ in range(4):
        port.reply(b"")
    port.reply(with_crc("05 83 02"))
    assert main(["scan", "fake"], port=port) == 0
    out = capsys.readouterr().out
    assert "Sensor at address 5\n" in out and out.endswith("1 found.\n")
    assert port.requests == 247


def test_one_example_per_sensor():
    names = {path.stem for path in (ROOT / "examples" / "sensors").glob("*.py")}
    assert names == {s["model"].lower().replace("-", "_") for s in DEFINITIONS}
    assert {path.stem for path in (ROOT / "docs" / "sensors").glob("*.md")} == {s["model"].lower() for s in DEFINITIONS}


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda path: path.name)
def test_example_uses_only_what_the_package_has(path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    compile(tree, str(path), "exec")
    used = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name) and node.value.id == "agrinovo"}
    assert used and all(hasattr(agrinovo, name) for name in used)


@pytest.mark.parametrize("s", DEFINITIONS, ids=lambda s: s["model"])
def test_sensor_example_runs(s, monkeypatch, capsys):
    """Runs the generated example for one reading against the datasheet frame."""
    import time

    frame = s["frames"][0]
    port = FakeSerial()
    port.reply(frame["response"])
    monkeypatch.setattr(agrinovo.Bus, "__init__", lambda self, _port, **options: _init(self, port, frame_gap=0))

    def stop(_seconds):
        raise KeyboardInterrupt

    monkeypatch.setattr(time, "sleep", stop)
    path = ROOT / "examples" / "sensors" / (s["model"].lower().replace("-", "_") + ".py")
    with pytest.raises(KeyboardInterrupt):
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), {"__name__": "__main__"})
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == len(s["values"])
    assert all(re.match(r".+: -?\d+(\.\d+)? .+", line) for line in lines)


def test_readme_example_runs():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    code = re.search(r"```python\n(.*?)```", readme, re.S).group(1)
    port = FakeSerial()
    port.reply(next(s for s in DEFINITIONS if s["model"] == "NO3-100")["frames"][0]["response"])
    original = agrinovo.Bus.__init__
    agrinovo.Bus.__init__ = lambda self, _port, **options: original(self, port)
    try:
        exec(compile(code, "README.md", "exec"), {})
    finally:
        agrinovo.Bus.__init__ = original
    assert port.requests == 1


def test_generated_files_are_up_to_date():
    source = Path(os.environ.get("AGRINOVO_ARDUINO") or ROOT.parent / "agrinovo-arduino")
    if not (source / "dist" / "sensors.json").is_file():
        pytest.skip("the Agrinovo Arduino library is not next to this repository")
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate.py"), "--check", "--source", str(source)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
