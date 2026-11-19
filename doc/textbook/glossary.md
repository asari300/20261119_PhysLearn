# 用語集

五十音順ではなく、分野ごとに並べています。

## 全体

| 用語 | 英語 | 意味 |
|---|---|---|
| Physical AI | Physical AI | AI を画面の外へ出し、ロボットなどの体を通して物理の世界で知覚・判断・行動させる取り組みの総称。 |
| sim（シミュレーション） | simulation | 現実を式やプログラムで近似し、計算で動かしたもの。 |
| 実機 | real robot / hardware | 本物のロボット。この教材では XIAO を載せた 2 輪の車。 |
| V-World | Virtual World | この教材での sim の世界の呼び名。PoC 設計書からの呼称で、製品の機能名ではない。 |
| R-World | Real World | この教材での実機の世界の呼び名。 |
| reality gap | reality gap | sim と実機の振る舞いの差。 |
| S2R（Sim2Real） | sim-to-real | sim で作った制御器や方策を実機へ持っていくこと。 |
| R2S（Real2Sim） | real-to-sim | 実機の測定から sim を直すこと。 |
| ドメインランダム化 | domain randomization | sim の数字（ゲイン・遅延など）をばらつかせ、その全部で動く制御器を作ること。 |
| システム同定 | system identification | 入力と出力の記録から、モデルの数字（`K`・`τ` など）を推定すること。 |
| 偽の XIAO | fake XIAO | 擬似端末（pty）の向こうでスケッチと同じ取り決めを話し、中で `Plant` を回すプログラム（`python -m physlearn.fakexiao`）。部品が無くても実機と同じコマンドを練習できる（12 章）。 |
| 代役 | stand-in | 実機が無くても手順を回せるように、実機の代わりに使う sim。隠しパラメータを持つ sim（`physlearn.HIDDEN`）か MuJoCo の車体（07 章）。 |
| デジタルツイン | digital twin | 実物と対応づけて動かす仮想のモデル。安全の仕組みの代わりにはならない。 |

## 制御

| 用語 | 英語 | 意味 |
|---|---|---|
| 制御器 | controller | 観測を受けて指令を出すもの。この教材では `Obs` を受けて `Command` を返す。 |
| 制御対象 | plant | 制御される側。この教材の `Plant` は sim も実機も表す。 |
| 方策 | policy | 観測から行動を決める規則。強化学習でよく使う言い方。 |
| 閉ループ | closed loop | 出力を測って、その結果で次の指令を変える制御。 |
| ゲイン | gain | 入力に対する出力の倍率。モーターの `K` や、制御器の比例ゲインなど。 |
| 一次遅れ | first-order lag | `τ·ω̇ + ω = K·u` の形の応答。指令の値へ、時定数くらいの時間をかけて近づく。 |
| 時定数 | time constant | 一次遅れで、最終値の約 63% に届くまでの時間。記号は `τ`。 |
| ステップ応答 | step response | 指令を急に一段変えたときの応答。同定によく使う。 |
| デッドバンド | dead band | 指令が小さすぎて出力が動かない範囲。モーターでは摩擦が主な原因。 |
| PI 制御 | PI control | 誤差（目標 − 測った値）に比例した分（P）と、誤差を積分した分（I）を足して指令にする方法（06 章）。 |
| 積分 | integral | 値を時間で足し合わせること。PI の I は誤差の積分で、P だけでは残るずれを消す。 |
| ばらつきの幅 `SPREAD` | spread | ドメインランダム化で各数字を振る幅。`(下, 上)` で下側と上側を別々に持つ（`randomize.SPREAD`）。何回かの同定の幅から決め直す（06・14 章）。 |
| 極零相殺 | pole-zero cancellation | 制御器の零点で制御対象の極（遅れ）を打ち消すようにゲインを決めること。06 章では Kp/Ki = τ。 |
| 整定時間 | settling time | 応答が目標の ±5% に入ったきり出なくなる時刻（06 章の `metrics`）。 |
| 残差 | residual | 実機のログの `gz` と、同じ指令を流した sim の `gz` の差。雑音の大きさと比べて、モデルが足りているかを見る（14 章）。 |
| ホールドアウト | holdout | 同定に使わなかったデータで確かめること。この教材では正の向きで同定し、負の向きで確かめる（14 章）。 |
| `HardPlant` | HardPlant | sim の式に無い現象（遅延・左右差・向きの差・電池の低下・IMU の位置ずれ）を足した代役。パラメータを合わせても残る差を見る（15 章）。 |
| 行き過ぎ | overshoot | 応答が目標を越えて振れた分。目標に対する比で表す。 |
| 通過率 | pass rate | ばらつかせた sim のうち、仕様を満たした台数の割合（06 章の `physlearn eval`）。 |
| 飽和 | saturation | 出力や測定が上限に張りつくこと。 |
| 遅延 | delay / latency | 指令や観測が届くまでの時間の遅れ。通信や処理で生まれる。 |
| デューティ比 | duty cycle | PWM で ON の時間の割合。この教材の `Command` は -1..1 で、符号が回る向き。XIAO 側で ±0.6 に切る（09 章）。 |
| PWM | pulse width modulation | ON と OFF を速く切り替え、その割合で平均の電力を調整する方法。 |

