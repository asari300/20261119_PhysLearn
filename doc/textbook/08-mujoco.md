# 8. MuJoCo で車体を動かす

## なぜ物理エンジンも使うのか

numpy の sim は、モーターと車体の式を自分で書いたものです。式が見えるので学ぶには一番よいのですが、書いたことしか起きません。
MuJoCo のような物理エンジンを使うと、次のことを自分で書かずに済みます。

- **接触**: 車輪が床を押す力、キャスターが床に乗っていること。
- **摩擦**: 車輪が滑るかどうか。急に大きなトルクをかけたときの空転。
- **慣性**: 車体の重さと形から、回りにくさが自動で決まる。

もう一つの使い道は **sim-to-sim** です。MuJoCo の車体を「実機の代役」にして、そのログから numpy の sim のパラメーターを同定する (R2S) 練習ができます。
実機と違って答え（MJCF に書いた値）が分かっているので、同定がどれだけ当たったかを確かめられます。

## 入れ方と走らせ方

MuJoCo は任意の依存です。GPU も画面も要りません（この章では描画はせず、物理だけを回します）。

```sh
uv sync --extra mujoco
uv run --extra mujoco pytest -q tests/test_mujoco_plant.py
uv run --extra mujoco python -m physlearn.mujoco_plant --out log.csv
```

使った版は `mujoco 4.0.1` です。
最後のコマンドは、静止 1 秒 → 左 -0.5・右 +0.5 の duty（その場で左旋回）2 秒 → 停止 1 秒 を 0.01 秒刻みで回し、
`t,ax,ay,az,gx,gy,gz,left,right` の CSV（1 行 = 1 step）を書きます。`--noise` をつけると IMU に雑音とジャイロのバイアス (gz に +0.02 rad/s) を足します。`--duty`・`--dt`・`--seed` も変えられます。

Python からは `Plant` として使えます。

```python
from physlearn.api import Command
from physlearn.mujoco_plant import MujocoPlant

plant = MujocoPlant()            # 雑音つき: MujocoPlant(noise_acc=0.05, noise_gyro=0.005, bias_gyro=(0, 0, 0.02), seed=1)
obs = plant.reset()
obs = plant.step(Command(left=-0.5, right=0.5), dt=0.01)
```

## MJCF の読み方

モデルは `src/physlearn/models/diffdrive.xml` です。上から順に読みます。

1. `<option timestep="0.002">`: 物理を 2 ms 刻みで解きます。`step(cmd, dt=0.01)` は中で 5 回回ります。
2. `<geom name="floor" type="plane">`: 床。`friction` は（滑り、ねじり、転がり）の 3 つの摩擦係数です。
3. `<body name="chassis">` と `<freejoint/>`: 車体。freejoint で空間を自由に動けます。箱 (`box`) は 0.25 kg。
4. `caster_front`・`caster_rear`: 前後のキャスターの代わりの小さな球。`condim="1"` は「押す力だけで摩擦なし」の接触です。
   MuJoCo は 2 つの geom の condim の大きい方を使うので、`priority="1"` で床より優先させています（これが無いと球に摩擦がつき、旋回が大きく遅れました）。
5. `<site name="imu">`: IMU を付ける場所。軸の向きを車体と同じ（x 前・y 左・z 上）にしてあるので、センサーの値をそのまま `Obs` に入れられます。
6. `left_wheel`・`right_wheel`: 車輪。`hinge` の軸は +y で、+y 回りに回すと前進します。半径 0.03 m、左右の間隔（トレッド）0.10 m、各 0.02 kg。
   形は円柱でなく球にしました。円柱で試すと縁で接触が跳ねて、gz がぎざぎざになったためです。
7. `<actuator>` の `general`: モーター。トルクは

   トルク = 0.05 × duty − (0.05 / 30) × 車輪の角速度　[N m]

   DC モーターは回るほど逆起電力でトルクが落ちます。この「速度に比例して落ちる」形を `biastype="affine"` と `biasprm` の 3 番目（速度の係数）で書いています。
   停動トルク 0.05 N m、無負荷で 30 rad/s です。一次遅れのフィルターを置く方法もありますが、こちらにすると時定数が車体の重さから自然に決まります（重くすれば遅くなる）。
