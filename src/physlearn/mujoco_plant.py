"""MuJoCo で動く 2 輪差動の `Plant`（任意の依存 `mujoco` が要る）。

    python -m physlearn.mujoco_plant --out log.csv
で 静止 -> 左右逆の duty -> 停止 のログを `LOG_COLUMNS` の CSV で書く。
"""

import argparse
import csv
from pathlib import Path

import mujoco
import numpy as np

from physlearn.api import LOG_COLUMNS, Command, Obs

MODEL = Path(__file__).parent / "models" / "diffdrive.xml"


class MujocoPlant:
    def __init__(self, noise_acc=0.0, noise_gyro=0.0, bias_gyro=(0.0, 0.0, 0.0), seed=0):
        self.model = mujoco.MjModel.from_xml_path(str(MODEL))
        self.data = mujoco.MjData(self.model)
        self.noise_acc, self.noise_gyro = noise_acc, noise_gyro
        self.bias_gyro = np.asarray(bias_gyro, float)
        self.seed = seed

    def reset(self) -> Obs:
        mujoco.mj_resetData(self.model, self.data)
        self.rng = np.random.default_rng(self.seed)
        # 初期姿勢で接触が落ち着くまで回してから t = 0 とする
        mujoco.mj_step(self.model, self.data, nstep=250)
        self.t0 = self.data.time
        return self._obs()

    def step(self, cmd: Command, dt: float) -> Obs:
        self.data.ctrl[:] = (cmd.left, cmd.right)
        mujoco.mj_step(self.model, self.data, nstep=max(1, round(dt / self.model.opt.timestep)))
        return self._obs()

    def _obs(self) -> Obs:
        # site の軸が機体座標 (x 前・y 左・z 上) なので、センサー値をそのまま使える
        acc = self.data.sensor("acc").data + self.noise_acc * self.rng.standard_normal(3)
        gyro = self.data.sensor("gyro").data + self.bias_gyro + self.noise_gyro * self.rng.standard_normal(3)
        return Obs(self.data.time - self.t0, *map(float, acc), *map(float, gyro))


def main():
    p = argparse.ArgumentParser(description="MuJoCo の車体でステップ応答のログを書く")
    p.add_argument("--out", required=True)
    p.add_argument("--duty", type=float, default=0.5)
    p.add_argument("--dt", type=float, default=0.01)
    p.add_argument("--noise", action="store_true", help="IMU に雑音とジャイロのバイアスを足す")
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    plant = MujocoPlant(0.05, 0.005, (0.0, 0.0, 0.02), a.seed) if a.noise else MujocoPlant(seed=a.seed)
    plant.reset()
    plan = [(1.0, Command(0, 0)), (2.0, Command(-a.duty, a.duty)), (1.0, Command(0, 0))]
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(LOG_COLUMNS)
        for seconds, cmd in plan:
            for _ in range(round(seconds / a.dt)):
                o = plant.step(cmd, a.dt)
                w.writerow([f"{v:.6g}" for v in (o.t, o.ax, o.ay, o.az, o.gx, o.gy, o.gz, cmd.left, cmd.right)])


if __name__ == "__main__":
    main()
