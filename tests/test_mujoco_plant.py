import pytest

pytest.importorskip("mujoco")

from physlearn.api import Command  # noqa: E402
from physlearn.mujoco_plant import MujocoPlant  # noqa: E402


def run(plant, cmd, seconds, dt=0.01):
    for _ in range(round(seconds / dt)):
        o = plant.step(cmd, dt)
    return o


def test_rest():
    p = MujocoPlant()
    p.reset()
    o = run(p, Command(0, 0), 0.5)
    assert o.az == pytest.approx(9.81, abs=0.05)
    assert abs(o.gz) < 1e-3


def test_left_turn_is_positive_gz():
    p = MujocoPlant()
    p.reset()
    assert run(p, Command(-0.5, 0.5), 1.0).gz > 1.0
    p.reset()
    assert run(p, Command(0.2, 0.6), 1.0).gz > 0.1


def test_both_forward_moves_forward():
    p = MujocoPlant()
    p.reset()
    x0 = p.data.qpos[0]
    run(p, Command(0.5, 0.5), 1.0)
    assert p.data.qpos[0] - x0 > 0.1
    assert abs(p.data.qpos[1]) < 0.01


def test_zero_duty_stops():
    p = MujocoPlant()
    p.reset()
    run(p, Command(-0.5, 0.5), 1.0)
    o = run(p, Command(0, 0), 1.0)
    assert abs(o.gz) < 0.01
    assert abs(p.data.qvel[:2]).max() < 0.01


def test_same_seed_same_result():
    def trace(seed):
        p = MujocoPlant(noise_acc=0.05, noise_gyro=0.005, bias_gyro=(0, 0, 0.02), seed=seed)
        p.reset()
        return [p.step(Command(-0.5, 0.5), 0.01) for _ in range(50)]

    assert trace(1) == trace(1)
    assert trace(1) != trace(2)
