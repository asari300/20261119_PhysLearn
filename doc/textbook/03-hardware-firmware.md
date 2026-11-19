# 3. 実機をつなぐ: 部品・配線・ファームウェア・ログ

この章では、IMU（加速度と角速度のセンサー）を内蔵した小さなマイコン基板 Seeed XIAO を PC につなぎ、
(1) IMU の値を PC に流し、(2) PC から 2 つのモーターを回せるようにする。
最後に、次の章の系同定（`physlearn sysid`）で使うログを取る。

> この章の手順は、実機が手元に無い状態で書いた。スケッチは XIAO nRF52840 Sense 向けに
> コンパイルが通ることだけを確かめてある。実機で動かして違いに気づいたら、この章を直してほしい。

価格と買う場所は `doc/research/2026-11-19-hardware.md`（S001 の調査）の「4. 推奨 BOM」(B) を見る。

## 3.1 部品

| 部品 | 役目 | メモ |
|---|---|---|
| Seeed XIAO nRF52840 Sense（第一候補） | マイコン + IMU (LSM6DS3TR-C) | 「Sense」の付かない XIAO nRF52840 には IMU が無い |
| Cytron Robo Base 2WD（車体キット） | 2 輪差動の車体・モーター 2 個・車輪 | 中身は買う前に確かめる（調査の文書） |
| 秋月 AE-DRV8835-S（DRV8835 モジュール） | モーター 2 個を 3.3 V の信号で回す | MODE を GND にして IN/IN で使う |
| 電池ボックス 単3×4 | モーター用の電源（約 6 V） | マイコンとは分ける（3.8 節） |
| ブレッドボードとジャンパー線 | 配線 | |
| USB-C ケーブル | 書き込みとシリアル通信 | 充電専用ケーブルでは通信できない |

- **在庫が細い**: XIAO nRF52840 Sense は秋月で残りわずか、スイッチサイエンスは売り切れだった（2026-11-19 13:36 時点）。
  次点の XIAO MG24 Sense は同じスケッチの `#if` で切り替えるが**未コンパイル・実機未確認**。
  保険の XIAO nRF54L15 Sense（在庫あり）は Arduino に第三者のコアが要り、このスケッチでは**確かめていない**。

**最小の構成は XIAO 単体**。モーターをつながなくても IMU のログ（3.5 節の静止ログ）は取れる。

注意: XIAO ESP32S3 Sense は「Sense」でもカメラとマイクの基板で、IMU は載っていない
（Seeed の wiki の仕様表に IMU が無い）。この教材では使わない。

## 3.2 配線

```
            USB-C (PC へ)
          +-----------+
     D0 --| XIAO      |-- 5V
     D1 --|           |-- GND ----------------+
     D2 --|           |-- 3V3                 |
     D3 --|           |                       |
          +-----------+                       |
           |  |  |  |    3V3 ---> VCC         |
           v  v  v  v                         |
         AIN1 AIN2 BIN1 BIN2   GND -----------+---- 電池 (-)
        +---------------------------+  MODE --+ (GND に直結 = IN/IN)
        | DRV8835 (AE-DRV8835-S)    |  VM ---------------- 電池 (+)  単3×4
        |  AOUT1 AOUT2  BOUT1 BOUT2 |
        +---------------------------+
            |     |      |     |
           [左モーター]  [右モーター]
```

| XIAO のピン | つなぐ先 | 定数名（スケッチ冒頭） |
|---|---|---|
| D0 | DRV8835 AIN1 | `PIN_L_IN1` |
| D1 | DRV8835 AIN2 | `PIN_L_IN2` |
| D2 | DRV8835 BIN1 | `PIN_R_IN1` |
| D3 | DRV8835 BIN2 | `PIN_R_IN2` |
| 3V3 | DRV8835 VCC（ロジック電源） | VCC が 0 V だと DRV8835 はスリープして動かない |
| GND | DRV8835 GND・MODE と電池 (-) | （共通の GND にする） |
| — | DRV8835 VM ← 電池 (+) | モーター電源は XIAO から取らない |

- DRV8835 の範囲（TI データシート SLVSB18H の推奨動作条件）: VCC 2〜7 V、VM 0〜11 V、外から入れる PWM 0〜250 kHz。
  XIAO の 3V3 と単3×4（約 6 V）はこの中に入る。
