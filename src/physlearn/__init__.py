"""physlearn: Sim2Real / Real2Sim を XIAO + IMU の 2 輪で学ぶ。CLI は `physlearn -h`。"""

import argparse

from physlearn.sim import Params, SimPlant, id_experiment

# loop-demo で実機の代役にする「隠しパラメータ」。公称 Params() とわざとずらしてある。
# 3 rad/s に要る duty 3/8 + 0.15 = 0.525 が安全ゲートの上限 0.6 に収まるようにしてある。
# motor_gain 40/3 は yaw_gain 8 rad/s になる値（r・b は Params と同じ 0.030・0.100 m）。
HIDDEN = Params(motor_gain=40 / 3, motor_tau=0.2, deadband=0.15, gyro_bias=0.08, gyro_noise=0.015)
PLANTS = ("sim", "hidden", "mujoco", "hard")


def make_plant(name: str, base: Params = Params(), seed: int = 0):
    """`PLANTS` の名前から Plant を作る。mujoco は IMU に雑音とジャイロのバイアスを足した「実機の代役」、
    hard は HIDDEN に式の外の現象（むだ時間・左右差・電池の低下・IMU の前ずれ）を全部入れたもの（`mismatch.HardPlant`）。"""
    if name == "mujoco":
        try:
            from physlearn.mujoco_plant import MujocoPlant
        except ImportError:
            raise SystemExit("mujoco が入っていない。`uv sync --extra mujoco` で入れる") from None
        return MujocoPlant(noise_acc=0.05, noise_gyro=0.005, bias_gyro=(0.0, 0.0, 0.02), seed=seed)
    if name == "hard":
        from physlearn.mismatch import DEFAULTS, HardPlant

        return HardPlant(seed=seed, **DEFAULTS)
    return SimPlant(HIDDEN if name == "hidden" else base, seed=seed)


def sim_log(plant, dt: float = 0.01) -> list:
    """同定用の開ループ指令列を安全ゲート越しに流し、ログの行を返す。"""
    from physlearn.control import SafetyGate
    from physlearn.log import row

    gate = SafetyGate()
    obs = plant.reset()
    rows = []
    for c in id_experiment(dt):
        cmd = gate(c, obs, dt)
        obs = plant.step(cmd, dt)
        rows.append(row(obs, cmd))
    return rows


def _show(m: dict) -> str:
    return f"整定 {m['settle']:.2f} s  行き過ぎ {m['overshoot'] * 100:.1f} %  定常偏差 {m['ss_error']:.3f} rad/s"


def loop_demo(seed: int = 0, n: int = 50, real: str = "hidden") -> dict:
    """公称の sim でゲインを決める → 代役で試す → 代役のログで同定 → 決め直す → 代役で試す。

    real は代役の Plant（"hidden" = 隠しパラメータの numpy sim、"mujoco" = MuJoCo、"hard" = 式の外の現象つき）。
    """
    from physlearn.control import SPEC, design, metrics, passes, run
    from physlearn.log import as_log
    from physlearn.randomize import tune
    from physlearn.sysid import apply, identify

    real = make_plant(real, seed=seed + 1000)
    print(f"仕様: 0 → 3 rad/s のステップで {SPEC}")
    out = {}
    for step, p in (("前 (公称の sim)", Params()), ("後 (同定した sim)", None)):
        if p is None:
            est = identify(as_log(sim_log(real)))
            print("代役のログから同定:", {k: round(v, 3) for k, v in est.items()})
            p = apply(Params(), est)
        tc, rate = tune(p, n=n, seed=seed)
        m = metrics(*run(real, design(p, tc))[1:])
        print(f"[{step}] tc={tc}  sim での通過率 {rate:.0%}  代役で: {_show(m)}  仕様 {'OK' if passes(m) else 'NG'}")
        out[step] = m
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="physlearn")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("loop-demo", help="代役の実機で R2S → S2R を 1 周回す")
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--real", choices=("hidden", "mujoco", "hard"), default="hidden", help="実機の代役")
    s = sub.add_parser("sim-log", help="sim で同定用の開ループ実験をしてログ CSV を書く")
    s.add_argument("out")
    s.add_argument("--plant", choices=PLANTS, default="sim", help="sim = 公称（か --params）、hidden = loop-demo の代役、hard = 式の外の現象つき")
    s.add_argument("--params", help="--plant sim のパラメータ JSON（無ければ公称値）")
    s.add_argument("--seed", type=int, default=0)
    s = sub.add_parser("sysid", help="ログ CSV（sim でも実機でも）から同定し、パラメータ JSON を書く")
    s.add_argument("csv")
    s.add_argument("--params", help="元にするパラメータ JSON（無ければ公称値）")
    s.add_argument("--out", help="直したパラメータ JSON の書き先")
    s = sub.add_parser("eval", help="ばらつきの下で制御器が仕様を満たす割合")
    s.add_argument("--params", help="パラメータ JSON（無ければ公称値）")
    s.add_argument("--tc", type=float, help="閉ループ時定数。無ければ探索する")
    s.add_argument("-n", type=int, default=100)
    a = ap.parse_args(argv)

    base = Params.load(a.params) if getattr(a, "params", None) else Params()
    if a.cmd == "loop-demo":
        loop_demo(a.seed, real=a.real)
    elif a.cmd == "sim-log":
        from physlearn.log import write_csv

        rows = sim_log(make_plant(a.plant, base, a.seed))
        write_csv(a.out, rows)
        print(f"{a.out}: {len(rows)} 行")
    elif a.cmd == "sysid":
        from physlearn.log import read_csv
        from physlearn.sysid import apply, identify

        est = identify(read_csv(a.csv))
        for k, v in est.items():
            print(f"{k:11s} {v:.4f}")
        if "yaw_gain" not in est:
            print("動いたステップが 2 つ未満なので、ゲイン・時定数・デッドバンドは推定しない（元の値のまま）")
        if a.out:
            apply(base, est).save(a.out)
            print(f"→ {a.out}")
    elif a.cmd == "eval":
        from physlearn.control import design
        from physlearn.randomize import evaluate, tune

        tc = a.tc or tune(base)[0]
        c = design(base, tc)
        print(f"tc={tc}  kp={c.kp:.4f}  ki={c.ki:.4f}  deadband={c.deadband:.3f}  bias={c.bias:.4f}")
        print(f"ばらつき {a.n} 台で仕様を満たした割合: {evaluate(base, tc, a.n):.0%}")

