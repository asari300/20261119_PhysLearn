# 06 Sim2Real — ばらつきの下でゲインを決めて実機へ

sim で決めたゲインは、sim と少し違う実機でも動かないと困ります。
この章では、ヨー角速度の PI 制御器のゲインをモデルから計算し、パラメータをばらつかせた sim で仕様を満たす割合を見てから実機へ持っていきます。
コードは `src/physlearn/control.py` と `src/physlearn/randomize.py` です。

## 仕様（この教材で決めた数値）

0 → 3 rad/s のステップを 2 秒（dt = 0.01 s）与えて、真のヨー角速度について

| 量 | 定義 | 上限 |
|---|---|---|
| 整定時間 | 目標の ±5% に入ったきり出なくなる時刻 | 0.6 s |
| 行き過ぎ | (最大値 − 目標) / 目標 | 10 % |
| 定常偏差 | 最後の 0.5 s の平均と目標の差 | 0.05 rad/s |

実機では真値が無いので、`run()` は代わりに gz で評価します（バイアスがあるとその分ずれます）。

## 制御器

```
 目標 r ──→(+)── e ──→ [ PI ] ──(+)──→ u ──→ [安全ゲート] ──→ Plant ──→ gz
            ↑−                   ↑                                   │
            │              sign(r)·d (デッドバンド補償)               │
            └──────────── gz − バイアス ←─────────────────────────────┘
```

```
 e = r − (gz − bias)
 u = sign(r)·d + Kp·e + Ki·∫e dt      （積分は ±1 で止める）
 Command(left = −u, right = +u)
```

### ゲインの決め方（モデルから計算）

同定したモデルは P(s) = K_yaw / (τ s + 1)。PI の零点で極を消し、閉ループを時定数 t_c の一次遅れにします。

```
 Kp = τ / (K_yaw · t_c)
 Ki = 1 / (K_yaw · t_c)
 → 開ループ = 1/(t_c s)、閉ループ = 1/(t_c s + 1)
```

目標値の FF（r / K_yaw）は入れていません。入れると閉ループに零点ができ、t_c < τ のとき行き過ぎが出るためです
（実装の途中で入れていたときは、同定後の代役（今とは少し違う隠しパラメータ）で行き過ぎ 33.9 % が出たので外しました）。

### t_c の決め方（粗い探索）

`randomize.tune()` が t_c を 0.08, 0.1, 0.15, 0.2, 0.25 s で試し、ばらつかせた sim で仕様を満たす割合が最大のもの（同率なら速いもの）を選びます。
ばらつきの幅（`SPREAD`）は、モーターのゲイン ±20 %、時定数 ±30 %、デッドバンド ±0.03、ジャイロのバイアス ±0.02 rad/s です。
この幅は「同定のあと電池や床で変わりそうな量」の当て推量で、実機で確かめてはいません。

## 安全ゲート

制御器と Plant の間に 1 つだけ置きます（`SafetyGate`）。sim でも実機でも同じものを通します。

- duty を ±0.6 に切る（スケッチの `DUTY_MAX = 0.6` と同じ。ゲートのほうが大きいと、ログの指令と実際に出た duty がずれて同定が狂う）
- duty の変化を 10 /s（dt = 0.01 なら 1 step 0.1）に抑える
- 指令か観測に NaN/inf がある、または |gz| > 15 rad/s なら (0, 0) にして、以後ずっと止めたまま（`tripped` に理由）

```
$ uv run python -c "
import math
from physlearn.api import Command, Obs
from physlearn.control import SafetyGate
g = SafetyGate()
o = Obs(0, 0, 0, 9.81, 0, 0, 0)
for c in [Command(1.0, -1.0)] * 3 + [Command(math.nan, 0.0), Command(0.1, 0.1)]:
    print(c, '->', g(c, o, 0.01), repr(g.tripped))
"
Command(left=1.0, right=-1.0) -> Command(left=0.1, right=-0.1) ''
Command(left=1.0, right=-1.0) -> Command(left=0.2, right=-0.2) ''
Command(left=1.0, right=-1.0) -> Command(left=0.30000000000000004, right=-0.30000000000000004) ''
Command(left=nan, right=0.0) -> Command(left=0.0, right=0.0) 'NaN/inf'
Command(left=0.1, right=0.1) -> Command(left=0.0, right=0.0) 'NaN/inf'
```

止めたあとに解除する口はわざと作っていません。止まったら、原因を見てから Plant ごと作り直します。

## 動かしてみる

公称の sim と、05 章で代役のログから作った `fixed.json` のそれぞれで評価します。

```
$ uv run physlearn eval -n 100
tc=0.08  kp=0.0833  ki=1.0417  deadband=0.050  bias=0.0000
ばらつき 100 台で仕様を満たした割合: 100%
$ uv run physlearn eval --params fixed.json -n 100
tc=0.2  kp=0.1246  ki=0.6362  deadband=0.150  bias=0.0780
ばらつき 100 台で仕様を満たした割合: 69%
$ uv run physlearn eval --params fixed.json --tc 0.25 -n 100
tc=0.25  kp=0.0996  ki=0.5089  deadband=0.150  bias=0.0780
ばらつき 100 台で仕様を満たした割合: 15%
```

同定した車体は公称より遅い（τ = 0.2 s）ので、同じ幅でばらつかせると仕様ぎりぎりになり、通過率が下がります。
t_c = 0.25 では 15 % まで下がりました。整定 0.6 s に間に合わなくなるためと考えていますが、内訳は見ていません。100 % でないことは、仕様か車体（モーター）を見直す材料です。

## 実機へ持っていく手順

1. 05 章で実機のログから `fixed.json` を作る。
2. `physlearn eval --params fixed.json` で t_c とゲインを決め、通過率を見る。
3. 実機でも同じ `YawPI` と `SafetyGate` を通して走らせる（`control.run(plant, design(p, tc))`、plant は 03 章の実機の `Plant`）。
   3 rad/s に要る duty は u = 3 / K_yaw + d です。これが 0.6 を超える車体では目標に届かないので、仕様か目標を見直します。
   最初は `max_duty` を小さくして、机の上で車輪を浮かせて試す。

3 は実機が手元に無いので **確かめていません**。

## 演習

1. `design()` に FF（u に r / K_yaw を足す）を戻し、公称の sim で行き過ぎがどう変わるか測る。
2. `SPREAD` の時定数の幅を ±30 % → ±60 % にすると、`eval` の通過率と選ばれる t_c はどう変わるか。
3. 安全ゲートの `max_rate` を 2 /s にすると、公称の sim で仕様を満たすか。なぜか。
