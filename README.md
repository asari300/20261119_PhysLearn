# PhysLearn

[![CI](https://github.com/asari300/20261119_PhysLearn/actions/workflows/ci.yml/badge.svg)](https://github.com/asari300/20261119_PhysLearn/actions/workflows/ci.yml) [![CAD](https://github.com/asari300/20261119_PhysLearn/actions/workflows/cad.yml/badge.svg)](https://github.com/asari300/20261119_PhysLearn/actions/workflows/cad.yml)

IMU を載せた Seeed Studio XIAO と小さな 2 輪車で、Physical AI の基本である **Sim2Real (S2R)** と **Real2Sim (R2S)** を学ぶリポジトリ。
教材（日本語）と Python のコード（sim・制御器・同定・ばらつき評価）、XIAO の Arduino スケッチを置いている。
課題は 1 つだけ: 「IMU のジャイロだけを見て、車体のヨー角速度を指令どおりにする」。

## できること・できないこと（2026-11-19 夜時点）

できる（この PC で確かめた）:

- numpy の sim で、R2S（ログから同定）→ S2R（ばらつきの下でゲインを決める）を 1 周回す（`physlearn loop-demo`）。試験は `uv run pytest` が通り、GitHub の CI（バッジ）でも通る。
- MuJoCo の車体モデルで同じ `Plant` を動かし、実機の代役にする（任意の依存。`loop-demo --real mujoco`）。式に無い現象（遅延・左右差・電池の低下など）を足した代役 `HardPlant` でも回す（`--real hard`、[15 章](doc/textbook/15-mismatch.md)）。
- 偽の XIAO（擬似端末の向こうでスケッチと同じ取り決めを話す）を相手に、実機と同じコマンドでログ取り → 同定 → 閉ループを通す（[12 章](doc/textbook/12-fake-xiao.md)）。実機の診断 `hwcheck` も偽物の相手に走らせた。
- XIAO nRF52840 Sense 向けのスケッチを、CI の arduino-cli でコンパイルする（必須の検査）。
- SolidCraft の CLI（v0.44.1）を WSL2 で動かし、`cad/` の設計データから STEP・質量特性・URDF を出して数字を確かめた。CI の `CAD` が同じ検査を回す（[手引き](doc/cad-mcp.md)）。MCP は登録済み。

できない・確かめていない:

- **実機では一度も動かしていない。** 部品はまだ手元に無い。「実機」の結果はすべて代役（隠しパラメータの sim・MuJoCo・偽の XIAO）のもの。
- XIAO MG24 Sense 向けは、CI でコンパイルは通った（落ちても全体は落とさない設定）。**動作は未確認**で、`printf` の浮動小数が入っておらず IMU の行の数値が空になる見込みがある（コードレビュー 3 巡目）。
- **Isaac Sim / Isaac Lab は実行していない**（WSL2・GPU 無し・RAM 7 GiB）。手引き（[90 章](doc/textbook/90-isaac-sim-guide.md)）だけ。理由は [ADR-0001](doc/adr/0001-sim-stack.md)。
- **SolidCraft の GUI とブラウザー版は誰も動かしていない。** MCP の登録はしたが、ツールごとの許可は未設定。
- **車体は Robo Base ミニ 2WD に決めたが、その寸法は未確認。** sim の寸法とモーター定数は**仮の値**（置き場は [cad/dimensions.csv](cad/dimensions.csv)）。
- 文書の根拠の監査は 6 巡（記録は [log/review/](log/review/)）。4 巡目は 89 件中 裏づけあり 59・誤り 3・断り書きの無い根拠なし 1、5 巡目は 77 件中 裏づけあり 62・誤り 6、6 巡目は 104 件中 裏づけあり 78・誤り 3・断り書きの無い根拠なし 1（テスターの 006P 電池の漏れ。直した）。コードレビューは 3 巡（指摘 9・7・7 件）。採否は各記録の表。
- 直っていない問題の一覧は [計画の「分かっている問題」](doc/plan/2026-11-19-plan.md#分かっている問題)（夜に更新済み。昼の 9 件のうち 8 件が閉じ、15 件を新しく足した）。

## 最短の道

[uv](https://docs.astral.sh/uv/) を入れてから。

**1. 実機なし（PC だけ）**

```bash
uv sync                    # MuJoCo と図も使うなら uv sync --extra mujoco --extra viz
uv run pytest              # 通ることを確かめる
uv run physlearn loop-demo # 代役の実機で R2S → S2R を 1 周回す
```

続きは教材の [00 章](doc/textbook/00-overview.md) から。`loop-demo` の出力（seed 0）の要点。通過率が 100 % → 42 % と下がるのは、同定で sim が現実に近づき、ばらつきの幅が広がって評価が厳しくなるため（[07 章](doc/textbook/07-loop.md)）:

```text
[前 (公称の sim)] tc=0.08  sim での通過率 100%  代役で: 整定 0.64 s  行き過ぎ 5.8 %  定常偏差 0.081 rad/s  仕様 NG
代役のログから同定: {'gyro_bias': 0.08, 'gyro_noise': 0.012, 'yaw_gain': 8.011, 'deadband': 0.15, 'motor_tau': 0.201, 'drift': 0.0}
[後 (同定した sim)] tc=0.2  sim での通過率 42%  代役で: 整定 0.51 s  行き過ぎ 0.1 %  定常偏差 0.001 rad/s  仕様 OK
```

**2. 部品が届く前に実機の手順を練習する**: [12 章 偽の XIAO](doc/textbook/12-fake-xiao.md)（`python -m physlearn.fakexiao`）。

**3. 実機が届いたら**: [doc/bringup.md](doc/bringup.md)（立ち上げ手順書。机上で書いたもので、実機では未確認）。先に [09 章 安全](doc/textbook/09-safety.md)。困ったら [つまずき集](doc/troubleshooting.md)（症状から引く）。

ほかの入口（どれも `--help` で使い方が出る）:

- `physlearn sim-log|sysid|eval|loop-demo`（`python -m physlearn …` でも同じ）: ログを書く・同定・ばらつきの下での評価・1 周（代役は `--plant`・`--real` に `hidden|mujoco|hard`）
- `python -m physlearn.link still|id|run|jog --port ...`: 実機とのシリアル接続（実機では未確認）
- `python -m physlearn.fakexiao`: 偽の XIAO（[12 章](doc/textbook/12-fake-xiao.md)）
- `python -m physlearn.imu still|turn|r2s`: IMU の実験（[11 章](doc/textbook/11-imu-lab.md)）
- `python -m physlearn.compare fit|holdout|spread`: 当てはまりの診断（[14 章](doc/textbook/14-fit-check.md)）
- `python -m physlearn.mismatch one|loop`: パラメータを合わせても残る差（[15 章](doc/textbook/15-mismatch.md)）
- `python -m physlearn.hwcheck stream|axes --port ...`: 実機の診断。流れの確認と軸の向きの割り出し（モーターは回さない。実機では未確認）
- `python -m physlearn.docs_check [章のファイル]`: 章に貼った出力を走らせ直して比べる（差があれば終了コード 1）
- `python -m physlearn.solidcraft_props mass.json`: SolidCraft の質量特性を SI にして読む（[cad-mcp](doc/cad-mcp.md)）
- `python -m physlearn.plot log|compare|still`: ログを図にする（`--extra viz`。[図の一覧](doc/textbook/fig/README.md)）

環境構築（arduino-cli、WSL2 で USB をつなぐ方法）は [doc/setup.md](doc/setup.md)。SolidCraft で筐体を設計する手引きは [doc/cad-mcp.md](doc/cad-mcp.md)。

## 買うもの

詳しい表は [発注リスト doc/shopping-list.md](doc/shopping-list.md)（JST 2026-11-19 17:55〜18:01 に秋月の商品ページを読んだ値。税込・送料別）。価格と在庫はすぐ変わる。

| 案 | 中身 | 合計 |
| --- | --- | --- |
| (A) 最小 | XIAO nRF52840 Sense ＋ USB ケーブル。IMU の雑音とバイアスを測る | 3,220 円 |
| (B) 車体込み | (A) ＋ Robo Base ミニキット 2WD（SKU 10530）・DRV8835 モジュール・電池ボックス・ブレッドボード・ケーブル・電池・テスター（と、その 006P 電池） | 7,603 円 |
| (C) 試し部品つき | (B) ＋ エンコーダー用の光センサー（次の一歩の試し） | 8,083 円 |

- 第一候補のボードは **XIAO nRF52840 Sense**（IMU は LSM6DS3TR-C、技適あり）。
- **在庫が細い。** 秋月の通販は残り 8 個（18:01。昼は 9 個）。次点は XIAO MG24 Sense（10/22 に値上がり）、在庫の保険は XIAO nRF54L15 Sense。スイッチサイエンスは商品ページが読めなかった（429）。
- 車体は、元の Robo Base キット 2WD（10708）が売り切れ（発注者が在庫数 0 を確認）のため、ミニキット 2WD に決めた。**ミニの商品ページは誰も読めておらず**、付属品と寸法は検索の要約。注文の前に確かめる点が 5 つ残っている（発注リストの冒頭）。
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
| `src/physlearn/` | Python パッケージ（sim・制御器・同定・ばらつき・MuJoCo・シリアル接続・診断・CLI） |
| `firmware/xiao_imu_drive/` | XIAO の Arduino スケッチ（IMU 100 Hz 送信、PWM、ウォッチドッグ） |
| `tests/` | pytest の試験 |
| `cad/` | 寸法の唯一の置き場 `dimensions.csv` と筐体の設計データ（SolidCraft。[cad/README.md](cad/README.md)） |
| `modelica/` | モーターの Modelica モデル（[13 章](doc/textbook/13-motor-physics.md)） |
| `doc/textbook/` | 教材。入口は [doc/textbook/README.md](doc/textbook/README.md) |
| `doc/` | 計画・調査・設計判断・手順書・取り決め。案内は [doc/README.md](doc/README.md) |
| `log/` | 作業記録・セッション記録・レビュー。[log/README.md](log/README.md) |

## 教材

[doc/textbook/README.md](doc/textbook/README.md) に章の一覧と読む順番がある。
00〜16 章・90 章・用語集・[解答集](doc/textbook/solutions.md)。実機が無くても、索引の「実機なしコース」で最後まで読める。

## 作業の進め方

- 1 つの作業（セッション）ごとに git worktree を切り、`feature/sNNN-<topic>` ブランチで作業する。main へは `--no-ff` でマージし、履歴をすべて残す。
- 作業記録は `log/work/`、伏せ字にしたセッション記録は `log/sessions/` に残す。
- 規約は [CLAUDE.md](CLAUDE.md)。計画とセッションの一覧は [doc/plan/2026-11-19-plan.md](doc/plan/2026-11-19-plan.md)。夜の展望と、発注者の決定の一覧は [doc/plan/2026-11-19-outlook-evening.md](doc/plan/2026-11-19-outlook-evening.md)。

## CI

GitHub Actions（[.github/workflows/](.github/workflows/)）。main への push と手動実行で動く。

- `CI`: 試験（`uv sync --locked` + `uv run pytest`）、スケッチのコンパイル（XIAO nRF52840 Sense、必須）、同（XIAO MG24 Sense、落ちても全体は落とさない）。初回（JST 18:14 に始まり、約 1 分）は全部成功した。
- `CAD`: SolidCraft の CLI で `cad/` の設計データを検査する。

## ライセンス

- コード（`src/`・`tests/`・`firmware/`・`modelica/`・`cad/`）は **MIT OR Apache-2.0**（どちらか好きなほう）。
- 文章と図（`doc/`・`README.md`・`log/`）は **CC BY 4.0**。
- 全文と範囲は [LICENSE.md](LICENSE.md)。第三者の資料（データシートや商品ページなど）の引用は、それぞれの権利者のもの。
