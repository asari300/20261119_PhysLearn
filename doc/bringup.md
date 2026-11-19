# 実機の立ち上げ手順（届いた日に上から順に）

> **この手順書は机上で作った（S022、2026-11-19）。実機で 1 度も通していない。** コマンドは `--help` で存在とオプションを確かめたが、実機につないで走らせてはいない。
> 合格基準の出どころは各項目の【】に書いた。根拠の無いものは「目安（根拠なし）」。通したら、その基準を実測で置き換える。

使い方: 各段のチェックを上から潰す。外れたら次の段に進まない。記録は `log/work/` のその日の作業記録に、ログ CSV は `log/` に置く。
詳しい手順は章にある。ここでは二重に書かず、章を指す。

ポートは `/dev/ttyACM0` と書く（WSL2 の usbipd の渡し方は [setup](setup.md) と [03 章 3.4](textbook/03-hardware-firmware.md)）。

## 0 開封・目視・秤

- [ ] 部品が BOM と合う（[hardware 調査](research/2026-11-19-hardware.md) の BOM 表）。XIAO が **Sense**（IMU つき）であること。
- [ ] 車輪の直径・左右の車輪の間隔（トレッド）・車体の質量を測る。
  基準: 比べる先は sim の公称 `wheel_radius` 0.016 m・`track` 0.08 m【`sim.py` の `Params`】。ずれは記録するだけ（合否なし）。
- [ ] 記録: 実測値を作業記録へ。`Params` の公称値を変えるかは段 9 で決める。

## 1 XIAO 単体（モーターも電池もつながない）

- [ ] 書き込む（[03 章 3.3](textbook/03-hardware-firmware.md)。FQBN `Seeeduino:nrf52:xiaonRF52840Sense`）。
  外れたら: リセットを素早く 2 回でブートローダー、usbipd の attach をやり直す（03 章 3.4）。
- [ ] 端末で `I` 行が流れる（03 章 3.5 の `picocom -b 115200 ...`）。
  基準: 1 秒に 100 行【スケッチ `PERIOD_US = 10000`】。`I` 行が出ず `# ` で始まる誤りの行だけなら IMU の初期化失敗。
- [ ] IMU のアドレスと電源ピン: `I` 行が出れば 0x6A で読めている【スケッチ `LSM6DS3 imu(I2C_MODE, 0x6A)`、電源は `begin()` が P1.08 を上げる】。
  出なければ: スケッチの 0x6A を 0x6B に変えて試す。Seeed の回路図の SA0 は誰も見ていない【監査 `log/review/2026-11-19-s016-audit-claude.md` の補足】。
- [ ] 記録: hardware 調査の I2C アドレスの【推測】、setup の「`I` 行が流れること」の【未確認】を消す（hardware 調査は S019 の持ち分なので、その時点の担当に渡す）。

## 2 静止ログと IMU の特性

- [ ] 机に置いて 10 秒（温度が落ち着くまでの待ち時間は未確認。届いたら通電 5 分後と直後の 2 本を取って比べる＝目安（根拠なし））。
  `uv run python -m physlearn.link still --port /dev/ttyACM0 --seconds 10 --out log/still.csv`
- [ ] `uv run python -m physlearn.imu still log/still.csv`（読み方は [11 章 実験 1・2](textbook/11-imu-lab.md)）。
  基準: `gz` のバイアスの大きさ ≤ 0.02 rad/s【`randomize.SPREAD["gyro_bias"]`。これを超えると eval のばらつきの外】。
  `gz` の雑音の標準偏差は 0.01 rad/s 前後【sim の公称 `gyro_noise`。合否ではなく比べるだけ】。
  `az` ≈ +9.81 m/s²、ずれ ±0.5 以内＝目安（根拠なし）。
- [ ] 手で回す: `link still --seconds 20` で記録しながら、最初の数秒は置いたまま、その後に手で 1 回転（360°）させて置く。
  `uv run python -m physlearn.imu turn log/turn.csv --still-seconds 3`
  基準: 積分が 2π rad の ±5% 以内＝目安（根拠なし）。回している最中に `link still` が記録し続けられるかも未確認【S014】。
- [ ] `uv run python -m physlearn.imu r2s log/still.csv --out log/params_imu.json`（11 章 実験 4）。
- [ ] 記録: 11 章・02 章の「実機でやるときの注意」と S014 の【未確認】（サンプル間隔の揺れ・温度でのバイアス）に実測を書く。

## 3 軸の向き

