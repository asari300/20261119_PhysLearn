"""R2S: ログ CSV からジャイロのバイアス・雑音と、ヨー角速度のゲイン・時定数・デッドバンドを推定する。

前提: 指令は区間ごとに一定（`sim.id_experiment` の形）。同じ振幅のステップが 4 回以上あれば、前半と後半の K の比 `drift` も返す。最初の区間は静止 (0, 0)。
動いたステップが 2 つ未満なら（静止だけのログ）、ジャイロのバイアスと雑音だけを返す。
旋回成分 u = (right - left) / 2 だけを見る。ゲイン・デッドバンド・時定数は、ログ全体へ一次遅れ
モデル（`first_order`）を当てはめて決める（τ と d の格子ごとに K を最小二乗で出し、残差が最小の組）。
各区間の定常値は「動いたか」の判定にだけ使う。
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
    a = 1 - np.exp(-dt[:, None] / taus)  # 各時刻・各 τ の一次遅れの係数
    y, out = np.zeros_like(taus), np.empty((len(u), len(taus)))
    for n in range(len(u)):
        y += (drive[n] - y) * a[n]
        out[n] = y
    return out


def _best(u, t, y, taus, dbs):
    """(残差二乗和, K, d, τ) の最小。各 (d, τ) の K は y ≈ K m の最小二乗（K < 0 は 0 に切る）。"""
    best = (np.inf, 0.0, 0.0, 0.0)
    for d in dbs:
        m = first_order(u, t, 1.0, d, taus)
        mm, my = (m * m).sum(axis=0), m.T @ y
        k = np.maximum(0.0, np.divide(my, mm, out=np.zeros_like(mm), where=mm > 0))
        err = y @ y - 2 * k * my + k * k * mm
        j = int(np.argmin(err))
        best = min(best, (float(err[j]), float(k[j]), float(d), float(taus[j])))
    return best


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

    # 動いたステップの数: 各区間の後ろ 30% を定常とみなして、雑音の 10 倍を超えたもの
    ss = [np.sign(u[j - 1]) * y[i + int(0.7 * (j - i)) : j].mean() for i, j in segs[1:] if u[j - 1] != 0]
    if sum(v > 10 * noise for v in ss) < 2:  # 静止だけのログ（モーター無しの XIAO など）ではゲインとデッドバンドを分けられない
        return {"gyro_bias": bias, "gyro_noise": noise}
    # モデル K*dz(u; d) を τ の格子に通した応答は K に比例するので、(d, τ) ごとに K は最小二乗で閉じた形で出る。
    # 実際に出した指令（ゲートの傾斜込み）で走らせるので、立ち上がりの遅れを定常値に混ぜない。
    taus = np.geomspace(0.01, 2.0, 400)
    _, k, db, tau = _best(u, t, y, taus, np.arange(0, 0.301, 0.01))
    _, k, db, tau = _best(u, t, y, taus, np.clip(np.arange(db - 0.01, db + 0.0101, 0.001), 0, None))  # 最良の近くを細かく
    out = {
        "gyro_bias": bias,
        "gyro_noise": noise,
        "yaw_gain": float(k),
        "deadband": float(db),
        "motor_tau": float(tau),
    }
    drift = _drift(u, y, first_order(u, t, 1.0, db, np.array([tau]))[:, 0], segs)
    if drift is not None:
        out["drift"] = drift
    return out


def _drift(u, y, m, segs):
    """同じ振幅のステップが 4 回以上あれば、最初の 2 回と最後の 2 回（と直後の 0 の区間）で K を別々に出し、K後 / K前 - 1。

    m は当てはめたモデルの K = 1 での応答。電池が減るなどして K が途中で変わると 0 から外れる。無ければ None。
    """
    amps = {}
    for n, (_, j) in enumerate(segs):
        if u[j - 1] != 0:
            amps.setdefault(round(abs(float(u[j - 1])), 2), []).append(n)
    runs = [v for v in amps.values() if len(v) >= 4]
    if not runs:
        return None

    def gain(n1, n2):  # 区間 n1..n2（n2 の後ろが 0 の区間ならそれも）で y ≈ K m
        end = n2 + 1 if n2 + 1 < len(segs) and u[segs[n2 + 1][1] - 1] == 0 else n2
        w = slice(segs[n1][0], segs[end][1])
        return (m[w] @ y[w]) / (m[w] @ m[w])

    first, last = runs[0][:2], runs[0][-2:]
    return float(gain(*last) / gain(*first) - 1)


def apply(p: Params, est: dict) -> Params:
    """推定値で sim のパラメータを直す（車輪半径・トレッドは測れないのでそのまま）。推定しなかった値も元のまま。"""
    p = replace(p, **{k: est[k] for k in ("gyro_bias", "gyro_noise", "deadband", "motor_tau") if k in est})
    return p.with_yaw_gain(est["yaw_gain"]) if "yaw_gain" in est else p