- IN/IN の動き（同 Table 3）: IN1=1・IN2=0 で正転、0・1 で逆転、0・0 で空転（coast）、1・1 でブレーキ。
  MODE が LOW か未接続なら IN/IN（入力は約 100 kΩ で GND に引かれている）。それでも MODE は GND に直結する。
- スケッチは **fast decay**（回す向きの入力に PWM、反対側は 0。PWM の休みは空転）にしている。
  duty 0 やウォッチドッグの停止が「両入力 LOW = 空転」になり、急ブレーキがかからないため。
  duty と回転の速さの関係は直線から外れるが、それは次の章の系同定で測る。
- PWM は nRF52 コアの `analogWrite` の既定で 8 bit・約 62.7 kHz（16 MHz / 255。コアのソースで確認）。耳には聞こえない。
- **AE-DRV8835-S の 12 ピンの並びは【未確認】**（秋月の取扱説明書の図がテキストで読めなかった）。基板のシルクと説明書の図で確かめてからつなぐ。
- GND は必ず共通にする。共通でないと信号が伝わらない。
- 前に進めたいのに後ろに回るモーターは、そのモーターの 2 本の線を入れ替える（ソフトで直さない方が分かりやすい）。

## 3.3 書き込み

使うもの: ボード定義「Seeed nRF52 Boards」（非 mbed 版）と、ライブラリ「Seeed Arduino LSM6DS3」。

### Arduino IDE

1. 「ファイル → 基本設定 → 追加のボードマネージャの URL」に
   `https://files.seeedstudio.com/arduino/package_seeeduino_boards_index.json` を足す。
2. ボードマネージャで「Seeed nRF52 Boards」を入れる。ボードは「Seeed XIAO nRF52840 Sense」。
3. ライブラリマネージャで「Seeed Arduino LSM6DS3」を入れる。
4. `firmware/xiao_imu_drive/xiao_imu_drive.ino` を開いて書き込む。

### arduino-cli

```sh
arduino-cli config add board_manager.additional_urls \
  https://files.seeedstudio.com/arduino/package_seeeduino_boards_index.json
arduino-cli core update-index
arduino-cli core install Seeeduino:nrf52
arduino-cli lib install "Seeed Arduino LSM6DS3"
arduino-cli compile --fqbn Seeeduino:nrf52:xiaonRF52840Sense firmware/xiao_imu_drive
arduino-cli upload  --fqbn Seeeduino:nrf52:xiaonRF52840Sense -p /dev/ttyACM0 firmware/xiao_imu_drive
```

- コンパイルの最後に `python` と `adafruit-nrfutil` のコマンドが要る（書き込み用の zip を作るため）。
  無ければ `pipx install adafruit-nrfutil` などで入れ、`python` が `python3` を指すようにする。
- 書き込みに失敗したら、リセットボタンを素早く 2 回押してブートローダーに入れてから、もう一度。

## 3.4 WSL2 で USB シリアルを使う

WSL2 の Linux からは、そのままでは USB 機器が見えない。Windows 側の usbipd-win で渡す。

1. Windows に usbipd-win を入れる（PowerShell で `winget install usbipd`）。
2. 管理者の PowerShell で一覧を見て、XIAO の BUSID（例 `2-3`）を探す。
   ```powershell
   usbipd list
   usbipd bind --busid 2-3        # 初回だけ
   usbipd attach --wsl --busid 2-3
   ```
3. WSL 側で `ls /dev/ttyACM*` に出てくれば成功。読めないときは `sudo usermod -aG dialout $USER` してから入り直す。
4. 書き込みでブートローダーに入ると USB 機器が付け替わるので、もう一度 `attach` が要ることがある。
   Windows 側の Arduino IDE で書き込み、WSL ではログ取りだけをする、という分け方でもよい。

## 3.5 端末で動作を確かめる

```sh
picocom -b 115200 --omap crlf --echo /dev/ttyACM0     # 抜けるのは Ctrl-A Ctrl-X
```

1. `I 52310 0.012 -0.034 9.806 0.0011 -0.0007 0.0002` のような行が 1 秒に 100 行流れれば IMU は動いている。
   形の説明は `doc/protocol.md`。
2. **車輪を浮かせてから**、`M 0.3 0.3` と打って Enter。両輪が前に回り、約 0.2 秒で止まる（ウォッチドッグ）。
   人の打つ速さでは指令が途絶えるので、止まるのが正しい。
