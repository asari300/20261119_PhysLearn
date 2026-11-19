from dataclasses import replace

import pytest

from physlearn import HIDDEN, sim_log
from physlearn.compare import fit, holdout, spread
from physlearn.log import as_log
from physlearn.sim import Params, SimPlant


@pytest.fixture(scope="module")
def log():
    return as_log(sim_log(SimPlant(HIDDEN, seed=1)))


def test_same_model_is_within_noise(log):
    f = fit(log, HIDDEN)
    assert f["all"] < 2 * f["noise"]
    assert f["verdict"] == "雑音の範囲で合っている"


def test_wrong_tau_raises_rise_residual_and_verdict(log):
    ok, bad = fit(log, HIDDEN), fit(log, replace(HIDDEN, motor_tau=2 * HIDDEN.motor_tau))
    assert bad["rise"] > 5 * ok["rise"]
    assert bad["verdict"].startswith("時定数")
    assert 0.4 < bad["tau"][0] < 0.7  # 半分に戻せと言う


def test_wrong_gain_is_called_gain(log):
    assert fit(log, HIDDEN.with_yaw_gain(0.8 * HIDDEN.yaw_gain()))["verdict"].startswith("ゲイン")


def test_holdout_runs_and_generalizes_on_symmetric_plant(log):
    train, test = holdout(log)
    assert test["all"] < 2 * test["noise"] and train["all"] < 2 * train["noise"]


def test_spread_known_input():
    ps = [Params(motor_gain=g, motor_tau=t, deadband=d) for g, t, d in ((18, 0.1, 0.1), (22, 0.1, 0.14))]
    s = spread(ps)
    assert s["motor_gain"]["half"] == pytest.approx(0.1)  # (22-18)/2 / 20
    assert s["motor_gain"]["ratio"] == pytest.approx(0.5)
    assert s["motor_tau"]["half"] == 0
    assert s["deadband"]["half"] == pytest.approx(0.02)
