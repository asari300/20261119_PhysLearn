"""偽の XIAO: 擬似端末 (pty) の向こうでスケッチと同じ取り決めを話し、中で Plant を回す。

    uv run python -m physlearn.fakexiao                 # 表示された /dev/pts/N に
    uv run python -m physlearn.link id --port /dev/pts/N --out real.csv

中身は HIDDEN（loop-demo の「実機の代役」）の SimPlant。取り決めは doc/protocol.md。
"""

import argparse
import math
import os
import select
import time

from physlearn import HIDDEN
from physlearn.api import Command
from physlearn.link import parse_axes
from physlearn.sim import SimPlant

# 以下 3 つは firmware/xiao_imu_drive/xiao_imu_drive.ino の同名の定数と、buf[48]（47 文字 + 終端）から
DUTY_MAX = 0.6
WATCHDOG_MS = 200
PERIOD_MS = 10
LINE_MAX = 47


class FakeXiao:
    def __init__(self, plant, axes: str = "x,y,z", speed: float = 1.0):
        import pty
        import tty

        self.plant, self.rot, self.speed = plant, parse_axes(axes), speed
        self.master, self.slave = pty.openpty()
        tty.setraw(self.slave)  # 相手が開く前でも、エコーや改行の変換をさせない
        self.port = os.ttyname(self.slave)  # slave を開いたままにして、相手が閉じても master が EIO にならない
        os.set_blocking(self.master, False)
        self.duty = (0.0, 0.0)
        self.t_ms = self.last_cmd_ms = 0  # 偽物の中の時刻 (millis() の代わり)
        self.running = True

    def _write(self, s: str) -> None:
        try:
            os.write(self.master, s.encode())
        except BlockingIOError:
            pass  # スケッチと同じく、相手が読まずに詰まったら捨てる（止まらずウォッチドッグを生かす）

    def _line(self, s: str) -> None:
        if s == "S":
            self.duty, self.last_cmd_ms = (0.0, 0.0), self.t_ms
            return
        v = s[2:].split() if s.startswith("M ") else []
        try:
            lr = [float(x) for x in v]
        except ValueError:
            lr = []
        if len(lr) == 2 and all(map(math.isfinite, lr)):
            self.duty = tuple(max(-DUTY_MAX, min(DUTY_MAX, x)) for x in lr)
            self.last_cmd_ms = self.t_ms
        else:
            self._write("# ERR bad line\n")  # ウォッチドッグは延ばさない

    def run(self) -> None:
        try:
            self._run()
        finally:
            os.close(self.master)
            os.close(self.slave)

    def _run(self) -> None:
        self.plant.reset()
        buf, overflow = b"", False
        nxt = time.monotonic()
        while self.running:
            if select.select([self.master], [], [], max(0.0, nxt - time.monotonic()))[0]:
                for c in os.read(self.master, 4096):
                    if c == 10:  # '\n'
                        buf = buf.removesuffix(b"\r")
                        if overflow:
                            self._write("# ERR line too long\n")
                        elif buf:
                            self._line(buf.decode("ascii", "replace"))
                        buf, overflow = b"", False
                    elif len(buf) < LINE_MAX:
                        buf += bytes([c])
                    else:
                        overflow = True
            if time.monotonic() < nxt:
                continue
            nxt += PERIOD_MS / 1000 / self.speed
            self.t_ms += PERIOD_MS
            if self.t_ms - self.last_cmd_ms > WATCHDOG_MS:
                self.duty = (0.0, 0.0)
            o = self.plant.step(Command(*self.duty), PERIOD_MS / 1000)
            # 機体 = rot @ 基板 なので、基板 = rot.T @ 機体 にして送る（link の --axes で戻る）
            a, g = self.rot.T @ (o.ax, o.ay, o.az), self.rot.T @ (o.gx, o.gy, o.gz)
            self._write("I %d %.3f %.3f %.3f %.4f %.4f %.4f\n" % (self.t_ms, *a, *g))

    def close(self) -> None:
        self.running = False  # run() が抜けて fd を閉じる


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="python -m physlearn.fakexiao", description=__doc__.splitlines()[0])
    p.add_argument("--axes", default="x,y,z", help="基板の付け方（link の --axes と同じ書き方）。偽物はこの逆で送る")
    p.add_argument("--speed", type=float, default=1.0, help="時間の倍率（1 = 実時間 100 Hz）")
    p.add_argument("--plant", choices=["sim", "mujoco"], default="sim", help="sim = HIDDEN の SimPlant")
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args(argv)
    if a.plant == "mujoco":
        from physlearn.mujoco_plant import MujocoPlant  # 任意の依存なので選ばれたときだけ

        plant = MujocoPlant(seed=a.seed)
    else:
        plant = SimPlant(HIDDEN, seed=a.seed)
    try:
        fake = FakeXiao(plant, a.axes, a.speed)
    except (ImportError, OSError) as e:
        raise SystemExit(f"擬似端末 (pty) が使えない環境です（Windows の素の Python など。WSL2 なら使える）: {e}")
    print(f"偽の XIAO: --port {fake.port}  (axes={a.axes} speed={a.speed} plant={a.plant})  Ctrl-C で終わる", flush=True)
    try:
        fake.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
