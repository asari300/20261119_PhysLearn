"""ヨー角速度の PI 制御器（デッドバンド補償つき）、安全ゲート、閉ループの実行と評価。"""

import math
from dataclasses import dataclass

import numpy as np

from physlearn.api import Command, Obs, Plant
from physlearn.log import row
from physlearn.sim import Params

# 仕様: 0 → TARGET rad/s のステップに対して
TARGET = 3.0  # rad/s
DURATION = 2.0  # s
DT = 0.01  # s
SPEC = {"settle": 0.6, "overshoot": 0.10, "ss_error": 0.05}  # s, 比, rad/s


@dataclass
class YawPI:
    kp: float
    ki: float
    deadband: float  # 目標の向きにこれだけ足してデッドバンドを越す
    bias: float  # gz から引くジャイロのバイアス
    integ: float = 0.0

    def __call__(self, target: float, obs: Obs, dt: float) -> Command:
        e = target - (obs.gz - self.bias)
        # 目標値の FF (target/K) は入れない: 入れると閉ループに零点が出来て行き過ぎる
        ff = math.copysign(self.deadband, target) if target else 0.0
        # 積分は ±1 duty で止める（飽和中に溜めすぎないため）
        self.integ = min(1.0, max(-1.0, self.integ + self.ki * e * dt))
        u = ff + self.kp * e + self.integ
        return Command(-u, u)


def design(p: Params, tc: float = 0.15) -> YawPI:
    """モデル K/(tau s + 1) の極を PI の零点で消し、閉ループを 1/(tc s + 1) にする。"""
    k = p.yaw_gain()
    return YawPI(kp=p.motor_tau / (k * tc), ki=1 / (k * tc), deadband=p.deadband, bias=p.gyro_bias)


class SafetyGate:
    """制御器と Plant の間に置く。sim でも実機でも同じものを通す。

    duty を ±max_duty に切り、変化率を max_rate (duty/s) に抑える。
    指令か観測が NaN/inf、または |gz| が gz_limit を超えたら止めて (0, 0)、以後ずっと止めたまま。
    """

    def __init__(self, max_duty: float = 0.8, max_rate: float = 10.0, gz_limit: float = 15.0):
        self.max_duty, self.max_rate, self.gz_limit = max_duty, max_rate, gz_limit
        self.prev = Command(0.0, 0.0)
        self.tripped = ""

    def __call__(self, cmd: Command, obs: Obs, dt: float) -> Command:
        vals = [cmd.left, cmd.right, obs.ax, obs.ay, obs.az, obs.gx, obs.gy, obs.gz]
        if not all(math.isfinite(v) for v in vals):
            self.tripped = self.tripped or "NaN/inf"
        elif abs(obs.gz) > self.gz_limit:
            self.tripped = self.tripped or f"|gz| > {self.gz_limit}"
        if self.tripped:
            self.prev = Command(0.0, 0.0)
            return self.prev
        step = self.max_rate * dt

        def lim(u, u0):
            u = min(self.max_duty, max(-self.max_duty, u))
            return min(u0 + step, max(u0 - step, u))

        self.prev = Command(lim(cmd.left, self.prev.left), lim(cmd.right, self.prev.right))
        return self.prev


def run(plant: Plant, ctrl, target: float = TARGET, duration: float = DURATION, dt: float = DT):
    """閉ループで 1 回走らせる。(ログの行, 評価に使う時系列 t, y) を返す。

    y は sim なら真のヨー角速度、実機なら gz（真値が無いので）。
    """
    gate = SafetyGate()
    obs = plant.reset()
    rows, ts, ys = [], [], []
    for _ in range(round(duration / dt)):
        cmd = gate(ctrl(target, obs, dt), obs, dt)
        obs = plant.step(cmd, dt)
        rows.append(row(obs, cmd))
        ts.append(obs.t)
        ys.append(getattr(plant, "yaw_rate", obs.gz))
    return rows, np.array(ts), np.array(ys)


def metrics(t: np.ndarray, y: np.ndarray, target: float = TARGET) -> dict:
    """整定時間（±5% に入ったきり出ない時刻）、行き過ぎ（比）、定常偏差（最後の 0.5 s の平均）。"""
    out = np.abs(y - target) > 0.05 * abs(target)
    settle = t[np.nonzero(out)[0][-1]] if out.any() else 0.0
    if out[-1]:
        settle = math.inf
    return {
        "settle": float(settle),
        "overshoot": float(max(0.0, (y.max() - target) / target)),
        "ss_error": float(abs(y[t >= t[-1] - 0.5].mean() - target)),
    }


def passes(m: dict) -> bool:
    return all(m[k] <= SPEC[k] for k in SPEC)