- [ ] [03 章 3.7](textbook/03-hardware-firmware.md) の 4 つ（水平で `az` 正、鼻上げで `ax` 正、左上げで `ay` 正、上から見て反時計回りで `gz` 正）。
  確かめ方: `link still --seconds 10` で記録しながら姿勢を変え、CSV の列を見る。
  基準: 符号が 4 つとも合う【機体座標 x 前・y 左・z 上、03 章】。
- [ ] 合わなければ `--axes` を決める（例 `--axes y,-x,z`）。以後のすべての `link` コマンドに同じ `--axes` を付ける。
- [ ] 記録: 決めた `--axes` を作業記録と 03 章の脚注候補に。

## 止め方と、やってはいけないこと（段 4・5 の前に読む）

- 止め方: (1) PC のプログラムを Ctrl-C（`SerialPlant` が停止を送る）。(2) USB を抜く → 200 ms で止まる【スケッチ `WATCHDOG_MS = 200`】。(3) 電池ボックスのスイッチを切る。**(3) にいつも手が届くようにする。**
- やってはいけない:
  - モーターの電源を XIAO の 3V3 や 5V から取る（03 章 3.8）。
  - 電池をつないだまま配線を変える。
  - 初回から床に置く（段 5 のモーターの向きの確認までは必ず車輪を浮かせる。[09 章 チェックリスト](textbook/09-safety.md)）。
  - スケッチの `DUTY_MAX` を 0.6 より上げる（`SafetyGate` の既定も 0.6 で揃えてある。ずらすとログの指令と実際の duty が食い違い同定が狂う【`control.py` のコメント】）。

## 4 配線（電池を入れる前に）

- [ ] **AE-DRV8835-S のピンの並びを、手元の基板のシルクと秋月の説明書で確かめる。** 誰も確かめていない【03 章 3.2 の【未確認】、監査】。MODE を GND（IN/IN）にする【03 章、スケッチ】。基板上の MODE の引き下げの有無も未確認。
- [ ] 結線は 03 章 3.2 の表どおり（D0/D1 → AIN1/AIN2、D2/D3 → BIN1/BIN2）【スケッチ `PIN_L_IN1 = D0` ほか】。GND は XIAO・ドライバー・電池で共通。
- [ ] 電池を入れずにテスターで導通: 電池 + と GND の間が短絡していない（導通音が鳴らない）。VM と VCC が別の線であること。
- [ ] 電池だけ入れ（XIAO はまだ USB を挿さない）、VM の電圧を測る。
  基準: VM ≤ 11 V【DRV8835 の VM 範囲。TI の PDF は取り直していない】。モーターの定格内か（TT モーター 3〜6 V は根拠なし。新品のアルカリ 4 本で 6 V を超えうる＝hardware 調査の「根拠なし（断り書きあり）」）。
- [ ] VCC は XIAO の 3V3 から。基準: 2〜7 V【DRV8835 の VCC 範囲、同上】。
- [ ] 記録: ピンの並びと MODE を 03 章・hardware 調査の【未確認】に返す（その時点の担当へ）。

## 5 車輪を浮かせてモーター

- [ ] 車体を箱に載せ、車輪が空回りする状態。電池スイッチに手を置く。
- [ ] 端末（03 章 3.5）で `M 0.3 0.3` → 両輪が**前**に回り、約 0.2 秒で止まる【`WATCHDOG_MS = 200`】。
  逆なら: その側の IN1/IN2 を入れ替える（スケッチは変えない）。
- [ ] `M 0.3 -0.3` → 右が前・左が後ろ（上から見て反時計回りの向き）【取り決め: 左 = −u、右 = +u で u > 0 が左旋回、03 章 3.6】。
- [ ] 符号を PC 側からも確かめる（偽の XIAO で確かめた。実機では未確認）: `uv run python -m physlearn.link jog --port /dev/ttyACM0 --axes <段 3 の値> --right 0.3` と `--left 0.3`。
  0.5 s（`--seconds`、上限 1 s）だけ回して止め、後半の gz の平均を出す。基準: 右だけ → gz 正、左だけ → gz 負（`SafetyGate` を通す。duty は ±`DUTY_MAX` まで）。
  偽の XIAO では `+0.582` と `-0.419` rad/s（バイアス 0.08 込み）。
