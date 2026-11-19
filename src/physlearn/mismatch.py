"""sim の式に無い現象を足した「実機の代役」（教材 15 章）。`python -m physlearn.mismatch one|loop`。

`HIDDEN` は sim と同じ式で値だけ違うので、同定すれば必ず合う。`HardPlant` は式そのものをずらす。
現象はそれぞれ 0 で切れる: delay（むだ時間）、lr（左右のゲイン差）、sag（電池の低下）、imu_x（IMU の前ずれ）。
"""

import sys
from collections import deque
from dataclasses import replace

import numpy as np

from physlearn import HIDDEN, sim_log
from physlearn.api import Command, Obs
from physlearn.sim import Params, SimPlant

DEFAULTS = {
    "delay": 0.04,  # s。仮の値（USB・マイコン周期・ドライバー。30〜50 ms の真ん中）
    "lr": 0.10,  # 右のゲイン ×(1+lr)、左 ×(1-lr)。仮の値（01 章「左右で違う」の大きさは未測定）
    "fb": 0.10,  # 左モーターだけ前転のゲイン ×(1+fb)（回る向きで違うモーター）。仮の値
    "sag": 0.27,  # 13 章: アルカリ新品→消耗で K −27%。ここでは SAG_T 秒で使い切る（時間を縮めた仮の速さ）
    "imu_x": 0.03,  # m。IMU が旋回中心より前にずれている量。仮の値
}
SAG_T = 13.0  # s。同定の実験 1 回分（id_experiment の長さ）で消耗まで落とす


class HardPlant(SimPlant):
    def __init__(self, p: Params = HIDDEN, seed: int = 0, delay=0.0, lr=0.0, fb=0.0, sag=0.0, imu_x=0.0):
        super().__init__(p, seed)
        self.delay, self.lr, self.fb, self.sag, self.imu_x = delay, lr, fb, sag, imu_x
        self.used = 0.0  # 電池は reset しても戻らない

    def reset(self) -> Obs:
        self.q, self.x = None, 0.0  # x: 前後に動いた道のり m（その場旋回なら 0 のはず）
        return super().reset()

    def _scale(self, u: float, g: float) -> float:
        """デッドバンドの外側だけを g 倍した duty（_drive(u') = g·_drive(u) になる）。"""
        db = self.p.deadband
        return u if abs(u) <= db else np.sign(u) * db + g * (u - np.sign(u) * db)

    def step(self, cmd: Command, dt: float) -> Obs:
        if self.q is None:
            self.q = deque([Command(0.0, 0.0)] * round(self.delay / dt))
        self.q.append(cmd)
        cmd = self.q.popleft()
        g = 1 - self.sag * min(1.0, self.used / SAG_T)
        self.used += dt
        gl = g * (1 - self.lr) * (1 + self.fb * (cmd.left > 0))
        cmd = Command(self._scale(cmd.left, gl), self._scale(cmd.right, g * (1 + self.lr)))
        w0 = self.yaw_rate
        obs = super().step(cmd, dt)
        w1 = self.yaw_rate
        self.x += abs(self.v) * dt
        # IMU が前に d: 向心 −ω²d が ax に、接線 α·d が ay に乗る。gz は剛体のどこでも同じ
        return replace(obs, ax=obs.ax - w1**2 * self.imu_x, ay=obs.ay + (w1 - w0) / dt * self.imu_x)


def replay(p: Params, log: dict, dt: float = 0.01) -> np.ndarray:
    """ログと同じ指令を雑音なしの sim に流した真のヨー角速度。"""
    s = SimPlant(replace(p, gyro_noise=0.0, accel_noise=0.0))
    s.reset()
    out = []
    for l, r in zip(log["left"], log["right"]):
        s.step(Command(l, r), dt)
        out.append(s.yaw_rate)
    return np.array(out)


def one(name: str, value: float) -> dict:
    """現象 1 つだけの代役で同定し、同定した sim との残差をステップごとに出す。"""
    from physlearn.log import as_log
    from physlearn.sysid import apply, identify, segments

    plant = HardPlant(**{name: value})
    log = as_log(sim_log(plant))
    est = identify(log)
    p = apply(Params(), est)
    res = log["gz"] - est["gyro_bias"] - replay(p, log)
    u = (log["right"] - log["left"]) / 2
    rise, steady = [], []
    for i, j in segments(u)[1:]:
        if u[j - 1] != 0:
            sgn = np.sign(u[j - 1])  # 向きをそろえる: + は「実機のほうが速く回る」
            rise.append(sgn * res[i : i + 20].mean())  # 最初の 0.2 s
            steady.append(sgn * res[i + int(0.7 * (j - i)) : j].mean())
    moving = u != 0
    print(f"--- {name}={value}")
    print("  同定: " + "  ".join(f"{k}={est[k]:.3f}" for k in ("yaw_gain", "motor_tau", "deadband")))
    print("  残差 gz (rad/s、向きをそろえた。+ は代役のほうが速い)、ステップ順 +0.2 -0.2 +0.35 -0.35 +0.5 -0.5")
    print("    立ち上がり 0.2 s: " + " ".join(f"{x:+.2f}" for x in rise))
    print("    定常(後ろ 30%):  " + " ".join(f"{x:+.2f}" for x in steady))
    print(f"    全体の RMS {np.sqrt((res**2).mean()):.3f}   ax の平均（動いている間）{log['ax'][moving].mean():+.3f} m/s^2   前後の道のり {plant.x:.3f} m")
    return {"est": est, "rise": rise, "steady": steady, "ax": float(log["ax"][moving].mean())}


def loop(seed: int = 0, n: int = 30) -> None:
    """loop_demo と同じ流れを、HIDDEN と全部入りの代役で回し、最後に tc を緩めて試す。"""
    from physlearn.control import design, metrics, passes, run
    from physlearn.log import as_log
    from physlearn.randomize import tune
    from physlearn.sysid import apply, identify

    def show(m):
        ok = "OK" if passes(m) else "NG"
        return f"整定 {m['settle']:.2f} s 行き過ぎ {m['overshoot']:.0%} 定常偏差 {m['ss_error']:.3f} {ok}"

    for label, real in (("HIDDEN（同じ式）", SimPlant(HIDDEN, seed + 1000)), ("HardPlant（全部入り）", HardPlant(seed=seed + 1000, **DEFAULTS))):
        print(f"=== {label}")
        tc, _ = tune(Params(), n=n, seed=seed)
        print(f"  前 (公称) tc={tc}: {show(metrics(*run(real, design(Params(), tc))[1:]))}")
        est = identify(as_log(sim_log(real)))
        p = apply(Params(), est)
        tc, rate = tune(p, n=n, seed=seed)
        print(f"  同定: K={est['yaw_gain']:.2f} tau={est['motor_tau']:.3f} db={est['deadband']:.3f}")
        print(f"  後 (同定) tc={tc} sim 通過率 {rate:.0%}: {show(metrics(*run(real, design(p, tc))[1:]))}")
        for fresh in (False, True):
            for tc in (0.2, 0.3, 0.4):
                if fresh:
                    real.used = 0.0  # 電池を新品に替えてから試す
                m = metrics(*run(real, design(p, tc))[1:])
                print(f"    {'電池を新品に' if fresh else '電池そのまま'} tc={tc}: {show(m)}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["loop"]:
        loop()
    else:
        for k, v in DEFAULTS.items():
            one(k, v)
