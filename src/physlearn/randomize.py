"""S2R: パラメータをばらつかせて、制御器が仕様を満たす割合を見る。ゲインの粗い探索も。"""

from dataclasses import replace

import numpy as np

from physlearn.control import design, metrics, passes, run
from physlearn.sim import Params, SimPlant

# 公称値からの幅。gain・tau は比の (下, 上)（非対称）、deadband・bias は足す量（±）。
# 決め方は log/work/2026-11-19-s041-numbers-once.md: 物理（13 章 6 節）と代役の実測の広いほう。
SPREAD = {"motor_gain": (-0.30, +0.14), "motor_tau": (-0.14, +0.60), "deadband": 0.03, "gyro_bias": 0.02}


def sample(p: Params, rng: np.random.Generator) -> Params:
    s = SPREAD
    return replace(
        p,
        motor_gain=p.motor_gain * rng.uniform(1 + s["motor_gain"][0], 1 + s["motor_gain"][1]),
        motor_tau=p.motor_tau * rng.uniform(1 + s["motor_tau"][0], 1 + s["motor_tau"][1]),
        deadband=max(0.0, p.deadband + rng.uniform(-s["deadband"], s["deadband"])),
        gyro_bias=p.gyro_bias + rng.uniform(-s["gyro_bias"], s["gyro_bias"]),
    )


def evaluate(p: Params, tc: float, n: int = 100, seed: int = 0) -> float:
    """公称 p で設計したゲインを、p のまわりにばらつかせた n 台で試し、仕様を満たした割合。"""
    rng = np.random.default_rng(seed)
    ok = 0
    for i in range(n):
        _, t, y = run(SimPlant(sample(p, rng), seed=seed + i), design(p, tc))
        ok += passes(metrics(t, y))
    return ok / n


def tune(p: Params, n: int = 50, seed: int = 0) -> tuple[float, float]:
    """閉ループの時定数 tc を粗く探し、通過率が最大のもの（同率なら速いもの）を返す。"""
    rate, neg_tc = max((evaluate(p, tc, n, seed), -tc) for tc in (0.08, 0.1, 0.15, 0.2, 0.25))
    return -neg_tc, rate
