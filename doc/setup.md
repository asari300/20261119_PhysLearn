# 環境構築の手引き

この教材を動かすまでの準備。第一の読者は **Windows 11 + WSL2 (Ubuntu)** の人。素の Linux と macOS は差分だけ書く。
ボードの第一候補は **Seeed XIAO nRF52840 Sense**、次点は **XIAO MG24 Sense**。

## 印の意味

| 印 | 意味 |
|---|---|
| 【試した】 | 2026-11-19 にこの PC（WSL2, Ubuntu, カーネル 6.18.58.1-microsoft-standard-WSL2）で実際に走らせた |
| 【文書】 | 一次資料（出典を書く）で確かめただけ。この PC では走らせていない |
| 【未確認】 | 実機が無い・資料に無いなどで確かめていない |

出典は JST 2026-11-19 13:45〜13:50 に取得した。**夕方（18:45）に、CI で使っている版（`.github/workflows/ci.yml`・`cad.yml`）、SolidCraft の CLI、診断ツール、つまずき集への案内を足し、監査 4・5 巡目の指摘（Learn の頁の更新日、TinyUSB の行）を直した。**

困ったら先に [troubleshooting.md](troubleshooting.md)（症状から引く）を見る。実機をつないだ直後の診断は `python -m physlearn.hwcheck`（1.4）。

---

## 1. Python 側

### 1.1 要るもの

- Python **3.12 以上**（`pyproject.toml` の `requires-python = ">=3.12"`、`.python-version` は `3.12`）。uv が自動で入れるので、自分で入れなくてよい。
- **uv**。入れ方（Linux / WSL / macOS）【文書】https://docs.astral.sh/uv/getting-started/installation/ :

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

この PC は uv 0.13.6、Python 3.12.14 で動いた【試した】。CI（GitHub Actions）は `astral-sh/setup-uv@v10.3.3` で uv を入れ、Python は `.python-version`（3.12）を読んで uv が入れる（`.github/workflows/ci.yml`）。CI の `test` は `uv sync --locked --extra mujoco --extra viz` のあと `uv run pytest -q`。`--locked` は `uv.lock` のとおりに入れ、ずれていたら失敗する。

### 1.2 入れて、試して、動かす【試した】

```bash
cd <repo>
uv sync                      # numpy, pyserial, pytest が入る（CI は uv sync --locked）
uv run pytest -q             # 試験
uv run physlearn loop-demo   # 1 周の実演（sim → 同定 → ゲイン決め）
```

この PC での結果:

| コマンド | かかった時間 | 出力の要点 |
|---|---|---|
| `uv sync` | 0.3 秒（キャッシュあり。初回はダウンロードぶん延びる） | numpy, pyserial 3.5, pytest 9.2.0 など |
| `uv run pytest -q` | 約 1.5 分（この PC で 88〜95 秒。擬似端末の試験が実時間で走る） | すべて passed（本数は増えていくので書かない）。`--extra mujoco --extra viz` を付けないと、それらが要る試験は skip になる |
| `uv run physlearn loop-demo` | 約 10 秒 | 公称の sim で決めたゲインは代役で「仕様 NG」、同定した sim で決め直すと「仕様 OK」 |

### 1.3 任意の追加

```bash
uv sync --extra mujoco       # MuJoCo 4.x（CPU）。08 章で使う
```

- `uv sync --extra viz` で図を描く道具（`python -m physlearn.plot`）が入る（matplotlib）。両方要るときは `uv sync --extra mujoco --extra viz`（CI と、章の出力を走らせ直す `python -m physlearn.docs_check --mujoco` がこの形）。
- MuJoCo の注意【文書】（`doc/research/2026-11-19-software.md`、出典 https://mujoco.readthedocs.io/en/latest/changelog.html ）:
  - 4.0.1 が最新（2026-11-11）。Python 3.10 は対象外になった（本リポジトリは 3.12 以上なので問題ない）。
  - 4.0 で Python パッケージが `mujoco-core` / `mujoco-studio` / `mujoco` に分かれた。3.x を入れていた環境は入れ直しが要ることがある。
  - この PC では import と 10,000 step は動いた（S002）。描画（Studio / viewer）が WSL2 で動くかは【未確認】。

