"""hwcheck を偽の XIAO で試す。偽物は水平の姿勢しか出せないので、3 姿勢の対応づけは純粋な関数で試す。"""

import itertools
import threading

import numpy as np
import pytest
import serial

pytest.importorskip("pty")

from physlearn import HIDDEN  # noqa: E402
from physlearn.fakexiao import FakeXiao  # noqa: E402
from physlearn.hwcheck import G, gravity_axis, main, read, solve, stream_checks  # noqa: E402
from physlearn.link import BAUD, parse_axes  # noqa: E402
from physlearn.sim import SimPlant  # noqa: E402


@pytest.fixture
def fake_factory():
    fakes = []

    def make(axes="x,y,z"):
        f = FakeXiao(SimPlant(HIDDEN, seed=1), axes, speed=1.0)  # 周期の検査は実時間でないと意味が無い
        th = threading.Thread(target=f.run, daemon=True)
        th.start()
        fakes.append((f, th))
        return f

    yield make
    for f, th in fakes:
        f.close()
        th.join(2)


def test_stream_passes_period_gaps_and_gravity(fake_factory):
    f = fake_factory()
    with serial.Serial(f.port, BAUD, timeout=0.05) as ser:
        d, notes, bad = read(ser, 2.0)
    res = {c[0]: c for c in stream_checks(d, notes, bad)}
    assert 180 <= len(d) <= 200
    for name in ("MCU 周期 平均", "MCU 周期 最大", "欠けたサンプル", "壊れた行", "PC 壁時計 周期 平均", "# ERR の行", "加速度ノルム - 9.81", "飽和の疑い"):
        assert res[name][2], res[name]
    assert np.diff(d[:, 0]).mean() == pytest.approx(10.0, abs=0.01)
    assert d[:, 4].mean() == pytest.approx(9.81, abs=0.05)
    assert not res["ジャイロ平均 gx gy gz"][2]  # 偽物の gz バイアス 0.08 は SPREAD の 0.02 を超える。NG と言えること


def test_stream_detects_gap_and_saturation(fake_factory):
    f = fake_factory()
    with serial.Serial(f.port, BAUD, timeout=0.05) as ser:
        d, notes, bad = read(ser, 1.0)
    d = np.delete(d, [30, 31], axis=0)  # 2 個欠けた
    d[50:55, 7] = 20.0  # gz が端に張り付いた
    res = {c[0]: c for c in stream_checks(d, ["# ERR imu not found"], 1)}
    assert res["欠けたサンプル"][1] == "2 個" and not res["欠けたサンプル"][2]
    assert not res["飽和の疑い"][2] and not res["# ERR の行"][2] and not res["壊れた行"][2]


@pytest.mark.parametrize("axes", ["x,y,z", "-y,x,z", "x,-y,-z", "z,x,y"])
def test_fake_flat_pose_gives_z_row(fake_factory, axes):
    # 水平の姿勢で重力が出る基板の軸 = 機体 z に当たる行
    f = fake_factory(axes)
    with serial.Serial(f.port, BAUD, timeout=0.05) as ser:
        d, _, _ = read(ser, 0.5)
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
    code = main(["axes", "--port", f.port, "--no-prompt", "--settle", "0", "--seconds", "0.4"])
    out = capsys.readouterr().out
    assert code == 1 and "重力は基板の +z" in out and "同じ軸" in out
