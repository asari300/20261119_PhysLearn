"""偽の XIAO を相手に、実機の経路（link の jog・run・id）だけで S2R → R2S → S2R を 1 周する。偽物は仮想の時刻（tests/conftest.py）。"""

import numpy as np
import pytest

from physlearn import HIDDEN, sim_log  # noqa: E402
from physlearn.api import Command  # noqa: E402
from physlearn.control import design, metrics, run  # noqa: E402
from physlearn.fakexiao import WATCHDOG_MS, FakeXiao  # noqa: E402
from physlearn.link import SerialPlant, jog, main, run_loop  # noqa: E402
from physlearn.log import as_log  # noqa: E402
from physlearn.sim import Params, SimPlant  # noqa: E402
from physlearn.sysid import apply, identify  # noqa: E402

TC = 0.15  # tune の 5 × 50 回の sim を試験ごとに回さないため、手で固定


@pytest.fixture
def fake(fake_factory):
    return fake_factory()


def test_s2r_r2s_s2r_over_serial(fake, capsys):
    with SerialPlant(ser=fake.ser) as p:
        _, before, _ = run_loop(p, lambda: design(Params(), TC), 3.0, 2.0)
        rows = sim_log(p)
        est = identify(as_log(rows))
        fixed = apply(Params(), est)
        _, after, _ = run_loop(p, lambda: design(fixed, TC), 3.0, 2.0)
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
    with SerialPlant(ser=fake.ser) as p:
        assert jog(p, Command(0.0, 0.4), 0.5) > 0.5  # 右だけ前 → 左回り → gz 正
    wait_stopped(fake)


def test_args_rejected():
    for bad in (["--target", "9"], ["--target", "nan"], ["--seconds", "10"], ["--tc", "0"], ["--seconds", "0.004"], ["--dt", "0.001"]):  # dt < 0.01 は秒数の上限が効かなくなる
        with pytest.raises(SystemExit):
            main(["run", "--port", "/dev/null-none", *bad])
    with pytest.raises(SystemExit):
        main(["jog", "--port", "/dev/null-none", "--left", "0.9"])


def wait_stopped(f):
    # 停止 `S` は write した時点で偽物に届く（仮想の時刻では待ちが要らない）。実機のウォッチドッグ (200 ms) を待たずに 0 になること
    assert f.duty == (0.0, 0.0), f"停止が届かない: duty {f.duty}"


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

    with pytest.raises(Boom), SerialPlant(ser=fake.ser) as p:
        run_loop(p, ctrl_factory, 3.0, 1.0)
    wait_stopped(fake)


class Wild:  # 暴走した制御器の代わり: gz が 2 rad/s を超えるように、ゲートの閾値を下げた世界を作って使う
    bias = 0.0

    def __call__(self, target, obs, dt):
        return Command(-0.6, 0.6)


@pytest.fixture
def low_gate_limit(monkeypatch):
    import physlearn.control as control

    monkeypatch.setattr(control.SafetyGate.__init__, "__defaults__", (0.6, 10.0, 2.0))  # gz_limit を 2 rad/s に


def test_gate_trip_stops(fake, low_gate_limit):
    with SerialPlant(ser=fake.ser) as p:
        rows, res, why = run_loop(p, Wild, 3.0, 1.0)
    assert "|gz| >" in why  # 理由が分かる
    assert res == [] and len(rows) == 100  # 2 回目に進まない（1 回目の 1 s = 100 行）。ログは残る
    wait_stopped(fake)


def test_run_trip_writes_log_then_exits_with_reason(fake, low_gate_limit, monkeypatch, tmp_path):
    import physlearn.link as link

    monkeypatch.setattr(link, "open_port", lambda parser, port, **kw: fake.ser)
    out = tmp_path / "run.csv"
    with pytest.raises(SystemExit) as e:
        main(["run", "--port", "virtual", "--tc", "0.15", "--seconds", "1.0", "--out", str(out)])
    assert "安全ゲートが作動した" in str(e.value) and "|gz| >" in str(e.value)
    assert out.read_text().count("\n") == 101  # ヘッダー + 100 行


def test_id_failure_keeps_the_rows_so_far(fake, monkeypatch, tmp_path):
    import physlearn.link as link

    class Dies(SerialPlant):
        def step(self, cmd, dt):
            if self.n >= 50:
                raise TimeoutError("USB が抜けた")
            self.n += 1
            return super().step(cmd, dt)

        n = 0

    monkeypatch.setattr(link, "open_port", lambda parser, port, **kw: fake.ser)
    monkeypatch.setattr(link, "SerialPlant", lambda **kw: Dies(**kw))
    out = tmp_path / "id.csv"
    with pytest.raises(TimeoutError):
        main(["id", "--port", "virtual", "--out", str(out)])
    assert out.read_text().count("\n") == 51


def test_reset_waits_for_rotation_to_stop(fake, capsys):
    def spin_then_reset(settle):
        with SerialPlant(ser=fake.ser, settle=settle) as p:
            p.reset()
            for _ in range(100):  # 1 s 旋回する（gz は約 2.8 rad/s）
                p.step(Command(-0.5, 0.5), 0.01)
            return p.reset()  # 停止を送ったあとの最初の状態

    fast = spin_then_reset(False)
    assert abs(fast.gz - HIDDEN.gyro_bias) > 0.5  # 待たないと、回っている最中から次の回が始まる
    slow = spin_then_reset(True)
    assert slow.t == 0.0 and abs(slow.gz - HIDDEN.gyro_bias) < 0.1  # バイアス 0.08 の個体でも「止まった」と判定できる
    assert capsys.readouterr().err == ""  # 2 s のタイムアウトの警告は出ていない
