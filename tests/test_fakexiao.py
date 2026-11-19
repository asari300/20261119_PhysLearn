"""偽の XIAO に本物の SerialPlant をつなぎ、実機の経路を端から端まで通す。

偽物は仮想の時刻で回す（tests/conftest.py）: PC の読み 1 回 = 1 サンプル。負荷に依らず結果は毎回同じなので、
許容差は壁時計のゆらぎの余裕を含まない（S059 が広げる前の厳しさ）。
"""

import time

import numpy as np
import pytest
import serial

from physlearn import HIDDEN, sim_log
from physlearn.api import Command
from physlearn.fakexiao import DUTY_MAX, PERIOD_MS, FakeXiao
from physlearn.link import BAUD, SerialPlant, main as link_main
from physlearn.log import as_log, row
from physlearn.sim import SimPlant
from physlearn.sysid import identify


def collect(plant, schedule, dt=0.01):
    plant.reset()
    return as_log([row(plant.step(c, dt), c) for s, c in schedule for _ in range(round(s / dt))])


def test_still(fake_factory):
    with SerialPlant(ser=fake_factory().ser) as p:
        log = collect(p, [(2.0, Command(0, 0))])
    assert len(log["t"]) == 200 and np.allclose(np.diff(log["t"]), 0.01)
    assert log["az"].mean() == pytest.approx(9.81, abs=0.02)
    assert log["gz"].mean() == pytest.approx(HIDDEN.gyro_bias, abs=0.005)


def test_id_through_serial_recovers_hidden(fake_factory):
    with SerialPlant(ser=fake_factory().ser) as p:
        log = as_log(sim_log(p))
    assert log["t"][-1] == pytest.approx(len(log["t"]) * 0.01, abs=1e-6)  # 1 step = 1 サンプル。t は飛ばない
    est = identify(log)
    assert est["gyro_bias"] == pytest.approx(HIDDEN.gyro_bias, abs=0.01)
    assert est["motor_tau"] == pytest.approx(HIDDEN.motor_tau, rel=0.1)
    u = np.abs(log["right"] - log["left"]) / 2
    if u.max() > DUTY_MAX + 1e-9:
        # ログの指令はファームの上限を超えているが、実際に回ったのは DUTY_MAX。ゲインとデッドバンドがずれる
        pytest.xfail(f"id の指令 {u.max():.2f} > DUTY_MAX {DUTY_MAX}: 推定 {est}")
    assert est["yaw_gain"] == pytest.approx(HIDDEN.yaw_gain(), rel=0.1)
    assert est["deadband"] == pytest.approx(HIDDEN.deadband, abs=0.03)


def test_axes_swapped_then_restored(fake_factory):
    sched = [(0.5, Command(0, 0)), (1.0, Command(-0.5, 0.5))]
    ok, turned = fake_factory(), fake_factory(axes="x,z,-y")
    with SerialPlant(ser=ok.ser) as p:
        a = collect(p, sched)
    with SerialPlant(ser=turned.ser, axes="x,z,-y") as p:
        b = collect(p, sched)
    with SerialPlant(ser=turned.ser) as p:  # --axes を忘れると、重力が y に、ヨーが gy に出る
        c = collect(p, sched)
    # 同じ指令列を同じ時刻で受ける（仮想の時刻）ので、軸を戻せば値は一致する。取り違えなら 2.8 や 9.8 ずれる
    for k, tol in (("az", 0.03), ("gz", 0.05), ("ay", 0.05), ("ax", 0.05)):
        assert b[k][-30:].mean() == pytest.approx(a[k][-30:].mean(), abs=tol)
    assert c["ay"].mean() == pytest.approx(-9.81, abs=0.05) and abs(c["az"].mean()) < 0.05
    assert c["gy"][-30:].mean() == pytest.approx(-a["gz"][-30:].mean(), abs=0.05)


