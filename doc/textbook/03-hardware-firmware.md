# 3. 実機をつなぐ: 部品・配線・ファームウェア・ログ

この章では、IMU（加速度と角速度のセンサー）を内蔵した小さなマイコン基板 Seeed XIAO を PC につなぎ、
(1) IMU の値を PC に流し、(2) PC から 2 つのモーターを回せるようにする。
最後に、次の章の系同定（`physlearn sysid`）で使うログを取る。

> この章の手順は、実機が手元に無い状態で書いた。スケッチは XIAO nRF52840 Sense 向けに
> コンパイルが通ることだけを確かめてある。実機で動かして違いに気づいたら、この章を直してほしい。

価格と買う場所は `doc/research/2026-11-19-hardware.md`（S001 の調査）を見る。

## 3.1 部品

| 部品 | 役目 | メモ |
|---|---|---|
| Seeed XIAO nRF52840 Sense（第一候補） | マイコン + IMU (LSM6DS3TR-C) | 「Sense」の付かない XIAO nRF52840 には IMU が無い |
| Seeed XIAO MG24 Sense（次点） | 同上 | 同じスケッチの `#if` で切り替える。**未コンパイル・未確認** |
| DRV8833 モータードライバー基板 | モーター 2 個を 3.3 V の信号で回す | 入力は IN1/IN2 の 2 本 × 2 |
| DC ギヤモーター 2 個 + 車輪 + 車体 | 2 輪差動の車 | キャスター 1 個で 3 点支持 |
| 電池（例: 単 3 × 4 や 1 セル LiPo） | モーター用の電源 | マイコンとは分ける（3.6 節） |
| USB-C ケーブル | 書き込みとシリアル通信 | 充電専用ケーブルでは通信できない |

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
           |  |  |  |                         |
           v  v  v  v                         |
         AIN1 AIN2 BIN1 BIN2   GND -----------+---- 電池 (-)
        +---------------------+
        | DRV8833             |  VM ---------------- 電池 (+)
        |  AOUT1 AOUT2  BOUT1 BOUT2 |
        +---------------------+
            |     |      |     |
           [左モーター]  [右モーター]
```

| XIAO のピン | つなぐ先 | 定数名（スケッチ冒頭） |
|---|---|---|
| D0 | DRV8833 AIN1 | `PIN_L_IN1` |
| D1 | DRV8833 AIN2 | `PIN_L_IN2` |
| D2 | DRV8833 BIN1 | `PIN_R_IN1` |
| D3 | DRV8833 BIN2 | `PIN_R_IN2` |
| GND | DRV8833 GND と電池 (-) | （共通の GND にする） |
| — | DRV8833 VM ← 電池 (+) | モーター電源は XIAO から取らない |

- DRV8833 の基板に `nSLEEP`（`EEP`）ピンがあるものは、High（3.3 V）にしないと動かない。基板の説明を確かめる。
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
# ステップ応答: 静止 1 秒 → 左 -0.4・右 +0.4 で左旋回 2 秒 → 停止 2 秒
uv run python -m physlearn.link step --port /dev/ttyACM0 --duty 0.4 --out log/step.csv
```

出力は 1 行 = 1 step (10 ms) の CSV で、列は `t,ax,ay,az,gx,gy,gz,left,right`。
これを `physlearn sysid log/step.csv` に渡す（次の章）。

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
- モーターの電源は電池から DRV8833 の VM へ。XIAO の 3V3 から取らない（電流が足りず、電圧が下がって XIAO が落ちる）。
- duty の上限 `DUTY_MAX`（既定 0.6）はスケッチ冒頭にある。慣れるまで上げない。
- PC 側のプログラムが止まれば、200 ms でモーターも止まる。`SerialPlant` は終了時・例外時に停止を送る。
  それでも止まらなければ、電池を外す。

## 演習

1. 静止ログの `gz` の平均と標準偏差を求めよ。平均は「ゼロ点のずれ（バイアス）」、標準偏差は「ノイズ」である。
   10 秒の静止ログで、`gz` をそのまま積分すると 60 秒後に向きは何度ずれるか。
2. ステップ応答ログで、旋回を始めてから `gz` が最終値の 63% に達するまでの時間を読み取れ（これが 1 次遅れの時定数の目安）。duty を 0.2・0.4・0.6 と変えて、最終値が duty に比例するかを確かめよ。
3. 基板を車体に 180° 回して（USB 端子を後ろ向きに）付けたとき、`--axes` に何を指定すべきか答え、3.7 の手順で確かめよ。
