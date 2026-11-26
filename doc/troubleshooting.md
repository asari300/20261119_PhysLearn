# つまずき集（症状から引く）

症状を見つけて、原因 → 確かめ方 → 直し方 → 詳しい説明、の順に読む。実機を触る人も、偽の XIAO で練習する人も使える。
説明の本体は各章にある。ここは入口で、新しい事実は足していない。

| 印 | 意味 |
| --- | --- |
| ✔ 再現 | この文書を書いたとき（S052）に、偽の XIAO（`python -m physlearn.fakexiao`）か `physlearn sim-log`、短い Python で状況を作り、メッセージが出ることを確かめた。**メッセージは原文のまま** |
| （文書より） | 既存の文書かコード・CI の設定から拾っただけ。走らせていない |
| 【実機では未確認】 | 実機が無いと確かめようがない。実機の手順書（[bringup](bringup.md)）自体が、まだ実機で通していない |

実機の診断を 1 本で回す道具 `python -m physlearn.hwcheck stream|axes --port ...` がある（モーターは回さない。`stream` はサンプル周期・欠け・`# ERR`・加速度のノルム・飽和を基準つきで、`axes` は 3 つの姿勢から `--axes` を出す。[bringup](bringup.md)）。
章へのリンク: [setup](setup.md)、[bringup](bringup.md)、[protocol](protocol.md)、[03 章](textbook/03-hardware-firmware.md)、[09 章](textbook/09-safety.md)、[11 章](textbook/11-imu-lab.md)、[12 章](textbook/12-fake-xiao.md)、[14 章](textbook/14-fit-check.md)、[15 章](textbook/15-mismatch.md)。

## まずこれを試す

1. **`uv run pytest` が通るか。** 通れば Python 側の環境は正常。落ちたら下の「環境」へ。✔ 再現（通る）
2. **偽の XIAO で同じコマンドが動くか。** 端末 1 で `uv run python -m physlearn.fakexiao`、表示された `/dev/pts/N` を端末 2 の `--port` に入れる（[12 章](textbook/12-fake-xiao.md)）。偽物で動き、実機で動かないなら、疑うのは配線・ポート・ボード・書き込み。PC 側のコードではない。✔ 再現
3. **`# ERR` の行を見る。** `uv run python -m serial.tools.miniterm /dev/ttyACM0 115200`（抜けるのは Ctrl-]）。`I ...` の行が流れていなければ、その代わりに出ている `# ERR ...` が原因を示している（[protocol](protocol.md)）。（文書より）

## 環境（uv・Python・MuJoCo・図）

- **``mujoco が入っていない。`uv sync --extra mujoco` で入れる``** ✔ 再現。`--plant mujoco`・`--real mujoco` を選んだが追加パッケージが無い。→ メッセージどおり。MuJoCo 4.x の注意は [setup 1.3](setup.md)。
- **``matplotlib が無い。`uv sync --extra viz` で入れる``** ✔ 再現。`python -m physlearn.plot` に図の道具が要る。→ メッセージどおり。
- **`command not found: python`**（`physlearn` も）。`.venv` を有効にしていない。14 章のコマンドは `uv run` を付けずに書いてある。→ 前に `uv run` を付ける（`uv run python -m physlearn.compare ...`、`uv run physlearn sim-log ...`）。
- **`ModuleNotFoundError: No module named 'mujoco'`**。`python -m physlearn.cad`（16 章）は S093 から、MuJoCo が無ければこの例外ではなく「mujoco が入っていない」のメッセージで止まる（終了コード 1）。ほかに MuJoCo を直に読む所があれば、この例外のまま出る。→ `uv sync --extra mujoco --extra viz`。
- **`No module named physlearn.__main__; 'physlearn' is a package and cannot be directly executed`** ✔ 再現。`python -m physlearn sysid ...` と打った。`physlearn` は `-m` で呼ぶ名前ではなく、コマンド名。→ `uv run physlearn sysid ...`。`python -m physlearn.link` のようにサブモジュールは `-m` で呼ぶ。
- **`FileNotFoundError: [Errno 2] No such file or directory: 'xxx.csv'`**（`.json` も）✔ 再現。パスの打ち間違い、または作ったときと別のディレクトリにいる。→ `ls` で確かめる。`sim-log`・`link` は `--out` に書いた場所に作る。
- **`uv run pytest` が落ちる・止まる。** 偽の XIAO を使う試験は S092 から壁時計に依らない仮想のポートで回るので、遅い PC でも時間切れにはならない作りになった（高い負荷での確認はしていない）。擬似端末を使う実時間の形の試験 1 本（`tests/test_fakexiao.py` の `test_pty_realtime_form_still_works`）だけは今も壁時計に依る。CI は失敗した試験をやり直さない（[ci.yml](../.github/workflows/ci.yml)）。→ 落ちた試験の名前を見て、その 1 本だけをもう 1 回回す。同じ試験が同じ所で落ちたら本物の失敗。（文書より）
- **MuJoCo を 3.x から上げたら動かない。** 4.0 でパッケージが `mujoco-core`/`mujoco-studio`/`mujoco` に分かれた。→ 入れ直す（[setup 1.3](setup.md)）。描画（Studio・viewer）が WSL2 で動くかは、この PC でも未確認（実機とは関係なし）。

