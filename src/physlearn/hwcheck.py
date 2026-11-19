"""実機をつないだ直後の診断。モーターは回さない（送るのは停止 `S` だけ）。

    uv run python -m physlearn.hwcheck stream --port /dev/ttyACM0 [--seconds 5]
    uv run python -m physlearn.hwcheck axes   --port /dev/ttyACM0 [--no-prompt] [--seconds 2]

stream: サンプル周期・欠け・`#` 行・加速度のノルム・ジャイロの平均と標準偏差・飽和を、基準つきで出す。
axes: 静止した加速度計は重力の反作用で「上」を指す。車体を 水平 / 前を上 / 左を上 に置くと、
  機体の z / x / y が上になる。各姿勢の平均の加速度（基板座標）を b_z, b_x, b_y とすると、
  機体 = R @ 基板 の R の行は b_x, b_y, b_z（を |b| で割ったもの）。各行を最大成分の軸に丸めて
  `--axes` の文字列にする。3 つで右手系にならなければ姿勢の取り違え。gz の符号は右手系なら合う
  （動かして確かめるのは doc/bringup.md 段 5 の `link jog`）。

SerialPlant は生の行・`#` 行・MCU の時刻を外に出さないので、ここでは pyserial で直接読み、
`link.decode_sample` で解釈する。
"""

import argparse
import time

import numpy as np
import serial

from physlearn.link import BAUD, G, STOP, decode_sample, parse_axes

PERIOD_MS = 10  # スケッチの PERIOD_US = 10000
GYRO_FS = 20.0  # rad/s。ジャイロ ±1000 dps の int16 満スケール（doc/protocol.md）
ACC_FS = 16 * G  # スケッチの accelRange = 16
POSES = [("水平に置く", "z"), ("前を真上に向けて立てる", "x"), ("左を真上に向けて立てる", "y")]


def read(ser, seconds):
    """seconds 秒読む。返り値: (列 [t_ms, 壁時計 s, ax ay az gx gy gz] の配列, `#` 行, 壊れた行の数)。"""
    ser.reset_input_buffer()
    ser.readline()  # 途中から始まる最初の行を捨てる
    rows, notes, bad, end = [], [], 0, time.monotonic() + seconds
    while time.monotonic() < end:
        line = ser.readline()
        if not line:
            continue
        if line.startswith(b"#"):
            notes.append(line.decode("ascii", "replace").strip())
            continue
        s = decode_sample(line) if line.endswith(b"\n") else None
        if s is None:
            bad += 1
        else:
            rows.append((round(s.t * 1000), time.monotonic(), s.ax, s.ay, s.az, s.gx, s.gy, s.gz))
    return np.array(rows).reshape(-1, 8), notes, bad


def stream_checks(d, notes, bad):
    """(項目, 値, 合否, 基準, 基準の出どころ) の並び。しきい値の「目安」は根拠なし。"""
    t, w, a, g = d[:, 0], d[:, 1], d[:, 2:5], d[:, 5:8]
    dt, dw = np.diff(t), np.diff(w) * 1e3
    miss = int(np.maximum(np.round(dt / PERIOD_MS) - 1, 0).sum())  # 間隔が 2 周期なら 1 個欠け
    norm = np.linalg.norm(a, axis=1).mean()
    gm, gs = g.mean(0), g.std(0)
    err = [n for n in notes if n.startswith("# ERR")]
    sat = int(((np.abs(g) >= 0.98 * GYRO_FS).any(1) | (np.abs(a) >= 0.98 * ACC_FS).any(1)).sum())
    return [
        ("MCU 周期 平均", f"{dt.mean():.2f} ms", abs(dt.mean() - PERIOD_MS) <= 0.5, "10±0.5 ms", "スケッチ"),
        ("MCU 周期 最大", f"{dt.max():.0f} ms", dt.max() <= 1.5 * PERIOD_MS, "≤ 15 ms", "目安"),
        ("欠けたサンプル", f"{miss} 個", miss == 0, "0", "スケッチ"),
        ("壊れた行", f"{bad} 行", bad == 0, "0", "スケッチ"),
        ("PC 壁時計 周期 平均", f"{dw.mean():.2f} ms", abs(dw.mean() - PERIOD_MS) <= 0.5, "10±0.5 ms", "スケッチ"),
        ("PC 壁時計 周期 最大", f"{dw.max():.0f} ms", dw.max() <= 50, "≤ 50 ms", "目安"),
        ("# ERR の行", f"{len(err)} 行" + "".join(f"  [{e}]" for e in sorted(set(err))[:3]), not err, "0", "スケッチ"),
        ("加速度ノルム - 9.81", f"{norm - G:+.3f} m/s^2", abs(norm - G) <= 0.5, "±0.5", "目安"),
        # 0.02 は randomize.SPREAD["gyro_bias"]（gz の値。gx・gy にも同じ幅を当てる）
        ("ジャイロ平均 gx gy gz", " ".join(f"{x:+.4f}" for x in gm) + " rad/s", bool(np.abs(gm).max() <= 0.02), "|平均| ≤ 0.02", "SPREAD"),
        ("ジャイロ標準偏差", " ".join(f"{x:.4f}" for x in gs) + " rad/s", bool(gs.max() <= 0.05), "≤ 0.05（sim 公称 0.01 の 5 倍）", "目安"),
        ("飽和の疑い", f"{sat} 個", sat == 0, "0（端の 98% 以上）", "スケッチ"),
    ]


