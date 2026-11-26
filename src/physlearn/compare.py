"""同定した sim が実機（のログ）をどれだけ再現できているかを測る。

    python -m physlearn.compare fit LOG.csv PARAMS.json   # ログと同じ指令を sim に流し、gz の残差を見る
    python -m physlearn.compare holdout LOG.csv           # 正の向きで同定し、負の向きで確かめる
    python -m physlearn.compare spread A.json B.csv ...   # 複数回の同定の幅（下, 上）を randomize.SPREAD と並べる
"""

import sys
from dataclasses import replace

import numpy as np

from physlearn.log import read_csv
from physlearn.randomize import SPREAD
from physlearn.sim import Params
from physlearn.sysid import NO_STILL, apply, first_order, identify, segments

# 雑音だけなら残差 RMSE / 雑音 は 1 前後。2 倍を超えたら雑音では説明できない分がある
LIMIT = 2.0
NO_MOVE = "動かした区間が無い（静止だけのログ？）。`link id` か `sim-log` のログを渡す"


def model_gz(log: dict, p: Params) -> np.ndarray:
    """ログと同じ指令を雑音なしのモデルに流したときの gz。"""
    u = (log["right"] - log["left"]) / 2
    return p.gyro_bias + first_order(u, log["t"], p.yaw_gain(), p.deadband, np.array([p.motor_tau]))[:, 0]