### 1.4 つないだ直後の診断と、つまずいたとき

- 実機（または偽の XIAO）をつないだら、まず `uv run python -m physlearn.hwcheck stream --port /dev/ttyACM0`（サンプルの周期と欠け、`# ERR`、バイアス、飽和を見る）。次に `... hwcheck axes --port ...`（水平・前を上・左を上の 3 姿勢から `--axes` を割り出す）。手順は [bringup.md](bringup.md) の段 1〜3。偽の XIAO でだけ確かめた。実機では【未確認】。
- **`--axes` は `=` でつなぐ**: 値が `-` で始まるとき、`--axes -y,x,z` と空白で分けると argparse が別のオプションと取り違えて拒む。`--axes=-y,x,z` と書く（`-y,x,z` は基板データからの読み。実物では未確認。[03 章 3.7](textbook/03-hardware-firmware.md)）。`link` は空白区切りでも通り、`hwcheck axes` は `--axes=-y,x,z` の形で表示する（S059、18:43 に main へ。偽の XIAO でだけ確認）。`fakexiao --axes` は今も `=` が要る。
- 症状から引くなら [troubleshooting.md](troubleshooting.md)（約 60 項目。33 か所は偽の XIAO などで再現した原文のメッセージ）。

---

## 2. Arduino 側

### 2.1 ボード定義とライブラリ

| | nRF52840 Sense（第一候補） | MG24 Sense（次点） |
|---|---|---|
| 追加の URL | `https://files.seeedstudio.com/arduino/package_seeeduino_boards_index.json` | `https://siliconlabs.github.io/arduino/package_arduinosilabs_index.json` |
| コア | `Seeeduino:nrf52`（「Seeed nRF52 Boards」、**mbed でない方**） | `SiliconLabs:silabs` |
| FQBN | `Seeeduino:nrf52:xiaonRF52840Sense` | `SiliconLabs:silabs:xiao_mg24`。CI は無線を使わない `SiliconLabs:silabs:xiao_mg24:protocol_stack=none` で通した（メニュー `protocol_stack` は `matter`・`zigbee`・`ble_arduino`・`ble_silabs`・`none`） |
| CI で使っている版 | コア `Seeeduino:nrf52@1.1.13`、ライブラリ `Seeed Arduino LSM6DS3@2.0.8`、arduino-cli 1.6.0、`adafruit-nrfutil==0.5.3.post16`、Python 3.12 | コア `SiliconLabs:silabs@5.0.0`、同じライブラリ、arduino-cli 1.6.0 |
| ライブラリ | Seeed Arduino LSM6DS3（2.0.8） | 同じ（2.0.4 以上） |
| 確かめた度合い | コンパイル【試した】（S005 でこの PC、GitHub Actions の `firmware` ジョブで 2026-11-19 18:13 の初回に成功）、書き込み【未確認】 | コンパイルは GitHub Actions の `firmware-mg24` ジョブで初回に成功（コンパイルが通っただけ）。書き込み・動作【未確認】。**コアが `printf` の浮動小数を持たず、IMU の行が空になる見込み**（S053。未確認）。ローカルでは入れていない（/tmp があふれた） |

出典: https://wiki.seeedstudio.com/XIAO_BLE/ 、https://wiki.seeedstudio.com/xiao_mg24_getting_started/ 【文書】。
上の FQBN とコア名は、`arduino-cli board search xiao` の出力でも確かめた【試した】（arduino-cli 1.6.0）。MG24 のコア 5.0.0 の `boards.txt` に `xiao_mg24.name=Seeed Studio XIAO MG24 (Sense)` がある（監査 4 巡目、GitHub のタグ）。版は CI の `ci.yml` が正で、上げるときは意識して上げる。
Seeed wiki は IMU を使うなら mbed 版を勧めているが、本リポジトリのスケッチは非 mbed 版で書いてある（03 章）。