## Arduino と書き込み

- **コンパイルの最後に `python` や `adafruit-nrfutil` が無いと言われる。** nRF52 のコアが書き込み用 zip を作るのに使う。Ubuntu は `python3` だけのことが多い。→ `pipx install adafruit-nrfutil`、`sudo apt install python-is-python3`。（文書より: [setup 2.3・5](setup.md)、CI もこの 2 つを先に入れる）
- **コアを入れる途中で `no space left on device`。** ツール一式で約 1 GB。`/tmp` が RAM ディスクの環境で起きる。→ 置き場（`directories.data`）を空きのある所に。（文書より: [setup 5](setup.md)）
- **書き込みが止まる・ポートが出ない（nRF52840）。** → リセットを素早く 2 回でブートローダーへ。それでもだめなら抜き差し。充電専用のケーブルでもポートは出ない。MG24 は BOOT ボタンが無く、PC1 を GND に落としてリセット。（文書より: [setup 2.4・5](setup.md)）
- **書き込みの途中で WSL からポートが消える。** ブートローダーに入ると USB の機器としてつなぎ直され、WSL に渡した分が外れる。→ 書き込みは Windows 側の Arduino IDE で、WSL はログ取りだけ。または `usbipd attach --wsl --busid <ID> --auto-attach`。（文書より: [setup 3.3](setup.md)。効くかは【実機では未確認】）
- **非 mbed 版で `Serial` がコンパイルできない。** Seeed wiki が `#include <Adafruit_TinyUSB.h>` を勧める。（文書より: [setup 5](setup.md)。今のスケッチは足さずに CI でコンパイルが通っているので、当たるのは別のスケッチを書いたとき）
- **MG24 向けのコンパイルだけ CI で落ちる。** `firmware-mg24` は `continue-on-error`（落ちても全体は落とさない）。第一候補は nRF52840。（文書より: [ci.yml](../.github/workflows/ci.yml)）

## WSL2 と USB

- **`usbipd bind` が失敗する。** 管理者権限が要る。→ 管理者の PowerShell で。`attach` は管理者が要らない。（文書より: [setup 3.1・5](setup.md)）
- **`usbipd attach` で失敗、または WSL の `lsusb` に出ない。** WSL の VM が止まっている、またはカーネルが古い（5.10.60.1 以上が要る）。→ WSL の端末を開いたままにする。`wsl --update`。確かめ: `uname -r`、`lsusb`。（文書より: [setup 3.1・3.2](setup.md)）
- **`/dev/ttyACM0` が無い。** `ls -l /dev/ttyACM*`。attach 済みで `lsusb` に出ているのに無いなら CDC ACM のモジュールが読まれていない。→ `sudo modprobe cdc_acm`。自動で読まれるかは【実機では未確認】。（[setup 3.2](setup.md)）
- **`error: ポート /dev/ttyACM0 が開けない（[Errno 13] could not open port /dev/ttyACM0: [Errno 13] Permission denied）。…`**（`link`・`hwcheck` は開けなかったとき、原文を括弧に入れて案内を添えた 1 行で終わる。終了コード 2）✔ 再現（`chmod 000` した擬似端末で原文を確認。原因が `dialout` かどうかは実機では未確認）。→ `groups | grep -w dialout`、無ければ `sudo usermod -aG dialout $USER` して入り直す。（[setup 3.2・5](setup.md)）
- **`error: ポート /dev/ttyACM9 が開けない（[Errno 2] could not open port /dev/ttyACM9: [Errno 2] No such file or directory: '/dev/ttyACM9'）。`ls /dev/ttyACM*` で名前を確かめる。WSL2 なら doc/setup.md の usbipd の節…`**（以前は `serial.serialutil.SerialException` のトレースバックだった。自分で `serial.Serial` を開くと今も出る）✔ 再現。ポート名の違い、または USB が WSL に渡っていない。ポート名は環境で変わる。→ `ls /dev/ttyACM*` で今の名前を見る。出ないときは上の 2 項。偽の XIAO の名前は起動のたびに変わる（`/dev/pts/N`）。✔ 再現

