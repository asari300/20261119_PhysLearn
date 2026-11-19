"""numpy の差動 2 輪 + IMU の sim。`Plant` を実装する。"""

import json
from dataclasses import asdict, dataclass, replace

import numpy as np

from physlearn.api import Command, Obs

G = 9.81


@dataclass(frozen=True)
class Params:
    wheel_radius: float = 0.016  # m
    track: float = 0.08  # m（左右の車輪の間隔）
    motor_gain: float = 30.0  # 車輪の角速度 rad/s / duty（デッドバンドを除いた分）
    motor_tau: float = 0.08  # s（一次遅れの時定数）
    deadband: float = 0.05  # duty。これ以下では回らない
    gyro_bias: float = 0.0  # rad/s（gz のバイアス）
    gyro_noise: float = 0.01  # rad/s（白色雑音の標準偏差、1 サンプルあたり）
    accel_noise: float = 0.05  # m/s^2

    def save(self, path) -> None:
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path) -> "Params":
        with open(path) as f:
            return cls(**json.load(f))

    def yaw_gain(self) -> float:
        """その場旋回 (left=-u, right=+u) での定常ヨー角速度 / (u - deadband)。"""
        return 2 * self.wheel_radius * self.motor_gain / self.track

    def with_yaw_gain(self, k: float) -> "Params":
        return replace(self, motor_gain=k * self.track / (2 * self.wheel_radius))


class SimPlant:
    def __init__(self, p: Params = Params(), seed: int = 0):
        self.p = p
        self.seed = seed

    def reset(self) -> Obs:
        self.rng = np.random.default_rng(self.seed)
        self.t = 0.0
        self.w = np.zeros(2)  # 左右の車輪の角速度 rad/s
        return self._obs(0.0)

    def _drive(self, u: float) -> float:
        p = self.p
        return 0.0 if abs(u) <= p.deadband else p.motor_gain * (u - np.sign(u) * p.deadband)

    def step(self, cmd: Command, dt: float) -> Obs:
        p = self.p
        v0 = self.v
        target = np.array([self._drive(cmd.left), self._drive(cmd.right)])
        # 一次遅れを厳密に離散化（dt が tau に近くても安定）
        self.w += (target - self.w) * (1 - np.exp(-dt / p.motor_tau))
        self.t += dt
        return self._obs((self.v - v0) / dt)

    @property
    def v(self) -> float:
        return self.p.wheel_radius * self.w.mean()

    @property
    def yaw_rate(self) -> float:
        """真のヨー角速度（sim だけが知っている。評価に使う）。"""
        return self.p.wheel_radius * (self.w[1] - self.w[0]) / self.p.track

    def _obs(self, a_lin: float) -> Obs:
        p, n = self.p, self.rng.normal
        an, gn = p.accel_noise, p.gyro_noise
        return Obs(
            t=self.t,
            ax=a_lin + n(0, an),
            ay=self.v * self.yaw_rate + n(0, an),  # 向心加速度（左旋回で +y）
            az=G + n(0, an),
            gx=n(0, gn),
            gy=n(0, gn),
            gz=self.yaw_rate + p.gyro_bias + n(0, gn),
        )


def id_experiment(dt: float = 0.01) -> list[Command]:
    """同定用の開ループ指令列（その場旋回）。静止 1 s のあと、振幅を変えたステップと 0 を交互に。"""
    seq = [0.0] * round(1.0 / dt)
    for u in (0.2, 0.35, 0.5, -0.35, 0.65):
        seq += [u] * round(1.0 / dt) + [0.0] * round(1.0 / dt)
    return [Command(-u, u) for u in seq]
