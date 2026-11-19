import math

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