## シリアルと取り決め

- **`TimeoutError: 1.0 秒間 IMU のサンプルが来ない`**（秒数は `SerialPlant.timeout`）✔ 再現（何も返さない擬似端末で）。原因の候補: ポートが違う、別のスケッチが入っている、IMU の初期化に失敗している、別のプログラム（miniterm など）がポートを開いている、USB が抜けた。→ miniterm で `I` の行が流れるか。流れなければ次の項。（[protocol](protocol.md)）
- **`TimeoutError: ...（MCU の最後の報告: # ERR imu not found）`**（`hwcheck stream` も、サンプルが来ないときの `NG` の行に同じ報告を添える）✔ 再現（MCU の代わりにその行を流した）。スケッチが IMU を見つけられていない。モーターの指令は受ける。→ ① 「Sense」の付く基板か（付かない XIAO に IMU は無い）。② アドレスは変えない: XIAO nRF52840 Sense（V1.1 の基板）は IMU の SA0 が GND に固定で、アドレスは 0x6A のまま。0x6B にしても読めない。電源（IMU の電源 P1.08 が High になっているか）・`Wire1`（IMU はこちらの I2C につながる）・ライブラリ（`Seeed Arduino LSM6DS3`）・コアの種類を疑う（根拠: `log/review/2026-11-19-s055-audit5-claude.md` E1、`s043-audit4`）。③ 非 mbed 版で出続けるなら mbed 版（FQBN `Seeeduino:mbed:xiaonRF52840Sense`、未確認）で書き込み直す。（[03 章 3.3・3.5](textbook/03-hardware-firmware.md)、[bringup 段 1](bringup.md)。【実機では未確認】）
- **`# ERR bad line`** ✔ 再現（`hello`、`M 1 x`、`M nan 0`、`M inf 0` で出る）。MCU が解釈できない行を捨てた。形は `M <左> <右>`（数が 2 つ、区切りは空白）と `S` だけ。数にならない値（NaN・無限大を含む）も捨てる。壊れた行はウォッチドッグを延ばさない。→ 手で打つときは `M 0.3 0.3`。（[protocol](protocol.md) 「エラーの扱い」）
- **`# ERR line too long`** ✔ 再現（`M ` に 60 桁続けた）。47 文字を超えた行。端末から長い文を流し込んだとき。→ 1 行を短くする。（[protocol](protocol.md)）
- **`RuntimeError: MCU の時刻が戻った (1.02 -> 0.5 s)`** ✔ 再現（時刻が戻る行を流した）。MCU が再起動した（電源の揺れ、USB の抜き差し、リセットの押下）、または `millis` が桁あふれした（約 49 日）。→ 実機ならモーター電源が XIAO の 3V3/5V から出ていないか、GND が共通かを見る（[09 章 電源](textbook/09-safety.md)）。ログを取り直す。
- **`ValueError: 有限でない指令 Command(left=nan, right=0)`** ✔ 再現。制御器か計算が NaN を出した。`SerialPlant` は送らずに `S` を送って止める。→ 制御器のゲイン・入力を見る。`--left nan` のようにコマンドラインで渡した場合は、先に `--left・--right は ±0.6 以内` で弾かれる（下の「コマンドの引数」）。
- **`I` の行が 1 秒に 100 行より少ない。** PC が読まないと MCU は送信バッファが埋まった周期のサンプルを捨てる（止まってウォッチドッグが効かなくなるのを避けるため）。端末で貼り付けた長い文があった場合も同じ。（文書より: [protocol](protocol.md)）
- **コマンドの引数。** ✔ 再現。原文: `--left・--right は ±0.6 以内`、`--target は 0〜5.0 rad/s（負の向きは自動で回す）`、`--tc は 0.03〜1 秒`、`--dt は 0〜1 秒（今 0.0）`、`--seconds は 0〜1.0 秒（今 5.0）`（どちらが悪いかを別々に言う。jog は 1.0、run は 3.0、still・id は 3600）、`still には --out が要る`。→ 範囲を守る。上限は安全のために決めてある（[03 章 3.9](textbook/03-hardware-firmware.md)）。

