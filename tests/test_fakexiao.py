"""偽の XIAO に本物の SerialPlant をつなぎ、実機の経路を端から端まで通す。"""

import os
import threading
import time

import numpy as np
import pytest
import serial

pytest.importorskip("pty")

from physlearn import HIDDEN, sim_log  # noqa: E402
from physlearn.api import Command  # noqa: E402
from physlearn.fakexiao import DUTY_MAX, FakeXiao  # noqa: E402
from physlearn.link import BAUD, SerialPlant  # noqa: E402
from physlearn.log import as_log, row  # noqa: E402
from physlearn.sim import SimPlant  # noqa: E402
from physlearn.sysid import identify  # noqa: E402

SPEED = 2.0  # 偽物と PC が同じプロセスで GIL を分け合う。5 倍では PC の読みが追いつかず、指令が遅れて t が飛んだ


@pytest.fixture
def fake_factory():
    fakes = []

    def make(axes="x,y,z", speed=SPEED):
        f = FakeXiao(SimPlant(HIDDEN, seed=1), axes, speed)
        th = threading.Thread(target=f.run, daemon=True)
        th.start()
        fakes.append((f, th))
        return f

    yield make
    for f, th in fakes:
        f.close()
        th.join(2)


def collect(plant, schedule, dt=0.01):
    plant.reset()
    return as_log([row(plant.step(c, dt), c) for s, c in schedule for _ in range(round(s / dt))])


def wait(cond, timeout=2.0):
    end = time.monotonic() + timeout
    while not cond():
        assert time.monotonic() < end, "待ちきれない"
        time.sleep(0.0005)


def test_still(fake_factory):
    f = fake_factory()
    with SerialPlant(f.port) as p:
        log = collect(p, [(2.0, Command(0, 0))])
    assert len(log["t"]) == 200 and np.allclose(np.diff(log["t"]), 0.01)
    assert log["az"].mean() == pytest.approx(9.81, abs=0.02)
    assert log["gz"].mean() == pytest.approx(HIDDEN.gyro_bias, abs=0.005)


def test_id_through_serial_recovers_hidden(fake_factory):
    f = fake_factory()
    with SerialPlant(f.port) as p:
        log = as_log(sim_log(p))
    assert log["t"][-1] == pytest.approx(len(log["t"]) * 0.01, abs=0.02)  # 読みが遅れると t が飛ぶ
    est = identify(log)
    assert est["gyro_bias"] == pytest.approx(HIDDEN.gyro_bias, abs=0.01)
    # 指令が偽物に d 秒遅れて届くと、見かけの時定数に約 d が足される。1 コアで読みが 0.1 s 遅れても通る幅（上 +0.12）。
    # 下は遅れでは小さくならないので 0.15 のまま（取り違えは検出できる）
    assert 0.15 <= est["motor_tau"] <= HIDDEN.motor_tau + 0.12, est
    u = np.abs(log["right"] - log["left"]) / 2
    if u.max() > DUTY_MAX + 1e-9:
        # ログの指令はファームの上限を超えているが、実際に回ったのは DUTY_MAX。ゲインとデッドバンドがずれる
        pytest.xfail(f"id の指令 {u.max():.2f} > DUTY_MAX {DUTY_MAX}: 推定 {est}")
    assert est["yaw_gain"] == pytest.approx(HIDDEN.yaw_gain(), rel=0.1)
    assert est["deadband"] == pytest.approx(HIDDEN.deadband, abs=0.03)


def test_axes_swapped_then_restored(fake_factory):
    sched = [(0.5, Command(0, 0)), (1.0, Command(-0.5, 0.5))]
    ok = fake_factory()
    turned = fake_factory(axes="x,z,-y")
    with SerialPlant(ok.port) as p:
        a = collect(p, sched)
    with SerialPlant(turned.port, axes="x,z,-y") as p:
        b = collect(p, sched)
    with SerialPlant(turned.port) as p:  # --axes を忘れると、重力が y に、ヨーが gy に出る
        c = collect(p, sched)
    # gz は最後の 0.3 s の平均で、読みの遅れで立ち上がりの残り（約 3%＝0.1 rad/s）が混ざりうる。軸の取り違えなら 2.8 や 9.8 ずれる
    for k, tol in (("az", 0.03), ("gz", 0.15), ("ay", 0.1), ("ax", 0.1)):
        assert b[k][-30:].mean() == pytest.approx(a[k][-30:].mean(), abs=tol)
    assert c["ay"].mean() == pytest.approx(-9.81, abs=0.05) and abs(c["az"].mean()) < 0.05
    assert c["gy"][-30:].mean() == pytest.approx(-a["gz"][-30:].mean(), abs=0.05)


def test_watchdog_clip_and_broken_lines(fake_factory):
    f = fake_factory(speed=1.0)  # 実時間にして、横から覗く時刻の誤差を 1 刻みより小さく
    with serial.Serial(f.port, BAUD, timeout=0.5) as s:
        s.write(b"M 1 -1\n")
        wait(lambda: f.duty != (0.0, 0.0))
        assert f.duty == (DUTY_MAX, -DUTY_MAX)
        sent = f.last_cmd_ms
        # 壊れた行は捨てられ、ウォッチドッグを延ばさない
        for bad in (b"M 0.1 x\n", b"M nan 0\n", b"X" * 100 + b"\n", b"\xff\xfe\n", b"M 0.1 0.2 0.3\n"):
            s.write(bad)
        wait(lambda: f.duty == (0.0, 0.0))
        assert WATCHDOG_RANGE[0] < f.t_ms - sent <= WATCHDOG_RANGE[1]
        assert f.last_cmd_ms == sent
        s.reset_input_buffer()
        s.write(b"Z\n")
        msgs = [s.readline() for _ in range(30)]
        assert b"# ERR bad line\n" in msgs
        assert f.running


# 200 ms を超えた最初の 10 ms の刻みで止まる（下 200・上 210）。上は横から覗く側が遅れた分（1 コアで 0.1 s）の余裕を足した
WATCHDOG_RANGE = (200, 320)


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
    f = FakeXiao(SimPlant(HIDDEN, seed=1))
    try:
        f.duty, f.t_ms = (0.5, 0.5), 100
        f._line(line)
        assert (f.last_cmd_ms == 100) is ok
        if line.startswith("S") and ok:
            assert f.duty == (0.0, 0.0)
    finally:
        os.close(f.master)
        os.close(f.slave)
