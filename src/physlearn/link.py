"""実機 (XIAO + IMU + 2 輪) とのシリアル接続。取り決めは doc/protocol.md。

    uv run python -m physlearn.link still --port /dev/ttyACM0 --seconds 10 --out still.csv
    uv run python -m physlearn.link step  --port /dev/ttyACM0 --duty 0.4 --out step.csv
"""

import argparse
import csv
import time
from dataclasses import replace

import numpy as np
import serial

from physlearn.api import LOG_COLUMNS, Command, Obs

BAUD = 115200
STOP = b"S\n"
G = 9.80665


def encode_command(cmd: Command) -> bytes:
    """指令 1 行。範囲外は -1..1 に丸める（ファームも上限で丸める）。"""
    left, right = (min(1.0, max(-1.0, float(v))) for v in (cmd.left, cmd.right))
    return f"M {left:.3f} {right:.3f}\n".encode()


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
    for row, tok in enumerate(spec.replace(" ", "").split(",")):
        sign = -1.0 if tok.startswith("-") else 1.0
        m[row, "xyz".index(tok.lstrip("+-"))] = sign
    # 鏡映は角速度（擬ベクトル）の符号を壊すので、回転だけを許す
    if round(np.linalg.det(m)) != 1:
        raise ValueError(f"axes {spec!r} は回転になっていない（各軸 1 回・右手系に）")
    return m


class SerialPlant:
    """`Plant` の実機版。with で使うと、終了時・例外時に必ず停止を送る。"""

    def __init__(self, port: str = "", axes: str = "x,y,z", timeout: float = 1.0, ser=None):
        self.ser = ser if ser is not None else serial.Serial(port, BAUD, timeout=0.05)
        self.rot = parse_axes(axes)
        self.timeout = timeout
        self.t0 = 0.0  # reset 時の MCU 時刻 [s]
        self.t_target = 0.0  # 次に待つ時刻（reset からの秒）。dt を積んで時刻のずれを溜めない
        self.last_cmd = STOP
        self.sent_at = 0.0

    def _send(self, line: bytes) -> None:
        self.ser.write(line)
        self.last_cmd = line
        self.sent_at = time.monotonic()

    def _next(self) -> Obs:
        """次のサンプル（機体座標・reset からの時刻）。timeout 秒来なければ例外。"""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            # MCU のウォッチドッグ (200 ms) より短い間隔で同じ指令を送り直す
            if time.monotonic() - self.sent_at > 0.05:
                self._send(self.last_cmd)
            s = decode_sample(self.ser.readline())
            if s is not None:
                a = self.rot @ (s.ax, s.ay, s.az)
                g = self.rot @ (s.gx, s.gy, s.gz)
                return Obs(s.t - self.t0, *a, *g)
        raise TimeoutError(f"{self.timeout} 秒間 IMU のサンプルが来ない")

    def reset(self) -> Obs:
        try:
            self._send(STOP)
            self.ser.reset_input_buffer()
            self.t0 = 0.0
            first = self._next()
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
                w.writerow([f"{getattr(o, k):.6g}" for k in LOG_COLUMNS[:7]] + [cmd.left, cmd.right])


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="python -m physlearn.link", description=__doc__.splitlines()[0])
    p.add_argument("mode", choices=["still", "step"], help="still: IMU だけ記録 / step: 静止→旋回→停止")
    p.add_argument("--port", required=True, help="例 /dev/ttyACM0")
    p.add_argument("--out", required=True, help="出力 CSV")
    p.add_argument("--axes", default="x,y,z", help="機体 x,y,z に当たる基板の軸（符号つき）")
    p.add_argument("--dt", type=float, default=0.01)
    p.add_argument("--seconds", type=float, default=10.0, help="still の長さ")
    p.add_argument("--duty", type=float, default=0.4, help="step の旋回 duty（左 -duty・右 +duty で左旋回）")
    a = p.parse_args(argv)
    stop = Command(0.0, 0.0)
    if a.mode == "still":
        schedule = [(a.seconds, stop)]
    else:
        schedule = [(1.0, stop), (2.0, Command(-a.duty, a.duty)), (2.0, stop)]
    with SerialPlant(a.port, a.axes) as plant:
        record(plant, schedule, a.dt, a.out)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
