# PhysLearn

IMU を載せた Seeed Studio XIAO と小さな 2 輪車で、Physical AI の基本である **Sim2Real (S2R)** と **Real2Sim (R2S)** を学ぶリポジトリ。
教材（日本語）と Python のコード（sim・制御器・同定・ばらつき評価）、XIAO の Arduino スケッチを置いている。
課題は 1 つだけ: 「IMU のジャイロだけを見て、車体のヨー角速度を指令どおりにする」。

## できること・できないこと（2026-11-19 時点）

できる（この PC で確かめた）:

- numpy の sim で、R2S（ログから同定）→ S2R（ばらつきの下でゲインを決める）を 1 周回す（`physlearn loop-demo`）。試験は `uv run pytest` で 29 本が通る。
- MuJoCo 4.0.1 の車体モデルで同じ `Plant` を動かす（任意の依存）。
- XIAO nRF52840 Sense 向けのスケッチを arduino-cli でコンパイルする。

できない・確かめていない:

- **実機では何も動かしていない。** 部品はまだ手元に無い。IMU の軸の向き、PWM、ウォッチドッグ、USB シリアルはすべて未確認。
- XIAO MG24 Sense 向けは**未コンパイル**（ボードのコアを入れる容量が足りなかった）。
- **Isaac Sim / Isaac Lab は実行していない。** この PC は WSL2・GPU 無し・RAM 7 GiB で、要件に届かない。手引き（[90 章](doc/textbook/90-isaac-sim-guide.md)）だけを書いた。理由は [ADR-0001](doc/adr/0001-sim-stack.md)。
- エンコーダー、カメラ、ROS 2、強化学習は扱わない（[10 章 次の一歩](doc/textbook/10-next-steps.md)）。

## 最短の始め方

[uv](https://docs.astral.sh/uv/) を入れてから:

```bash
uv sync                    # MuJoCo も使うなら uv sync --extra mujoco
uv run pytest              # 29 passed
uv run physlearn loop-demo # 代役の実機で R2S → S2R を 1 周回す
```

`loop-demo` の出力（seed 0）の要点:

```text
[前 (公称の sim)] ... 代役で: 整定 0.47 s  行き過ぎ 3.3 %  定常偏差 0.085 rad/s  仕様 NG
代役のログから同定: {'gyro_bias': 0.08, ..., 'motor_tau': 0.196}
[後 (同定した sim)] ... 代役で: 整定 0.46 s  行き過ぎ 0.2 %  定常偏差 0.000 rad/s  仕様 OK
```

ほかのサブコマンドは `uv run physlearn --help`（`sim-log`・`sysid`・`eval`）。
環境構築の詳しい手順（arduino-cli、WSL2 で USB をつなぐ方法）は `doc/setup.md` に追加予定（S015）。
実機のログ取りは [03 章](doc/textbook/03-hardware-firmware.md) を見る。

## 買うもの

調査は JST 2026-11-19 13:35〜13:40 に取得した秋月電子とスイッチサイエンスの表示（税込・送料別）。価格と在庫はすぐ変わる。

| 案 | 中身 | 合計 |
| --- | --- | --- |
| (A) 最小 | XIAO nRF52840 Sense ＋ ピンヘッダー。IMU の雑音とバイアスを測る | 3,155 円 |
| (B) 車体込み | (A) ＋ Robo Base 2WD キット・DRV8835 モジュール・電池ボックス・ブレッドボード・ケーブル | 7,851 円 ＋ 単3 電池 4 本 |

- 第一候補のボードは **XIAO nRF52840 Sense**（IMU は LSM6DS3TR-C、技適あり）。
- **在庫が細い。** 取得時、秋月は残り 9 個（在庫僅少）、スイッチサイエンスは売り切れ。次点は XIAO MG24 Sense、在庫の保険は XIAO nRF54L15 Sense。
- モータードライバーは DRV8835（秋月 AE-DRV8835-S）。DRV8833 は秋月で見つからなかった。
- 品番・URL・理由は [doc/research/2026-11-19-hardware.md](doc/research/2026-11-19-hardware.md)。

## S2R と R2S の輪

```text
          R2S: 実機のログから同定して sim を直す
   ┌──────────────────────────────────────────────┐
   │                                              │
 [実機]  XIAO + IMU + 2 輪車   ──ログ CSV──▶  [同定 sysid]
   ▲                                              │ モーターの時定数・ゲイン・
   │                                              │ ジャイロのバイアス
   │                                              ▼
 [制御器 PI のゲイン]  ◀── ばらつきの下で評価 ──  [sim (numpy / MuJoCo)]
   │                         (eval)
   └──────────────────────────────────────────────┘
          S2R: sim で決めたゲインを実機へ
```

制御器は `src/physlearn/api.py` の `Command` / `Obs` / `Plant` だけを見る。sim も実機も `Plant` として差し替える。

## リポジトリの地図

| 場所 | 中身 |
| --- | --- |
| `src/physlearn/` | Python パッケージ（sim・制御器・同定・ばらつき・MuJoCo・シリアル接続・CLI） |
| `firmware/xiao_imu_drive/` | XIAO の Arduino スケッチ（IMU 100 Hz 送信、PWM、ウォッチドッグ） |
| `tests/` | pytest の試験 |
| `doc/textbook/` | 教材。入口は [doc/textbook/README.md](doc/textbook/README.md) |
| `doc/` | 計画・調査・設計判断・シリアルの取り決め。案内は [doc/README.md](doc/README.md) |
| `log/` | 作業記録・セッション記録・レビュー。[log/README.md](log/README.md) |

## 教材

[doc/textbook/README.md](doc/textbook/README.md) に章の一覧と読む順番がある。
実機が無くても、00 → 01 → 02 → 04 → 05 → 06 → 07 → 08 の順で sim だけで最後まで読める。

## 作業の進め方

- 1 つの作業（セッション）ごとに git worktree を切り、`feature/sNNN-<topic>` ブランチで作業する。main へは `--no-ff` でマージし、履歴をすべて残す。
- 作業記録は `log/work/`、伏せ字にしたセッション記録は `log/sessions/` に残す。
- 規約は [CLAUDE.md](CLAUDE.md)。計画とセッションの一覧は [doc/plan/2026-11-19-plan.md](doc/plan/2026-11-19-plan.md)。

## remote と CI

- いまは remote が無い。GitHub か GitLab は発注者が後で用意する。
- CI と push は、その用意ができたという知らせを待ってから設定する。それまでは手元の `uv run pytest` が検査のすべて。
