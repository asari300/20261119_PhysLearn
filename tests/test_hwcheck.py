"""hwcheck を偽の XIAO で試す。偽物は水平の姿勢しか出せないので、3 姿勢の対応づけは純粋な関数で試す。"""

import itertools
import threading

import numpy as np
import pytest

from physlearn.hwcheck import G, gravity_axis, main, read, solve, stream_checks
from physlearn.link import parse_axes


@pytest.fixture
def fake_factory(fake_factory, monkeypatch):  # conftest の同名の fixture を包む
    """仮想の時刻の偽物（tests/conftest.py）。hwcheck の壁時計と open_port を、この偽物の時刻・口に差し替える。

    実機では「PC 壁時計 周期」は USB・OS の遅れを測る意味のある項目。ここでは壁時計の代わりに偽物の時刻で測るので、
    項目は判定に残るが、負荷には依らず 10 ms ちょうどになる（判定の式と基準が効くことを確かめるための値）。
    """
    from types import SimpleNamespace

    import physlearn.hwcheck as hw

    def make(axes="x,y,z"):
        f = fake_factory(axes)
        monkeypatch.setattr(hw, "time", SimpleNamespace(monotonic=lambda: f.t_ms / 1000, sleep=lambda s: None))
        monkeypatch.setattr(hw, "open_port", lambda parser, port, **kw: f.ser)
        return f

    return make


def test_stream_passes_period_gaps_and_gravity(fake_factory):
    f = fake_factory()
    d, notes, bad = read(f.ser, 2.0)
    res = {c[0]: c for c in stream_checks(d, notes, bad)}
    assert len(d) == 200  # 2.0 s / 10 ms。仮想の時刻なので毎回ちょうど（壁時計だと境で ±1〜2 個ずれた）
    for name in ("MCU 周期 平均", "MCU 周期 最大", "欠けたサンプル", "壊れた行", "PC 壁時計 周期 平均", "# ERR の行", "加速度ノルム - 9.81", "飽和の疑い"):
        assert res[name][2], res[name]
    assert np.diff(d[:, 0]).mean() == pytest.approx(10.0, abs=0.01)
    assert d[:, 4].mean() == pytest.approx(9.81, abs=0.05)
    assert not res["ジャイロ平均 gx gy gz"][2]  # 偽物の gz バイアス 0.08 は SPREAD の 0.02 を超える。NG と言えること


def test_stream_detects_gap_and_saturation(fake_factory):
    f = fake_factory()
    d, notes, bad = read(f.ser, 1.0)
    d = np.delete(d, [30, 31], axis=0)  # 2 個欠けた
    d[50:55, 7] = 20.0  # gz が端に張り付いた
    res = {c[0]: c for c in stream_checks(d, ["# ERR imu not found"], 1)}
    assert res["欠けたサンプル"][1] == "2 個" and not res["欠けたサンプル"][2]
    assert not res["飽和の疑い"][2] and not res["# ERR の行"][2] and not res["壊れた行"][2]


@pytest.mark.parametrize("axes", ["x,y,z", "-y,x,z", "x,-y,-z", "z,x,y"])
def test_fake_flat_pose_gives_z_row(fake_factory, axes):
    # 水平の姿勢で重力が出る基板の軸 = 機体 z に当たる行
    f = fake_factory(axes)
    d, _, _ = read(f.ser, 0.5)
    row = parse_axes(axes)[2]
    assert gravity_axis(d[:, 2:5]) == (int(np.argmax(np.abs(row))), int(row.sum()))


def test_solve_recovers_all_24_mountings():
    n = 0
    for perm in itertools.permutations("xyz"):
        for signs in itertools.product("+-", repeat=3):
            spec = ",".join(s.replace("+", "") + c for s, c in zip(signs, perm))
            try:
                rot = parse_axes(spec)
            except ValueError:
                continue  # 鏡像の 24 通り
            # 基板の読み = rot.T @ (機体で上を向く軸) * g。水平・前上・左上の順
            b = [G * rot.T @ e for e in np.eye(3)[[2, 0, 1]]]
            assert solve([gravity_axis(np.tile(v, (50, 1))) for v in b]) == spec
            n += 1
    assert n == 24


def test_solve_refuses_mirror_and_repeats():
    flat, front, left = (2, 1), (0, 1), (1, 1)
    assert solve([flat, front, left]) == "x,y,z"
    with pytest.raises(ValueError, match="鏡像"):
        solve([flat, left, front])  # 前上と左上の取り違え
    with pytest.raises(ValueError, match="同じ軸"):
        solve([flat, flat, left])


def test_gravity_axis_refuses_tilt_and_motion():
    tilt = np.radians(35)
    with pytest.raises(ValueError, match="傾いている"):
        gravity_axis(np.tile([G * np.sin(tilt), 0, G * np.cos(tilt)], (50, 1)))
    ok = np.radians(15)
    assert gravity_axis(np.tile([0, -G * np.sin(ok), -G * np.cos(ok)], (50, 1))) == (2, -1)
    shaken = np.tile([0, 0, G], (50, 1)) + np.random.default_rng(0).normal(0, 2, (50, 3))
    with pytest.raises(ValueError, match="動いている"):
        gravity_axis(shaken)
    with pytest.raises(ValueError, match="ほとんど来ない"):
        gravity_axis(np.zeros((3, 3)))


def test_cli_axes_on_fake_refuses_when_poses_repeat(fake_factory, capsys):
    f = fake_factory()  # 偽物は 3 回とも水平。姿勢が同じなら断る
    code = main(["axes", "--port", "virtual", "--no-prompt", "--settle", "0", "--seconds", "0.4"])
    out = capsys.readouterr().out
    assert code == 1 and "重力は基板の +z" in out and "同じ軸" in out


def test_last_err_lists_distinct_err_lines():
    from physlearn.hwcheck import last_err

    assert last_err(["# hello", "# ERR imu not found"] * 5) == "（MCU の報告: # ERR imu not found）"
    assert last_err(["# hello"]) == ""
    assert last_err([f"# ERR e{i}" for i in range(9)]).count("# ERR") == 3


def test_stream_timeout_shows_the_err_the_mcu_sent(capsys):
    # サンプルが 1 つも来ず `# ERR imu not found` だけが流れ続ける（IMU が見つからないスケッチ）
    import os
    import pty
    import time

    pytest.importorskip("pty")

    master, slave = pty.openpty()
    stop = threading.Event()

    def spam():
        while not stop.is_set():
            os.write(master, b"# ERR imu not found\n")
            time.sleep(0.01)

    th = threading.Thread(target=spam, daemon=True)
    th.start()
    try:
        code = main(["stream", "--port", os.ttyname(slave), "--seconds", "0.5"])
    finally:
        stop.set()
        th.join(2)
        os.close(master)
        os.close(slave)
    out = capsys.readouterr().out
    assert code == 1 and "個しか来ない" in out and "# ERR imu not found" in out


def test_missing_port_gives_hint_not_traceback(capsys):
    with pytest.raises(SystemExit) as e:
        main(["stream", "--port", "/dev/no-such-port"])
    err = capsys.readouterr().err
    assert e.value.code == 2 and "ls /dev/ttyACM*" in err and "usbipd" in err