def test_watchdog_clip_and_broken_lines(fake_factory):
    f = fake_factory()
    s = f.ser
    s.write(b"M 1 -1\n")
    assert f.duty == (DUTY_MAX, -DUTY_MAX)  # 上限で切る
    sent = f.last_cmd_ms
    # 壊れた行は捨てられ、ウォッチドッグを延ばさない
    for bad in (b"M 0.1 x\n", b"M nan 0\n", b"X" * 100 + b"\n", b"\xff\xfe\n", b"M 0.1 0.2 0.3\n", b"Z\n"):
        s.write(bad)
    assert f.last_cmd_ms == sent
    msgs = []
    while f.duty != (0.0, 0.0):
        assert f.t_ms - sent <= 200, "200 ms を超えたのに止まらない"
        msgs.append(s.readline())
    # 200 ms を超えた最初の 10 ms の刻み (210 ms) で、ちょうど止まる。200 ms ちょうどではまだ止まらない
    assert f.t_ms - sent == 210  # スケッチの WATCHDOG_MS = 200（定数の取り違えも見えるよう、数を直に書く）
    assert msgs.count(b"# ERR bad line\n") == 5 and msgs.count(b"# ERR line too long\n") == 1
    assert f.last_cmd_ms == sent


@pytest.mark.parametrize(
    "line, ok",
    [
        ("S", True), ("S  ", True), ("S\t", False), ("SS", False),
        ("M 0.1 -0.2", True), ("M 0.1 -0.2 \r", True), ("M\t0.1 0.2", False), ("M \t0.1\t0.2", True),
        ("M 1-1", True), ("M .5 5.", True), ("M 0x1 0", True), ("M 1e3 0", True),
        ("M 1e39 0", False), ("M 1_0 0", False), ("M inf 0", False), ("M 0.1 0.2\t", False), ("M 1e 2", False), ("M 12", False),
    ],
)
def test_line_parsed_like_sketch(line, ok):
    # スケッチの handleLine（strtof・isfinite・末尾の空白と \r）と同じ行だけ受け付け、ウォッチドッグを延ばす
    f = FakeXiao(SimPlant(HIDDEN, seed=1), pty=False)
    f.duty, f.t_ms = (0.5, 0.5), 100
    f._line(line)
    assert (f.last_cmd_ms == 100) is ok
    if line.startswith("S") and ok:
        assert f.duty == (0.0, 0.0)


@pytest.mark.parametrize("axes", [["--axes", "-y,x,z"], ["--axes=-y,x,z"]])
def test_cli_axes_leading_minus_both_spellings(monkeypatch, capsys, axes):
    import physlearn.fakexiao as fx

    got = []

    class Stub:
        port = "stub"

        def __init__(self, plant, a, speed):
            got.append(a)

        def run(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(fx, "FakeXiao", Stub)
    fx.main(axes)
    assert got == ["-y,x,z"]


def test_same_run_twice_gives_identical_csv(fake_factory, monkeypatch, tmp_path):
    # 決定論: link の id を同じ偽物で 2 回回すと、CSV がバイト単位で同じ（壁時計・負荷に依らない）
    import physlearn.link as link

    outs = []
    for i in range(2):
        monkeypatch.setattr(link, "open_port", lambda parser, port, _f=fake_factory(), **kw: _f.ser)
        out = tmp_path / f"id{i}.csv"
        link_main(["id", "--port", "virtual", "--out", str(out)])
        outs.append(out.read_bytes())
    assert outs[0] == outs[1] and outs[0].count(b"\n") == 1701


def test_pty_realtime_form_still_works():
    # 人が端末 2 つで使う実時間の形（python -m physlearn.fakexiao）。壁時計に依るので、中身ではなく形だけを緩く見る
    import threading

    pytest.importorskip("pty")
    f = FakeXiao(SimPlant(HIDDEN, seed=1), speed=5.0)
    th = threading.Thread(target=f.run, daemon=True)
    th.start()
    try:
        with serial.Serial(f.port, BAUD, timeout=5) as ser:
            ts = [int(ser.readline().split()[1]) for _ in range(5)]
            assert np.diff(ts).tolist() == [PERIOD_MS] * 4  # 取りこぼしなく 10 ms 刻み（読み手が詰まらない限り）
            ser.write(b"M 1 -1\n")
            end = time.monotonic() + 10
            while f.duty != (DUTY_MAX, -DUTY_MAX):
                assert time.monotonic() < end, "指令が届かない"
                time.sleep(0.001)
    finally:
        f.close()
        th.join(5)
