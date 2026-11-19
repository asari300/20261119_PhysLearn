# PhysLearn

IMU を載せた Seeed Studio XIAO と小さな 2 輪車で、Physical AI の基本である **Sim2Real (S2R)** と **Real2Sim (R2S)** を学ぶリポジトリ。
教材（日本語）と Python のコード（sim・制御器・同定・ばらつき評価）、XIAO の Arduino スケッチを置いている。
課題は 1 つだけ: 「IMU のジャイロだけを見て、車体のヨー角速度を指令どおりにする」。

## できること・できないこと（2026-11-19 時点）

できる（この PC で確かめた）:

- numpy の sim で、R2S（ログから同定）→ S2R（ばらつきの下でゲインを決める）を 1 周回す（`physlearn loop-demo`）。試験は `uv run pytest` が通る。
- MuJoCo の車体モデルで同じ `Plant` を動かし、実機の代役にする（任意の依存。`loop-demo --real mujoco`）。
- 偽の XIAO（擬似端末の向こうでスケッチと同じ取り決めを話す）を相手に、実機と同じコマンドでログ取り → 同定 → 閉ループを通す（[12 章](doc/textbook/12-fake-xiao.md)）。
- XIAO nRF52840 Sense 向けのスケッチを arduino-cli でコンパイルする。

できない・確かめていない:

- **実機では一度も動かしていない。** 部品はまだ手元に無い。「実機」の結果はすべて代役（隠しパラメータの sim・MuJoCo・偽の XIAO）のもの。
- XIAO MG24 Sense 向けは**未コンパイル**。
- **Isaac Sim / Isaac Lab は実行していない**（WSL2・GPU 無し・RAM 7 GiB）。手引き（[90 章](doc/textbook/90-isaac-sim-guide.md)）だけ。理由は [ADR-0001](doc/adr/0001-sim-stack.md)。
- **SolidCraft は一度も動かしていない。** 本家と版（`tangency-labs/solidcraft` v0.44.1）、`cad/plate.json` が公式のコマンド表と一致することは監査 2 巡目が一次資料で裏づけた。公式の CLI を落として動かす作業は、この環境の権限の判定で止められ、発注者の許可待ち。
- モーター定数と車体の寸法は**仮の値**。寸法の置き場は [cad/dimensions.csv](cad/dimensions.csv)。
- 文書の根拠の監査: 1 巡目は 63 件中 誤り 5（直し済み）、2 巡目は 53 件中 裏づけあり 37・誤り 2（直し中）、3 巡目（配線・電圧まわり）は作業中。記録は [log/review/](log/review/)。
- 直っていない問題の一覧は [計画の「分かっている問題」](doc/plan/2026-11-19-plan.md#分かっている問題)。

## 最短の道

[uv](https://docs.astral.sh/uv/) を入れてから。

**1. 実機なし（PC だけ）**

```bash
uv sync                    # MuJoCo と図も使うなら uv sync --extra mujoco --extra viz
uv run pytest              # 通ることを確かめる
uv run physlearn loop-demo # 代役の実機で R2S → S2R を 1 周回す
```

続きは教材の [00 章](doc/textbook/00-overview.md) から。`loop-demo` の出力（seed 0）の要点:

```text
[前 (公称の sim)] tc=0.08  sim での通過率 100%  代役で: 整定 0.64 s  行き過ぎ 5.8 %  定常偏差 0.081 rad/s  仕様 NG
代役のログから同定: {'gyro_bias': 0.08, 'gyro_noise': 0.012, 'yaw_gain': 7.867, 'deadband': 0.15, 'motor_tau': 0.196}
[後 (同定した sim)] tc=0.2  sim での通過率 68%  代役で: 整定 0.50 s  行き過ぎ 0.1 %  定常偏差 0.001 rad/s  仕様 OK
```

**2. 部品が届く前に実機の手順を練習する**: [12 章 偽の XIAO](doc/textbook/12-fake-xiao.md)（`python -m physlearn.fakexiao`）。

**3. 実機が届いたら**: [doc/bringup.md](doc/bringup.md)（立ち上げ手順書。机上で書いたもので、実機では未確認）。先に [09 章 安全](doc/textbook/09-safety.md)。

ほかの入口（どれも `--help` で使い方が出る）:

- `physlearn sim-log|sysid|eval|loop-demo`: ログを書く・同定・ばらつきの下での評価・1 周
- `python -m physlearn.link still|id|run|jog --port ...`: 実機とのシリアル接続（実機では未確認）
- `python -m physlearn.fakexiao`: 偽の XIAO（[12 章](doc/textbook/12-fake-xiao.md)）
- `python -m physlearn.imu still|turn|r2s`: IMU の実験（[11 章](doc/textbook/11-imu-lab.md)）
- `python -m physlearn.compare fit|holdout|spread`: 当てはまりの診断（[14 章](doc/textbook/14-fit-check.md)）
- `python -m physlearn.mismatch one|loop`: パラメータを合わせても残る差（[15 章](doc/textbook/15-mismatch.md)）
- `python -m physlearn.plot log|compare|still`: ログを図にする（`--extra viz`。[図の一覧](doc/textbook/fig/README.md)）

環境構築（arduino-cli、WSL2 で USB をつなぐ方法）は [doc/setup.md](doc/setup.md)。

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
| `cad/` | 寸法の唯一の置き場 `dimensions.csv` と筐体の設計データ |
| `modelica/` | モーターの Modelica モデル（[13 章](doc/textbook/13-motor-physics.md)） |
| `doc/textbook/` | 教材。入口は [doc/textbook/README.md](doc/textbook/README.md) |
| `doc/` | 計画・調査・設計判断・シリアルの取り決め。案内は [doc/README.md](doc/README.md) |
| `log/` | 作業記録・セッション記録・レビュー。[log/README.md](log/README.md) |

## 教材

[doc/textbook/README.md](doc/textbook/README.md) に章の一覧と読む順番がある。
00〜16 章・90 章・用語集・[解答集](doc/textbook/solutions.md)。実機が無くても、索引の「実機なしコース」で最後まで読める。

## 作業の進め方

- 1 つの作業（セッション）ごとに git worktree を切り、`feature/sNNN-<topic>` ブランチで作業する。main へは `--no-ff` でマージし、履歴をすべて残す。
- 作業記録は `log/work/`、伏せ字にしたセッション記録は `log/sessions/` に残す。
- 規約は [CLAUDE.md](CLAUDE.md)。計画とセッションの一覧は [doc/plan/2026-11-19-plan.md](doc/plan/2026-11-19-plan.md)。

## remote と CI

- いまは remote が無い。GitHub か GitLab は発注者が後で用意する。
- CI と push は、その用意ができたという知らせを待ってから設定する。それまでは手元の `uv run pytest` が検査のすべて。
