"""sim と実機で共通の指令・観測の型（V-World / R-World の境界）。

制御器はこの型だけを見る。相手が numpy の sim か、MuJoCo か、実機 (XIAO) かは
`Plant` の実装で差し替える。ログ (CSV) の列も `LOG_COLUMNS` で揃える。
"""

from dataclasses import dataclass, fields
from typing import Protocol


@dataclass(frozen=True)
class Command:
    """左右モーターの指令。-1..1 の PWM デューティ比で、前進が正。"""

    left: float
    right: float


@dataclass(frozen=True)
class Obs:
    """IMU の観測。機体座標は x 前・y 左・z 上（右手系）。"""

    t: float  # 秒。reset からの経過
    ax: float  # 加速度 m/s^2（静止時 az ≈ +9.81）
    ay: float
    az: float
    gx: float  # 角速度 rad/s（gz > 0 が左旋回）
    gy: float
    gz: float


class Plant(Protocol):
    """制御対象。sim も実機もこの 2 つだけを実装する。"""

    def reset(self) -> Obs: ...

    def step(self, cmd: Command, dt: float) -> Obs:
        """cmd を dt 秒かけて、その終わりの観測を返す。"""
        ...


# ログ CSV の列。1 行 = 1 step（その step で出した指令と、終わりの観測）
LOG_COLUMNS = [f.name for f in fields(Obs)] + ["left", "right"]
