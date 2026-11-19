import math

import numpy as np

from physlearn.api import Command, Obs
from physlearn.control import SafetyGate, design, metrics, passes, run
from physlearn.sim import Params, SimPlant

OBS = Obs(0, 0, 0, 9.81, 0, 0, 0)


def test_nominal_meets_spec():
    m = metrics(*run(SimPlant(Params()), design(Params()))[1:])
    assert passes(m), m


def test_gate_saturates_and_rate_limits():
    g = SafetyGate(max_duty=0.8, max_rate=10.0)
    assert g(Command(5.0, -5.0), OBS, 0.01) == Command(0.1, -0.1)
    for _ in range(20):
        c = g(Command(5.0, -5.0), OBS, 0.01)
    assert c == Command(0.8, -0.8)


def test_gate_stops_on_nan_and_latches():
    g = SafetyGate()
    g(Command(0.05, 0.05), OBS, 0.01)
    assert g(Command(math.nan, 0.1), OBS, 0.01) == Command(0.0, 0.0)
    assert g(Command(0.05, 0.05), OBS, 0.01) == Command(0.0, 0.0)
    assert g.tripped


def test_gate_stops_on_out_of_range_obs():
    g = SafetyGate(gz_limit=15.0)
    bad = Obs(0, 0, 0, 9.81, 0, 0, 20.0)
    assert g(Command(0.05, 0.05), bad, 0.01) == Command(0.0, 0.0)
    assert g(Command(0.05, 0.05), OBS, 0.01) == Command(0.0, 0.0)


def test_metrics_negative_target_overshoot():
    t = np.arange(1, 201) * 0.01
    y = np.where(t < 0.5, -3.6, -3.0)  # -3 を目標に -3.6 まで行き過ぎる
    assert abs(metrics(t, y, target=-3.0)["overshoot"] - 0.2) < 1e-9


def test_metrics_zero_target_no_division():
    t = np.arange(1, 201) * 0.01
    with np.errstate(all="raise"):
        m = metrics(t, np.zeros_like(t), target=0.0)
    assert m["overshoot"] == 0.0 and m["settle"] == 0.0


def test_run_accepts_caller_gate():
    from physlearn.api import Command
    from physlearn.control import SafetyGate, run
    from physlearn.sim import SimPlant

    gate = SafetyGate(max_duty=0.3)
    rows, _, _ = run(SimPlant(), lambda target, obs, dt: Command(-1.0, 1.0), gate=gate)
    assert max(max(abs(r[7]), abs(r[8])) for r in rows) <= 0.3 and gate.tripped == ""
    bad = SafetyGate()
    run(SimPlant(), lambda target, obs, dt: Command(float("nan"), 0.0), gate=bad)
    assert bad.tripped  # NaN で止まった理由が呼び出し側から読める
