import xml.etree.ElementTree as ET

import pytest

from physlearn import HIDDEN
from physlearn.cad import DEFAULT_PARTS, MODEL, TABLE, dimension, mass_props, part_izz, to_mjcf
from physlearn.sim import Params

MJCF_ROWS = ("sim の今の値 (MJCF)",)


def test_params_table_and_mjcf_agree():
    # 寸法の食い違いを試験で固定する。実行時に表は読まない（Params の既定値は定数のまま）
    p = Params()
    assert p.wheel_radius == pytest.approx(dimension("wheel_radius", MJCF_ROWS))
    assert p.track == pytest.approx(dimension("track", MJCF_ROWS))
    root = ET.parse(MODEL).getroot()
    left, right = (root.find(f".//body[@name='{n}_wheel']") for n in ("left", "right"))
    assert float(left.find("geom").get("size")) == pytest.approx(p.wheel_radius)
    assert float(left.get("pos").split()[1]) == pytest.approx(p.track / 2)
    assert float(right.get("pos").split()[1]) == pytest.approx(-p.track / 2)
    assert p.yaw_gain() == pytest.approx(12.0, abs=1e-9)
    assert HIDDEN.yaw_gain() == pytest.approx(8.0, abs=1e-9)


def test_measured_beats_other_sources(tmp_path):
    rows = open(TABLE, encoding="utf-8").read().splitlines()
    assert dimension("wheel_radius") == pytest.approx(0.030)  # 実物の行は【未確認】なので MJCF の行
    # Robo Base の行に measured を入れると、それが優先される
    new = [r.replace("Cytron Robo Base 2WD,wheel_radius,【未確認】,mm,,,,,", "Cytron Robo Base 2WD,wheel_radius,【未確認】,mm,,,,27.5,") for r in rows]
    assert new != rows
    f = tmp_path / "d.csv"
    f.write_text("\n".join(new), encoding="utf-8")
    assert dimension("wheel_radius", table=f) == pytest.approx(0.0275)
    assert dimension("track", table=f) == pytest.approx(0.100)  # 他の項目は変わらない
    # datasheet は assumed に勝つ。measured は datasheet に勝つ
    new2 = [r.replace("Cytron Robo Base 2WD,track,【未確認】,mm,,,,,", "Cytron Robo Base 2WD,track,95,mm,datasheet,,,,") for r in new]
    f.write_text("\n".join(new2), encoding="utf-8")
    assert dimension("track", table=f) == pytest.approx(0.095)
    with pytest.raises(KeyError):
        dimension("no_such_item")


def test_to_mjcf_from_table_and_override():
    pytest.importorskip("mujoco")
    import mujoco

    a, b = mujoco.MjModel.from_xml_string(to_mjcf()), mujoco.MjModel.from_xml_path(str(MODEL))  # 表の寸法 = diffdrive.xml
    assert a.body_pos == pytest.approx(b.body_pos) and a.geom_pos == pytest.approx(b.geom_pos) and a.geom_size == pytest.approx(b.geom_size)
    root = ET.fromstring(to_mjcf(wheel_radius=0.025, track=0.12))
    assert root.find(".//body[@name='chassis']").get("pos") == "0 0 0.025"
    assert root.find(".//body[@name='left_wheel']").get("pos") == "0 0.06 0"
    assert root.find(".//body[@name='left_wheel']/geom").get("size") == "0.025"
    caster = root.find(".//geom[@name='caster_front']").get("pos").split()
    assert float(caster[2]) == pytest.approx(0.01 - 0.025)


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