def gravity_axis(a):
    """1 つの静止姿勢の加速度（N x 3、基板座標）→ (重力が出た軸 0..2, 符号)。ダメなら ValueError（やり直し）。"""
    if len(a) < 10:
        raise ValueError("サンプルがほとんど来ない")
    m, n = a.mean(0), np.linalg.norm(a, axis=1)
    # ノルムの 1.0 と揺れ 0.3 は、手で持って静止したときの目安（根拠なし）
    if abs(n.mean() - G) > 1.0 or n.std() > 0.3:
        raise ValueError(f"動いている（ノルム {n.mean():.2f}±{n.std():.2f} m/s^2）。置き直して")
    i = int(np.argmax(np.abs(m)))
    # 45° で 2 軸が同じ大きさになり決められない。余裕をみて 0.9（傾き約 26° まで）。目安（根拠なし）
    if abs(m[i]) < 0.9 * np.linalg.norm(m):
        raise ValueError(f"傾いている（重力が 1 つの軸に乗り切っていない: {np.round(m, 2)}）。真上に向け直して")
    return i, 1 if m[i] > 0 else -1


def solve(poses):
    """[(軸, 符号)] を 水平・前上・左上 の順に渡す → `--axes` に渡せる "x,y,z" 形式の文字列。"""
    (iz, sz), (ix, sx), (iy, sy) = poses
    if len({iz, ix, iy}) < 3:
        raise ValueError("2 つ以上の姿勢で重力が基板の同じ軸に出た。姿勢を取り違えたか、動かしていない")
    spec = ",".join(("-" if s < 0 else "") + "xyz"[i] for i, s in ((ix, sx), (iy, sy), (iz, sz)))
    try:
        parse_axes(spec)
    except ValueError:
        raise ValueError(f"{spec} は鏡像（右手系にならない）。前上と左上を取り違えたか、裏返しに置いた") from None
    return spec


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m physlearn.hwcheck", description="実機の診断（モーターは回さない）")
    p.add_argument("mode", choices=["stream", "axes"])
    p.add_argument("--port", required=True)
    p.add_argument("--seconds", type=float, help="stream は全体で 5、axes は姿勢ごとに 2")
    p.add_argument("--no-prompt", action="store_true", help="axes: Enter を待たず、--settle 秒で姿勢を取らせる")
    p.add_argument("--settle", type=float, default=3.0, help="axes --no-prompt: 合図から測り始めるまでの秒数")
    a = p.parse_args(argv)
    secs = a.seconds if a.seconds is not None else {"stream": 5.0, "axes": 2.0}[a.mode]
    if not 0 < secs <= 600:
        p.error("--seconds は 0〜600")
    with serial.Serial(a.port, BAUD, timeout=0.05) as ser:
        ser.write(STOP)  # 念のため。この道具はこれ以外を送らない
        if a.mode == "stream":
            d, notes, bad = read(ser, secs)
            if len(d) < 10:
                print(f"NG  サンプルが {len(d)} 個しか来ない（{secs} 秒）。ポート・ファーム・IMU を確かめて")
                return 1
            checks = stream_checks(d, notes, bad)
            print(f"サンプル {len(d)} 個 / {secs} 秒、`#` 行 {len(notes)} 本、壊れた行 {bad} 本")
            for name, val, ok, thr, src in checks:
                print(f"{'OK' if ok else 'NG'}  {name}: {val}   基準 {thr}【{src}】")
            return 0 if all(c[2] for c in checks) else 1
        poses = []
        for k, (name, up) in enumerate(POSES, 1):
            while True:
                print(f"姿勢 {k}/3: 車体を{name}（機体 {up} が上）。{secs:g} 秒じっと動かさない", flush=True)
                input("  置いたら Enter > ") if not a.no_prompt else time.sleep(a.settle)
                try:
                    poses.append(gravity_axis(read(ser, secs)[0][:, 2:5]))
                    print(f"  重力は基板の {'+-'[poses[-1][1] < 0]}{'xyz'[poses[-1][0]]} に出た")
                    break
                except ValueError as e:
                    print(f"  やり直し: {e}")
                    if a.no_prompt:
                        return 1
        try:
            spec = solve(poses)
        except ValueError as e:
            print(f"NG  {e}")
            return 1
        print(f"OK  --axes {spec}\n以後の link コマンドすべてに同じ --axes を付ける")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
