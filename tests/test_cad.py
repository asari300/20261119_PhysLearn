import pytest

from physlearn.cad import DEFAULT_PARTS, mass_props, part_izz, to_mjcf


def test_parallel_axis_matches_box():
    # 同じ箱を 2 つに割って左右に並べても、1 つの箱の Izz と同じになる
    whole = mass_props([("box", 2.0, (0, 0, 0), (0.2, 0.1, 0.02))])[2]
    halves = mass_props([("box", 1.0, (0, 0.025, 0), (0.2, 0.05, 0.02)), ("box", 1.0, (0, -0.025, 0), (0.2, 0.05, 0.02))])[2]
    assert halves == pytest.approx(whole)


def test_matches_mujoco_and_imu_offset():
    mujoco = pytest.importorskip("mujoco")
    from physlearn.cad import spin

    model = mujoco.MjModel.from_xml_string(to_mjcf())
    # 車体の箱は MuJoCo が geom から出す慣性と一致する
    shape, m, _, size = DEFAULT_PARTS[0]
    assert model.body("chassis").inertia[2] == pytest.approx(part_izz(shape, m, size))
    assert model.body("chassis").mass[0] + 2 * model.body("left_wheel").mass[0] == pytest.approx(mass_props(DEFAULT_PARTS)[0])
    # IMU を 4 cm 前に置くと、一定の旋回で ax = -ω² d（向心加速度）
    rows = spin(to_mjcf(imu=(0.04, 0, 0)))
    ax, w = rows[-1][1], rows[-1][2]
    assert ax == pytest.approx(-w * w * 0.04, rel=0.1)