3. `M abc` と打つと `# ERR bad line` が返り、モーターは回らない。

## 3.6 ログを取る

```sh
# 静止ログ: 机に置いたまま 10 秒（IMU だけでよい）
uv run python -m physlearn.link still --port /dev/ttyACM0 --seconds 10 --out log/still.csv
# 同定用のログ: sim と同じ指令列（physlearn.sim.id_experiment）を同じ安全ゲート越しに流す
uv run python -m physlearn.link id --port /dev/ttyACM0 --out log/id.csv
```

出力は 1 行 = 1 step (10 ms) の CSV で、列は `t,ax,ay,az,gx,gy,gz,left,right`。
使い方（`physlearn sysid log/id.csv`）は 05 章を見る。

指令の並び（旋回成分 u。左 = −u、右 = +u で、u > 0 が左旋回）:
静止 1 秒 → u = +0.2, −0.2, +0.35, −0.35, +0.5, −0.5 を各 1 秒、それぞれの後に 0 を 1 秒。全体 13 秒。
先頭の静止でバイアスと雑音、振幅の違う段でゲイン・時定数・デッドバンドを見る。

### USB ケーブルのねじれ

ロボットは USB でつないだままその場で回る。一方向に回り続けるとケーブルがねじれて車体を引っぱる。
そこで右と左を同じ大きさ・同じ長さで交互に回し、**正味の回転をほぼ 0** にしている（空転の惰性の差でわずかに残る）。

1 段でどれだけ回るかの見積もり（MuJoCo のモデルで duty 0.5 のとき約 9 rad/s だった値からの換算。実機では未確認）:
u = 0.5 を 1 秒で最大 約 9 rad ≈ 1.4 回転。立ち上がりの遅れとデッドバンドがあるので実際はこれより少ない。
次の段で逆に回して戻るので、ねじれは最大で 1.5 回転ほどと見ておく。

- ケーブルは**上から吊る**（スタンドや棚から垂らし、車体の真上で回るようにする）。床を引きずらない。
- ログは短く取り、**終わったらすぐ止める**（`SerialPlant` は終了時に停止を送る）。何本も続けて取るときは、間でねじれを手で戻す。

## 3.7 軸の向きを確かめる

この教材の機体座標は **x 前・y 左・z 上**。基板の向きが違えば `--axes` で付け替える。

1. 車体を水平に置いて静止ログを取る。`az ≈ +9.8`、`ax ≈ ay ≈ 0` になるはず。
   `az ≈ -9.8` なら基板が裏返し。
2. 車体の前を持ち上げる（鼻上げ）。加速度センサーは重力の反対向き（上向き）を測るので、上を向いた機体 x の成分 `ax` が**正**に動く。
3. 左側を持ち上げる。同じ理由で `ay` が正に動く。
4. 上から見て反時計回り（左旋回）に回す。`gz` が**正**になる。
5. 合わなければ `--axes` を直す。例: 基板の y が車の前を向いているなら `--axes y,-x,z`
   （機体 x = 基板 y、機体 y = 基板 -x）。

## 3.8 安全

- 初めて回すときは**車輪を浮かせる**（箱の上に載せる）。
- モーターの電源は電池から DRV8835 の VM へ。XIAO の 3V3 から取らない（電流が足りず、電圧が下がって XIAO が落ちる）。
- duty の上限 `DUTY_MAX`（既定 0.6）はスケッチ冒頭にある。慣れるまで上げない。
- PC 側のプログラムが止まれば、200 ms でモーターも止まる。`SerialPlant` は終了時・例外時に停止を送る。
  それでも止まらなければ、電池を外す。

## 演習

1. 静止ログの `gz` の平均と標準偏差を求めよ。平均は「ゼロ点のずれ（バイアス）」、標準偏差は「ノイズ」である。
   10 秒の静止ログで、`gz` をそのまま積分すると 60 秒後に向きは何度ずれるか。
2. 同定用のログで、u = +0.5 の段が始まってから `gz` がその段の最終値の 63% に達するまでの時間を読み取れ（これが 1 次遅れの時定数の目安）。u = 0.2・0.35・0.5 の段の最終値が u に比例するかを確かめよ（比例しなければデッドバンドを疑う）。
3. 基板を車体に 180° 回して（USB 端子を後ろ向きに）付けたとき、`--axes` に何を指定すべきか答え、3.7 の手順で確かめよ。
