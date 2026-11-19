"""SolidCraft の質量特性の出力ファイルを読み、SI（kg・m・kg m^2）の質量・重心・慣性テンソルにする。

CLI は呼ばない。出力のファイルを読むだけなので、SolidCraft が無い環境でも試験できる。
読めるもの:
  - `solidcraft-cli run cad/plate_mass.json --in X.sc --results --json-out mass.json` の JSON
    （`assembly.mass_properties`。慣性は `inertia_*_kg_mm2` = kg mm^2、長さは mm）
  - `file.export_urdf` の URDF の `<inertial>`（もともと m・kg・kg m^2）
  - 公式の文書にある `inertia_g_mm2`（g mm^2）の JSON
単位の換算はこのファイルの `_KEY_TO_SI` の 1 か所。キーの名前で単位を決め、知らない名前は読まずに落とす。

    python -m physlearn.solidcraft_props mass.json      # または plate.urdf
"""

import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from math import sqrt
from pathlib import Path

MM = 1e-3
# 慣性のキー名 → SI（kg m^2）への倍率。単位の取り違え（1e3・1e6・1e9 のずれ）はここだけで起こる。
_KEY_TO_SI = {"inertia_kg_mm2": 1e-6, "inertia_local_kg_mm2": 1e-6, "inertia_world_kg_mm2": 1e-6,
              "inertia_g_mm2": 1e-9}


@dataclass(frozen=True)
class MassProps:
    mass: float  # kg
    com: tuple  # 重心 [m]（出力した座標系）
    inertia: tuple  # 重心回りの慣性テンソル 3x3 [kg m^2]（行の入れ子のタプル）

    @property
    def izz(self) -> float:
        return self.inertia[2][2]


def _check(p: MassProps) -> MassProps:
    """物理的にありえない値（質量が 0 以下、主モーメントが三角不等式を破る）を落とす。"""
    if not p.mass > 0:
        raise ValueError(f"質量が正でない: {p.mass}")
    ixx, iyy, izz = p.inertia[0][0], p.inertia[1][1], p.inertia[2][2]
    for a, b, c in ((ixx, iyy, izz), (iyy, izz, ixx), (izz, ixx, iyy)):
        if a + b < c * (1 - 1e-6):
            raise ValueError(f"慣性が三角不等式を破る（単位の取り違えかもしれない）: {ixx:.4g} {iyy:.4g} {izz:.4g}")
    return p


def _tensor(rows, scale):
    return tuple(tuple(float(v) * scale for v in r) for r in rows)


def from_mass_json(data, frame="world") -> MassProps:
    """`assembly.mass_properties` の結果（JSON を読んだもの）。groups が 1 つのときだけ。frame: "world" か "local"。"""
    if isinstance(data, list):  # run --results は設計ごとの配列
        if len(data) != 1:
            raise ValueError(f"設計が {len(data)} 個ある。1 個ずつ渡す")
        data = data[0]
    groups = data["groups"]
    if len(groups) != 1:
        raise ValueError(f"groups が {len(groups)} 個ある。足し合わせは cad.py の持ち分で、ここでは 1 個だけ")
    m = groups[0]["mass"]
    key = f"inertia_{frame}_kg_mm2"
    if key not in m:
        raise KeyError(f"{key} が無い。あるキー: {sorted(m)}")
    com_key = "center_of_mass_mm" if frame == "world" else "center_of_mass_local_mm"
    return _check(MassProps(m["mass_kg"], tuple(v * MM for v in m[com_key]), _tensor(m[key], _KEY_TO_SI[key])))


def from_inertia_g_mm2(mass_g, com_mm, inertia_g_mm2) -> MassProps:
    """公式の文書の形（g・mm・g mm^2。`total.inertia_g_mm2`）から。"""
    return _check(MassProps(mass_g * 1e-3, tuple(v * MM for v in com_mm), _tensor(inertia_g_mm2, _KEY_TO_SI["inertia_g_mm2"])))


def from_urdf(path, link=None) -> MassProps:
    """URDF の最初の（または名前 link の）`<inertial>`。URDF は m・kg・kg m^2 なので換算はしない。rpy は 0 のみ受ける。"""
    for lk in ET.parse(path).getroot().iter("link"):
        inertial = lk.find("inertial")
        if inertial is None or (link and lk.get("name") != link):
            continue
        o = inertial.find("origin")
        xyz = tuple(float(v) for v in (o.get("xyz", "0 0 0") if o is not None else "0 0 0").split())
        if o is not None and any(float(v) for v in o.get("rpy", "0 0 0").split()):
            raise ValueError("<origin rpy> が 0 でない URDF は未対応")
        i = inertial.find("inertia").attrib
        g = lambda k: float(i[k])
        t = ((g("ixx"), g("ixy"), g("ixz")), (g("ixy"), g("iyy"), g("iyz")), (g("ixz"), g("iyz"), g("izz")))
        return _check(MassProps(float(inertial.find("mass").get("value")), xyz, t))
    raise ValueError("<inertial> のある link が無い")


def load(path) -> MassProps:
    path = Path(path)
    return from_urdf(path) if path.suffix == ".urdf" else from_mass_json(json.loads(path.read_text()))


def check_box(p: MassProps, size_m, rel=0.5) -> None:
    """バウンディングボックス size_m=(sx, sy, sz) [m] の中の物体として、Izz がありえる範囲か確かめる。

    同じ質量の中身の詰まった直方体の Izz m(sx²+sy²)/12 の rel 倍以内。穴あきの板は数 % 動くだけ、
    単位を取り違えると 1e3 以上ずれるので、粗い範囲で十分。
    """
    ref = p.mass * (size_m[0] ** 2 + size_m[1] ** 2) / 12
    if not (1 - rel) * ref <= p.izz <= (1 + rel) * ref:
        raise ValueError(f"Izz {p.izz:.4g} が直方体 {ref:.4g} から {rel:.0%} 以上ずれる（単位の取り違えかもしれない）")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        raise SystemExit(__doc__)
    p = load(argv[0])
    print(f"質量 {p.mass:.6g} kg（{p.mass * 1e3:.4f} g）")
    print("重心 [m] " + " ".join(f"{v:+.4e}" for v in p.com))
    for r in p.inertia:
        print("慣性 [kg m^2] " + " ".join(f"{v:+.4e}" for v in r))
    print(f"Izz {p.izz:.4e} kg m^2、回転半径 {sqrt(p.izz / p.mass) * 1e3:.2f} mm")


if __name__ == "__main__":
    main()
