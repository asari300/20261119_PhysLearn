import numpy as np
import pytest

from physlearn import HIDDEN, sim_log
from physlearn.api import Command
from physlearn.log import as_log
from physlearn.mismatch import DEFAULTS, HardPlant, one
from physlearn.sim import SimPlant
from physlearn.sysid import identify


def test_all_off_equals_simplant():
    assert sim_log(HardPlant(HIDDEN, seed=3)) == sim_log(SimPlant(HIDDEN, seed=3))


@pytest.mark.parametrize("name", list(DEFAULTS))
def test_each_on_is_reproducible(name):
    a, b = (sim_log(HardPlant(seed=5, **{name: DEFAULTS[name]})) for _ in range(2))
    assert a == b


def test_delay_raises_tau():
    base = identify(as_log(sim_log(HardPlant())))["motor_tau"]
    late = identify(as_log(sim_log(HardPlant(delay=0.04))))["motor_tau"]
    assert late > base * 1.1


def _spin(plant, u):
    plant.reset()
    for _ in range(200):
        plant.step(Command(-u, u), 0.01)
    return plant.yaw_rate


def test_fb_splits_directions_lr_does_not():
    p = HIDDEN
    assert abs(_spin(HardPlant(p, fb=0.1), 0.4) + _spin(HardPlant(p, fb=0.1), -0.4)) > 0.05
    # 左右のゲイン差だけなら旋回の速さは向きで同じ。かわりに前後に動く
    lr = HardPlant(p, lr=0.1)
    assert _spin(lr, 0.4) == pytest.approx(-_spin(HardPlant(p, lr=0.1), -0.4))
    assert abs(lr.v) > 0.005


def test_imu_offset_moves_ax_only():
    p = HIDDEN.__class__(**{**HIDDEN.__dict__, "gyro_noise": 0.0, "accel_noise": 0.0})
    a, b = SimPlant(p), HardPlant(p, imu_x=0.03)
    a.reset(), b.reset()
    for _ in range(200):
        oa, ob = a.step(Command(-0.4, 0.4), 0.01), b.step(Command(-0.4, 0.4), 0.01)
    assert ob.gz == oa.gz
    assert ob.ax - oa.ax == pytest.approx(-(b.yaw_rate**2) * 0.03)


def test_one_runs(capsys):
    r = one("imu_x", 0.03)
    assert r["ax"] < -0.05 and np.isfinite(r["est"]["yaw_gain"])