## 車体

| 用語 | 英語 | 意味 |
|---|---|---|
| 差動 2 輪 | differential drive | 左右の車輪の速さの差で曲がる車の形。 |
| トレッド | track width | 左右の車輪の間隔。式では `b`。 |
| ヨー角速度 | yaw rate | 上から見て回る速さ。z 軸まわりの角速度。この教材では `gz`、左旋回が正。 |
| エンコーダー | encoder | 車輪やモーターの回転を数えるセンサー。この教材では使わない。 |
| オドメトリ | odometry | 車輪の回転などを積み重ねて、位置と向きを推定すること。 |
| 機体座標 | body frame | 車体に固定した座標。この教材では x 前・y 左・z 上の右手系。 |

## IMU

| 用語 | 英語 | 意味 |
|---|---|---|
| IMU | inertial measurement unit | 加速度計とジャイロを 1 つにしたセンサー。 |
| 加速度計 | accelerometer | 比力を測るセンサー。静止時は上向きに約 +9.81 m/s^2 を出す。 |
| ジャイロ | gyroscope | 角速度を測るセンサー。重力は感じない。 |
| 比力 | specific force | 重力以外の力による加速度。加速度計が実際に測っているもの。 |
| LSB | least significant bit | センサーが出す整数の 1 目盛り。感度を掛けて物理量に直す。 |
| 感度 | sensitivity | 1 LSB が何の物理量に当たるか。例: mg/LSB、mdps/LSB。 |
| フルスケール | full scale | センサーが測れる範囲。広くすると目盛りが粗くなる。 |
| バイアス | bias | いつも同じ向きにずれる分。静止ログの平均で測る。 |
| 雑音 | noise | 毎回ばらばらに揺れる分。静止ログの標準偏差で測る。 |
| ドリフト | drift | バイアスが温度や時間でゆっくり変わること。 |
| dps | degrees per second | 度毎秒。角速度の単位。rad/s に直すには π/180 を掛ける。 |

## 安全・道具

| 用語 | 英語 | 意味 |
|---|---|---|
| ウォッチドッグ | watchdog | 一定時間指令が来ないとモーターを止める仕組み。マイコン側に置く。この教材のスケッチは 200 ms（09 章）。 |
| 安全ゲート | safety gate | 制御器と Plant の間に置き、duty の上限・変化率を抑え、NaN や大きすぎる角速度で止める関門（`control.SafetyGate`、06・09 章）。 |
| 診断ツール `hwcheck` | hwcheck | 実機の流れの確認（`stream`）と IMU の軸の向きの割り出し（`axes`）を、合否つきで出す道具。モーターは回さない。`link` や `fakexiao` と同じポートを同時に開けない（03・12 章、`doc/bringup.md`）。 |
| 章の出力の検査 `docs_check` | docs_check | 章に貼った「実際に走らせた出力」を走らせ直して比べる道具。差があれば終了コード 1（07・12 章、`python -m physlearn.docs_check`）。 |
| 非常停止 | emergency stop | 手で物理的に動力を切る仕組み。 |
| LiPo | lithium polymer battery | 軽く強いリチウムポリマー電池。過充電・過放電・ショートで発火のおそれがある。 |
| MuJoCo | MuJoCo | 接触を含む物理の sim の道具。GPU 無しでも動く。この教材は 4.0.1 以上を任意の依存にする（`doc/adr/0001-sim-stack.md`）。 |
| Isaac Sim / Isaac Lab | Isaac Sim / Isaac Lab | NVIDIA のロボット sim と、その上で学習させる道具。GPU が要る（Isaac Sim 6.2 の最小要件は RTX 4080・RAM 32GB。`doc/research/2026-11-19-software.md`）。 |
| SolidCraft | SolidCraft | 筐体を設計する CAD（Rust 製、`tangency-labs/solidcraft`）。ブラウザー版・CLI・MCP がある（16 章、`doc/cad-mcp.md`）。 |
| MCP | Model Context Protocol | Claude Code などから外部の道具（ここでは SolidCraft）を呼ぶための取り決め。16 章。 |
| 設計 JSON | design JSON | SolidCraft の設計の保存形式。この教材では `cad/plate_mount.design.json` が正本で、コマンド列の `cad/plate_mount.json` はレシピ（16 章）。 |
| STEP / URDF | STEP / URDF | CAD の形を渡す形式（STEP）と、ロボットの形と慣性を書く形式（URDF）。SolidCraft の CLI が書き出す（16 章）。 |
| 質量特性と Izz | mass properties / Izz | 質量・重心・慣性テンソルをまとめた呼び名。`Izz` は鉛直軸（z）まわりの慣性で、ヨーの回りにくさを決める（16 章）。 |
| ROS 2 | Robot Operating System 2 | ロボットの部品（ノード）同士をメッセージでつなぐための仕組み。 |
| 強化学習 | reinforcement learning | 試行と報酬から方策を学ぶ方法。 |
| 模倣学習 | imitation learning | 人などの手本の記録から方策を学ぶ方法。 |
| VLA | vision-language-action model | 画像と言葉を受けて、ロボットの行動を出す大きなモデル。 |
