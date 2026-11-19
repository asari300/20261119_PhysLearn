# ADR 0001: sim の構成（numpy 必須・MuJoCo 任意・Isaac Sim は手引きだけ）

- 状態: 採用（2026-11-19、S002）
- 根拠: [../research/2026-11-19-software.md](../research/2026-11-19-software.md)（JST 2026-11-19 13:35〜13:40 取得）

## 背景

- 2026-10-22 の PoC 設計書（[../physical_ai_isaacsim_poc_ja.md](../physical_ai_isaacsim_poc_ja.md)）は Isaac Sim を V-World の中心に置いていた。
- しかし作業する PC は WSL2・GPU 無し・RAM 7 GiB。
- Isaac Sim 6.2 の要件は最小で RTX 4080 (VRAM 16GB)・RAM 32GB、RT コアのある NVIDIA GPU が必須。WSL2 は要件ページに記載がなく、NVIDIA 職員はフォーラムで非対応と答えている。
- 課題は「IMU だけを見て、差動 2 輪のヨー角速度を指令どおりにする」。必要な物理はモーターの 1 次遅れと車体の回転くらいで、接触や見た目の再現は要らない。
- MuJoCo 4.0.1（2026-11-11）は CPU で動き、この PC で import と 10,000 step（0.038 秒）を確かめた。4.0 から `mujoco-core` は numpy だけに依存する。
- MJX / MuJoCo Warp / Newton / Isaac Lab は GPU で多数の環境を並列に回す道具で、単一の小さな sim では CPU の MuJoCo より速くならない（MJX の文書は最大 10 倍遅いと書く）。

## 決定

1. **numpy の sim を必須**とする。制御器・同定 (R2S)・ばらつき (S2R) の試験はすべてこれで回る。
2. **MuJoCo を任意の依存**（`pip install physlearn[mujoco]` / `uv run --extra mujoco`、`mujoco>=4.0.1`）とする。接地・慣性を物理エンジンで確かめたいときに使う。
3. **Isaac Sim / Isaac Lab は手引きだけ**（[../textbook/90-isaac-sim-guide.md](../textbook/90-isaac-sim-guide.md)）。このリポジトリでは実行しない。
4. どの sim も実機も `src/physlearn/api.py` の `Plant`（`reset` / `step`）として実装し、制御器は `Command` / `Obs` だけを見る。

## 帰結

- 良い点: GPU もクラウド費用も無しで S2R / R2S の輪を 1 周回せる。試験が速く、CI でも回せる。
- 良い点: `Plant` の境界があるので、あとで Isaac Sim や Genesis の `Plant` を足しても制御器は変えなくてよい。
- 悪い点: Isaac Sim のセンサー模擬・描画・USD 資産・ROS 2 Bridge は体験できない。教材では手引きとクラウドの道（NVIDIA Brev など、L4 で見積もり $0.17/h〜）の紹介にとどまる。
- 悪い点: MuJoCo 4.0 は 3.x からの破壊的変更があり、Python 3.10 を切った。3.x 向けの例をそのまま写すと動かないことがある。
- 見直す条件: RTX 4080 級の GPU と RAM 32GB 以上の Linux 機（または Windows 11 ネイティブ）が使えるようになったとき、またはカメラ・接触の多い課題に進むとき。

## 検討した代案

- Isaac Sim をクラウドで必須にする: 費用と手間（アカウント・課金・帯域）が、IMU だけの課題に対して大きすぎる。不採用。
- Genesis を CPU で使う: CPU バックエンドはあるが、この PC で試していない。numpy + MuJoCo で足りるので今回は見送り。
- 調べた事実のなかに、この決定に反するものは無かった。
