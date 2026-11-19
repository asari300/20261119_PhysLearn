import numpy as np
import pytest

from physlearn import motor
from physlearn.api import Command


def test_first_order_matches_second_order():
    m, j = motor.mujoco_model()
    k, tau = motor.first_order(m, j)
    t, w = motor.simulate(m, j, 0.5, 10 * tau)
    assert w[-1] == pytest.approx(0.5 * k, rel=1e-3)
    assert t[np.argmax(w >= 0.632 * w[-1])] == pytest.approx(tau, rel=0.02)


def test_to_params():
    m, j = motor.mujoco_model()
    p = motor.to_params(m, j)
    assert (p.motor_gain, p.motor_tau) == pytest.approx(motor.first_order(m, j))


def test_prediction_matches_mujoco():
    pytest.importorskip("mujoco")
    from physlearn.mujoco_plant import MujocoPlant

    m, j = motor.mujoco_model()
    k, tau = motor.first_order(m, j)
    plant = MujocoPlant()
    t0 = plant.reset().t
    obs = [plant.step(Command(-0.5, 0.5), 0.002) for _ in range(500)]
    t = np.array([o.t for o in obs]) - t0
    gz = np.array([o.gz for o in obs])
    ss = gz[-50:].mean()
    assert ss == pytest.approx(0.5 * k * 2 * 0.03 / 0.10, rel=0.01)
    # MuJoCo の接触は柔らかく、少し遅れる（0.072 s 対 0.067 s）
    assert t[np.argmax(gz >= 0.632 * ss)] == pytest.approx(tau, rel=0.15)
