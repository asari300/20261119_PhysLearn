# 作業記録 S005 firmware-link (2026-11-19)

## 作ったもの
- `doc/protocol.md`: 行単位テキスト。PC→MCU `M <l> <r>` / `S`、MCU→PC `I <t_ms> ax ay az gx gy gz`（基板座標、m/s^2・rad/s、100 Hz）、`# ...` は読み捨て。
- `firmware/xiao_imu_drive/xiao_imu_drive.ino`: 起動時停止、200 ms ウォッチドッグ、`DUTY_MAX=0.6`、壊れた行・長すぎる行は捨てる（ウォッチドッグ延長なし）、送信バッファが埋まればサンプルを捨てる。
- `src/physlearn/link.py`: `encode_command` / `decode_sample` / `parse_axes`、`SerialPlant`（`with` で終了・例外時に `S`）、`record`、CLI `still` / `step`。
- `tests/test_link.py`: 15 件。
- `doc/textbook/03-hardware-firmware.md`。

## 決めたことと根拠
- 単位は MCU 側で SI に直す。PC 側の `Obs` と同じ単位にしておくと、端末で見て意味が分かる。
- 軸の付け替えは PC 側（`--axes`、符号つき置換、det=+1 のみ）。ファームを板の付け方で書き換えずに済む。鏡映は角速度の符号を壊すので拒否。
- step の時間は MCU の時刻で累計 dt に達するまで待つ。PC の遅れで時間軸がずれない。
- 走行中は 50 ms ごとに同じ指令を送り直す（ウォッチドッグ 200 ms の 1/4）。
- ボード差は冒頭の `#if` 1 か所。IMU の電源ピン・I2C バス (Wire1) は Seeed のライブラリが板ごとに選ぶ（ライブラリ 2.0.8 のソースで確認: MG24 は `PD5` を High、nRF52840 Sense は variant の `PIN_LSM6DS3TR_C_POWER`=15）。
- DRV8833 は fast decay（片側 PWM・片側 0）、停止は両方 0（惰性）。

## 確かめたこと
- `uv run pytest -q tests/test_link.py` → 15 passed（loop:// と偽ポート。往復、壊れた行、軸、送受、タイムアウトと呼び出し側例外での停止送信、CSV）。
- コンパイル: `arduino-cli compile --fqbn Seeeduino:nrf52:xiaonRF52840Sense firmware/xiao_imu_drive`（Seeeduino:nrf52 1.1.13、Seeed Arduino LSM6DS3 2.0.8）が通った（58 KB）。後段で `python` と `adafruit-nrfutil` が要った（scratchpad に shim を置いた）。
- ウェブ（2026-11-19 取得）:
  - Seeed wiki「XIAO-BLE-Sense-IMU-Usage」: 6 軸 IMU、ライブラリ Seeed_Arduino_LSM6DS3。無印 nRF52840 には IMU 無し。
  - Seeed wiki「xiao_esp32s3_getting_started」: ESP32S3 Sense はカメラ・マイク・SD。IMU の記載無し（第三者サイトに IMU ありとする記述があるが公式に無い）。
  - Seeed wiki「xiao_mg24_sense_built_in_sensor」とフォーラム: LSM6DS3TR-C、PD5 を High で電源、Wire1。
  - I2C アドレス 0x6A はライブラリの既定値（wiki の本文では確認できず）。

## 確かめていないこと（未了）
- **実機では何も動かしていない**（IMU の値、軸の向き、PWM、ウォッチドッグ、USB CDC の挙動、`availableForWrite` の振る舞い）。
- **MG24 Sense は未コンパイル**: Silicon Labs のコア (5.0.0, 約 620 MB) を入れようとして /tmp (tmpfs) の空きが尽きて失敗。消して諦めた。`ARDUINO_XIAO_MG24` マクロ名はライブラリのソースから取ったもの。D0..D3 の PWM も未確認。
- WSL2 + usbipd-win の手順は一般的な手順を書いただけで、この環境で試していない。
- DRV8833 基板の nSLEEP の扱いは基板次第。
- `physlearn sysid` (S004) が実際にこの CSV を読めるかは、S004 の実装と突き合わせていない（列は `LOG_COLUMNS` に合わせた）。