## 軸の向きと符号（`--axes`）

- **`ValueError: axes '-x,y,z' は回転になっていない（各軸 1 回・右手系に）`** ✔ 再現（`x,x,z` でも同じ）。鏡映や、同じ軸の重複は受け付けない。→ 基板を回して付けた分を、符号つきで入れ替える（例 `y,-x,z`、`-y,x,z`）。右手系になる組だけ。（[protocol](protocol.md)、[03 章 3.7](textbook/03-hardware-firmware.md)）
- **`python -m physlearn.link: error: argument --axes: expected one argument`** 以前は `--axes -x,y,z` で出た（`-` で始まる値を argparse がオプションと読む）。`link` は `--axes -x,y,z` も `--axes=-x,y,z` も通すようにした。`fakexiao` の `--axes` は今も `=` が要る（`--axes=-x,y,z`）。
- **`error: --axes: axes 'a,b,c' は読めない。x・y・z を 3 つ、…。'a' は軸の名前でない`** ✔ 再現（以前は `ValueError: substring not found`）。軸の名前は `x`・`y`・`z`（と `-`・`+`）を 3 つ、コンマ区切り。→ `x,y,z` の並べ替えにする。
- **`az` が 9.81 にならない。** `uv run python -m physlearn.imu still still.csv` の平均と傾き（roll・pitch）を見る。`az ≈ -9.8` なら基板が裏返し。重力が `ax` か `ay` に出ているなら基板を立てて付けた。→ `--axes` で付け替える。偽の XIAO を `--axes x,z,-y` で立てて `--axes` なしで取ると `ay ≈ -9.8`、`--axes x,z,-y` を付けると `az ≈ +9.8` に戻った。✔ 再現。数 % のずれは机の傾きやケーブルの重みでも出る。（[03 章 3.7](textbook/03-hardware-firmware.md)、[11 章 実験 1](textbook/11-imu-lab.md)、[12 章 演習 1](textbook/12-fake-xiao.md)）
- **4 つの向きの符号が合わない**（水平で `az` 正、鼻上げで `ax` 正、左上げで `ay` 正、反時計回りで `gz` 正）。→ `link still` で記録しながら姿勢を変え、CSV の列を見て `--axes` を決める。以後の `link` コマンドすべてに同じ値を付ける。（[03 章 3.7](textbook/03-hardware-firmware.md)、[bringup 段 3](bringup.md)。【実機では未確認】）

## IMU の値

- **止めているのに `gz` が 0 でない（バイアス）。** 偽の XIAO でも `gz` は 0.08 rad/s 付近（HIDDEN のバイアス）。`imu still` の「バイアスを引いた後」の積分でドリフトが消えるかを見る。実機の基準は [bringup 段 2](bringup.md)（`gz` のバイアス ≤ 0.02 rad/s は目安）。積分した角度のずれの正体はバイアスとその測り残し。（✔ 再現: 偽の XIAO。[11 章 実験 1・2](textbook/11-imu-lab.md)）
- **`冒頭 0 s にサンプルが無く、バイアスを測れない。--still-seconds を長くする`** ✔ 再現（`imu turn ... --still-seconds 0`）。冒頭の静止区間が空。→ `--still-seconds` を、ログの最初の静止の長さに合わせる（既定 1 s。[bringup 段 2](bringup.md) は 3 s）。
- **`gz` が ±20.0 rad/s 付近で平らになる（飽和）。** スケッチは ±1000 deg/s（≈ ±17.5 rad/s）に設定し、超えると約 ±20.0 で張り付く。飽和を知らせる行は無い。→ duty を下げるか、スケッチの範囲を ±2000 に戻す。偽の XIAO は飽和を写さない。（文書より: [03 章 3.5](textbook/03-hardware-firmware.md)。次の「安全ゲート」も参照）
- **手で 1 回転させたのに積分が 360 度にならない**（尺度が 0.9 未満か 1.1 超）。手の誤差ならもう 1 回、1 回転で。大きく外れるならスケッチの感度設定（LSB の換算）を疑う。（文書より: [11 章 実験 3](textbook/11-imu-lab.md)）
- **`gx`・`gy` や `az` に sim に無い値が出る。** sim の IMU はバイアスを `gz` にだけ持ち、`az` は常に 9.81、雑音は白色だけ。実機で出たら「モデルに足りないもの」として記録する。（文書より: [11 章](textbook/11-imu-lab.md) 「sim の IMU モデルに無いもの」）