def fit(log: dict, p: Params) -> dict:
    u = (log["right"] - log["left"]) / 2
    segs = segments(u)
    if not segs:
        raise ValueError(NO_STILL)
    if len(segs) < 2:
        raise ValueError(NO_MOVE)
    r = log["gz"] - model_gz(log, p)
    i0, j0 = segs[0]
    noise = float(log["gz"][i0 + (j0 - i0) // 2 : j0].std(ddof=1))  # sysid.identify と同じ静止区間の後半
    if not noise > 0:  # 比 RMSE / 雑音 が inf・NaN になり、判定が意味を失う
        raise ValueError("静止区間の雑音が 0（雑音なしの sim のログ？）。残差を雑音と比べられない")
    rise, steady, rows = [], [], []
    for i, j in segs[1:]:
        k = i + int(0.3 * (j - i))  # 前 30% を立ち上がり（立ち下がり）、後ろ 30% を定常とみなす（sysid と同じ）
        s = i + int(0.7 * (j - i))
        rise.append(r[i:k])
        steady.append(r[s:j])
        rows.append((u[j - 1], _rms(r[i:k]), float(r[s:j].mean())))
    out = {
        "noise": noise,
        "all": _rms(r),
        "rise": _rms(np.concatenate(rise)),
        "steady": _rms(np.concatenate(steady)),
        # 残差が指令やその変化と相関していれば、雑音ではなくモデルの式が足りない
        "corr_u": float(np.corrcoef(r, u)[0, 1]),
        "corr_du": float(np.corrcoef(r, np.gradient(u))[0, 1]),
        "segments": rows,
    }
    out["unexplained"] = float(np.sqrt(max(0.0, out["all"] ** 2 - noise**2)))
    # 定常の窓（後ろ 30%）は tau が大きいと遅れも拾う。そこで「ゲインだけ / tau だけ を少し変えた sim との差」で
    # 残差を説明してみて、どちらがよく説明するかで分ける（線形化した感度への射影）
    m0 = model_gz(log, p)
    for key, q in (("gain", p.with_yaw_gain(1.1 * p.yaw_gain())), ("tau", replace(p, motor_tau=1.1 * p.motor_tau))):
        d = model_gz(log, q) - m0
        c = float(d @ r / (d @ d))
        out[key] = (1 + 0.1 * c, 1 - np.sum((r - c * d) ** 2) / np.sum(r**2))  # (直すべき倍率, 説明できる割合)
    out["verdict"] = verdict(out)
    return out


def _rms(x) -> float:
    return float(np.sqrt(np.mean(np.square(x))))


def verdict(f: dict) -> str:
    if f["all"] <= LIMIT * f["noise"]:
        return "雑音の範囲で合っている"
    (_, eg), (_, et) = f["gain"], f["tau"]
    if max(eg, et) < 0.5:  # どちらで直しても残差の半分も消えない
        return "ゲインでも時定数でも説明できない → 式の形が違う（遅延・左右差・非線形など）"
    return "ゲイン（かデッドバンド）がずれている" if eg > et else "時定数（か遅延）がずれている"


def show(f: dict) -> None:
    n = f["noise"]
    print(f"雑音（静止の標準偏差） {n:.4f} rad/s")
    for key, name in (("all", "全体"), ("rise", "立ち上がり"), ("steady", "定常")):
        print(f"RMSE {name:6s} {f[key]:.4f} rad/s  （雑音の {f[key] / n:.1f} 倍）")
    print(f"モデルで説明できていない分 {f['unexplained']:.4f} rad/s")
    print(f"残差と指令の相関 {f['corr_u']:+.2f}  指令の変化との相関 {f['corr_du']:+.2f}")
    for key, name in (("gain", "ゲイン"), ("tau", "時定数")):
        print(f"{name}だけを {f[key][0]:.2f} 倍にすると、残差の {f[key][1]:.0%} を説明できる（線形近似）")
    print("区間ごと  指令 u   立ち上がり RMSE   定常の差（実 - sim）")
    for u, rr, ss in f["segments"]:
        print(f"          {u:+.2f}   {rr:.4f}           {ss:+.4f}")
    print("判定:", f["verdict"])


def split(log: dict) -> tuple[dict, dict]:
    """最初の静止 + 正の向きのステップ（とその後の 0）/ 同じ静止 + 負の向き、の 2 本に分ける。"""
    u = (log["right"] - log["left"]) / 2
    segs = segments(u)
    if not segs:
        raise ValueError(NO_STILL)
    pos, neg, sign = [segs[0]], [segs[0]], 0.0
    for i, j in segs[1:]:
        sign = np.sign(u[j - 1]) or sign  # 0 の区間は直前のステップの側に付ける
        (pos if sign > 0 else neg).append((i, j))

    def take(ss):
        idx = np.concatenate([np.arange(i, j) for i, j in ss])
        d = {c: v[idx] for c, v in log.items()}
        d["t"] = log["t"][0] + np.arange(len(idx)) * np.median(np.diff(log["t"]))  # 継ぎ目で時刻を飛ばさない
        return d

    return take(pos), take(neg)


def holdout(log: dict) -> tuple[dict, dict]:
    """正の向きだけで同定し、(同定に使ったデータでの当てはまり, 使っていないデータでの当てはまり)。"""
    train, test = split(log)
    p = apply(Params(), identify(train))
    return fit(train, p), fit(test, p)


def load(path: str) -> Params:
    return apply(Params(), identify(read_csv(path))) if path.endswith(".csv") else Params.load(path)


def spread(ps: list[Params]) -> dict:
    """SPREAD の各キーについて、実測の幅。

    motor_gain・motor_tau は平均に対する比の (下, 上)（lo ≤ 0 ≤ hi）。deadband・gyro_bias は ± の半幅（足す量）。
    ratio は SPREAD に対する割合で、1 を超えたら SPREAD の外（下か上のどちらかがはみ出した）。
    """
    out = {}
    for k, s in SPREAD.items():
        v = np.array([getattr(p, k) for p in ps])
        mean = float(v.mean())
        if isinstance(s, tuple):
            lo, hi = float(v.min() / mean - 1), float(v.max() / mean - 1)
            ratio = max(lo / s[0], hi / s[1])
        else:
            lo, hi = -float(v.max() - v.min()) / 2, float(v.max() - v.min()) / 2
            ratio = hi / s
        out[k] = {"mean": mean, "lo": lo, "hi": hi, "half": (hi - lo) / 2, "spread": s, "ratio": float(ratio)}
    return out


def _range(lo, hi, spec=False) -> str:
    return f"({lo:+.3f}, {hi:+.3f})" if spec else f"{lo:+.3f}/{hi:+.3f}"


def main(argv=None) -> None:
    a = sys.argv[1:] if argv is None else argv
    if len(a) == 3 and a[0] == "fit":
        show(fit(read_csv(a[1]), Params.load(a[2])))
    elif len(a) == 2 and a[0] == "holdout":
        tr, te = holdout(read_csv(a[1]))
        for name, f in (("同定に使った（正の向き）", tr), ("使っていない（負の向き）", te)):
            print(f"== {name}")
            show(f)
    elif len(a) >= 3 and a[0] == "spread":
        print(f"{len(a) - 1} 回の同定から。gain・tau は平均に対する比の (下, 上)、deadband・bias は足す量の ± の半幅")
        print("キー         平均      実測 (下, 上)           SPREAD                  比")
        sp = spread([load(x) for x in a[1:]])
        for k, d in sp.items():
            tup = isinstance(d["spread"], tuple)
            real = _range(d["lo"], d["hi"], True) if tup else f"±{d['half']:.4f}"
            want = _range(*d["spread"], True) if tup else f"±{d['spread']:.3f}"
            mark = "  ← SPREAD の外" if d["ratio"] > 1 else ""
            print(f"{k:11s} {d['mean']:8.4f}  {real:22s}  {want:22s}  {d['ratio']:.0%}{mark}")
        print("提案: 回数が少ないと幅を小さく見積もるので、実測の幅の 1.5 倍を SPREAD の候補にする（書き換えはしない）")
        print("  ", {k: (round(1.5 * d["lo"], 3), round(1.5 * d["hi"], 3)) if isinstance(d["spread"], tuple) else round(1.5 * d["half"], 3) for k, d in sp.items()})
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
