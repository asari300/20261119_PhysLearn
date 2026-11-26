"""ログ CSV を PNG の図にする（任意の依存 `viz` が要る: `uv sync --extra viz`）。

    python -m physlearn.plot log <csv> --out x.png [--params p.json]
    python -m physlearn.plot compare <csv_a> <csv_b> --out x.png
    python -m physlearn.plot still <csv> --out x.png
教材の図は `figures(outdir)` で作り直す（doc/textbook/fig/README.md）。
"""

import argparse
import sys
from pathlib import Path

try:
    import matplotlib

    matplotlib.use("Agg")  # 画面の無い環境でも PNG に書けるように
    import matplotlib.pyplot as plt
except ImportError:
    sys.exit("matplotlib が無い。`uv sync --extra viz` で入れる")

from physlearn.compare import model_gz
from physlearn.log import read_csv
from physlearn.sim import Params

C = ["tab:blue", "tab:orange", "tab:green"]


def turn(log: dict):
    return (log["right"] - log["left"]) / 2


def plot_log(log: dict, out, params: Params | None = None, label="log", title=None):
    fig, (a, b) = plt.subplots(2, 1, sharex=True, figsize=(7, 4.5), height_ratios=[1, 2])
    a.plot(log["t"], turn(log), color=C[0])
    a.set_ylabel("turn cmd (R-L)/2 [duty]")
    b.plot(log["t"], log["gz"], color=C[0], lw=0.8, label=label)
    if params is not None:
        b.plot(log["t"], model_gz(log, params), color=C[1], lw=1.5, ls="--", label="model")
        b.legend()
    b.set(xlabel="time [s]", ylabel="gz [rad/s]")
    _save(fig, out, title)


def plot_compare(logs: dict, out, title=None):
    fig, ax = plt.subplots(figsize=(7, 3.5))
    for c, (name, log) in zip(C, logs.items()):
        ax.plot(log["t"], log["gz"], color=c, lw=0.8, label=name)
    ax.set(xlabel="time [s]", ylabel="gz [rad/s]")
    ax.legend()
    _save(fig, out, title)


def plot_still(log: dict, out, title=None):
    gz = log["gz"]
    m, s = gz.mean(), gz.std(ddof=1)
    fig, (a, b) = plt.subplots(1, 2, figsize=(8, 3.2), width_ratios=[2, 1])
    a.plot(log["t"], gz, color=C[0], lw=0.6)
    a.axhline(m, color=C[1], label=f"bias {m:.4f} rad/s")
    a.set(xlabel="time [s]", ylabel="gz [rad/s]")
    a.legend()
    b.hist(gz, bins=40, color=C[0])
    b.axvline(m, color=C[1])
    b.set(xlabel="gz [rad/s]", ylabel="count", title=f"mean {m:.4f}, std {s:.4f}")
    _save(fig, out, title)


def plot_steps(runs: dict, target: float, out, title=None):
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.axhline(target, color="gray", ls="--", lw=1, label="target")
    for c, (name, (t, y)) in zip(C, runs.items()):
        ax.plot(t, y, color=c, label=name)
    ax.set(xlabel="time [s]", ylabel="yaw rate [rad/s]")
    ax.legend()
    _save(fig, out, title)


def _save(fig, out, title):
    if title:
        fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(out, dpi=90)
    plt.close(fig)


def figures(outdir, seed: int = 0) -> None:
    """教材の図を作る。中身は公開された関数を呼ぶだけなので、sim や同定が変わっても作り直せばよい。"""
    from physlearn import HIDDEN, sim_log
    from physlearn.api import Command
    from physlearn.control import TARGET, design, run
    from physlearn.log import as_log
    from physlearn.randomize import tune
    from physlearn.sim import SimPlant
    from physlearn.sysid import apply, identify

    d = Path(outdir)
    d.mkdir(parents=True, exist_ok=True)
    nom = as_log(sim_log(SimPlant(Params(), seed=seed)))
    real = SimPlant(HIDDEN, seed=seed + 1000)  # loop_demo と同じ代役
    hid = as_log(sim_log(real))
    fixed = apply(Params(), identify(hid))
    plot_log(nom, d / "01-sim-nominal.png", title="Nominal sim: identification experiment")
    plot_log(hid, d / "02-stand-in-vs-nominal.png", Params(), "stand-in", "Stand-in log vs nominal model")
    plot_log(hid, d / "03-stand-in-vs-identified.png", fixed, "stand-in", "Stand-in log vs identified model")
    runs = {}
    for name, p in (("before (nominal gains)", Params()), ("after (re-identified gains)", fixed)):
        tc = tune(p, seed=seed)[0]
        runs[name] = run(real, design(p, tc))[1:]
    plot_steps(runs, TARGET, d / "04-step-before-after.png", "Closed loop on stand-in")
    real.reset()
    still = as_log([[*vars(real.step(Command(0, 0), 0.01)).values(), 0, 0] for _ in range(500)])
    plot_still(still, d / "05-still.png", "Stand-in at rest (5 s)")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python -m physlearn.plot")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("log", help="指令の旋回成分と gz。--params でモデルを重ねる")
    s.add_argument("csv")
    s.add_argument("--params", help="重ねるモデルのパラメータ JSON")
    s = sub.add_parser("compare", help="2 本のログの gz を重ねる")
    s.add_argument("csv", nargs=2)
    s = sub.add_parser("still", help="静止ログの gz の時系列とヒストグラム")
    s.add_argument("csv")
    for s in sub.choices.values():
        s.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "log":
        plot_log(read_csv(a.csv), a.out, Params.load(a.params) if a.params else None, title=Path(a.csv).name)
    elif a.cmd == "compare":
        plot_compare({c: read_csv(c) for c in a.csv}, a.out)
    else:
        plot_still(read_csv(a.csv), a.out, title=Path(a.csv).name)
    print(f"→ {a.out}")


if __name__ == "__main__":
    main()