## モーターと配線

先に [bringup 段 4・5](bringup.md) と [03 章 3.2・3.8](textbook/03-hardware-firmware.md)。**最初は必ず車輪を浮かせ、電池のスイッチに手を置く。** いずれも【実機では未確認】（手順書は実機で通していない）。

- **`M 0.3 0.3` を打っても 0.2 秒ほどで止まる。** 正常。人が打つ速さでは指令が途絶え、ウォッチドッグ（200 ms）が止める。✔ 再現（偽の XIAO で `M` を 1 回送ると、約 0.2 秒後に `gz` が下がる。[12 章 演習 2](textbook/12-fake-xiao.md)）。走らせ続けるには同じ `M` を 200 ms より短い間隔で送り直す（`SerialPlant` は 50 ms ごと）。
- **何度やっても回らない。** 順に: 電池 → DRV8835 の VM（スイッチは入っているか）／VCC が 3V3 につながっているか（0 V だとスリープ）／GND が XIAO・ドライバー・電池で共通か／MODE を GND にしたか（IN/IN）／ピンの並びを基板の印字（シルク）で確かめたか（AE-DRV8835-S の並びは誰も実物で確かめていない）／`M abc` が `# ERR bad line` を返すか（通信は生きている）。（文書より: [03 章 3.2](textbook/03-hardware-firmware.md)、[bringup 段 4・5](bringup.md)）
- **片方しか回らない。** 回らない側の IN1/IN2 の結線（D0/D1 が左、D2/D3 が右）とモーターの線を見る。`jog --left 0.3` と `--right 0.3` を別々に。（文書より: [03 章 3.2](textbook/03-hardware-firmware.md)）
- **逆向きに回る。** → そのモーターの 2 本の線を入れ替える（ソフトで直さない）。PC 側からの確認: `jog --right 0.3` は `gz` が正、`--left 0.3` は負が正しい。偽の XIAO では正（約 +0.58）と負（約 −0.4）が出た。✔ 再現（数は実行ごとに少し変わる）。（[03 章 3.2・3.9](textbook/03-hardware-firmware.md)、[bringup 段 5](bringup.md)）
- **小さい duty では回らない。** デッドバンド。回り出す duty を `M 0.05 0.05`、`M 0.1 0.1` … で見て、同定の `deadband` と比べる。（文書より: [bringup 段 5](bringup.md)）
- **走らせているうちに止まる・ログが途切れる。** ウォッチドッグ。PC のプログラムが落ちた、USB が抜けた、壊れた行が続いた（壊れた行は延長しない）。電池切れや XIAO のリセットでも止まる。→ 端末で `# ERR` と `I` の行が続いているか。時刻が戻っていないか（上の `MCU の時刻が戻った`）。（文書より: [protocol](protocol.md)、[09 章](textbook/09-safety.md)）
- **XIAO がリセットされる・IMU の値が乱れる。** モーターの電流で電圧が揺れる。モーター電源を XIAO の 3V3/5V から取っていないか、GND が共通か、VCC・VM の近くにコンデンサがあるかを見る。（文書より: [09 章 電源](textbook/09-safety.md)、[03 章 3.2](textbook/03-hardware-firmware.md)）
- **ドライバーやモーターが熱い・回りが断続する。** DRV8835 は 1 ch 連続 1.5 A。トリップ電流を超えると約 1 ms 切れて自動で戻り、外へは知らせない。モーターのストール電流は未測定。→ 車輪を指で止めない。電流を測る手順は [03 章 3.2](textbook/03-hardware-firmware.md)。
- **USB ケーブルがねじれて車体を引っぱる。** → ケーブルは上から吊る。何本も取るときは間でねじれを手で戻す。（文書より: [03 章 3.6](textbook/03-hardware-firmware.md)）
- **浮かせると `gz` がほとんど 0。** 車体が回らないので当然。同定と閉ループは床の上で取る。浮かせるのは向きの確認まで。（文書より: [bringup 段 8](bringup.md)）

