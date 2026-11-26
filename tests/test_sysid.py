from dataclasses import replace

import pytest

from physlearn import HIDDEN, sim_log
from physlearn.api import Command
from physlearn.log import as_log, read_csv, row, write_csv
from physlearn.mismatch import HardPlant
from physlearn.sim import Params, SimPlant, id_experiment
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
    assert abs(est["drift"]) < 0.03  # 雑音ありでも


def test_experiment_shape_and_zero_net_rotation():
    cmds = id_experiment()
    assert len(cmds) == 1700 and sum(c.right for c in cmds) == pytest.approx(0, abs=1e-9)


def test_drift_is_zero_for_constant_plant_and_negative_for_sagging_battery():
    quiet = replace(Params(), gyro_noise=0.0, accel_noise=0.0)
    assert abs(identify(as_log(sim_log(SimPlant(quiet))))["drift"]) < 0.03
    sag = identify(as_log(sim_log(HardPlant(sag=0.27))))  # 電池の低下で K が後半に下がる
    assert sag["drift"] < -0.03


def test_no_drift_without_repeated_amplitude():
    log = as_log(sim_log(SimPlant(HIDDEN, seed=0)))
    n = 1300  # 古い 13 s の実験（同じ振幅が 2 回ずつ）の長さで切る
    assert "drift" not in identify({c: v[:n] for c, v in log.items()})


def test_header_only_csv_is_refused_with_a_sentence(tmp_path, capsys):
    from physlearn import main as cli
    from physlearn.compare import fit, split
    from physlearn.log import LOG_COLUMNS

    p = tmp_path / "empty.csv"
    p.write_text(",".join(LOG_COLUMNS) + "\n")
    log = read_csv(p)
    for f in (identify, split, lambda lg: fit(lg, Params())):
        with pytest.raises(ValueError, match="静止区間"):
            f(log)
    with pytest.raises(SystemExit, match="静止区間"):  # トレースバックではなく 1 行の文で終わる
        cli(["sysid", str(p)])


def test_reversed_motor_is_called_reversed_not_still(tmp_path):
    from physlearn import main as cli

    log = as_log(sim_log(SimPlant(HIDDEN, seed=0)))
    log["gz"] = -log["gz"]  # 配線が逆
    with pytest.raises(ValueError, match="逆向き"):
        identify(log)
    write_csv(tmp_path / "rev.csv", [[log[c][i] for c in log] for i in range(len(log["t"]))])
    with pytest.raises(SystemExit, match="逆向き"):
        cli(["sysid", str(tmp_path / "rev.csv")])
