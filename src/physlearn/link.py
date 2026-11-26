"""実機 (XIAO + IMU + 2 輪) とのシリアル接続。取り決めは doc/protocol.md。

    uv run python -m physlearn.link still --port /dev/ttyACM0 --seconds 10 --out still.csv
    uv run python -m physlearn.link id    --port /dev/ttyACM0 --out id.csv
    uv run python -m physlearn.link jog   --port /dev/ttyACM0 --left 0.3        # 車輪を浮かせて
    uv run python -m physlearn.link run   --port /dev/ttyACM0 --params p.json --out run.csv
"""

import argparse
import csv
import sys
import time
from dataclasses import replace

import numpy as np
import serial

from physlearn import sim_log
from physlearn.api import LOG_COLUMNS, Command, Obs
from physlearn.log import write_csv

BAUD = 115200
STOP = b"S\n"
G = 9.80665
SETTLE_N, SETTLE_GZ, SETTLE_S = 20, 0.05, 2.0  # reset が回転の止まるのを待つ: 直近 20 サンプルが平均から 0.05 rad/s 以内、最大 2 s
DUTY_MAX = 0.6  # スケッチの DUTY_MAX と同じ（tests/test_link.py が照合）。ログに MCU が実際に出す値を残すため


def limit(cmd: Command) -> Command:
    """MCU と同じく |duty| を DUTY_MAX で切る。有限でなければ ValueError。"""
    left, right = float(cmd.left), float(cmd.right)
    # NaN は min/max を素通りして -1（全速逆転）になるので、送らずに止める
    if not (np.isfinite(left) and np.isfinite(right)):
        raise ValueError(f"有限でない指令 {cmd}")
    return Command(*(min(DUTY_MAX, max(-DUTY_MAX, v)) for v in (left, right)))


def encode_command(cmd: Command) -> bytes:
    """指令 1 行（`limit` を通した値）。"""
    c = limit(cmd)
    return f"M {c.left:.3f} {c.right:.3f}\n".encode()


def decode_sample(line: bytes | str) -> Obs | None:
    """`I <t_ms> ax ay az gx gy gz` を基板座標の Obs に。サンプル以外・壊れた行は None。"""
    if isinstance(line, bytes):
        line = line.decode("ascii", "replace")
    parts = line.split()
    if len(parts) != 8 or parts[0] != "I":
        return None
    try:
        t_ms = int(parts[1])
        v = [float(p) for p in parts[2:]]
    except ValueError:
        return None
    if t_ms < 0 or not all(np.isfinite(v)):
        return None
    return Obs(t_ms / 1000, *v)


def parse_axes(spec: str) -> np.ndarray:
    """"x,y,z" 形式（機体の x,y,z がそれぞれ基板のどの軸か、符号つき）→ 3x3 行列。

    例: 基板を Z 軸まわりに 90° 回して付けたら "-y,x,z"（機体 x = 基板 -y）。
    """
    m = np.zeros((3, 3))
    toks = spec.replace(" ", "").split(",")
    bad = [t for t in toks if t.lstrip("+-") not in ("x", "y", "z")]
    if len(toks) != 3 or bad:
        raise ValueError(f"axes {spec!r} は読めない。x・y・z を 3 つ、符号つきでよい、コンマ区切りで（例 x,y,z / -y,x,z）" + (f"。{bad[0]!r} は軸の名前でない" if bad else ""))
    for row, tok in enumerate(toks):
        sign = -1.0 if tok.startswith("-") else 1.0
        m[row, "xyz".index(tok.lstrip("+-"))] = sign
    # 鏡映は角速度（擬ベクトル）の符号を壊すので、回転だけを許す
    if round(np.linalg.det(m)) != 1:
        raise ValueError(f"axes {spec!r} は回転になっていない（各軸 1 回・右手系に）")
    return m


PORT_HINT = "`ls /dev/ttyACM*` で名前を確かめる。WSL2 なら doc/setup.md の usbipd の節（USB を WSL2 に渡す）、権限なら dialout グループ"


def open_port(parser, port: str, **kw):
    """ポートを開く。開けなければ原因の案内つきで parser.error（終了コード 2）。"""
    try:
        return serial.Serial(port, BAUD, **kw)
    except serial.SerialException as e:
        parser.error(f"ポート {port} が開けない（{e}）。{PORT_HINT}")


