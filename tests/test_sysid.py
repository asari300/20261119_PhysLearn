from dataclasses import replace

import pytest

from physlearn import HIDDEN, sim_log
from physlearn.api import Command
from physlearn.log import as_log, read_csv, row, write_csv
from physlearn.sim import Params, SimPlant
from physlearn.sysid import apply, identify


def test_recovers_known_params_via_csv(tmp_path):
    true = HIDDEN
    write_csv(tmp_path / "log.csv", sim_log(SimPlant(true, seed=7)))
    est = identify(read_csv(tmp_path / "log.csv"))
    assert abs(est["gyro_bias"] - true.gyro_bias) < 0.01
    assert abs(est["gyro_noise"] - true.gyro_noise) < 0.005
    assert abs(est["yaw_gain"] / true.yaw_gain() - 1) < 0.05
    assert abs(est["motor_tau"] / true.motor_tau - 1) < 0.1
    assert abs(est["deadband"] - true.deadband) < 0.02
    p = apply(Params(), est)
    assert abs(p.motor_gain / true.motor_gain - 1) < 0.05


def test_still_only_log_gives_bias_and_noise():
    plant = SimPlant(HIDDEN, seed=3)
    plant.reset()
    rows = [row(plant.step(Command(0, 0), 0.01), Command(0, 0)) for _ in range(300)]
    est = identify(as_log(rows))
    assert set(est) == {"gyro_bias", "gyro_noise"}
    assert abs(est["gyro_bias"] - HIDDEN.gyro_bias) < 0.01
    assert apply(Params(), est).motor_gain == Params().motor_gain


@pytest.mark.parametrize("tau", [0.02, 0.2, 0.4])
def test_noise_free_fit_recovers_gain_deadband_tau(tau):
    # 各段の後ろ 30 % の平均だと、τ が大きいほど K が低く出た（0 / -1.8 / -14 %）。モデルの当てはめなら出ない
    p = replace(Params(), motor_tau=tau, gyro_noise=0.0, accel_noise=0.0)
    est = identify(as_log(sim_log(SimPlant(p))))
    assert abs(est["yaw_gain"] / p.yaw_gain() - 1) < 0.02
    assert abs(est["deadband"] - p.deadband) < 0.005
    assert abs(est["motor_tau"] / tau - 1) < 0.05


def test_hidden_noisy_log_gain():
    est = identify(as_log(sim_log(SimPlant(HIDDEN, seed=0))))
    assert est["yaw_gain"] == pytest.approx(8.0, abs=0.1)
