from physlearn import loop_demo
from physlearn.control import passes


def test_loop_demo_improves():
    before, after = loop_demo(n=20).values()
    assert not passes(before)
    assert passes(after)
    assert after["ss_error"] < before["ss_error"]
