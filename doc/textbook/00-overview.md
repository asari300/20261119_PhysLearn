# 00. 全体の地図

## この章でわかること

- Physical AI という言葉が何を指すか。2026 年の時点でどう語られているか。
- この教材がその中の、どの小さな一部を扱うか。
- 作るもの、章の順番、所要時間の目安、必要なもの。

## Physical AI とは

Physical AI は、AI を画面の中から物理の世界へ出す取り組みの総称です。
ロボットが周りを感じ取り、判断し、体を動かして働きかけます。
NVIDIA は 2026 年 4 月の記事で、これを「AI を物理の世界へ持ち込む」こととして書いています。
そこでは、ロボットが複雑な環境で知覚し、推論し、行動すると説明されています [1]。

2026 年の動きを少しだけ挙げます（取得は下の出典の時刻）。

- NVIDIA は 2026-10-21 の GTC Berlin で、ロボット開発基盤 Isaac の拡張を発表しました。人型ロボットの参照機や、新しいデータセット、シミュレーションの流れが含まれます [2]。
- 同じ発表を伝えた報道もあります [3]。また 2026 年 4 月の NVIDIA の記事には、Isaac Sim 6.0 や Isaac Lab 3.0 が出てきます [1]。2026-11-19 の調査では、現行は Isaac Sim 6.2・Isaac Lab 3.0.0 です（`doc/research/2026-11-19-software.md`）。Isaac Lab はロボットの方策（制御のしかた）を sim で学習させるための道具です。
- 2026 年 4 月の NVIDIA の記事では、sim で学んだ振る舞いが実世界へどれだけ移るかを測る取り組みが紹介されています [1]。

大きな会社が大きなモデルと人型ロボットに取り組んでいます。
しかし、その足元には昔からの問いがあります。
**「sim で動いたものが、実機でも同じように動くか」** という問いです。

## この教材が扱うもの

この教材は、大きなモデルも人型ロボットも扱いません。
扱うのは、その足元の芯だけです。

> sim と実機の差を測って、縮める。

題材は小さな車です。

- Seeed XIAO（IMU LSM6DS3TR-C を内蔵したもの。第一候補は XIAO nRF52840 Sense、モータードライバーは DRV8835。`doc/research/2026-11-19-hardware.md`）を載せた、2 輪差動の車体。
- 観測は IMU だけ。エンコーダー（車輪の回転を数える部品）は使いません。
- 課題は「ヨー角速度（上から見て、くるっと回る速さ）を目標値に追従させる」。

この小さな課題でも、Physical AI で起きる問題の多くがそのまま出てきます。
モーターの遅れ、電池の電圧、床の摩擦、センサーのくせ、通信の遅延です。

## 全体の図

```text
            ┌────────────────────────────────────────┐
            │ 制御器（PC 上の Python）                 │
            │  Obs を受けて Command を返す             │
            └───────────────┬────────────────────────┘
                            │  Command（左右の duty -1..1）
                            │  Obs（加速度・角速度）
              ┌─────────────┴──────────────┐
              │        Plant の境界         │
       ┌──────▼───────┐             ┌──────▼───────┐
       │ V-World      │             │ R-World      │
       │ numpy の sim │             │ XIAO + 車体  │
       │ (MuJoCo 任意)│             │ USB シリアル │
       └──────┬───────┘             └──────┬───────┘
              │  sim のログ               │ 実機のログ（CSV）
              └─────────────┬──────────────┘
                            ▼
            ┌────────────────────────────────────────┐
            │ 比べる・同定する（R2S）                  │
            │ ばらつかせて確かめる（S2R）              │
            └────────────────────────────────────────┘
```

V-World は仮想の世界（sim）、R-World は実の世界（実機）です。
この呼び方は PoC 設計書から引き継いだ、この教材だけの呼び名です。製品の機能名ではありません。

制御器は、相手が sim か実機かを知りません。
`src/physlearn/api.py` の `Plant` という約束（`reset` と `step` の 2 つ）だけを見ます。
詳しくは 01 章で説明します。

## 章の地図と学ぶ順番

