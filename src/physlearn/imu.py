"""XIAO 単体（モーター無し）でやる IMU の実験。静止ログの特性・積分のドリフト・回転の検算・IMU モデルの R2S。

    python -m physlearn.imu still still.csv            # 特性とドリフト
    python -m physlearn.imu turn turn.csv              # 手で回したログの角度
    python -m physlearn.imu r2s still.csv --out p.json # sim の IMU の項を直し、直した sim と並べる
"""

import argparse
from dataclasses import replace

import numpy as np

from physlearn.api import Command
from physlearn.log import as_log, read_csv, row, write_csv
from physlearn.sim import G, Params, SimPlant

AXES = ("ax", "ay", "az", "gx", "gy", "gz")


def yaw_deg(log, bias: float = 0.0) -> float:
    """gz を時刻の実測差で積分したヨー角（度）。"""
    return float(np.degrees(np.sum((log["gz"][1:] - bias) * np.diff(log["t"]))))


def allan(x: np.ndarray, dt: float) -> list[tuple[float, float]]:
    """非重複の Allan 偏差。クラスタが 9 個未満になる長い τ は出さない（推定がばらつきすぎる）。"""
    out = []
    for m in (1, 10, 100, 1000):
        k = len(x) // m
        if k < 9:
            break
        means = x[: k * m].reshape(k, m).mean(axis=1)
        out.append((m * dt, float(np.sqrt(0.5 * np.mean(np.diff(means) ** 2)))))
    return out


def stats(log) -> dict:
    dt = np.diff(log["t"])
    a = np.stack([log["ax"], log["ay"], log["az"]])
    norm = np.linalg.norm(a, axis=0).mean()
    ax, ay, az = a.mean(axis=1)
    return {
        "n": len(log["t"]),
        "T": float(log["t"][-1] - log["t"][0]),
        "dt_mean": float(dt.mean()),
        "dt_std": float(dt.std()),
        "dt_max": float(dt.max()),
        "mean": {c: float(log[c].mean()) for c in AXES},
        "std": {c: float(log[c].std()) for c in AXES},
        "norm_err": float(norm - G),
        "roll": float(np.degrees(np.arctan2(ay, az))),
        "pitch": float(np.degrees(np.arctan2(-ax, np.hypot(ay, az)))),
        "drift_raw": yaw_deg(log),
        "drift_fix": yaw_deg(log, log["gz"].mean()),
    }


def fit(log, base: Params = Params()) -> Params:
    """静止ログから sim の IMU の項だけを直す。sim の IMU はバイアスを gz にだけ持つ。"""
    s = stats(log)["std"]
    return replace(
        base,
        gyro_bias=float(log["gz"].mean()),
        gyro_noise=float(np.mean([s["gx"], s["gy"], s["gz"]])),
        accel_noise=float(np.mean([s["ax"], s["ay"], s["az"]])),
    )


def simulate(p: Params, n: int, dt: float, seed: int = 1, cmds=None):
    """SimPlant で n サンプルのログを作る。cmds が無ければ静止。真のヨー角（度）も返す。"""
    plant = SimPlant(p, seed)
    obs, cmd = plant.reset(), Command(0.0, 0.0)
    rows, yaw = [row(obs, cmd)], 0.0
    for i in range(n - 1):
        cmd = cmds[i] if cmds else Command(0.0, 0.0)
        obs = plant.step(cmd, dt)
        yaw += plant.yaw_rate * dt
        rows.append(row(obs, cmd))
    return as_log(rows), float(np.degrees(yaw))


# 代役の「実物」: バイアスと雑音を公称 (Params()) と違う値にした sim
STAND_IN = Params(gyro_bias=0.006, gyro_noise=0.02, accel_noise=0.03)