- [ ] `M abc` → `# ERR bad line`、回らない【03 章 3.5】。
- [ ] duty の上限: `M 1 1` と `M 0.6 0.6` で回り方が同じに見える【`DUTY_MAX = 0.6`】。目で見るだけなので弱い確かめ。オシロがあれば D0 の PWM のデューティ比 60% 以下・周期 約 62.7 kHz【`HardwarePWM.cpp`、監査】。
- [ ] どこまで小さい duty で回り出すかを `M 0.05 0.05`、`M 0.1 0.1` … で見る。比べる先: 公称デッドバンド 0.05【`Params.deadband`】。
- [ ] 1 分ほど回したあと、ドライバーとモーターが熱すぎない（09 章 電源）。
- [ ] 記録: 向きの入れ替えの有無、回り出す duty。

## 6 床で同定ログ

- [ ] USB ケーブルを上から吊る（ねじれ: 最大 1.5 回転ほどの見積もり、実機では未確認【03 章 3.6】）。周りに物と人がいない。
- [ ] `uv run python -m physlearn.link id --port /dev/ttyACM0 --axes <段 3 の値> --out log/id.csv`
  全体 13 秒（静止 1 秒 → u = ±0.2, ±0.35, ±0.5 を 1 秒ずつ、間に 0 を 1 秒）【03 章 3.6、`sim.id_experiment`】。
- [ ] 基準: 途中で安全ゲートが止めていない（`|gz| > 15` で止まる【`SafetyGate` の `gz_limit = 15.0`】）。CSV が約 1300 行・列 `t,ax,ay,az,gx,gy,gz,left,right`【03 章】。
- [ ] 終わったらねじれを手で戻す。2〜3 本取る（ばらつきを見るため。本数は目安（根拠なし））。

## 7 同定

- [ ] `uv run physlearn sysid log/id.csv --params log/params_imu.json --out log/params_real.json`（[05 章](textbook/05-real2sim.md)）。
- [ ] 基準: 同定値が eval のばらつきの幅に入る【`randomize.SPREAD`】。`motor_gain` 30 × (1 ± 0.2)・`motor_tau` 0.08 × (1 ± 0.3)・`deadband` 0.05 ± 0.03・`gyro_bias` ± 0.02。外なら段 8 の前に `SPREAD` と公称値を見直す。
- [ ] 2〜3 本のログで同定値が揃う（ばらつき ±10% 以内＝目安（根拠なし））。
- [ ] 記録: S004「実機ログでの sysid」、S005「sysid が CSV を読めるか」の【未確認】。

## 8 ゲインを決めて閉ループ

- [ ] `uv run physlearn eval --params log/params_real.json` で閉ループ時定数 `tc` を選ぶ（[06 章](textbook/06-sim2real.md)）。
  基準: 仕様を満たす割合が高い `tc`。仕様は整定 ≤ 0.6 s・行き過ぎ ≤ 10%・定常誤差 ≤ 0.05 rad/s【`control.SPEC`】。
- [ ] 実機で閉ループを回す（偽の XIAO で確かめた。実機では未確認）:
  `uv run python -m physlearn.link run --port /dev/ttyACM0 --axes <段 3 の値> --params log/params_real.json --out log/run.csv`
  ゲインは `loop-demo` と同じく `randomize.tune` で決める（`--tc` で手で与えてもよい）。+3 → −3 rad/s を 2 s ずつ、間に 1 s 止める。
  正味の回転は ほぼ 0、片道は 3 × 2 = 6 rad ≈ 1 回転（見積もり）。`--target` の上限 5 rad/s、`--seconds` の上限 3 s。
- [ ] 同定のログと性能の評価は床の上で取る。車輪を浮かせると車体が回らず、gz がほぼ 0 になる（浮かせるのは段 5 のモーターの向きの確認まで）。
- [ ] 基準: 2 回とも `仕様 OK`（`control.SPEC`: 整定 ≤ 0.6 s・行き過ぎ ≤ 10%・定常偏差 ≤ 0.05 rad/s）。床の上で。
  評価は gz − 同定したバイアス。真の角速度ではないので、バイアスがずれていても定常偏差に出ない（07 章「実機の経路で 1 周」）。
  安全ゲートが作動したら（`|gz| > 15`）、止めて例外で終わる。

## 9 結果を sim と文書に戻す

- [ ] `log/params_real.json` で `uv run physlearn eval` を回し、sim の予測と実機の応答を並べる（[07 章](textbook/07-loop.md) の 1 周を、代役ではなく実機で）。
- [ ] 公称値（`sim.py` の `Params`）と `SPREAD` を変えるかを決め、変えるなら ADR を書く。
- [ ] 各章・調査文書の【未確認】のうち、この手順で確かめたものを消す。どれを消したかを作業記録に並べる。
