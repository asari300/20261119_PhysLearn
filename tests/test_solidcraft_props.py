"""SolidCraft の質量特性の出力を SI で読む。見本は tests/data/solidcraft/（v0.44.1 の CLI の実際の出力）。"""

import copy
import json
from math import pi
from pathlib import Path

import pytest

from physlearn import solidcraft_props as sp

DATA = Path(__file__).parent / "data" / "solidcraft"
MASS = DATA / "plate_mount.mass.json"
URDF = DATA / "plate_mount.urdf"

# cad/plate_mount.json: 120 x 90 x 3 mm、窓 21.6 x 18.4、穴 4 個 径 3.2、PLA 1.24 g/cm3
V = 3 * (120 * 90 - 21.6 * 18.4 - 4 * pi * 1.6**2)  # mm3


def test_mass_json_matches_s042_values():
    p = sp.load(MASS)
    assert p.mass * 1e3 == pytest.approx(38.578, abs=5e-4)  # g
    assert p.izz == pytest.approx(7.4826e-5, rel=1e-4)  # S042 の値。自分で走らせた値も 7.48264e-5
    assert p.com == pytest.approx((0, 0, 1.5e-3), abs=1e-12)


def test_matches_hand_calculation():
    p = sp.load(MASS)
    assert p.mass == pytest.approx(V * 1.24e-6, rel=1e-5)  # mm3 * g/cm3 -> kg
    # Izz = 大きい板 - 窓 - 4 穴（円は 1/2 m r^2 + m d^2）
    rho = 1.24e-6  # kg/mm3。kg mm2 で組み、最後に 1e-6 で SI にする
    box = lambda w, d, t: rho * w * d * t * (w**2 + d**2) / 12
    hole = lambda r, x, y: rho * pi * r**2 * 3 * (r**2 / 2 + x**2 + y**2)
    izz = (box(120, 90, 3) - box(21.6, 18.4, 3) - sum(hole(1.6, sx * 50, sy * 30) for sx in (1, -1) for sy in (1, -1))) * 1e-6
    assert p.izz == pytest.approx(izz, rel=1e-3)
    # 同じ質量の直方体（cad.mass_props の近似）は Izz を低く見積もる（S042: 0.967 倍）
    assert p.mass * (0.12**2 + 0.09**2) / 12 == pytest.approx(0.967 * p.izz, abs=2e-3 * p.izz)


def test_urdf_agrees_with_mass_json():
    a, b = sp.load(MASS), sp.load(URDF)
    assert b.mass == pytest.approx(a.mass, rel=1e-4)  # URDF は STL 積分で 0.007 % 違う
    assert b.izz == pytest.approx(a.izz, rel=1e-3)
    assert b.com == pytest.approx(a.com, abs=1e-8)


def test_unit_mixup_is_caught():
    data = json.loads(MASS.read_text())
    ok = sp.from_mass_json(data)
    sp.check_box(ok, (0.12, 0.09, 0.003))
    # 慣性の単位を誤って「m の SI のまま」読むと 1e6 倍になる
    wrong = sp.MassProps(ok.mass, ok.com, tuple(tuple(v * 1e6 for v in r) for r in ok.inertia))
    with pytest.raises(ValueError, match="直方体"):
        sp.check_box(wrong, (0.12, 0.09, 0.003))
    # g mm2 を kg mm2 の倍率で読んだ場合（1e3 のずれ）
    g_mm2 = [[v * 1e3 for v in r] for r in data[0]["groups"][0]["mass"]["inertia_world_kg_mm2"]]
    right = sp.from_inertia_g_mm2(ok.mass * 1e3, [0, 0, 1.5], g_mm2)
    assert right.izz == pytest.approx(ok.izz, rel=1e-12)
    # 未知のキーは読まない
    bad = copy.deepcopy(data)
    m = bad[0]["groups"][0]["mass"]
    m["inertia_world_g_mm2"] = m.pop("inertia_world_kg_mm2")
    with pytest.raises(KeyError):
        sp.from_mass_json(bad)


def test_rejects_impossible_tensor():
    with pytest.raises(ValueError, match="三角不等式"):
        sp.from_inertia_g_mm2(10, [0, 0, 0], [[1, 0, 0], [0, 1, 0], [0, 0, 5]])
    with pytest.raises(ValueError, match="質量"):
        sp.from_inertia_g_mm2(0, [0, 0, 0], [[1, 0, 0], [0, 1, 0], [0, 0, 1]])


def test_cli_prints(capsys):
    sp.main([str(MASS)])
    assert "Izz 7.4826e-05" in capsys.readouterr().out