## 同定（`physlearn sysid`）

- **`動いたステップが 2 つ未満なので、ゲイン・時定数・デッドバンドは推定しない（元の値のまま）`** ✔ 再現（`link still` の静止ログを `sysid` に掛けた。出力は `gyro_bias` と `gyro_noise` だけ）。「動いたステップ」は、定常の `gz` が静止の雑音の 10 倍を超えた段。2 つ以上要るのは、傾きと切片から K と deadband を出すため。静止ログなら正常。同定用のログなのに出るなら: モーターが動いていない（電源・配線）、車輪を浮かせた、duty が小さすぎる、安全ゲートが止めた（次の項）。→ CSV の `left`・`right` 列と `gz` 列を見る。
- **`ValueError: 最初に静止区間 (指令 0) が 20 行以上いる`** ✔ 再現（ログの先頭 1.5 s を切り落とした）。ログの先頭が静止でない、または静止が短い。→ `link id` が取ったログをそのまま渡す（先頭に静止 1 s が付く）。
- **`ValueError: xxx.csv: 列が足りない ['gz']`** ✔ 再現。CSV の見出しは `t,ax,ay,az,gx,gy,gz,left,right`。→ 見出しの綴りと列を直す。
- **結果が変: `deadband 0.0000`、`motor_tau 0.0100`（探索範囲の下端）、`RankWarning: Polyfit may be poorly conditioned`。** ✔ 再現（ゲートが途中から指令を 0 にしたログで）。`SafetyGate` が作動すると以後ずっと (0, 0) を返す。`sim-log` と `link id` は標準エラーに `# 安全ゲートが作動した（|gz| > 15.0、t = … s）。以後の指令は 0 になり、このログは同定に使えない` を 1 行出す（標準出力と CSV は変わらない。以前は無言だった）。→ その行が出ていたら、CSV を開き、`left`・`right` が途中から全部 0 になっていないか、`gz` が 15 rad/s を超えていないかを見る。取り直す。
- **ゲインが想定（真値）より少し小さい。** 各段の後ろ 30% を定常とみなすため、時定数が大きいと落ち着く前の値を拾う。既知の偏りで、直していない。（文書より: [05 章](textbook/05-real2sim.md)、[14 章](textbook/14-fit-check.md) の (a)）
- **`deadband` が 0 になる。** 傾きと切片の直線で、切片が負（＝いちばん小さい段が既にデッドバンドより大きい）だと 0 に丸める。指令の段が全部デッドバンドより大きいと、本当の値は見えない。→ 小さい段を足して取る。（コードを読んだだけ: `sysid.py`）
- **同定値が `randomize.SPREAD` の幅の外・取るたびに揃わない。** 電池や床で変わる。→ 何回か取って `python -m physlearn.compare spread a.json b.json ...` で幅を見る。（[14 章](textbook/14-fit-check.md)、[bringup 段 7](bringup.md)）
- **`ValueError: 静止区間の雑音が 0（雑音なしの sim のログ？）。残差を雑音と比べられない`** ✔ 再現（`gyro_noise=0` の Params で作った sim-log に `compare fit`）。雑音の無いログでは当てはまりの判定ができない。→ 実機のログか、雑音ありの sim-log で。
- **`compare fit` が「式の形が違う」と言う。** ゲインも時定数も変えても残差が減らない。遅延・向きでゲインが違うモーター・電池の低下を疑う。→ [15 章](textbook/15-mismatch.md) の「実機でこれを見分けるには」、`compare holdout`。（文書より: [14 章](textbook/14-fit-check.md)）
- **`python -m physlearn.compare` を引数なしで打つと使い方（usage）を出して終わる。** ✔ 再現。`fit LOG.csv PARAMS.json`、`holdout LOG.csv`、`spread A.json B.json ...` の 3 通り。

## 制御（`link run`・`physlearn eval`）

