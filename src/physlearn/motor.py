"""DC モーターの式から sim の K・τ を導く（教材 13 章）。

電気: V·u = R·i + L·di/dt + Ke·n·ω      （u は duty。平均電圧 = V·u とみなす近似）
機械: J_eff·dω/dt = n·Kt·i − b·ω         （ω は車輪の角速度、n は減速比）
L を無視すると τ·dω/dt + ω = K·u で、
    K = n·Kt·V / (n²·Kt·Ke + b·R) [rad/s per duty]、τ = J_eff·R / (n²·Kt·Ke + b·R)。
"""

from dataclasses import dataclass, replace

import numpy as np

from physlearn.sim import Params


@dataclass(frozen=True)
class Motor:
    V: float  # 電源電圧 V
    R: float  # 巻線抵抗 Ω
    L: float  # インダクタンス H
    Kt: float  # トルク定数 N m/A（SI では Ke と同じ値）
    n: float  # 減速比（モーター軸 / 車輪）
    b: float = 0.0  # 車輪軸から見た粘性摩擦 N m s

    @property
    def stall(self) -> float:  # 車輪軸の停動トルク / duty
        return self.n * self.Kt * self.V / self.R

    @property
    def damping(self) -> float:  # 車輪軸の「トルク / 角速度」の傾き（逆起電力 + 粘性）
        return self.n**2 * self.Kt**2 / self.R + self.b


def yaw_inertia_on_wheel(j_wheel, i_yaw, r, track):
    """その場旋回で 1 輪のモーターが見る慣性。ヨー Ω = 2rω/track なので
    運動エネルギー ½(2·j_wheel + i_yaw·(2r/track)²)ω² を 2 個のモーターで分ける。"""
    return j_wheel + i_yaw * 2 * r**2 / track**2


def first_order(m: Motor, j_eff: float):
    """(K 車輪 rad/s per duty, τ s)"""
    return m.stall / m.damping, j_eff / m.damping


def simulate(m: Motor, j_eff: float, u: float, t_end: float, dt: float = 1e-5):
    """電気と機械の 2 階の式をそのまま積分（半陰的 Euler）。返り値は (t, ω)。"""
    n = int(round(t_end / dt))
    w, i, out = 0.0, 0.0, np.empty(n)
    for k in range(n):
        # L が小さいと電気側は硬いので、i だけ陰的に解く
        i = (i + dt / m.L * (m.V * u - m.Kt * m.n * w)) / (1 + dt * m.R / m.L)
        w += dt / j_eff * (m.n * m.Kt * i - m.b * w)
        out[k] = w
    return dt * np.arange(1, n + 1), out


def to_params(m: Motor, j_eff: float, base: Params = Params()) -> Params:
    """計算した K・τ を入れた sim の Params（車輪半径・トレッドは base のまま）。"""
    k, tau = first_order(m, j_eff)
    return replace(base, motor_gain=k, motor_tau=tau)


def mujoco_model():
    """models/diffdrive.xml の定数を Motor と j_eff で表す。トルク = 0.05·u − (0.05/30)·ω
    になるように n=1・b=0・Kt=Ke=0.05 と置き、傾き Kt²/R = 0.05/30 から R = 1.5 Ω、
    停動 Kt·V/R = 0.05 から V = 1.5 V。傾きは全部が逆起電力なので、R を足すと K が下がる。"""
    kt, slope = 0.05, 0.05 / 30
    r_coil = kt**2 / slope
    m = Motor(V=0.05 * r_coil / kt, R=r_coil, L=1e-6, Kt=kt, n=1.0, b=0.0)
    r, track = 0.03, 0.10
    j_wheel = 0.4 * 0.02 * r**2  # 球の車輪
    i_box = 0.25 / 12 * (0.12**2 + 0.09**2)  # 箱の z 回り
    i_yaw = i_box + 2 * (0.02 * (track / 2) ** 2 + j_wheel)
    return m, yaw_inertia_on_wheel(j_wheel, i_yaw, r, track)
