from physlearn.api import Command
from physlearn.sim import Params, SimPlant


def test_seed_reproducible_and_still_imu(tmp_path):
    a, b = SimPlant(seed=3), SimPlant(seed=3)
    assert a.reset() == b.reset()
    assert a.step(Command(-0.5, 0.5), 0.01) == b.step(Command(-0.5, 0.5), 0.01)
    o = SimPlant().reset()
    assert abs(o.az - 9.81) < 0.3


def test_params_json_roundtrip(tmp_path):
    p = Params(motor_gain=12.0, gyro_bias=0.1)
    p.save(tmp_path / "p.json")
    assert Params.load(tmp_path / "p.json") == p


def test_steady_yaw_rate_matches_model():
    p = Params(gyro_noise=0.0)
    s = SimPlant(p)
    s.reset()
    for _ in range(200):
        s.step(Command(-0.5, 0.5), 0.01)
    assert abs(s.yaw_rate - p.yaw_gain() * (0.5 - p.deadband)) < 1e-6