8. `<sensor>`: `accelerometer` と `gyro`。加速度計は重力の反対向きを感じるので、静止時に az = +9.81 になります。

## 実際に走らせた結果

上の `python -m physlearn.mujoco_plant --out log.csv`（雑音なし）のログを次で調べました。

```sh
uv run --extra mujoco python - <<'EOF'
import numpy as np
d = np.genfromtxt("log.csv", delimiter=",", names=True)
t, gz = d["t"], d["gz"]
on = (t > 1.0) & (t <= 3.0); ss = gz[(t > 2.5) & (t <= 3.0)].mean(); print("steady gz %.3f" % ss)
t63 = t[on][np.argmax(gz[on] >= 0.632 * ss)]; print("t63 after step %.3f s" % (t63 - 1.0))
off = t > 3.0; t37 = t[off][np.argmax(gz[off] <= 0.368 * ss)]; print("t37 after stop %.3f s" % (t37 - 3.0))
print("final gz %.2e" % gz[-1], "rest az mean %.4f" % d["az"][t <= 1].mean())
EOF
```

出力:

```
steady gz 8.978
t63 after step 0.080 s
t37 after stop 0.080 s
final gz 3.52e-06 rest az mean 9.8100
```

- 定常の gz は 8.978 rad/s。式から見積もると、duty 0.5 で車輪は 15 rad/s、車輪の速さ 0.45 m/s、gz = 2 × 0.45 / 0.10 = 9.0 rad/s なので、ほぼ一致します。
- 立ち上がりで定常の 63% を超えたのは、ステップから 0.080 秒後のサンプル。止めたときも 0.080 秒で 37% を下回りました。ログが 0.01 秒刻みなので、時定数はおよそ 0.07〜0.08 秒です。
- 静止の az は 9.8100、止めた 1 秒後の gz はほぼ 0 です。

`--noise` をつけたときの最初の 2 行（静止中）は次のとおりで、gz に 0.02 前後のバイアスが乗っています。

```
0.01,0.0652,0.047354,9.77481,-0.00632711,-0.00311637,0.0202066,0,0
0.02,-0.116252,-0.0109396,9.7477,-0.00366134,-0.00272129,0.0184185,0,0
```

このログを S004 の `physlearn sysid <csv>` に食わせて同定することを想定していますが、**この章を書いた時点では実際に食わせて確かめていません**。

## numpy の sim との違いが出そうなところ

確かめてはいませんが、次のところで差が出ると考えられます。

- **滑り**: duty を急に大きくすると、車輪が床に対して滑ることがあります。numpy の sim が「滑らない」と仮定していれば、立ち上がりがそちらより速く見えるはずです。
- **慣性の決まり方**: 時定数は MJCF の質量・形・モーター係数から決まります。numpy の sim では時定数を直接パラメーターとして与えているなら、同定した時定数は「MuJoCo の車体の全部をまとめた一つの数」になります。
- **加速度計**: 旋回中、IMU が回転中心からずれていれば遠心力が ay に出ます。このモデルは IMU を車軸の真ん中に置いているので小さく、出したログで ax・ay に何が出ているかはまだ詳しく見ていません。
- **接触の細かい揺れ**: 物理エンジンは接触を少しやわらかく解くので、静止中にもごく小さな値（1e-17 程度）がセンサーに出ます。

## 演習

1. `diffdrive.xml` の車体の質量を 0.25 から 0.5 kg に変えて、同じコマンドで時定数がどう変わるか測ってください。定常の gz は変わるでしょうか。それはなぜでしょう。
2. `python -m physlearn.mujoco_plant --out log.csv --noise` のログから、静止中の gz の平均を取ってジャイロのバイアスを推定してください。何秒ぶんの静止があれば 0.001 rad/s の精度で当てられるでしょう。
3. （sim-to-sim）MuJoCo のログで numpy の sim の時定数とゲインを同定し、同じ指令で numpy の sim を回して gz を重ねて比べてください。どこが合い、どこが合わないでしょうか。
