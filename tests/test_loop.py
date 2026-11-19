import pytest

from physlearn import loop_demo
from physlearn.control import passes


def test_loop_demo_improves():
    before, after = loop_demo(n=20).values()
    assert not passes(before)
    assert passes(after)
    assert after["ss_error"] < before["ss_error"]


def test_loop_demo_with_mujoco_stand_in():
    pytest.importorskip("mujoco")
    before, after = loop_demo(n=10, real="mujoco").values()
    assert passes(after)
    assert after["ss_error"] < before["ss_error"]


def test_hard_plant_by_name_and_loop():
    from physlearn import PLANTS, make_plant
    from physlearn.mismatch import HardPlant

    assert "hard" in PLANTS and isinstance(make_plant("hard"), HardPlant)
    out = loop_demo(n=10, real="hard")  # 1 周が動く（通るかは問わない。式の外の現象があるので）
    assert set(out) == {"前 (公称の sim)", "後 (同定した sim)"}
