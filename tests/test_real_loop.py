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


def test_args_rejected(capsys):
    # SystemExit だけ見ると、ポートを開く段の失敗でも通る。引数の確認の文に、悪い引数の名前が出ること（S126 #4）
    cases = [("run", ["--target", "9"]), ("run", ["--target", "nan"]), ("run", ["--seconds", "10"]), ("run", ["--tc", "0"]),
             ("run", ["--seconds", "0.004"]), ("run", ["--dt", "0.001"]),  # dt < 0.01 は秒数の上限が効かなくなる
             ("run", ["--dt", "0.5"]),  # dt が大きいと round で切り上がり、jog の上限 1.0 s が 1.3 s まで超えた
             ("jog", ["--left", "0.9"])]
    for mode, bad in cases:
        with pytest.raises(SystemExit):
            main([mode, "--port", "/dev/null-none", *bad])
        assert bad[0] in capsys.readouterr().err.split("error:")[-1], bad  # usage の行にも引数名が出るので、error: の後ろを見る


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


def test_run_failure_keeps_the_rows_so_far(fake, monkeypatch, tmp_path):
    """run の途中で通信の例外が出ても、その回までの行を --out に残す（S129、問題 38）。停止は書くより先に届いている。"""
    import physlearn.link as link

    class Dies(SerialPlant):  # 51 回目の step の読み取りで失敗する（step の except が停止を送る所を通すため、_next で投げる）
        def step(self, cmd, dt):
            self.n += 1
            return super().step(cmd, dt)

        def _next(self):
            if self.n > 50:
                raise TimeoutError("USB が抜けた")
            return super()._next()

        n = 0

    duty_at_write = []
    write_csv = link.write_csv
    monkeypatch.setattr(link, "write_csv", lambda *a: (duty_at_write.append(fake.duty), write_csv(*a))[1])
    monkeypatch.setattr(link, "open_port", lambda parser, port, **kw: fake.ser)
    monkeypatch.setattr(link, "SerialPlant", lambda **kw: Dies(**kw))
    out = tmp_path / "run.csv"
    with pytest.raises(TimeoutError):
        main(["run", "--port", "virtual", "--tc", "0.15", "--seconds", "1.0", "--out", str(out)])
    assert out.read_text().count("\n") == 51  # ヘッダー + 50 行
    assert duty_at_write == [(0.0, 0.0)]
    wait_stopped(fake)


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


def test_run_loop_checks_the_last_sample(fake):
    """ゲートは step の前の観測しか見ない。最後のサンプルだけ gz が閾値超えでも、次の回に進まない（S126 #6）。"""
    class LastSpike(SerialPlant):
        def step(self, cmd, dt):
            o = super().step(cmd, dt)
            self.n = getattr(self, "n", 0) + 1
            return o if self.n != 200 else type(o)(o.t, o.ax, o.ay, o.az, o.gx, o.gy, 100.0)   # 1 回目（2.0 s）の最後

    with LastSpike(ser=fake.ser) as p:
        rows, res, why = run_loop(p, lambda: design(Params(), TC), 3.0, 2.0)
    assert "最後のサンプル" in why and "|gz| >" in why
    assert res == [] and len(rows) == 200     # 2 回目に進んでいない
