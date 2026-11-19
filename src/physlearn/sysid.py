"""R2S: ログ CSV からジャイロのバイアス・雑音と、ヨー角速度のゲイン・時定数・デッドバンドを推定する。

前提: 指令は区間ごとに一定（`sim.id_experiment` の形）。最初の区間は静止 (0, 0)。
動いたステップが 2 つ未満なら（静止だけのログ）、ジャイロのバイアスと雑音だけを返す。
旋回成分 u = (right - left) / 2 だけを見る。ゲインとデッドバンドは各区間の定常値から、
時定数はログ全体へのモデルの当てはめから。
"""

from dataclasses import replace

import numpy as np

from physlearn.sim import Params


def segments(u: np.ndarray, min_len: int = 10) -> list[tuple[int, int]]:
    """指令が一定の区間 [i, j) の一覧。安全ゲートの傾斜で出来る短い区間は次の区間に含める。"""
    cut = np.nonzero(np.diff(u))[0] + 1
    edges = [0, *cut.tolist(), len(u)]
    segs, start = [], 0
    for i, j in zip(edges[:-1], edges[1:]):
        if j - i >= min_len:
            segs.append((start, j))
            start = j
    return segs


def first_order(u: np.ndarray, t: np.ndarray, k: float, db: float, taus: np.ndarray) -> np.ndarray:
    """K*dz(u) を一次遅れに通した応答を、taus の各値について同時に計算する（行 = 時刻）。"""
    drive = k * np.where(np.abs(u) > db, u - np.sign(u) * db, 0.0)
    dt = np.diff(t, prepend=t[0] - (t[1] - t[0]))
    y, out = np.zeros_like(taus), np.empty((len(u), len(taus)))
    for n in range(len(u)):
        y += (drive[n] - y) * (1 - np.exp(-dt[n] / taus))
        out[n] = y
    return out


def identify(log: dict) -> dict:
    t, gz = log["t"], log["gz"]
    u = (log["right"] - log["left"]) / 2
    segs = segments(u)
    i0, j0 = segs[0]
    if np.any(u[i0:j0]) or j0 - i0 < 20:
        raise ValueError("最初に静止区間 (指令 0) が 20 行以上いる")
    still = gz[i0 + (j0 - i0) // 2 : j0]  # 前半は動き出しや前の揺れを避けて捨てる
    bias, noise = float(still.mean()), float(still.std(ddof=1))
    y = gz - bias

    ss_u, ss_y = [], []
    for i, j in segs[1:]:
        if u[j - 1] != 0:
            ss_u.append(abs(u[j - 1]))
            ss_y.append(np.sign(u[j - 1]) * y[i + int(0.7 * (j - i)) : j].mean())  # 後ろ 30% を定常とみなす
    ss_u, ss_y = np.array(ss_u), np.array(ss_y)
    moving = ss_y > 10 * noise
    if moving.sum() < 2:  # 静止だけのログ（モーター無しの XIAO など）ではゲインとデッドバンドを分けられない
        return {"gyro_bias": bias, "gyro_noise": noise}
    # 定常: y = K (u - db)  →  u に対する直線の傾きが K、y = 0 の切片が db
    k, c = np.polyfit(ss_u[moving], ss_y[moving], 1)
    db = float(max(0.0, -c / k))
    # 時定数: 実際に出した指令（ゲートの傾斜込み）でモデルを走らせ、二乗誤差が最小の tau
    taus = np.geomspace(0.01, 2.0, 400)
    err = ((first_order(u, t, k, db, taus) - y[:, None]) ** 2).sum(axis=0)
    return {
        "gyro_bias": bias,
        "gyro_noise": noise,
        "yaw_gain": float(k),
        "deadband": db,
        "motor_tau": float(taus[np.argmin(err)]),
    }


def apply(p: Params, est: dict) -> Params:
    """推定値で sim のパラメータを直す（車輪半径・トレッドは測れないのでそのまま）。推定しなかった値も元のまま。"""
    p = replace(p, **{k: est[k] for k in ("gyro_bias", "gyro_noise", "deadband", "motor_tau") if k in est})
    return p.with_yaw_gain(est["yaw_gain"]) if "yaw_gain" in est else p