- **`RuntimeError: 安全ゲートが作動した（|gz| > 15.0 か NaN）。止めた`** ✔ 再現（`gz` が 30 rad/s を返す代役で `run_loop`）。`run` は止まって次の回に進まない。原因の候補: 制御が正帰還になった（`--axes` や配線の向きが逆）、`gz` が飽和の張り付き値（約 20）を返した、NaN。→ 車輪を浮かせて `jog` で向きを確かめる。ゲインを下げる（`--tc` を大きく）。（[09 章](textbook/09-safety.md)、[03 章 3.9](textbook/03-hardware-firmware.md)）
- **`仕様 NG`。** 仕様は整定 ≤ 0.6 s・行き過ぎ ≤ 10%・定常偏差 ≤ 0.05 rad/s。sim では OK でも実機で NG になるのは遅延・電池・向きの差。→ `--tc` を 0.2 → 0.3 に緩めると通った例がある（0.4 では遅すぎて NG）。(文書より: [15 章](textbook/15-mismatch.md)、[bringup 段 8](bringup.md))
- **定常偏差が小さいのに、実際の回転は目標とずれていそう。** 実機の評価は `gz` からバイアスを引いたもので、真の角速度ではない。バイアスがずれていても定常偏差に出ない。（文書より: [bringup 段 8](bringup.md)、07 章）
- **`loop-demo` で公称の sim で決めたゲインが「仕様 NG」。** 想定どおり。同定した sim で決め直すと「仕様 OK」になる。✔ 再現（`uv run physlearn loop-demo`。[setup 1.2](setup.md)）

## 偽の XIAO

- **`擬似端末 (pty) が使えない環境です（Windows の素の Python など。WSL2 なら使える）: ...`** （文書より: `fakexiao.py` のメッセージ。Windows の素の Python では再現できない）→ WSL2 の中で。
- **偽の XIAO は動くのに実機は動かない。** 偽物が写さないもの: USB の遅れ、IMU の量子化・温度・取り付けの傾き、電池の電圧低下、機械（滑り・がた・床・ケーブル）、`# ERR imu not found`。偽物の `gz` は飽和しない。（文書より: [12 章](textbook/12-fake-xiao.md)）
- **ポート名が毎回違う。** `/dev/pts/N` は起動のたびに変わる。→ 起動時に表示される `--port` を使う。✔ 再現
- **偽の XIAO が残る。** → 立てた端末で Ctrl-C。

## SolidCraft の CLI

[調査の記録](research/2026-11-19-solidcraft.md)（S042）から。いずれも WSL2・GPU なしで走らせた記録で、この文書では走らせていない。

- **`snapshot`（画像）が返らない。** stderr に `libEGL warning: failed to open /dev/dri/renderD128: Permission denied` が出て 90 秒たっても止まらなかった。`gpu` も同じ。→ GPU の無い WSL2 では画像の書き出しに頼らず、形の確認は `solidcraft-cli eval` の数値（体積・重心）で。（文書より）
- **`mcp setup` は Claude Code などの設定を書き換える。** 実行しない。登録は設定を変えることなので、決めてから。（文書より）
- **AppImage・snap が動かない。** AppImage は FUSE、snap は WSL2 の systemd の設定が要る。→ tar.gz を展開するだけの方法は動いた（root・FUSE 不要）。（文書より）
- **Windows 版で SmartScreen の警告。** 署名はあるが、本番の証明書が入るまでは警告が出ることがある。→ 「詳細情報」→「実行」。（文書より）
- **ブラウザー版・GUI・MCP の操作。** 誰も走らせていない（調査の「確かめていないこと」）。

## CI

- **`test` が落ちる。** 手元で `uv sync --locked --extra mujoco --extra viz` のあと `uv run pytest -q`。失敗した試験のやり直しはしない設定（S092 が外した）。落ちたら本物の失敗として、ログの試験名から調べる。（文書より: [ci.yml](../.github/workflows/ci.yml)）
- **`firmware` が落ちる。** コンパイルの最後に `python` と `adafruit-nrfutil` が要る。コアとライブラリのバージョンは CI で固定してある。（文書より: [ci.yml](../.github/workflows/ci.yml)、[setup 2.3](setup.md)）
- **章に貼った出力が今のコードとずれた。** `uv run python -m physlearn.docs_check`（章のコードブロックを走らせ直して比べる）。数字は期待の最後の桁の半分以内で一致とする。pytest には入っていない。（文書より: `docs_check.py` の説明）
