"""MuJoCo で動く 2 輪差動の `Plant`（任意の依存 `mujoco` が要る）。

同定用のログは `physlearn sim-log --plant mujoco log.csv` で書く。
"""

from pathlib import Path

import mujoco
import numpy as np

from physlearn.api import Command, Obs

MODEL = Path(__file__).parent / "models" / "diffdrive.xml"


class MujocoPlant:
    def __init__(self, noise_acc=0.0, noise_gyro=0.0, bias_gyro=(0.0, 0.0, 0.0), seed=0, xml: str | None = None):
        # xml: 書き換えた MJCF の文字列（cad.to_mjcf の出力など）。None なら diffdrive.xml
        self.model = mujoco.MjModel.from_xml_string(xml) if xml else mujoco.MjModel.from_xml_path(str(MODEL))
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

    @property
    def yaw_rate(self) -> float:
        """真のヨー角速度（雑音・バイアスなしのジャイロ z。平らな床なので機体の z と鉛直が一致する）。評価に使う。"""
        return float(self.data.sensor("gyro").data[2])

    def _obs(self) -> Obs:
        # site の軸が機体座標 (x 前・y 左・z 上) なので、センサー値をそのまま使える
        acc = self.data.sensor("acc").data + self.noise_acc * self.rng.standard_normal(3)
        gyro = self.data.sensor("gyro").data + self.bias_gyro + self.noise_gyro * self.rng.standard_normal(3)
        return Obs(self.data.time - self.t0, *map(float, acc), *map(float, gyro))
