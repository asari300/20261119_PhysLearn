"""偽の XIAO を相手に、実機の経路（link の jog・run・id）だけで S2R → R2S → S2R を 1 周する。"""

import threading
import time

import numpy as np
import pytest

pytest.importorskip("pty")

from physlearn import HIDDEN, sim_log  # noqa: E402
from physlearn.api import Command  # noqa: E402
from physlearn.control import design, metrics, run  # noqa: E402
from physlearn.fakexiao import FakeXiao  # noqa: E402
from physlearn.link import SerialPlant, jog, main, run_loop  # noqa: E402
from physlearn.log import as_log  # noqa: E402
from physlearn.sim import Params, SimPlant  # noqa: E402
from physlearn.sysid import apply, identify  # noqa: E402

SPEED = 2.0  # tests/test_fakexiao.py と同じ（5 倍では読みが追いつかない）
TC = 0.15  # tune の 5 × 50 回の sim を試験ごとに回さないため、手で固定


@pytest.fixture
def fake():
    f = FakeXiao(SimPlant(HIDDEN, seed=1), speed=SPEED)
    th = threading.Thread(target=f.run, daemon=True)
    th.start()
    yield f
    f.close()
    th.join(2)


def test_s2r_r2s_s2r_over_serial(fake, capsys):
    with SerialPlant(fake.port) as p:
        _, before = run_loop(p, lambda: design(Params(), TC), 3.0, 2.0)
        rows = sim_log(p)
        est = identify(as_log(rows))
        fixed = apply(Params(), est)
        _, after = run_loop(p, lambda: design(fixed, TC), 3.0, 2.0)
    # 同じゲインを Python の中で直に（シリアル無しで）回したもの = loop_demo の数値の出どころ
    direct = metrics(*run(SimPlant(HIDDEN, seed=1001), design(fixed, TC))[1:])
    with capsys.disabled():
        print(f"\n前 {before}\n後 {after}\n直 {direct}\n同定 {est}")
    assert len(rows) == 1700 and abs(est["drift"]) < 0.05  # 同定の実験は 17 s。シリアル越しでも K は前後で変わらない
    assert est["gyro_bias"] == pytest.approx(HIDDEN.gyro_bias, abs=0.01)
    # 「前」も gz では合格に見える: 公称バイアス 0 なので gz を 3 に合わせ、真の角速度は 3 - 0.08。gz で測る限り見えない
    for _, m in after:
        assert m["ss_error"] < 0.05 and m["overshoot"] < 0.3


def test_jog_sign(fake):
    with SerialPlant(fake.port) as p:
        assert jog(p, Command(0.0, 0.4), 0.5) > 0.5  # 右だけ前 → 左回り → gz 正
    wait_stopped(fake)


def test_args_rejected():
    for bad in (["--target", "9"], ["--target", "nan"], ["--seconds", "10"], ["--tc", "0"]):
        with pytest.raises(SystemExit):
            main(["run", "--port", "/dev/null-none", *bad])
    with pytest.raises(SystemExit):
        main(["jog", "--port", "/dev/null-none", "--left", "0.9"])


def wait_stopped(f, timeout=1.0):
    # 停止は別スレッドの偽物に非同期で届く。ウォッチドッグ (200 ms) より短い時間で 0 になること
    end = time.monotonic() + min(timeout, 0.2 / SPEED)
    while f.duty != (0.0, 0.0):
        assert time.monotonic() < end, f"停止が届かない: duty {f.duty}"
        time.sleep(0.001)


class Boom(Exception):
    pass


def test_exception_sends_stop(fake):
    def ctrl_factory():
        def c(target, obs, dt):
            if obs.t > 0.2:
                raise Boom
            return Command(-0.4, 0.4)

        c.bias = 0.0
        return c

    with pytest.raises(Boom), SerialPlant(fake.port) as p:
        run_loop(p, ctrl_factory, 3.0, 1.0)
    wait_stopped(fake)


def test_gate_trip_stops(fake):
    class Wild:  # 暴走した制御器の代わり: gz を大きく見せるためバイアスを使わず、ゲートの閾値を下げた世界を真似る
        bias = 0.0

        def __call__(self, target, obs, dt):
            return Command(-0.6, 0.6)

    import physlearn.control as control

    old = control.SafetyGate.__init__.__defaults__
    control.SafetyGate.__init__.__defaults__ = (0.6, 10.0, 2.0)  # gz_limit を 2 rad/s に
    try:
        with pytest.raises(RuntimeError, match="安全ゲート"), SerialPlant(fake.port) as p:
            run_loop(p, Wild, 3.0, 1.0)
    finally:
        control.SafetyGate.__init__.__defaults__ = old
    wait_stopped(fake)
