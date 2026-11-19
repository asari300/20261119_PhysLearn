"""偽の XIAO: 擬似端末 (pty) の向こうでスケッチと同じ取り決めを話し、中で Plant を回す。

    uv run python -m physlearn.fakexiao                 # 表示された /dev/pts/N に
    uv run python -m physlearn.link id --port /dev/pts/N --out real.csv

中身は HIDDEN（loop-demo の「実機の代役」）の SimPlant。取り決めは doc/protocol.md。

試験は pty も壁時計も使わない形で回す: `FakeXiao(plant, pty=False).ser` は pyserial と同じ形（write・readline・
reset_input_buffer・flush・close）の物で、`SerialPlant(ser=...)` に渡せる。PC が 1 行 readline するごとに偽物の時刻が
1 サンプル (10 ms) 進み、write した指令は次のサンプルから効く。PC の負荷に依らず結果が毎回同じ（決定論）。
"""

import argparse
import os
import re
import select
import time

from physlearn import HIDDEN
from physlearn.api import Command
from physlearn.link import axes_with_equals, parse_axes
from physlearn.sim import SimPlant

# 以下 3 つは firmware/xiao_imu_drive/xiao_imu_drive.ino の同名の定数と、buf[48]（47 文字 + 終端）から
DUTY_MAX = 0.6
WATCHDOG_MS = 200
PERIOD_MS = 10
LINE_MAX = 47
FLT_MAX = 3.4028234663852886e38  # strtof はこれを超えると inf を返し、スケッチの isfinite が拒む
# strtof が読む数（10 進・16 進。inf・nan は読めても isfinite で拒まれるので最初から外す）
_NUM = r"[+-]?(?:0[xX](?:[0-9a-fA-F]+\.?[0-9a-fA-F]*|\.[0-9a-fA-F]+)(?:[pP][+-]?\d+)?|(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)"
# handleLine と同じ: strtof は貪欲なので (?>) で "12" を "1" "2" に割らない。数の前は strtof が飛ばす空白類、間は無くてもよい（"1-1"）、後ろは ' ' と '\r' だけ
_M = re.compile(rf"M [ \t\v\f\r]*((?>{_NUM}))[ \t\v\f\r]*((?>{_NUM}))[ \r]*")


class FakeXiao:
    def __init__(self, plant, axes: str = "x,y,z", speed: float = 1.0, pty: bool = True):
        self.plant, self.rot, self.speed = plant, parse_axes(axes), speed
        self.duty = (0.0, 0.0)
        self.t_ms = self.last_cmd_ms = 0  # 偽物の中の時刻 (millis() の代わり)
        self.running = True
        self.buf, self.overflow = b"", False
        if pty:
            import pty as _pty
            import tty

            self.master, self.slave = _pty.openpty()
            tty.setraw(self.slave)  # 相手が開く前でも、エコーや改行の変換をさせない
            self.port = os.ttyname(self.slave)  # slave を開いたままにして、相手が閉じても master が EIO にならない
            os.set_blocking(self.master, False)
        else:
            self.out = bytearray()
            self.ser = VirtualPort(self)

    def _write(self, s: str) -> None:
        if hasattr(self, "out"):
            self.out += s.encode()
            return
        try:
            os.write(self.master, s.encode())
        except BlockingIOError:
            pass  # スケッチと同じく、相手が読まずに詰まったら捨てる（止まらずウォッチドッグを生かす）

    def _line(self, s: str) -> None:
        if re.fullmatch("S *", s):
            self.duty, self.last_cmd_ms = (0.0, 0.0), self.t_ms
            return
        m = _M.fullmatch(s)
        lr = [float.fromhex(x) if "x" in x.lower() else float(x) for x in m.groups()] if m else []
        if len(lr) == 2 and all(abs(x) <= FLT_MAX for x in lr):
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

    def feed(self, data: bytes) -> None:
        """PC から届いたバイトを行に切って解釈する（スケッチの loop の読み側）。"""
        for c in data:
            if c == 10:  # '\n'
                buf = self.buf.removesuffix(b"\r")
                if self.overflow:
                    self._write("# ERR line too long\n")
                elif buf:
                    self._line(buf.decode("ascii", "replace"))
                self.buf, self.overflow = b"", False
            elif len(self.buf) < LINE_MAX:
                self.buf += bytes([c])
            else:
                self.overflow = True

    def tick(self) -> None:
        """偽物の時刻を 1 サンプル (10 ms) 進め、サンプルの行を 1 本出す。"""
        self.t_ms += PERIOD_MS
        if self.t_ms - self.last_cmd_ms > WATCHDOG_MS:
            self.duty = (0.0, 0.0)
        o = self.plant.step(Command(*self.duty), PERIOD_MS / 1000)
        # 機体 = rot @ 基板 なので、基板 = rot.T @ 機体 にして送る（link の --axes で戻る）
        a, g = self.rot.T @ (o.ax, o.ay, o.az), self.rot.T @ (o.gx, o.gy, o.gz)
        self._write("I %d %.3f %.3f %.3f %.4f %.4f %.4f\n" % (self.t_ms, *a, *g))

    def _run(self) -> None:
        self.plant.reset()
        nxt = time.monotonic()
        while self.running:
            if select.select([self.master], [], [], max(0.0, nxt - time.monotonic()))[0]:
                self.feed(os.read(self.master, 4096))
            if time.monotonic() < nxt:
                continue
            nxt += PERIOD_MS / 1000 / self.speed
            self.tick()

    def close(self) -> None:
        self.running = False  # run() が抜けて fd を閉じる


class VirtualPort:
    """pyserial.Serial の代わり（試験用）。readline が偽物の時刻を進める。壁時計は見ない。"""

    def __init__(self, fake: FakeXiao):
        self.fake = fake
        fake.plant.reset()

    def write(self, data: bytes) -> int:
        self.fake.feed(data)
        return len(data)

    def readline(self) -> bytes:
        out = self.fake.out
        while b"\n" not in out:
            self.fake.tick()
        line = bytes(out[: out.index(b"\n") + 1])
        del out[: len(line)]
        return line

    def reset_input_buffer(self) -> None:
        self.fake.out.clear()

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="python -m physlearn.fakexiao", description=__doc__.splitlines()[0])
    p.add_argument("--axes", default="x,y,z", help="基板の付け方（link の --axes と同じ書き方）。偽物はこの逆で送る")
    p.add_argument("--speed", type=float, default=1.0, help="時間の倍率（1 = 実時間 100 Hz）")
    p.add_argument("--plant", choices=["sim", "mujoco"], default="sim", help="sim = HIDDEN の SimPlant")
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args(axes_with_equals(argv))  # `--axes -y,x,z` も通す（link と同じ）
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
