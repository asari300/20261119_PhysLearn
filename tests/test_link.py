import csv

import numpy as np
import pytest
import serial

from physlearn.api import LOG_COLUMNS, Command
from physlearn.link import STOP, SerialPlant, decode_sample, encode_command, parse_axes, record


def sample(t_ms, a=(0.1, 0.2, 9.8), g=(0.01, 0.02, 0.03)):
    return ("I %d %.3f %.3f %.3f %.4f %.4f %.4f\n" % (t_ms, *a, *g)).encode()


def test_encode_clamps_and_formats():
    assert encode_command(Command(0.25, -0.5)) == b"M 0.250 -0.500\n"
    assert encode_command(Command(2, -3)) == b"M 1.000 -1.000\n"


def test_decode_roundtrip():
    o = decode_sample(sample(1234))
    assert o.t == pytest.approx(1.234)
    assert (o.ax, o.az, o.gz) == pytest.approx((0.1, 9.8, 0.03))


@pytest.mark.parametrize(
    "line",
    [b"", b"# hello", b"I 1 2 3", b"I x 1 2 3 4 5 6", b"I 1 1 2 3 4 5 nan", b"I -5 1 2 3 4 5 6", b"\xff\xfe", b"M 0 0"],
)
def test_decode_rejects_broken(line):
    assert decode_sample(line) is None


def test_axes():
    m = parse_axes("-y,x,z")
    assert m @ np.array([1.0, 2.0, 3.0]) == pytest.approx([-2, 1, 3])
    with pytest.raises(ValueError):
        parse_axes("x,y,-z")  # 鏡映


def test_step_over_loopback():
    # loop:// は書いたものがそのまま返る。指令行は捨てられ、I 行だけが観測になる
    ser = serial.serial_for_url("loop://", timeout=0.01)
    ser.write(sample(1000) + b"garbage\n" + sample(1010) + sample(1020, g=(0, 0, 0.5)))
    p = SerialPlant(ser=ser, axes="-y,x,z")
    ser.reset_input_buffer = lambda: None  # 仕込んだサンプルを reset で捨てさせない
    assert p.reset().t == 0.0
    o = p.step(Command(-0.3, 0.3), 0.02)
    assert o.t == pytest.approx(0.02)
    assert (o.ax, o.ay, o.gz) == pytest.approx((-0.2, 0.1, 0.5))


class FakePort:
    def __init__(self, lines):
        self.lines, self.written, self.closed = list(lines), [], False

    def write(self, b):
        self.written.append(b)

    def readline(self):
        return self.lines.pop(0) if self.lines else b""

    def reset_input_buffer(self):
        pass

    def flush(self):
        pass

    def close(self):
        self.closed = True


def test_timeout_sends_stop():
    port = FakePort([sample(0)])
    with pytest.raises(TimeoutError):
        with SerialPlant(ser=port, timeout=0.05) as p:
            p.reset()
            p.step(Command(0.5, 0.5), 0.01)  # 以後サンプルが来ない
    assert port.written[-1] == STOP and port.closed
    assert b"M 0.500 0.500\n" in port.written


def test_exception_in_caller_sends_stop():
    port = FakePort([sample(0), sample(10)])
    with pytest.raises(RuntimeError):
        with SerialPlant(ser=port) as p:
            p.reset()
            p.step(Command(0.5, -0.5), 0.01)
            raise RuntimeError("controller bug")
    assert port.written[-1] == STOP


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_command_raises_and_stops(bad):
    port = FakePort([sample(0), sample(10)])
    with pytest.raises(ValueError):
        with SerialPlant(ser=port) as p:
            p.reset()
            p.step(Command(bad, 0.2), 0.01)
    assert not any(w.startswith(b"M") for w in port.written)  # 逆転の指令を 1 行も送らない
    assert port.written[-1] == STOP


def test_record_csv(tmp_path):
    port = FakePort([sample(t) for t in range(0, 60, 10)])
    out = tmp_path / "log.csv"
    record(SerialPlant(ser=port), [(0.02, Command(0, 0)), (0.03, Command(-0.4, 0.4))], 0.01, str(out))
    rows = list(csv.reader(out.open()))
    assert rows[0] == LOG_COLUMNS
    assert len(rows) == 1 + 5
    assert float(rows[-1][0]) == pytest.approx(0.05)
    assert rows[-1][-2:] == ["-0.4", "0.4"]


def test_id_mode_over_serial(tmp_path, monkeypatch):
    from physlearn.link import main
    from physlearn.sim import id_experiment

    n = len(id_experiment(0.01))
    port = FakePort([sample(t) for t in range(0, 10 * (n + 1), 10)])
    out = tmp_path / "id.csv"
    monkeypatch.setattr(serial, "Serial", lambda *a, **k: port)
    main(["id", "--port", "fake", "--out", str(out)])
    rows = list(csv.reader(out.open()))
    assert rows[0] == LOG_COLUMNS and len(rows) == 1 + n
    assert port.written[-1] == STOP
