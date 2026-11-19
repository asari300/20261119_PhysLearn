import numpy as np

from physlearn.randomize import SPREAD, sample
from physlearn.sim import Params


def test_sample_stays_in_range():
    p, rng = Params(), np.random.default_rng(0)
    for _ in range(100):
        q = sample(p, rng)
        for k in ("motor_gain", "motor_tau"):
            lo, hi = SPREAD[k]
            assert (1 + lo) * getattr(p, k) <= getattr(q, k) <= (1 + hi) * getattr(p, k)
        assert abs(q.deadband - p.deadband) <= SPREAD["deadband"] and q.deadband >= 0
        assert abs(q.gyro_bias - p.gyro_bias) <= SPREAD["gyro_bias"]