def axes_with_equals(argv):
    """`--axes -y,x,z`（負号始まりの値）を `--axes=-y,x,z` にする。argparse は前者を別のオプションと読んで拒む。"""
    out = []
    for t in sys.argv[1:] if argv is None else argv:
        if out and out[-1] == "--axes" and not t.startswith("--"):
            out[-1] = f"--axes={t}"
        else:
            out.append(t)
    return out


class SerialPlant:
    """`Plant` の実機版。with で使うと、終了時・例外時に必ず停止を送る。"""

    def __init__(self, port: str = "", axes: str = "x,y,z", timeout: float = 1.0, ser=None, settle: bool = True):
        self.ser = ser if ser is not None else serial.Serial(port, BAUD, timeout=0.05)  # 開けないときの案内は main の open_port
        self.rot = parse_axes(axes)
        self.timeout = timeout
        self.settle = settle  # False なら reset は最初のサンプルで t0 を決める（サンプルを固定した試験用）
        self.t0 = 0.0  # reset 時の MCU 時刻 [s]
        self.t_target = 0.0  # 次に待つ時刻（reset からの秒）。dt を積んで時刻のずれを溜めない
        self.last_cmd = STOP
        self.sent_at = 0.0
        self.last_mcu_t = -np.inf  # 前のサンプルの MCU 時刻 [s]。戻ったら止める

    def _send(self, line: bytes) -> None:
        self.ser.write(line)
        self.last_cmd = line
        self.sent_at = time.monotonic()

    def _next(self) -> Obs:
        """次のサンプル（機体座標・reset からの時刻）。timeout 秒来なければ例外。"""
        deadline = time.monotonic() + self.timeout
        err = ""  # MCU が "# ERR ..." で原因を言っていれば、時間切れの文に添える
        while time.monotonic() < deadline:
            # MCU のウォッチドッグ (200 ms) より短い間隔で同じ指令を送り直す
            if time.monotonic() - self.sent_at > 0.05:
                self._send(self.last_cmd)
            line = self.ser.readline()
            # timeout で途中まで読んだ行は最後の数が切れていても数として読めてしまう
            s = decode_sample(line) if line.endswith(b"\n") else None
            if line.startswith(b"# ERR"):
                err = "（MCU の最後の報告: " + line.decode("ascii", "replace").strip() + "）"
            if s is not None:
                # MCU の再起動・millis の桁あふれで時刻が戻ると、step が t_target に届かず走り続ける
                if s.t < self.last_mcu_t:
                    raise RuntimeError(f"MCU の時刻が戻った ({self.last_mcu_t} -> {s.t} s)")
                self.last_mcu_t = s.t
                a = self.rot @ (s.ax, s.ay, s.az)
                g = self.rot @ (s.gx, s.gy, s.gz)
                return Obs(s.t - self.t0, *a, *g)
        raise TimeoutError(f"{self.timeout} 秒間 IMU のサンプルが来ない{err}")

    def _wait_still(self) -> Obs:
        """停止を送ったあと、回転が止まる（直近 SETTLE_N サンプルの gz が平均から SETTLE_GZ 以内）まで読み、最後のサンプルを返す。

        前の回の回転が残ったまま次の回を始めないため。gz の絶対値でなく平均からの幅で見るのは、
        ジャイロのバイアスが 0.05 を超える個体（偽の XIAO の HIDDEN は 0.08）でも止まったと判定できるように。
        SETTLE_S を超えたら警告の行を標準エラーに出して、そのまま続ける。
        """
        win, start = [], None
        while True:
            s = self._next()
            start = s.t if start is None else start
            win = (win + [s.gz])[-SETTLE_N:]
            if len(win) == SETTLE_N and np.abs(np.array(win) - np.mean(win)).max() < SETTLE_GZ:
                return s
            if s.t - start > SETTLE_S:
                print(f"# 停止を送って {SETTLE_S:g} s 待っても gz が落ち着かない。そのまま始める", file=sys.stderr)
                return s

    def reset(self) -> Obs:
        try:
            self._send(STOP)
            self.ser.reset_input_buffer()
            self.t0 = 0.0
            self.last_mcu_t = -np.inf
            first = self._wait_still() if self.settle else self._next()
            self.t0 = first.t
            self.t_target = 0.0
            return replace(first, t=0.0)
        except BaseException:
            self.stop()
            raise

    def step(self, cmd: Command, dt: float) -> Obs:
        try:
            self._send(encode_command(cmd))
            self.t_target += dt
            obs = self._next()
            while obs.t < self.t_target - 1e-4:
                obs = self._next()
            return obs
        except BaseException:
            self.stop()
            raise

    def stop(self) -> None:
        self._send(STOP)
        self.ser.flush()

    def close(self) -> None:
        try:
            self.stop()
        finally:
            self.ser.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def record(plant: SerialPlant, schedule, dt: float, out: str) -> None:
    """schedule: (秒数, Command) の並び。1 step = 1 行の CSV に書く。"""
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(LOG_COLUMNS)
        plant.reset()
        for seconds, cmd in schedule:
            for _ in range(round(seconds / dt)):
                o = plant.step(cmd, dt)
                sent = limit(cmd)  # 頼んだ値ではなく MCU が出す値を残す
                w.writerow([f"{getattr(o, k):.6g}" for k in LOG_COLUMNS[:7]] + [sent.left, sent.right])


