# 90. Isaac Sim / Isaac Lab へ進むときの手引き

> **注意: この章の手順は、このリポジトリでは一度も実行していない。**
> 作業 PC（WSL2・GPU 無し・RAM 7 GiB）は Isaac Sim の要件を満たさないため（[ADR 0001](../adr/0001-sim-stack.md)）。
> 要件と版は JST 2026-11-19 13:35〜13:40 に取得した情報（[調査](../research/2026-11-19-software.md)）。
> API の名前（クラス名・拡張名）は版ごとに変わるので、使う版の公式文書で確かめること。下に出す名前は確かめていない。

## 1. 要るもの

| 項目 | 最小（Isaac Sim 6.2） |
|---|---|
| OS | Ubuntu 24.04（22.04 は非推奨化）か Windows 11。WSL2 は公式要件に記載なし |
| GPU | RT コアのある NVIDIA GPU。最小 GeForce RTX 4080 / VRAM 16GB |
| RAM | 32GB（推奨 64GB）。Isaac Lab の学習はさらに多く要る |
| ストレージ | SSD 50GB（推奨 500GB） |
| ドライバー | テスト済み Linux 595.58.03 / Windows 595.97 |
| ネット | アセット取得に HTTPS 接続が要る |

出典: https://docs.isaacsim.omniverse.nvidia.com/6.2.0/installation/requirements.html （取得 13:3x JST）

手元に無ければクラウドを使う（NVIDIA Brev、AWS EC2 G6e (L40S) など）。Brev の見積もり価格は L4 $0.17/h など（出典は調査文書 §3）。止め忘れに注意する。

## 2. 入れ方の流れ（概略）

1. 公式の要件ページの互換チェッカーで GPU とドライバーを確かめる。
2. 入れ方を 1 つ選ぶ: pip（Python パッケージ）、ワークステーション版、コンテナ（Linux のみ、NVIDIA Container Toolkit が要る）、ソースから（GitHub `isaac-sim/IsaacSim`、初回に Omniverse Licensing Terms への同意が要る）。
3. 学習もしたいなら Isaac Lab（v3.0.0 は Isaac Sim 6.2 対応、物理は Newton か PhysX）を入れる: https://github.com/isaac-sim/IsaacLab/releases
4. 付属の例（車輪ロボットを動かす例）を 1 つ動かしてから、自分の車体に進む。

## 3. このリポジトリの境界を Isaac Sim 側で作る筋道

制御器は `Command` / `Obs` / `Plant`（`src/physlearn/api.py`）だけを見る。Isaac Sim は `Plant` の 1 実装として足す。

```python
class IsaacPlant:  # Plant を満たす（スケッチ。未実行）
    def reset(self) -> Obs: ...
    def step(self, cmd: Command, dt: float) -> Obs: ...
```

### 3.1 車体（V-World のモデル）

- 差動 2 輪 + キャスター（または滑る点）の車体を URDF か USD で作る。MuJoCo 版（S007）の寸法・質量と揃える。
- 左右の車輪を回転ジョイントにし、速度駆動にする。

### 3.2 `Command` → 車輪

- `Command.left/right` は -1..1 の PWM デューティ比。実機ではモーターが 1 次遅れでついてくる。
- Isaac Sim の関節は理想に近く動くので、**モーターモデルは自分の `step` の中で書く**: `ω_target = K * duty`、`ω += (ω_target − ω) * dt / τ`。K と τ は R2S（実機ログからの同定）で求めた値を使う。
- その ω を各車輪の関節速度目標として渡す。差動用のコントローラー（Isaac Sim にあるもの）は使わなくてよい。

### 3.3 IMU → `Obs`

- 車体の基準リンクに IMU センサーを付ける（Isaac Sim には物理ベースの IMU センサーがある。名前と使い方は版の文書で確認）。
- 座標系を `Obs` に合わせる: x 前・y 左・z 上、静止時 `az ≈ +9.81`、`gz > 0` が左旋回。センサーの出す向きと符号を、静止・左旋回の 2 つの場面で必ず確かめる。
- 実機に寄せるため、ジャイロのバイアスと白色雑音を `step` の中で足す（値は R2S で求めたもの）。
- `t` は `reset` からの経過秒。

### 3.4 時間の進め方

- 物理の刻みを `dt` の約数にし（例: 物理 200 Hz、`dt` = 0.01 s なら 2 回）、`step` の中で必要回数だけ進める。
- 描画は切ってよい（headless）。速さが要るなら Isaac Lab の並列環境で多数の車体を同時に回し、domain randomization に使う。

### 3.5 確かめ方

- numpy の sim・MuJoCo の sim と同じ指令列を与え、`LOG_COLUMNS` の CSV を出して比べる。ステップ応答の時定数・定常値が揃えば境界は正しい。

## 4. ROS 2 とつなぐ場合（今回は後回し）

- Isaac Sim には ROS 2 Bridge がある。Isaac Sim 6.2.0 の文書は「Ubuntu 24.04 with Jazzy is recommended」（推奨は Ubuntu 24.04 と Jazzy）、「Humble and Jazzy are tested」（試験済みは Humble と Jazzy）、ほかの ROS 2 は experimental（動作の保証なし）としている。Humble は Ubuntu 24.04 では未対応（"Humble on Ubuntu 24.04 is not supported"）。ブリッジの試験済みに Lyrical Luth は入っていない。出典: https://docs.isaacsim.omniverse.nvidia.com/6.2.0/installation/install_ros.html （2026-11-19 18:22 JST 取得）。
- ROS 2 全般の推奨は Lyrical Luth（LTS、EOL 2031-05）だが、Isaac Sim のブリッジに使う ROS 2 は上の Jazzy か Humble にする（Lyrical を入れると、試験されていない組み合わせになる）。Lyrical の日付は今回取り直していない【未確認】。
- 公式文書には Windows の Isaac Sim と WSL2 の ROS 2 をつなぐ手順がある（6.0.0 の文書）: https://docs.isaacsim.omniverse.nvidia.com/6.0.0/installation/install_ros_other_platforms.html （取得 13:3x JST、検索要約。本文は未読）。
- 実機 XIAO を micro-ROS でつなぐ場合、`micro_ros_platformio` の公式対応表に XIAO は無い（ESP32 は `esp32dev` のみ）。自分で確かめる必要がある。