### 2.2 Arduino IDE 2 で【文書】

1. 「ファイル → 基本設定 → 追加のボードマネージャの URL」に上の URL を足す。
2. ボードマネージャで「Seeed nRF52 Boards」（MG24 は Silicon Labs のパッケージ）を入れる。
3. ライブラリマネージャで「Seeed Arduino LSM6DS3」を入れる。
4. ボード「Seeed XIAO nRF52840 Sense」、ポートは名前に「Seeed Studio XIAO nRF52840」を含むもの（Windows では COM3 以降が多い）を選んで書き込む。

### 2.3 arduino-cli で

```bash
arduino-cli config init
arduino-cli config add board_manager.additional_urls \
  https://files.seeedstudio.com/arduino/package_seeeduino_boards_index.json
arduino-cli core update-index
arduino-cli core install Seeeduino:nrf52@1.1.13        # CI と同じ版。版を付けなければ最新
arduino-cli lib install "Seeed Arduino LSM6DS3@2.0.8"
arduino-cli compile --fqbn Seeeduino:nrf52:xiaonRF52840Sense firmware/xiao_imu_drive          # 【試した】(S005、CI)
arduino-cli upload  --fqbn Seeeduino:nrf52:xiaonRF52840Sense -p /dev/ttyACM0 firmware/xiao_imu_drive  # 【未確認】
```

- **`python` と `adafruit-nrfutil` が PATH に要る**【試した】(S005)。コンパイルの最後に書き込み用の zip を作るため。Ubuntu では `python` が無く `python3` だけのことが多い。
  例: `pipx install adafruit-nrfutil`、`sudo apt install python-is-python3`（どちらもこの PC では実行していない）。
- **ディスク**【試した】（S005 の置き場を `du` で測った）: arduino-cli 本体 40 MB、nRF52 コアとツール一式で約 **1 GB**（コア 72 MB、コンパイラなどのツール 837 MB）。MG24 のコアはさらに約 620 MB（S005 の記録）。`/tmp` が RAM ディスクの環境では置き場をホーム側にする。

### 2.4 ブートローダーに入れる【文書】

- **nRF52840**: リセットボタンを **素早く 2 回** 押す。書き込みが止まったらまずリセット 1 回、だめなら 2 回、それでもだめなら抜き差し（Seeed wiki XIAO_BLE）。
- **MG24**: BOOT ボタンが無い。応答しなくなったら **PC1 を GND に落としたままリセット** すると無限ループで止まり、書き込めるようになる。消去用のスクリプトも wiki にある（Seeed wiki xiao_mg24_getting_started）。

---

## 3. WSL2 で USB シリアルを使う

### 3.1 Windows 側（usbipd-win）【文書】

出典: https://learn.microsoft.com/en-us/windows/wsl/connect-usb （en-us の頁。`ms.date` は 2024-04-16、ページ下端は「Last updated on 2024-07-02」。2026-11-19 17:50 に監査 4 巡目が取得。日本語版は読んでいない。usbipd-win 5.0.0 以上が前提）、https://github.com/dorssel/usbipd-win/releases （最新 **5.3.0**、2025-10-11 公開。JST 2026-11-19 14:10 に Releases の API で確認）。

```powershell
winget install --interactive --exact dorssel.usbipd-win   # 入れる。--interactive を外すと勝手に再起動することがある
usbipd list                          # 管理者の PowerShell で。XIAO の BUSID（例 4-4）を見る
usbipd bind --busid 4-4              # 共有する。管理者が要る。1 台につき 1 回で、再起動後も残る
usbipd attach --wsl --busid 4-4      # WSL に渡す。管理者は不要。WSL の端末を開いたままにしておく
usbipd detach --busid 4-4            # 返す
```

- WSL に渡している間、その機器は Windows からは使えない。抜くか WSL を再起動すると外れる（usbipd-win wiki「WSL support」）。
- WSL のカーネルは 5.10.60.1 以上が要る。古ければ `wsl --shutdown` してから `wsl --update`。

### 3.2 WSL 側