TARGET_MAX = 5.0  # rad/s。SafetyGate の gz_limit 15 より十分小さく
RUN_MAX_S = 3.0
JOG_MAX_S = 1.0
REST_S = 1.0  # 回の間に止めて待つ秒数。モーターの時定数 0.08〜0.2 s の 5 倍以上


def jog(plant: SerialPlant, cmd: Command, seconds: float, dt: float = 0.01) -> float:
    """cmd を seconds だけ（ゲート越しに）出して止める。後半の gz の平均を返す（立ち上がりを除く）。"""
    from physlearn.control import SafetyGate

    gate, obs, gz = SafetyGate(), plant.reset(), []
    for _ in range(round(seconds / dt)):
        obs = plant.step(gate(cmd, obs, dt), dt)
        gz.append(obs.gz)
    plant.stop()
    return float(np.mean(gz[len(gz) // 2 :]))


def jog_hint(left: float, right: float) -> str:
    """jog の結果の見方。右だけ正の文は従来のまま、左だけ・両方のときは指定に合わせる。"""
    if left == 0 and right > 0:
        return "右だけ正 → gz 正（左回り）が正しい向き"
    if right == 0 and left > 0:
        return "左だけ正 → gz 負（右回り）が正しい向き"
    if right == left:
        return "左右が同じ duty なら旋回しない（gz はバイアスだけ）"
    return f"右 - 左 が{'正' if right > left else '負'} → gz {'正（左回り）' if right > left else '負（右回り）'}が正しい向き"


def run_loop(plant: SerialPlant, ctrl_factory, target: float, seconds: float, dt: float = 0.01):
    """+target → -target の 2 回、control.run で回す（正味の回転を 0 に近づけ、ケーブルをねじらない）。

    返り値: (ログの行, [(符号, metrics), ...], 作動の理由)。評価は gz からバイアスを引いたもの（実機には真値が無い）。
    安全ゲートが作動したら、そこで止めて（次の回に進まず）理由を返す。作動しなければ理由は ""。例外は投げないので、集めた行は呼び出し側が書ける。
    """
    from physlearn.control import SafetyGate, metrics, run

    rows, res = [], []
    for sign in (1, -1):
        ctrl, gate = ctrl_factory(), SafetyGate()
        r, t, y = run(plant, ctrl, sign * target, seconds, dt, gate=gate)
        plant.stop()
        # run は reset から測り始める。回ったままだと次の回の初期値になるので、止まるまで待つ
        for _ in range(round(REST_S / dt)):
            plant.step(Command(0.0, 0.0), dt)
        rows += r
        if gate.tripped:
            return rows, res, gate.tripped
        res.append((sign, metrics(t, sign * (y - ctrl.bias), target)))
    return rows, res, ""


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="python -m physlearn.link", description=__doc__.splitlines()[0])
    p.add_argument(
        "mode",
        choices=["still", "id", "jog", "run"],
        help="still: IMU だけ記録 / id: 同定用の左右交互の旋回 / jog: 車輪を少し回して gz を見る / run: PI の閉ループ",
    )
    p.add_argument("--port", required=True, help="例 /dev/ttyACM0")
    p.add_argument("--out", help="出力 CSV（still・id では必須）")
    p.add_argument("--axes", default="x,y,z", help="機体 x,y,z に当たる基板の軸（符号つき）")
    p.add_argument("--dt", type=float, default=0.01)
    p.add_argument("--seconds", type=float, help=f"長さ。still 10 / jog 0.5（上限 {JOG_MAX_S}）/ run 1 回ぶん 2.0（上限 {RUN_MAX_S}）")
    p.add_argument("--left", type=float, default=0.0, help="jog の左 duty")
    p.add_argument("--right", type=float, default=0.0, help="jog の右 duty")
    p.add_argument("--params", help="run: ゲインを決めるパラメータ JSON（physlearn sysid --out。無ければ公称値）")
    p.add_argument("--tc", type=float, help="run: 閉ループ時定数を手で与える（無ければ randomize.tune で探す）")
    p.add_argument("--target", type=float, help=f"run: 目標のヨー角速度 [rad/s]（既定 control.TARGET、上限 {TARGET_MAX}）")
    a = p.parse_args(axes_with_equals(argv))
    from physlearn.control import DURATION, TARGET

    a.seconds = a.seconds if a.seconds is not None else {"still": 10.0, "jog": 0.5, "run": DURATION}.get(a.mode, 10.0)
    a.target = TARGET if a.target is None else a.target
    smax = {"jog": JOG_MAX_S, "run": RUN_MAX_S}.get(a.mode, 3600)
    # `not (a < x < b)` の形で NaN も弾く
    if not 0 < a.dt < 1:
        p.error(f"--dt は 0〜1 秒（今 {a.dt}）")
    if not 0 < a.seconds <= smax:
        p.error(f"--seconds は 0〜{smax} 秒（今 {a.seconds}）")
    try:
        parse_axes(a.axes)
    except ValueError as e:
        p.error(f"--axes: {e}")
    if a.mode in ("still", "id") and not a.out:
        p.error(f"{a.mode} には --out が要る")
    if a.mode == "jog" and not (abs(a.left) <= DUTY_MAX and abs(a.right) <= DUTY_MAX):
        p.error(f"--left・--right は ±{DUTY_MAX} 以内")
    if a.mode == "run" and not (0 < a.target <= TARGET_MAX):
        p.error(f"--target は 0〜{TARGET_MAX} rad/s（負の向きは自動で回す）")
    if a.mode == "run" and a.tc is not None and not (0.03 <= a.tc <= 1):
        p.error("--tc は 0.03〜1 秒")
    if a.mode == "run":
        from physlearn.control import SPEC, design, passes
        from physlearn.randomize import tune
        from physlearn.sim import Params

        base = Params.load(a.params) if a.params else Params()
        tc = a.tc or tune(base)[0]  # loop_demo と同じ決め方
        c = design(base, tc)
        print(f"tc={tc}  kp={c.kp:.4f}  ki={c.ki:.4f}  deadband={c.deadband:.3f}  bias={c.bias:.4f}")
        print(f"仕様 {SPEC}。+{a.target} → -{a.target} rad/s を {a.seconds} s ずつ。車輪を浮かせたか、床なら周りを空けたか確かめて。", flush=True)
    elif a.mode == "jog":
        print(f"jog left={a.left} right={a.right} を {a.seconds} s。車輪を浮かせたか確かめて。", flush=True)
    with SerialPlant(ser=open_port(p, a.port, timeout=0.05), axes=a.axes) as plant:
        if a.mode == "jog":
            g = jog(plant, Command(a.left, a.right), a.seconds, a.dt)
            print(f"gz の平均（後半）{g:+.3f} rad/s（バイアス込み）。{jog_hint(a.left, a.right)}")
            return
        if a.mode == "run":
            rows, res, why = run_loop(plant, lambda: design(base, tc), a.target, a.seconds, a.dt)
            if a.out:
                write_csv(a.out, rows)
                print(f"wrote {a.out}")
            for sign, m in res:
                print(
                    f"[{'+' if sign > 0 else '-'}{a.target}] 整定 {m['settle']:.2f} s  行き過ぎ {m['overshoot'] * 100:.1f} %"
                    f"  定常偏差 {m['ss_error']:.3f} rad/s  仕様 {'OK' if passes(m) else 'NG'}"
                )
            if why:
                raise SystemExit(f"安全ゲートが作動した（{why}）。止めた")
            return
        if a.mode == "still":
            record(plant, [(a.seconds, Command(0.0, 0.0))], a.dt, a.out)
        else:
            # sim と同じ指令列・同じ安全ゲート。左右交互なので USB ケーブルの正味のねじれはほぼ 0
            rows = []
            try:
                sim_log(plant, a.dt, rows)
            finally:  # 途中で失敗しても、そこまでのログを残す
                if rows:
                    write_csv(a.out, rows)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
