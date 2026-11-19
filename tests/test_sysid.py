from physlearn import HIDDEN, sim_log
from physlearn.log import read_csv, write_csv
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