```bash
uname -r                                     # 5.10.60.1 以上か
zcat /proc/config.gz | grep -E 'CONFIG_USB_ACM|CONFIG_USBIP'
lsusb                                        # attach した機器が見えるか（usbutils が要る）
ls -l /dev/ttyACM*                           # nRF52840 は USB CDC なので ttyACM になる
groups | grep -w dialout                     # 無ければ下を実行して入り直す
# sudo usermod -aG dialout $USER
```

この PC の結果【試した】: カーネル `6.18.58.1-microsoft-standard-WSL2`。`CONFIG_USB_ACM=m`、`CONFIG_USBIP_VHCI_HCD=m`、`CONFIG_USB_SERIAL_CP210X=m`、`CONFIG_USB_SERIAL_CH341=m`。
つまり CDC ACM はモジュールとしてある。ボードをつないでいないので `/dev/ttyACM*` は無く、モジュールが自動で読み込まれるかは【未確認】（出ないときは `sudo modprobe cdc_acm`）。

### 3.3 書き込みで attach が外れる問題

- nRF52840 は書き込みのときブートローダーに入り直し、USB の機器としてつなぎ直される（ID も変わる）。WSL に渡した機器は「抜くと外れる」ので、**書き込みの途中で WSL から見えなくなる**ことがある【文書】から推した。実機では【未確認】。
- 避け方:
  1. **書き込みは Windows 側の Arduino IDE、WSL ではログ取りだけ**。いちばん確実。書き込む前に `usbipd detach`、終わったら `attach` し直す。
  2. `usbipd attach --wsl --busid 4-4 --auto-attach` で、つなぎ直されたら自動で渡し直させる。リリースノートに「WSL auto-attach の改善」(5.1.0)、未接続の機器を対象にする `--unplugged` (4.4.0) がある【文書】。ただし ID の変わったブートローダーの機器が bind 済み扱いになるか、間に合うかは【未確認】。`usbipd attach --help` で手元の版のオプションを確かめる。

---

## 4. つながったかの確かめ方

追加の道具なしで、pyserial に入っている端末を使う【試した: `--help` が起動することまで】。

```bash
uv run python -m serial.tools.miniterm /dev/ttyACM0 115200   # 抜けるのは Ctrl-]
```

`doc/protocol.md` の通りなら、`I <t_ms> <ax> <ay> <az> <gx> <gy> <gz>` の行が 100 Hz で流れる。`# ...` の行は知らせ（エラーなど）。
`S` と打って Enter で停止。実機での確認は【未確認】。
Windows 側で見るなら `uv run python -m serial.tools.miniterm COM3 115200`（COM 番号は読み替え）。

その後のログ取りは 03 章の `uv run python -m physlearn.link ...` を使う。

---

## 5. つまずきやすい所

| 症状 | 原因 | 対処 |
|---|---|---|
| コンパイルの最後で `python` や `adafruit-nrfutil` が無いと言われる | nRF52 のコアが書き込み用 zip を作るのに使う | `adafruit-nrfutil` を入れ、`python` で python3 が呼べるようにする（2.3） |
| コアを入れる途中で `no space left on device` | ツール一式で約 1 GB、MG24 はさらに約 620 MB。`/tmp` が RAM ディスク | 置き場（`directories.data`）を空きのある所にする |
| `usbipd bind` が失敗する | 管理者権限が要る | 管理者の PowerShell で実行 |
| `usbipd attach` で失敗、または WSL で見えない | WSL の VM が止まっている／カーネルが古い | WSL の端末を開いておく。`wsl --update` |
| 書き込みの途中で WSL からポートが消える | ブートローダーに入り直してつなぎ直される | 書き込みは Windows 側で（3.3） |
| `/dev/ttyACM0` が `Permission denied` | `dialout` グループに入っていない | `sudo usermod -aG dialout $USER` して入り直す |
| ボードがポートとして出ない | 充電専用のケーブル、またはスケッチが固まっている | データ用ケーブルにする。リセット 2 回でブートローダーへ（MG24 は PC1 を GND） |
| `Serial` が未定義と言われてコンパイルできない（別のコアや別のスケッチのとき） | Seeed wiki は非 mbed 版の USB シリアルに TinyUSB を勧めている。**今のスケッチ `xiao_imu_drive` は `#include <Adafruit_TinyUSB.h>` を入れておらず、非 mbed 版のコア 1.1.13 で CI のコンパイルが通る**（コアが TinyUSB を同梱し、`Serial` は何も足さずに使える）。この行が当たる条件は、別のコアの版や別のスケッチを使うとき【wiki が勧める条件は未確認】 | コアを 1.1.13 に揃える（2.3）。それでも出るときだけ `#include <Adafruit_TinyUSB.h>` を足す（Seeed wiki） |

