from dataclasses import replace

import pytest

from physlearn import HIDDEN, sim_log
from physlearn.compare import fit, holdout, spread
from physlearn.log import as_log
from physlearn.randomize import SPREAD
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
    assert (s["motor_gain"]["lo"], s["motor_gain"]["hi"]) == pytest.approx((-0.1, 0.1))  # 平均 20 に対する比
    assert s["motor_gain"]["half"] == pytest.approx(0.1)
    assert s["motor_tau"]["half"] == 0 and s["motor_tau"]["ratio"] == 0
    assert s["deadband"]["half"] == pytest.approx(0.02)


def test_spread_asymmetric_outside_is_judged_per_side():
    assert SPREAD["motor_gain"] == (-0.30, +0.14)  # 下に広く（電池の消耗）、上に狭い

    def ratio(*gains):
        return spread([Params(motor_gain=g) for g in gains])["motor_gain"]["ratio"]

    assert ratio(14, 20, 20, 20) < 1  # 平均 18.5 に対し 下 -24 % 上 +8 %: 下に広い幅の中
    assert ratio(20, 20, 20, 26) > 1  # 下 -7 % 上 +21 %: 上の幅 +14 % を超える
    assert ratio(10, 20, 20) > 1  # 下 -40 %: 下の幅 -30 % を超える
    assert ratio(14, 20, 20, 20) == pytest.approx(max(0.2432 / 0.30, 0.0811 / 0.14), rel=1e-3)


def test_noise_free_log_is_refused():
    p = replace(HIDDEN, gyro_noise=0.0, accel_noise=0.0)
    with pytest.raises(ValueError, match="雑音が 0"):
        fit(as_log(sim_log(SimPlant(p, seed=0))), p)