| 章 | 内容 | 目安 |
|---|---|---|
| 00 | この章 | 15 分 |
| 01 | S2R と R2S の考え方 | 45 分 |
| 02 | IMU の基礎 | 45 分 |
| 03 | 部品・配線・XIAO のスケッチ・ログ取り（`python -m physlearn.link`） | 2〜4 時間（組み立て込み） |
| 04 | numpy の sim | 1〜2 時間 |
| 05 | ログから同定する（`physlearn sysid`） | 1 時間 |
| 06 | ばらつきの下でゲインを決めて実機へ | 1〜2 時間 |
| 07 | 1 周を回す（`physlearn loop-demo`） | 1 時間 |
| 08 | MuJoCo の車体モデル（任意） | 1〜2 時間 |
| 09 | 安全 | 30 分（実機を動かす前に必ず） |
| 10 | 次の一歩 | 20 分 |
| 90 | Isaac Sim へ進む手引き | 読むだけ |
| glossary | 用語集 | 引くたびに |

所要時間は推測による目安です。人と環境で大きく変わります。

おすすめの順番は次のとおりです。

1. 00 → 01 → 02 で考え方をつかむ。
2. **実機を動かす前に 09 を読む。**
3. 03 で実機を組み、ログを取る。
4. 04 → 05 → 06 → 07 で輪を 1 周回す。
5. 余力があれば 08、そして 10 と 90。

実機がまだ手元に無ければ、04 から先に進んでもかまいません。sim だけでも輪の考え方は試せます。

## 必要なもの

- PC。**GPU は無くてよい。** この教材の sim は numpy で動きます。MuJoCo は任意です。
- Python と、このリポジトリ（依存は numpy・pyserial、任意で mujoco 4.0.1 以上。`uv sync --extra mujoco`）。
- 実機の部品（XIAO、車体、モータードライバー、電池など）。一覧と価格は 03 章と `doc/research/2026-11-19-hardware.md` を見てください（BOM の案は、最小 3,155 円、車体込み 7,851 円）。
- USB ケーブル。
- 机の上の小さな台（車輪を浮かせて試すため。09 章）。

Isaac Sim は GPU が必要なので、この教材では動かしません。90 章で手引きだけを書きます。

## 演習

1. 身の回りで「画面の中で作って、実物で動かす」ものを 1 つ挙げてください。sim と実物の差は何から生まれそうですか。
   - 手がかり: 重さ、摩擦、電池の減り、遅れ、センサーの雑音。
2. 上の図で、制御器が「相手が sim か実機か」を知らなくてよいのはなぜですか。
   - 手がかり: 制御器が見ているのは `Command` と `Obs` という型だけです。
3. この教材がエンコーダーを使わないことで、何が測れなくなるでしょうか。
   - 手がかり: 02 章の最後で答え合わせをします（位置と車輪の速さ）。

## 出典

取得: JST 2026-11-19 13:35〜13:40 ごろ。

1. NVIDIA Blog, "National Robotics Week — Latest Physical AI Research, Breakthroughs and Resources"（2026-04-10）. https://blogs.nvidia.com/blog/national-robotics-week-2026/ （本文を取得して確認）
2. NVIDIA Newsroom, "NVIDIA Advances Isaac Platform for General-Purpose Robotics With New Reference Humanoid, Frameworks, Simulation Pipelines and Data". https://nvidianews.nvidia.com/news/nvidia-advances-isaac-platform-for-general-purpose-robotics-with-new-reference-humanoid-frameworks-simulation-pipelines-and-data （検索結果の見出しと要約で確認。本文は未確認）
3. StorageNewsletter, "NVIDIA GTC Berlin 2026: NVIDIA Advances Isaac Platform …"（2026-10-21）. https://www.storagenewsletter.com/2026/10/21/nvidia-gtc-berlin-2026-nvidia-advances-isaac-platform-for-general-purpose-robotics-with-new-reference-humanoid-frameworks-simulation-pipelines-and-data/ （検索結果の要約で確認。本文は未確認）

## 次の章

[01. S2R と R2S の考え方](01-s2r-r2s.md)
