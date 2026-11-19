# S016 `s016-audit` の監査（Claude）

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s016-audit`（main 6bd11a2 から） |
| 対象 | main 6bd11a2 時点の文書: `doc/research/*.md`、`doc/adr/0001-sim-stack.md`、`doc/textbook/02・03・04・06・08`、`doc/protocol.md`、`firmware/xiao_imu_drive/xiao_imu_drive.ino`（00・90 章と `doc/physical_ai_isaacsim_poc_ja.md` は一部だけ） |
| レビュアー | Claude Opus 5.5（主）＋ 下請けの 1 体（software 調査と ADR の担当） |
| 依頼の文面 | 文書の事実の主張が、一次資料・実行結果・コードで裏づけられているかを監査する。直さない |
| 作業記録 | `log/work/2026-11-19-s016-audit.md` |

取り直しはすべて JST 2026-11-19 13:47〜13:52。Web は WebFetch / WebSearch（WebFetch は小さなモデルの要約を返すので、引用はその要約）。ローカルのソースは S005 が入れた arduino-cli 一式（Seeed_Arduino_LSM6DS3 2.0.8、Seeeduino nrf52 コア 1.1.13）を読んだ。

## 要約

見た主張 **63 件**（下の表の行を 1 件と数えた。複数の値をまとめた行もある）。

| 判定 | 件数 |
| --- | --- |
| 裏づけあり | 46（うち 00/poc の「矛盾ではない」2 件を含む） |
| 出典はあるが取り直せなかった | 5 |
| 出典が二次的・要約だけ | 5 |
| 根拠なし（断り書きあり） | 2 |
| 根拠なし（断り書き無し） | 0 |
| 誤り | 5 |

### 誤り（読者への害が大きい順）

| # | 文書:行 | 主張 | 正しい値・出典 | 直し方 |
| --- | --- | --- | --- | --- |
| 1 | `doc/research/2026-11-19-hardware.md:167` | 「ライブラリの既定は 0x6B なので、スケッチで 0x6A を明示しているのは必要」 | 半分だけ正しい。スケッチが使う `LSM6DS3` クラスの既定は **0x6A**（`LSM6DS3.h:149` `LSM6DS3(uint8_t busType = I2C_MODE, uint8_t inputArg = 0x6A)`）。0x6B は下位の `LSM6DS3Core` の既定（`LSM6DS3.cpp:59`、コメントも 0x6B）。S001/S005 の「既定は 0x6A」も S009 の「既定は 0x6B」も、どちらのクラスの話かを言わずに書いた食い違い。スケッチ `xiao_imu_drive.ino:28` は 0x6A を明示しているので動作には影響しない | 「`LSM6DS3` クラスの既定は 0x6A（`LSM6DS3Core` は 0x6B）。スケッチは 0x6A を明示しており、どちらでも同じ」に直す |
| 2 | `doc/research/2026-11-19-software.md:30` | LeRobot は 0.6.x（0.6.1、2026-08-03） | 最新は **0.7.0（2026-11-05）**。https://pypi.org/project/lerobot/ 13:48 | 0.7.0 に直す |
| 3 | `doc/research/2026-11-19-software.md:27` | Genesis は 1.2.1 以降（第三者で 1.3.3） | 最新は **1.4.7（2026-11-17）**。https://pypi.org/project/genesis-world/ 13:49 | 1.4.7 に直す |
| 4 | `doc/research/2026-11-19-software.md:25` | MJWarp は 3.5.0 / 3.7.0 で「正式リリース」 | 正式リリースは 3.5.0（2026-02-12）だけ。出典は changelog の検索要約（原文は読めていない） | 「3.5.0 で正式リリース」に直す |
| 5 | `doc/research/2026-11-19-hardware.md:54` | スイッチサイエンス 8146 の行を「確認（13:36）」 | 値（3,069 円・売り切れ）は 13:50 に取り直して一致したが、同じ文書の 5 行目は「スイッチサイエンスは 429 で直接読めなかった」と書いており、種別の記載が自己矛盾 | 54 行目の種別を、実際に読めたなら 5 行目の断りを「8146 だけは読めた」に直す |

### 根拠なし（断り書き無し）

なし。推測・記憶の主張は、どれも本文で「推測」「記憶」「【未確認】」と断ってあった。

### 読者に伝えたい補足（誤りではない）

- **I2C アドレス 0x6A は実物と合う見込みが高い**: Zephyr の基板定義 `boards/seeed/xiao_ble/xiao_ble_nrf52840_sense.dts` が IMU を `i2c0` の `reg = <0x6a>`、電源を `gpio1 8`（P1.08）で定義（https://raw.githubusercontent.com/zephyrproject-rtos/zephyr/main/boards/seeed/xiao_ble/xiao_ble_nrf52840_sense.dts 13:49）。コアの `variant.cpp` でも D15 = P1.08 (6D_PWR)。ライブラリ 2.0.8 の例 6 本はすべて `LSM6DS3 (I2C_MODE, 0x6A)`。ただし **Seeed の回路図の SA0 は見ていない**（Seeed wiki の IMU ページにアドレスの記載なし、13:48）。
- **IMU のバス選び**: ライブラリは `TARGET_SEEED_XIAO_NRF52840_SENSE` が定義されたとき `Wire` を `Wire1` に置き換える（`LSM6DS3.cpp:35-37`）。非 mbed のコア 1.1.13 の `variant.h:4` がこのマクロを定義しているので、IMU 用の `Wire1`（SDA 17・SCL 16）が使われる。`Wire1` 自体はコアの `Wire_nRF52.cpp:431` で定義。整合している。
- 02 章 104 行の「`imu.settings.gyroRange` を `begin()` の前に設定」は、コンストラクタが `settings` を既定値で埋めるので（`LSM6DS3.cpp:368-377`）正しい。

## 文書ごとの表

### `doc/research/2026-11-19-hardware.md`（最優先）

| 行 | 主張 | 判定 | 根拠 |
| --- | --- | --- | --- |
| 13, 97 | BOM (A) 3,120 + 35 = 3,155 円 | 裏づけあり | 検算で一致 |
| 13, 111 | BOM (B) 3,155 + 3,366 + 550 + 170 + 450 + 160 = 7,851 円 | 裏づけあり | 検算で一致。ただし 3,366 円の Robo Base は「検索抜粋」（70 行）で、合計の 4 割強が直読していない値 |
| 9, 53 | 秋月 117342 税込 3,120 円・在庫僅少・通販 9 個 | 裏づけあり | https://akizukidenshi.com/catalog/g/g117342/ 13:49（同じ値。店頭は秋葉原 0・八潮 3） |
| 38, 120 | 技適 211-220207 | 裏づけあり | 同上 |
| 54 | スイッチサイエンス 8146 3,069 円・売り切れ | 裏づけあり（記載は自己矛盾、誤り #5） | https://www.switch-science.com/products/8146 13:50 |
| 74, 107 | AE-DRV8835-S 550 円・在庫僅少・通販 139 | 裏づけあり | https://akizukidenshi.com/catalog/g/g109848/ 13:49（店頭は 0） |
| 85 | DRV8835 モーター 2〜11 V、ロジック 2〜7 V、1.5 A/ch | 裏づけあり | 同上。秋月の仕様表は電源 min 0 V（TI の VM 0〜11 V と同じ） |
| 77, 108 | 電池ボックス 単3×4 フタ・スイッチ付 170 円・在庫あり | 裏づけあり | https://akizukidenshi.com/catalog/g/g100311/ 13:50 |
| 10, 56 / 11, 57 / 59 / 72-73 / 78-80 | MG24・nRF54L15・ESP32S3 Sense・タミヤ・EIC-801・ケーブル・ピンヘッダーの価格と在庫 | 出典はあるが取り直せなかった（時間切れ） | 本文の取得時刻は 13:35〜13:37 |
| 70-71, 76 | Robo Base 3,366 円・Mini 1,958 円・SS の DRV8835 880 円 | 出典が二次的（本文が「検索抜粋」と断り） | — |
| 33 | variant.h の `PIN_LSM6DS3TR_C_POWER (15)`、`PIN_WIRE1_SDA (17)`、`SCL (16)`、`INT1 (18)` | 裏づけあり | コア 1.1.13 `variants/Seeed_XIAO_nRF52840_Sense/variant.h:116-119` |
| 34, 157 | I2C アドレス 0x6A（推測） | 断り書きあり → 今は裏づけあり（二次） | Zephyr DTS `reg = <0x6a>`、ライブラリの例。回路図は未見 |
| 167 | 「ライブラリの既定は 0x6B」 | 誤り #1 | `LSM6DS3.h:149` |
| 168 | `beginCore()` が電源ピンを HIGH | 裏づけあり | `LSM6DS3.cpp:72-84`（`#ifdef PIN_LSM6DS3TR_C_POWER`、10 ms 待つ） |
| 162-165 | DRV8835 の IN/IN 真理値表・VCC 2〜7 V・VM 0〜11 V・PWM 0〜250 kHz | 出典はあるが取り直せなかった | TI の PDF は時間内に取り直していない。スケッチ 36 行の表とは一致 |
| 169 | analogWrite 既定 8 bit・16 MHz・COUNTERTOP 255 で約 62.7 kHz | 裏づけあり | `HardwarePWM.cpp:94,104`。16 MHz / 255 = 62.75 kHz |
| 170 | D0〜D3 = ピン 0〜3 | 裏づけあり | `variant.h:46` 付近、`variant.cpp` の対応表 |
| 143-147 | 単3×4 が 6 V を超えうる、TT モーター 3〜6 V、起動直後のピン不定 | 根拠なし（断り書きあり） | — |
| 12, 17-26 | IMU 内蔵の XIAO は Sense の 4 種、ESP32 系に IMU 無し | 出典はあるが取り直せなかった | 比較表を取り直していない |

### `doc/research/2026-11-19-software.md` と `doc/adr/0001-sim-stack.md`（下請けの監査、17 件）

| 文書:行 | 主張 | 判定 | 根拠（取得 13:47〜13:49） |
| --- | --- | --- | --- |
| R:11,19 / A:10 | Isaac Sim 6.2 の要件（Ubuntu 22.04/24.04・Win 11、RAM 32 GB、RTX 4080 16 GB、Linux ドライバー 595.58.03、A100/H100 非対応、22.04 非推奨） | 裏づけあり | https://docs.isaacsim.omniverse.nvidia.com/6.2.0/installation/requirements.html 。原文の区分は Minimum / Good / Ideal（「推奨」は Good） |
| R:11,45 / A:10 | WSL2 は要件ページに記載なし | 裏づけあり | 同上 |
| R:45 / A:10 | 「NVIDIA 職員」が WSL2 上のコンテナは非対応と回答 | 出典が二次的 | https://forums.developer.nvidia.com/t/is-it-possible-to-run-isaac-sim-in-wsl2/349609 （回答者 VickNV、2025-10-31。役職の表示なし、6.2 より前） |
| R:20 | Isaac Sim は Apache-2.0、初回ビルドで Omniverse の規約に同意 | 裏づけあり（断り書きあり） | https://github.com/isaac-sim/IsaacSim |
| R:21 | Isaac Lab v3.0.0 は Isaac Sim 6.2・Newton 1.6.1 対応 | 裏づけあり | https://github.com/isaac-sim/IsaacLab/releases （年の表示なし） |
| R:22 | Newton: Apache-2.0、Py 3.11 以上、R580 以上、macOS は CPU のみ | 裏づけあり | https://github.com/newton-physics/newton （「Linux/Windows の CPU 実行は明記なし」は README に `--device cpu` の例あり、軽微） |
| R:10,23,42 / A:12 | MuJoCo 4.0.1（2026-11-11）、import できる | 裏づけあり | changelog https://mujoco.readthedocs.io/en/latest/changelog.html 、ローカルで `mujoco.__version__` = 4.0.1 |
| R:23 / A:12,27 | 4.0 の変更点（mujoco-core 分割、Py3.10 削除、cable/composite 削除 ほか） | 裏づけあり | 同 changelog（「flex の弾性定数」は原文では rod の曲げ・ねじれ。言い直すとよい） |
| R:24 / A:13 | MJX の JAX 版・Warp 版、単一シーンで最大 10 倍遅い | 裏づけあり | https://mujoco.readthedocs.io/en/latest/mjx.html （遅いのは MJX-JAX） |
| R:25 | MJWarp 3.5.0 / 3.7.0 で正式 | 誤り #4 | — |
| R:25 | MJWarp は Newton の一部として保守 | 出典が二次的 | https://mujoco.readthedocs.io/en/latest/mjwarp/ は共同保守とだけ書く |
| R:28 | ROS 2 Lyrical LTS 2026-05-22 GA | 出典はあるが取り直せなかった | docs.ros.org がアクセス拒否。https://endoflife.date/ros-2 とは一致 |
| R:28 | Kilted の EOL | 出典が二次的 | endoflife.date では 2026-12-31 |
| R:29 | micro_ros_platformio に lyrical 無し、XIAO・nRF52・MG24 無し | 裏づけあり | https://github.com/micro-ROS/micro_ros_platformio |
| R:30 | LeRobot 0.6.1 | 誤り #2 | — |
| R:27 | Genesis 1.2.1 / 1.3.3 | 誤り #3 | — |
| R:51 / A:26 | Brev の見積もり L4 $0.17/h・A10G $1.01/h・A10 $0.60/h | 裏づけあり | https://www.nvidia.com/en-us/launchables/pricing （A10 は Lambda Labs） |
| R:51 | 公式に「コンテナでローカルか Brev ほか」 | 裏づけあり | https://docs.isaacsim.omniverse.nvidia.com/6.2.0/installation/install_cloud.html |

ADR 0001 の決定を変える事実の誤りは無かった。

### `doc/textbook/02-imu.md`・`03-hardware-firmware.md`・`doc/protocol.md`・スケッチ

| 文書:行 | 主張 | 判定 | 根拠 |
| --- | --- | --- | --- |
| ino:28 | `LSM6DS3 imu(I2C_MODE, 0x6A)` で初期化 | 裏づけあり（コード） | Zephyr DTS の 0x6a と一致。回路図は未見 |
| ino:5-6 | `begin()` が電源ピンを HIGH | 裏づけあり | `LSM6DS3.cpp:72-84` |
| 02:61-74 | 加速度 0.061/0.122/0.244/0.488 mg/LSB、角速度 4.375〜70 mdps/LSB | 裏づけあり（ライブラリの式） | `calcAccel` = raw×0.061×(範囲/2)、`calcGyro` = raw×4.375×(範囲/125)（`LSM6DS3.cpp:671-738`）。データシート本体は取り直していない（本文も 80 行で【未確認】と断り） |
| 02:84-87, protocol:35 | 既定 ±16 g・±2000 dps・416 Hz | 裏づけあり | `LSM6DS3.cpp:368-377` |
| 02:95-96 | 換算式（±2 g・±245 dps の例） | 裏づけあり | 上の式と一致 |
| 02:89, protocol:35 | g×9.80665、dps×π/180 | 裏づけあり | `ino:26,92-93` |
| 03:55-61, protocol:22 | D0〜D3 → AIN1/AIN2/BIN1/BIN2、MODE=GND、duty の向き | 裏づけあり（コード） | `ino:16-17, 35-42` と一致 |
| 03:63, protocol:22 | DRV8835 の範囲、IN/IN、fast decay | 出典はあるが取り直せなかった（TI PDF） | 秋月ページの電圧範囲とは一致 |
| 03:70, protocol:22 | PWM 8 bit・約 62.7 kHz | 裏づけあり | `HardwarePWM.cpp:94,104` |
| 03:71 | AE-DRV8835-S のピンの並び【未確認】 | 断り書きあり | 秋月ページにも並びの記載なし（13:49）。配線前に確かめる必要は残る |

### `doc/textbook/04〜08`（式と説明だけ。数値の一致は見ない）

| 文書:行 | 主張 | 判定 | 根拠 |
| --- | --- | --- | --- |
| 04:31,37 | 一次遅れ τ dω/dt = ω_ref − ω と厳密な離散化 | 裏づけあり | `sim.py:61` |
| 04:43-44 | v = r(ω_R+ω_L)/2、ψ' = r(ω_R−ω_L)/b | 裏づけあり | `sim.py:67,72` |
| 04:50,53 | K_yaw = 2 r K_m / b = 12 rad/s | 裏づけあり | `sim.py:35`。2×0.016×30/0.08 = 12 |
| 04:50 | ψ'_ss = K_yaw (u − d) | 裏づけあり | `sim.py:54` の不感帯の形 |
| 06:13-14 | 整定時間（±5% に入ったきり）、行き過ぎ (max−目標)/目標 | 裏づけあり | `control.py:91-99` |
| 06:29-31 | PI の式、積分を ±1 で止める、left=−u・right=+u | 裏づけあり | `control.py:27-34` |
| control.py:37-40（05/06 章が使う） | PI の零点で極を消し閉ループ 1/(tc s+1) | 裏づけあり（式を手で確かめた） | kp=τ/(K tc)、ki=1/(K tc) で C·P = 1/(tc s) |
| 08:44 | timestep 0.002、dt 0.01 で 5 回 | 裏づけあり | `diffdrive.xml:12` |
| 08:50,54 | 車輪半径 0.03 m・トレッド 0.10 m、トルク = 0.05 duty − (0.05/30) ω | 裏づけあり | `diffdrive.xml:27-41`（biasprm 0.0016667 = 0.05/30） |
| 08:50 | hinge 軸 +y で正回転が前進 | 裏づけあり（右手系で手計算） | 軸 (0,1,0) で接地点の速度が −x になり車体は +x |
| 08:85 | 定常 15 rad/s・0.45 m/s・gz 9.0 rad/s の見積もり | 裏づけあり | 0.05×0.5/(0.05/30) = 15、15×0.03 = 0.45、2×0.45/0.10 = 9.0 |
| 08:48 | condim は大きい方、priority で上書き | 出典が二次的（本文に出典なし） | MuJoCo の文書を今日は取り直していない |

### `doc/textbook/00・90` と `doc/physical_ai_isaacsim_poc_ja.md`（浅く）

| 文書:行 | 主張 | 判定 | 根拠 |
| --- | --- | --- | --- |
| 00:108 | BOM 3,155 円・7,851 円 | 裏づけあり | 調査文書と一致、検算済み |
| 90:10-16 | Isaac Sim 6.2 の要件表 | 裏づけあり | 下請けが要件ページで確認（上表 R:11,19） |
| poc:20,131 と software 調査 | poc（10 月）は「最新 6.1.0」、今日は 6.2 | 矛盾ではない | poc の時点でも要件ページの URL は 6.2.0 を指しており、要件の数値（RTX 4080・16 GB・32 GB）は今日と同じ |
| poc:17 と今日の方針 | poc はエンコーダー付きシャーシ＋ESP32 を挙げ、今日は XIAO nRF52840 Sense＋エンコーダー無し | 方針の変更（事実の矛盾ではない） | hardware 調査 12 行が「ESP32 系に IMU 内蔵は無い」と理由を書いている |

## 監査できなかった範囲

- `doc/textbook/00-overview.md`・`01-s2r-r2s.md`・`09-safety.md`・`10-next-steps.md`・`glossary.md` の年次の動向・手法の説明（未着手）。
- TI の DRV8835 データシート（SLVSB18H）と ST の LSM6DS3TR-C データシートの取り直し（±245 か ±250 かを含む）。
- Seeed の XIAO nRF52840 Sense の回路図（SA0 の接続）。
- 秋月の MG24・nRF54L15・タミヤ・小物の価格と在庫の取り直し、Seeed の比較表。
- AE-DRV8835-S の 12 ピンの並び（秋月の説明書の図）。
- docs.ros.org（アクセス拒否）、arXiv の総説、AWS G6e と GCP の価格。
- 04〜08 章の「実際に走らせた出力」の数値（S008 が書き換え中のため対象外）。
- 05・07 章（同期・同定）は式を見ていない。
