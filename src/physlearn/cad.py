"""CAD（寸法と質量の表）から sim へ: 質量・重心・ヨーの慣性を足し合わせ、MJCF を書き換える。

部品は直方体・球・円柱（軸 y）で近似し、平行軸の定理で合成する。
CAD が質量特性（質量・重心・重心回りの Izz）を出せるなら、その値を 1 つの部品として渡せばよい。

    python -m physlearn.cad        # 既定の車体の質量特性と、電池・IMU を動かした MuJoCo の結果を表示
"""

import csv
import xml.etree.ElementTree as ET
from pathlib import Path

MODEL = Path(__file__).parent / "models" / "diffdrive.xml"
TABLE = Path(__file__).parents[2] / "cad" / "dimensions.csv"
SOURCES = ("datasheet", "cad", "assumed")  # measured 欄が最優先。続いて value の source 欄がこの順
# 車輪半径・トレッドを探す行。実物の行（測れば入る）が先、無ければ sim の今の値（assumed）
WHEEL_PARTS = ("Cytron Robo Base 2WD", "sim の今の値 (MJCF)")


def part_izz(shape: str, m: float, size) -> float:
    """部品の重心回り・鉛直軸 z の慣性 [kg m^2]。size は box: 全長 (sx, sy, sz)、sphere: (r,)、cyl_y: (r, 長さ)。"""
    if shape == "box":
        return m * (size[0] ** 2 + size[1] ** 2) / 12
    if shape == "sphere":
        return 0.4 * m * size[0] ** 2
    if shape == "cyl_y":  # 車輪のように y 軸回りに回る円柱。z は直径の向き
        return m * (3 * size[0] ** 2 + size[1] ** 2) / 12
    raise ValueError(shape)


def mass_props(parts):
    """parts: [(shape, 質量, (x, y, z), size)]（機体座標 x 前・y 左・z 上）。→ (質量, 重心, 重心回りの Izz)。"""
    m = sum(p[1] for p in parts)
    c = [sum(p[1] * p[2][i] for p in parts) / m for i in range(3)]
    izz = sum(part_izz(s, mi, sz) + mi * ((x - c[0]) ** 2 + (y - c[1]) ** 2) for s, mi, (x, y, _), sz in parts)
    return m, c, izz


# diffdrive.xml と同じ値（どれも assumed。寸法表 cad/dimensions.csv の「sim の今の値」の行）
DEFAULT_PARTS = [
    ("box", 0.25, (0, 0, 0), (0.12, 0.09, 0.02)),
    ("sphere", 0.02, (0, 0.05, 0), (0.03,)),
    ("sphere", 0.02, (0, -0.05, 0), (0.03,)),
]


def dimension(item: str, parts=WHEEL_PARTS, table=TABLE) -> float:
    """表から item の値 [m] を返す。優先順は measured > datasheet > cad > assumed、同順なら parts の前のほう。

    数として読めない行（【未確認】など）は無いものとする。どの行にも値が無ければ KeyError。
    """
    best = None
    with open(table, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["part"] not in parts or r["item"] != item:
                continue
            for rank, text in ((0, r["measured"]), (1 + SOURCES.index(r["source"]) if r["source"] in SOURCES else 9, r["value"])):
                try:
                    v = float(text)
                except ValueError:
                    continue
                if r["unit"] != "mm":
                    raise ValueError(f"{item}: 単位 {r['unit']!r}（mm のみ）")
                key = (rank, parts.index(r["part"]))
                if best is None or key < best[0]:
                    best = (key, v / 1000)
    if best is None:
        raise KeyError(item)
    return best[1]


def to_mjcf(imu=(0.0, 0.0, 0.0), extra=(), wheel_radius=None, track=None, table=TABLE) -> str:
    """diffdrive.xml を書き換えた文字列。imu: IMU の site の位置 [m]、extra: 車体に足す直方体 [(質量, (x,y,z), (sx,sy,sz))]。

    車輪半径とトレッドは、指定が無ければ寸法表（`dimension`）から。車輪が床に着くよう車体の高さとキャスターの z も合わせる。
    """
    r = dimension("wheel_radius", table=table) if wheel_radius is None else wheel_radius
    b = dimension("track", table=table) if track is None else track
    root = ET.parse(MODEL).getroot()
    chassis = root.find(".//body[@name='chassis']")
    chassis.set("pos", f"0 0 {r}")
    for g in ("caster_front", "caster_rear"):  # 球の半径 0.01 の底が床に着く高さ
        c = chassis.find(f"geom[@name='{g}']")
        x = c.get("pos").split()[0]
        c.set("pos", f"{x} 0 {0.01 - r}")
    for name, side in (("left_wheel", 1), ("right_wheel", -1)):
        w = chassis.find(f"body[@name='{name}']")
        w.set("pos", f"0 {side * b / 2} 0")
        w.find("geom").set("size", str(r))
    chassis.find("site[@name='imu']").set("pos", " ".join(map(str, imu)))
    for m, pos, size in extra:
        ET.SubElement(chassis, "geom", type="box", mass=str(m), contype="0", conaffinity="0",
                      pos=" ".join(map(str, pos)), size=" ".join(str(s / 2) for s in size))
    return ET.tostring(root, encoding="unicode")


def spin(xml: str, u=0.6, seconds=1.5, dt=0.002):
    """その場旋回 (left=-u, right=+u) の時刻と (ax, gz) の列。"""
    from physlearn.api import Command
    from physlearn.mujoco_plant import MujocoPlant

    p = MujocoPlant(xml=xml)
    p.reset()
    out = []
    for _ in range(round(seconds / dt)):
        o = p.step(Command(-u, u), dt)
        out.append((o.t, o.ax, o.gz))
    return out


def tau_63(rows) -> float:
    """gz が定常値（最後の 0.2 s の平均）の 63 % に届く時刻 [s]。"""
    tail = [g for t, _, g in rows if t > rows[-1][0] - 0.2]
    w = sum(tail) / len(tail)
    return next(t for t, _, g in rows if g >= 0.632 * w)


def main():
    m, c, izz = mass_props(DEFAULT_PARTS)
    print(f"既定の車体: 質量 {m:.3f} kg、重心 x {c[0]:+.3f} m、Izz {izz:.3e} kg m^2")
    mb, size = 0.1, (0.06, 0.06, 0.015)  # 単3×4 と箱の想定（assumed、cad/dimensions.csv）
    for dx in (0.0, 0.04):
        m, c, izz = mass_props(DEFAULT_PARTS + [("box", mb, (dx, 0, 0.0175), size)])
        rows = spin(to_mjcf(extra=[(mb, (dx, 0, 0.0175), size)]))
        print(f"電池 0.1 kg を x={dx:+.2f} m: Izz {izz:.3e}、MuJoCo の τ(63%) {tau_63(rows):.3f} s")
    rows = spin(to_mjcf())
    print(f"電池なし: MuJoCo の τ(63%) {tau_63(rows):.3f} s")
    for d in (0.0, 0.04):
        rows = spin(to_mjcf(imu=(d, 0, 0)))
        tail = [(a, g) for t, a, g in rows if t > rows[-1][0] - 0.2]
        ax = sum(a for a, _ in tail) / len(tail)
        w = sum(g for _, g in tail) / len(tail)
        print(f"IMU を x={d:+.2f} m: ω {w:.2f} rad/s、ax {ax:+.3f} m/s^2、-ω²d {-w * w * d:+.3f}")


if __name__ == "__main__":
    main()