---

## 6. SolidCraft（筐体の設計。任意）

筐体の設計に SolidCraft（solidcraft.io の OSS-CAD）を使うときの準備。GUI は Windows 側（ブラウザー版 https://solidcraft.io/app が主）、CLI と MCP は WSL に置く（発注者の決定 17:50 頃）。**手順の詳細・MCP の許可・worktree の注意は [cad-mcp.md](cad-mcp.md) が正**。ここは入れ方だけ。

CLI（v0.44.1、Linux x86_64）【試した: WSL2 で S042・S051 が、`CAD` ワークフローが GitHub Actions で】:

```bash
curl -sSfL -O https://github.com/tangency-labs/solidcraft/releases/download/v0.44.1/solidcraft-0.44.1-linux-x86_64.tar.gz
echo "164097743f6ff11c1eeb90a4313964728955e297689052053e4e5d8d20a64229  solidcraft-0.44.1-linux-x86_64.tar.gz" | sha256sum -c -   # 照合が通ってから展開する
mkdir -p ~/.local/opt ~/.local/bin && tar -xzf solidcraft-0.44.1-linux-x86_64.tar.gz -C ~/.local/opt   # 展開すると 469 MB
ln -s ~/.local/opt/solidcraft-0.44.1-linux-x86_64/bin/solidcraft-cli ~/.local/bin/solidcraft-cli
solidcraft-cli --version      # solidcraft-cli 0.44.1
```

- 置き場所は `~/.local/opt/`（展開した物）と `~/.local/bin/`（symlink、PATH に要る）。root・FUSE・GPU は要らない。GPU の無い WSL2 では `snapshot`・`gpu` は返らない。
- SHA-256 は公式の Release の資産の digest と `SHA256SUMS.txt` と手元の `sha256sum` の 3 つで一致した。版を上げるときは意識して上げ、`.github/workflows/cad.yml` の `SC_VERSION`・`SC_SHA256` と揃える。
- 動作の確認: `solidcraft-cli run cad/plate.json --out /tmp/plate.step`（STEP ができる）、`bash cad/check.sh <出力フォルダ>`（体積・質量・Izz が `cad/expected.csv` と合う。省略すると `cad-out/` に書く）、`uv run python -m physlearn.solidcraft_props <mass.json>`。ブラウザー版・GUI の操作は【未実行】。

MCP（Claude Code から設計させる）。**統括が 17:58 に登録済み**（local スコープ。`.mcp.json` は作っていない）:

```bash
claude mcp add solidcraft -- solidcraft-cli mcp --allow-path <リポジトリの根>/cad
claude mcp list      # solidcraft: ... - ✔ Connected
```

- `--allow-path` が無いと `cad/` が開けない（実測。cad-mcp.md の 4 節）。許可は main のチェックアウトの `cad/` の絶対パスだけで、**worktree の `cad/` は拒否される見込み**（推論。試していない）。
- ツールごとの許可は未設定。

---

## 7. 素の Linux と macOS

- **素の Linux**: 3 章は要らない。`/dev/ttyACM0` と `dialout` は同じ。ModemManager がポートをつかむことがある【未確認】。
- **macOS**: uv と arduino-cli は同じ手順。ポートは `/dev/cu.usbmodem*`、`dialout` は無い【未確認】。