def stand_in(still_out: str, turn_out: str, seconds: float = 30.0) -> float:
    """実機の代わりに静止ログと旋回ログを書く。旋回の真のヨー角（度）を返す。"""
    log, _ = simulate(STAND_IN, round(seconds / 0.01) + 1, 0.01)
    write_csv(still_out, np.stack([log[c] for c in log], axis=1))
    cmds = [Command(0.0, 0.0)] * 100 + [Command(-0.3, 0.3)] * 40 + [Command(0.0, 0.0)] * 200
    log, truth = simulate(STAND_IN, len(cmds) + 1, 0.01, seed=2, cmds=cmds)
    write_csv(turn_out, np.stack([log[c] for c in log], axis=1))
    return truth


def report(s: dict) -> None:
    print(f"サンプル {s['n']} 個、{s['T']:.2f} s")
    print(f"サンプル間隔 平均 {s['dt_mean'] * 1e3:.2f} ms  揺れ(std) {s['dt_std'] * 1e3:.2f} ms  最大 {s['dt_max'] * 1e3:.2f} ms")
    for c in AXES:
        unit = "m/s^2" if c[0] == "a" else "rad/s"
        print(f"  {c}: 平均 {s['mean'][c]:+.5f}  標準偏差 {s['std'][c]:.5f} {unit}")
    print(f"加速度のノルム - 9.81 = {s['norm_err']:+.4f} m/s^2")
    print(f"傾き roll {s['roll']:+.2f} 度  pitch {s['pitch']:+.2f} 度")
    print(f"gz の積分（ドリフト）: そのまま {s['drift_raw']:+.3f} 度  バイアスを引いた後 {s['drift_fix']:+.3f} 度")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python -m physlearn.imu")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("still", help="静止ログの特性とドリフト").add_argument("csv")
    t = sub.add_parser("turn", help="手で回したログの gz の積分")
    t.add_argument("csv")
    t.add_argument("--still-seconds", type=float, default=1.0, help="冒頭の静止区間（バイアスを測る）")
    r = sub.add_parser("r2s", help="静止ログから sim の IMU の項を直し、直した sim と比べる")
    r.add_argument("csv")
    r.add_argument("--base", help="元にする Params の JSON（無ければ公称）")
    r.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    log = read_csv(a.csv)

    if a.cmd == "still":
        s = stats(log)
        report(s)
        print("gz の Allan 偏差（τ s: rad/s）:", "  ".join(f"{tau:g}: {d:.5f}" for tau, d in allan(log["gz"], s["dt_mean"])))
    elif a.cmd == "turn":
        bias = float(log["gz"][log["t"] - log["t"][0] < a.still_seconds].mean())
        deg = yaw_deg(log, bias)
        print(f"冒頭 {a.still_seconds:g} s のバイアス {bias:+.5f} rad/s")
        print(f"gz の積分 {deg:+.2f} 度（バイアスを引く前 {yaw_deg(log):+.2f} 度）。左回し（上から見て反時計回り）で正")
        print(f"90 度回したなら尺度 {deg / 90:.3f}、1 回転なら {deg / 360:.3f}")
    else:
        p = fit(log, Params.load(a.base) if a.base else Params())
        p.save(a.out)
        print(f"{a.out}: gyro_bias {p.gyro_bias:+.5f}  gyro_noise {p.gyro_noise:.5f}  accel_noise {p.accel_noise:.5f}")
        real = stats(log)
        sim = stats(simulate(p, real["n"], real["dt_mean"])[0])
        print(f"{'':16}{'実物':>10}{'直した sim':>12}")
        for name, f in [
            ("gz の平均", lambda s: s["mean"]["gz"]),
            ("gz の標準偏差", lambda s: s["std"]["gz"]),
            ("az の標準偏差", lambda s: s["std"]["az"]),
            ("ドリフト 度", lambda s: s["drift_raw"]),
            ("引いた後 度", lambda s: s["drift_fix"]),
        ]:
            print(f"{name:14}{f(real):+12.5f}{f(sim):+12.5f}")


if __name__ == "__main__":
    main()
