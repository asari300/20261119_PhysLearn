# S041 `numbers-once`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s041-numbers-once` |
| worktree | `.git-worktree/s041-numbers-once` |
| セッション記録 | 統括が `log/sessions/` に作る（このセッションでは作っていない） |

## 依頼

`doc/plan/2026-11-19-outlook.md` の 12.0 節（決まりと定数の 1 ページ）と 12.1 節。教材の出力を動かすコードの変更を 1 本のブランチに順に入れる: (a) 寸法の一本化、(b) 同定のゲインをモデルの当てはめで、(c) 実験の末尾に同じ振幅を足して `drift`、(d) `SPREAD` を決め直す、(e) 小さな積み残し。**章（`doc/`）は直さない**。出力の作り直しは第 2 段（S070〜S077）。統括からの上書き: `fakexiao.py`・スケッチ・`doc/protocol.md` は触らない。締め切り JST 18:35。マージと push はしない。

## 決めたこと

- 定数は 12.0 の 1 ページのとおり。r = 0.030 m、b = 0.100 m、`motor_gain` 20（`HIDDEN` は 40/3）、duty 上限・ゲート・dt・seed は変えない。
- 5 段すべてを入れた。段ごとに 1 コミット、各コミットで全試験が通っている。
- 下の「受け入れ条件と実測」のとおり、条件を黙って変えた所は無い。**条件と違う作りにした所は 3 つ**（次の節）。

### 依頼文と違う作りにした所（理由つき）

1. **(e)(3) の「止まった」の判定**。依頼文は「`|gz|` が 0.05 rad/s 未満が 20 サンプル続く」。偽の XIAO の中身 `HIDDEN` はジャイロのバイアスが 0.08 rad/s なので、この条件は永久に満たされず、`reset` のたびに 2 s 待って警告が出る（走らせて確かめたわけではなく、バイアスの値からの判断）。そこで **「直近 20 サンプルの gz がその平均から 0.05 rad/s 以内」**に変えた（`link.SETTLE_N/SETTLE_GZ/SETTLE_S`）。バイアスが何でも判定できる。弱点: 一定の速さで回り続けるもの（止まらないモーター）は「落ち着いた」と判定する。その場合は閉ループの安全ゲート（|gz| > 15）が拾う。さらに、固定サンプルを流す `tests/test_link.py` の試験のために `SerialPlant(settle=True)` の引数を足した（False なら従来どおり最初の 1 サンプルで `t0` を決める）。
2. **(d) の「実測」に使うログ**。依頼文は「`HIDDEN`・`HardPlant`・MuJoCo の代役のログ数本」。MuJoCo のログを混ぜると、K が 8（HIDDEN）と 18（MuJoCo）という別の機体の差が「ばらつき」に入り、K の幅が (−0.41, +0.67) になって使えない。そこで**同じ機体のばらつきとみなせる 5 本（HIDDEN・HardPlant の全部入り・電池なし・電池だけ・むだ時間だけ）**を実測の欄に使い、MuJoCo を混ぜた 3 本の結果は参考として別に書いた。
3. **`compare.spread` の「実測の幅」**。(下, 上) にするため、gain・tau は「平均に対する比の最小・最大」（`lo`・`hi`）で測る。これまでの「半幅」(`half`) の欄は残した。deadband・bias は今までどおり ± の半幅。公称からでなく**ログどうしの平均**を中心にするのは今までと同じ。

## やったこと

コミット（日本語、`S041: (x) ...`）:

| 段 | 変更 |
| --- | --- |
| (a) | `sim.Params` の既定を 0.030 / 0.100 / 20。`HIDDEN` を `motor_gain=40/3`。`cad.dimension(item, parts, table)`（優先順 measured > datasheet > cad > assumed、同順は `parts` の前。数でない行 `【未確認】` は無視。単位は mm のみ）。`cad.to_mjcf(..., wheel_radius=None, track=None, table=...)`: 指定が無ければ表から。車輪の size・pos、車体の高さ、キャスターの z を合わせる。`cad/dimensions.csv` は `note` 欄の追記だけ。 |
| (b) | `sysid.identify`: τ の格子 400 点 × d の格子（0〜0.3 を 0.01 刻み、最良の近くを 0.001 刻み）で K を最小二乗。`first_order` を使い回し（一次遅れの係数を最初に一括計算する形に直した。結果は同じ）。「動いたか」の判定だけ従来の定常値。 |
| (c) | `sim.id_experiment` の末尾に +0.35, −0.35（17 s、1700 行）。`identify` が `drift`（同じ振幅が 4 回以上あるとき、最初の 2 回と最後の 2 回の K の比 − 1）を返す。無ければ欄を出さない。`apply` は無視する。 |
| (d) | `randomize.SPREAD` を `(下, 上)` に。`sample` を `rng.uniform(1+下, 1+上)` に。`compare.spread` と表示を非対称に対応。`tests/test_randomize.py` を新設。 |
| (e) | `make_plant("hard")`、`PLANTS` に `"hard"`、`loop-demo --real hard`・`sim-log --plant hard`。`control.run(..., gate=None)`。`SerialPlant.reset` が回転の止まるのを待つ。 |

触らなかったファイル: `fakexiao.py`、スケッチ、`doc/`、`README.md`、`.claude/`、`mujoco_plant.py`、`models/diffdrive.xml`、`plot.py`、`imu.py`、`motor.py`。`mismatch.py` も触っていない（`SAG_T = 13.0` の説明文が「id_experiment の長さ」のままで、17 s になった今は古い。値は 13 のまま。下の残したこと）。

試験の側の直し: `tests/test_link.py`（固定サンプルの試験に `settle=False`、`link id` の試験にサンプル 20 個分を足す）。`tests/test_real_loop.py`・`test_fakexiao.py` は実験の長さ 1300 を固定していなかった。

### (d) SPREAD の根拠の表

| 欄 | 物理から（13 章 6 節） | 実測から（5 本。`compare spread`） | 今の値（変更前） | 採用（広いほう） |
| --- | --- | --- | --- | --- |
| motor_gain | (−0.30, +0.10) | (−0.186, +0.138) | ±0.20 | **(−0.30, +0.14)** |
| motor_tau | (−0.10, +0.60) | (−0.131, +0.089) | ±0.30 | **(−0.14, +0.60)** |
| deadband | 対称のまま | ±0.006 | ±0.03 | ±0.03 |
| gyro_bias | 対称のまま | ±0.000 | ±0.02 | ±0.02 |

- 実測の 5 本: HIDDEN、HardPlant 全部入り（`DEFAULTS`）、sag を 0 にした全部入り、sag 0.27 だけ、delay 0.04 だけ。いずれも seed 0。同定した K（yaw_gain）は 8.01 / 6.33 / 8.43 / 6.03 / 8.24。代役由来なので**暫定**。
- 参考（MuJoCo を混ぜた 3 本: HIDDEN・全部入り・MuJoCo）: motor_gain (−0.41, +0.67)、motor_tau (−0.59, +0.42)、deadband ±0.075、gyro_bias ±0.029。別の機体の差が入るので採用しなかった。
- motor_tau の下は実測 −0.131 に対し −0.14（0.01 刻みで外側に丸めた。−0.13 だと 101 % で「外」と出る）。
- 採用した SPREAD で同じ 5 本を判定すると、motor_gain 98 %、motor_tau 94 %（どちらも外ではない）。

## 受け入れ条件と実測

| 段 | 条件 | 実測 | 判定 |
| --- | --- | --- | --- |
| (a)(1) | `Params()` の r・b が表の MJCF の行と `diffdrive.xml` に一致 | `tests/test_cad.py::test_params_table_and_mjcf_agree` | 通る |
| (a)(2) | `Params().yaw_gain()` = 12 ± 1e-9、`HIDDEN` = 8 ± 1e-9 | 11.999999999999998、8（同上の試験） | 通る |
| (a)(3) | `measured` 欄の値が優先される | 一時 CSV で 27.5 mm → 0.0275 m、datasheet 95 mm が assumed に勝つ | 通る |
| (a)(4) | 既存の試験、`loop-demo` の gz の数字が動かない | 通る。`loop-demo` の「前」の行は完全に同じ。ただし 04 章の `python -c` の `yaw_gain 12.0` が `11.999999999999998` に、`model 5.4` が `5.3999999999999995` に変わる（浮動小数の表示） | 通る（表示の差あり） |
| (b) | 雑音なし SimPlant、τ = 0.02/0.2/0.4 で K 2 % 以内、d 0.005 以内、τ 5 % 以内 | K の誤差 −0.00 / +0.1 / +0.1 %、d の誤差 7e-18、τ の誤差 −0.3 / +0.5 / +0.3 % | 通る |
| (b) | `HIDDEN` の雑音ありログ（seed 0）で 8 ± 0.1 | 8.0063（plant の seed 0）。seed 1000 では 8.011 | 通る |
| (b) | 静止だけのログは今までどおり | `test_still_only_log_gives_bias_and_noise` | 通る |
| (b) | `physlearn sysid` が 5 秒以内 | 2.5 s（`uv run` の起動込み、17 s のログ） | 通る |
| (c)(1) | 1700 行、u の和が 0 | 1700、和 0 | 通る |
| (c)(2) | 雑音なしで \|drift\| < 0.03 | 6.9e-9（雑音ありの HIDDEN でも −0.0003） | 通る |
| (c)(3) | `HardPlant(sag=0.27)` で drift < −0.03 | −0.156（全部入りで −0.154） | 通る |
| (c)(4) | `link id`・`sim-log`・偽の XIAO 越しが 1700 行 | `sim-log` 1700 行、偽の XIAO 越しの `link id` は `fake_id.csv` が 1701 行（見出し + 1700）、試験が通る | 通る |
| (d)(1) | `sample` が範囲内（100 回） | `tests/test_randomize.py` | 通る |
| (d)(2) | `eval -n 100` が動き、公称の通過率が出る | tc=0.08、**100 %**（変更前も tc=0.08、100 %） | 通る |
| (d)(3) | `compare spread` が非対称の幅で「外」を判定 | `test_spread_asymmetric_outside_is_judged_per_side`（下に広い側と上に狭い側を別々に） | 通る |
| (d)(4) | 前→後の通過率と tc | 下の表 | 記録 |
| (e)(1) | `loop-demo --real hard` が動く | 動く（試験 `test_hard_plant_by_name_and_loop`） | 通る |
| (e)(2) | `gate=SafetyGate(max_duty=0.3)` で \|duty\| ≤ 0.3、NaN で `tripped` | `test_run_accepts_caller_gate` | 通る |
| (e)(3) | 旋回後の `reset` が待つ。1 周の試験を壊さない | `test_reset_waits_for_rotation_to_stop`（待たないと \|gz − バイアス\| > 0.5、待つと < 0.1、警告なし）。`test_s2r_r2s_s2r_over_serial` は 16.95 s → 17.08 s | 通る（判定の式は変更。上） |

- `uv run --extra mujoco --extra viz pytest -q`: **121 passed**（変更前 106）。所要 70〜90 s（4 回走らせて 70.4 s / 86.8 s / 89.5 s / 67.2 s。同じコードでも揺れる）。変更前は約 30 s。増えた理由: 同定が 1 回 約 2 s 遅くなった（格子の当てはめ。(b)）、実験が 13 s → 17 s で `link id` を使う 2 つの試験（`test_real_loop` 約 17 s、`test_fakexiao` 約 11 s）が 4 秒ずつ延びた、試験を 15 本足した。
- セッション記録の `--check`、ステージした差分の漏洩検査: このセッションでは行っていない（統括が `/finish-session` でやる前提。マージもしていない）。

### (d)(4) 前→後の通過率と tc

| 場面 | 前 | 後 |
| --- | --- | --- |
| 公称（`eval -n 100`、tune） | tc 0.08、100 % | tc 0.08、100 % |
| 公称の tc 別（n = 50） | （前は未測定） | 0.08: 100 %、0.1: 100 %、0.15: 98 %、0.2: 50 %、0.25: 0 % |
| 同定した `fixed.json`（HIDDEN）、`eval --params fixed.json -n 100`（tune） | tc 0.2、69 % | tc 0.2、**50 %** |
| 同上、`--tc 0.25` | 15 % | 15 % |
| `loop-demo`（n = 50）の「後」 | tc 0.2、68 % | tc 0.2、**42 %** |
| `mismatch loop` HIDDEN の「後」（n = 30） | tc 0.2、70 % | tc 0.2、40 % |
| `mismatch loop` HardPlant の「後」（n = 30） | tc 0.2、10 % | **tc 0.25、3 %** |

通過率が下がったのは、`SPREAD` が K の下側を −30 % まで広げた（以前は −20 %）ため。意図どおり（物理の幅を入れた）だが、07 章の「68 %」の読み方の文が変わる。

## 第 2 段への引き継ぎ（動いた数字の前→後）

走らせ方: 変更の前は main と同じ commit（`dbfa4e7`）、後は本ブランチ。同じコマンドを作業ディレクトリを分けて走らせた。`PYTHONHASHSEED=0`、seed は既定。偽の XIAO は `FakeXiao(SimPlant(HIDDEN, seed=0), speed=2.0)` を同じプロセスの中で立て、`link id` → `sysid` → `link run`（公称）→ `link run --params` を走らせた。**偽の XIAO 越しの `link run` は実時間に依存するので毎回少し揺れる**（下の注）。

全体の注意（どの章でも）:
- `sysid` / `loop-demo` の出力に **`drift` の行・欄が増えた**（`sysid`: `drift       -0.0003`、`loop-demo`: `'drift': 0.0`）。
- ログの行数が **1300 → 1700**（`sim-log` の「N 行」、`link id` の `wrote`、CSV の `wc -l`）。実験は 13 s → 17 s。
- `apply` した Params の JSON は `wheel_radius 0.03`・`track 0.1` になり、`motor_gain` が 19.65 → 13.34 などに変わる（同じ yaw_gain でも motor_gain が違う）。
- 同定の yaw_gain が 7.86 → 8.006（真値 8）に、τ が 0.196 → 0.201（真値 0.2）に、deadband 0.1499 → 0.1500。**これまでの章にあった「ゲインが 1.8 % 低く出る」「τ が大きいほど低く出る」類の注記は、原因が直ったので消える**。

### 04 章（`04-sim.md`）、`fig/01`〜`03`

| 出力 | 前 | 後 |
| --- | --- | --- |
| `python -c` の `yaw_gain` | `12.0` | `11.999999999999998` |
| 同 `model` | `5.4` | `5.3999999999999995` |
| `Obs(...)` の 2 行、`true yaw 5.399979876072871` | — | 同じ（変わらない） |

図 `01`〜`03`: `plot.py` は走らせていない【未確認】。r が 16 → 30 mm になったので `ax`・`ay` の大きさが変わる図があるかもしれない（S077 が確かめる）。

### 05 章（`05-real2sim.md`）、`sim-log` → `sysid`

| コマンド | 前 | 後 |
| --- | --- | --- |
| `sim-log sim.csv` | `sim.csv: 1300 行` | `sim.csv: 1700 行` |
| `sysid sim.csv`（公称の sim のログ） | gyro_bias −0.0014、noise 0.0103、yaw_gain 12.0009、deadband 0.0500、motor_tau 0.0804 | bias・noise・deadband・motor_tau は同じ、yaw_gain 12.0034、**drift −0.0001** の行が増える |
| `sim-log --plant hidden real.csv` | `real.csv: 1300 行` | `real.csv: 1700 行` |
| `sysid real.csv --out fixed.json` | yaw_gain 7.8597、deadband 0.1499、motor_tau 0.1958 | **8.0063、0.1500、0.2011**、drift −0.0003 |
| `cat fixed.json` | wheel_radius 0.016、track 0.08、motor_gain 19.649…、motor_tau 0.1957…、deadband 0.14993… | **0.03、0.1、13.343880481043009、0.20106676859199749、0.15** |
| `head -3 real.csv` | — | 【未確認】（雑音の値は変わらないが、走らせ直して貼る） |

### 06 章（`06-sim2real.md`）、`eval`

| コマンド | 前 | 後 |
| --- | --- | --- |
| `eval -n 100` | `tc=0.08 kp=0.0833 ki=1.0417 deadband=0.050 bias=0.0000`、100 % | 同じ（100 %）。SPREAD の形が変わる記述は本文で |
| `eval --params fixed.json -n 100` | `tc=0.2 kp=0.1246 ki=0.6362 deadband=0.150 bias=0.0780`、69 % | **`kp=0.1256 ki=0.6245`**、**50 %** |
| `eval --params fixed.json --tc 0.25 -n 100` | `kp=0.0996 ki=0.5089`、15 % | **`kp=0.1005 ki=0.4996`**、15 % |
| 本文の SPREAD の説明 | `±0.2`・`±0.3`・`±0.03`・`±0.02` | `(−0.30, +0.14)`・`(−0.14, +0.60)`・`±0.03`・`±0.02`。決め方は上の (d) の表 |

`python -c` の SafetyGate の出力（06 章 64 行）は変わらない。

### 07 章（`07-loop.md`）、`loop-demo`

| 出力 | 前 | 後 |
| --- | --- | --- |
| `[前 (公称の sim)]` の行 | `tc=0.08 通過率 100 % 整定 0.64 s 行き過ぎ 5.8 % 定常偏差 0.081 NG` | 同じ（変わらない） |
| 同定の行 | `{'gyro_bias': 0.08, 'gyro_noise': 0.012, 'yaw_gain': 7.867, 'deadband': 0.15, 'motor_tau': 0.196}` | `{..., 'yaw_gain': 8.011, 'deadband': 0.15, 'motor_tau': 0.201, 'drift': 0.0}` |
| `[後 (同定した sim)]` の行 | `tc=0.2 通過率 68 % 整定 0.50 s 行き過ぎ 0.1 % 定常偏差 0.001 OK` | `tc=0.2 通過率 **42 %** 整定 **0.51 s** 行き過ぎ 0.1 % 定常偏差 0.001 OK` |

本文の「通過率 100 % → 68 %、でも実機では良くなった」は **100 % → 42 %** になる。解釈（sim が現実に近づくと sim の側の余裕が減る）は変わらないが、下がり幅が大きいのは SPREAD の K の下側を広げたため。

### 08 章（`08-mujoco.md`）、MuJoCo

| コマンド | 前 | 後 |
| --- | --- | --- |
| `loop-demo --real mujoco` の同定の行 | `yaw_gain 17.958, deadband 0.0, motor_tau 0.07` | `yaw_gain 17.975, deadband 0.0, motor_tau 0.07, 'drift': -0.0` |
| 同「前」「後」の行（整定 0.08 s / 0.22 s など） | 前: 整定 0.08 s 行き過ぎ 2.6 % 定常偏差 0.020、後: tc=0.08 通過率 100 % 整定 0.22 s | 同じ（変わらない） |
| `sim-log --plant mujoco mj.csv` | `mj.csv: 1300 行` | `mj.csv: 1700 行` |
| `sysid mj.csv` | yaw_gain 17.9560、deadband 0.0000、motor_tau 0.0704 | **17.9740**、他は同じ、**drift −0.0000** の行が増える |

MuJoCo の物理（`diffdrive.xml`）は変えていないので、gz の値そのものは変わらない。

### 11 章（`11-imu-lab.md`）、`python -m physlearn.imu`

`stand_in` の「旋回の真のヨー角 +68.75 度」、`imu still`・`turn`・`r2s` の出力は**全部同じ**（走らせ直して差分 0 行）。IMU の項は r・b・K に依存しない。

### 12 章（`12-fake-xiao.md`）、偽の XIAO 越し

| 出力 | 前 | 後 |
| --- | --- | --- |
| `link id` が書く行数 | 1300 | 1700（実験が 17 s。実時間 2 倍速で約 8.5 s、等速なら 17 s） |
| `sysid real.csv` | bias 0.0782、noise 0.0145、yaw_gain 7.8600、deadband 0.1500、motor_tau 0.1958（本文の貼り付け） | 今回の走り: bias 0.0795、noise 0.0148、**yaw_gain 8.0063、deadband 0.1500、motor_tau 0.2011、drift −0.0002**。bias・noise は偽の XIAO の実時間のずれで毎回揺れる |
| `link run`（公称）+3.0 | 整定 inf、行き過ぎ 22.7 %、定常偏差 0.608 | 整定 0.84 s、行き過ぎ 12.9 %、定常偏差 0.001（`reset` が回転の止まるのを待つため。1 回しか走らせていない） |
| `link run`（公称）−3.0 | 整定 0.89 s、行き過ぎ 11.3 %、定常偏差 0.003 | 整定 0.88 s、行き過ぎ 10.8 %、定常偏差 0.002 |
| `link run --params`（同定後、tc=0.2）+3.0 | 整定 inf、20.0 %、0.547 | 整定 inf、20.3 %、0.438（変わらず NG。原因は【未確認】。ログでは最初の約 0.3 s の間 gz がほとんど動かず duty が 0.6 に張り付いている。偽の XIAO を実時間 2 倍速で使うときの読みの遅れが疑わしいが確かめていない） |
| `link run --params` −3.0 | 整定 0.49 s、1.1 %、0.000 OK | 整定 0.55 s、1.2 %、0.000 OK |
| 公称の `tc=` の行 | `tc=0.08 kp=0.0833 ki=1.0417 deadband=0.050 bias=0.0000` | 同じ |
| 同定後の `tc=` の行 | `tc=0.2 kp=0.1246 ki=0.6363 deadband=0.150 bias=0.0781` | `tc=0.2 kp=0.1256 ki=0.6245 deadband=0.150 bias=0.0795` |

12 章の貼り付けは偽の XIAO の実時間に依存して揺れる（outlook 12.3 のとおり `docs_check` で飛ばす印をつけて手で貼る）。`link run` の +3.0 が NG のまま残るのは、変更前からあった現象。

### 14 章（`14-fit-check.md`）、`python -m physlearn.compare`

`fit real.csv fixed.json`（HIDDEN のログと、それで同定した Params）:

| 項目 | 前 | 後 |
| --- | --- | --- |
| 雑音 | 0.0154 | 0.0154（同じ） |
| RMSE 全体 / 立ち上がり / 定常 | 0.0238 / 0.0256 / 0.0259（雑音の 1.5 / 1.7 / 1.7 倍） | **0.0150 / 0.0150 / 0.0151（雑音の 1.0 倍）** |
| モデルで説明できていない分 | 0.0182 | **0.0000** |
| 残差と指令の相関 | +0.52 | **+0.05** |
| 「ゲインだけを 1.01 倍にすると残差の 49 %」 | 49 % | **「1.00 倍で 0 %」** |
| 区間ごとの「定常の差」 | +0.0084 … +0.0474 / −0.0414 と指令に比例して開く | **全部 ±0.007 以内**。区間が 8 → 16 行に増える（実験が 17 s） |
| 判定 | 雑音の範囲で合っている | 同じ |

`holdout real.csv`: 正の向き（同定に使った）全体 0.0230 → **0.0147**、負の向き（使っていない）0.0210 → **0.0164**（モデルで説明できていない分 0.0143 → 0.0056）、判定は両方「雑音の範囲で合っている」で同じ。14 章の「ゲインが指令に比例してずれる」説明（定常の差が +0.03 / +0.05 と開く）は、**直ったので無くなる**。

`fit mj.csv fixed.json` と `holdout mj.csv`（MuJoCo のログ）: RMSE 全体 3.3270 → 3.3179、`holdout` の同定側 0.0177 → 0.0173、判定は両方とも前と同じ。区間ごとの行が 12 → 16 行に増える。

`compare spread real.csv sim.csv mj.csv`（`spread` の表示形式が変わる）:

```
前: 3 回の同定から。gain・tau は比、deadband・bias は足す量（どれも ± の半幅）
    motor_gain  31.5139  0.4005  0.200  200%  ← SPREAD の外
    motor_tau    0.1156  0.5425  0.300  181%  ← SPREAD の外
    deadband     0.0667  0.0750  0.030  250%  ← SPREAD の外
    gyro_bias    0.0320  0.0397  0.020  198%  ← SPREAD の外
後: 3 回の同定から。gain・tau は平均に対する比の (下, 上)、deadband・bias は足す量の ± の半幅
    motor_gain  21.1021  (-0.368, +0.420)  (-0.300, +0.140)  300%  ← SPREAD の外
    motor_tau    0.1173  (-0.400, +0.714)  (-0.140, +0.600)  285%  ← SPREAD の外
    deadband     0.0667  ±0.0750           ±0.030            250%  ← SPREAD の外
    gyro_bias    0.0320  ±0.0397           ±0.020            198%  ← SPREAD の外
提案の行は {'motor_gain': (-0.551, 0.629), 'motor_tau': (-0.599, 1.071), 'deadband': 0.112, 'gyro_bias': 0.059}
```

motor_gain の平均が 31.5 → 21.1 なのは r・b の変更（同じ yaw_gain に対する motor_gain が 5/3 倍小さい）と、求め直した K による。

### 15 章（`15-mismatch.md`）、`python -m physlearn.mismatch`

`one`（現象を 1 つずつ。同定の yaw_gain / motor_tau、残差 RMS 全体、判定）:

| 現象 | 前 | 後 |
| --- | --- | --- |
| delay=0.04 | 7.828 / 0.236、0.085、「式の形が違う」 | **8.242 / 0.249、0.066**、判定は同じ。定常の差が 6 行 → 8 行 |
| lr=0.1 | 7.860 / 0.196、0.024、雑音の範囲 | **8.006 / 0.201、0.015**、判定は同じ。前後の道のり **0.038 → 0.063 m**（r が 30 mm になったため） |
| fb=0.1 | 8.056 / 0.196、0.036、**「式の形が違う」**、前後の道のり 0.009 m | 8.206 / 0.201、0.030、**「雑音の範囲で合っている」**に判定が変わる、前後の道のり 0.016 m。負の向きの確かめは 0.070 → 0.052 |
| sag=0.27 | 5.901 / 0.193 / db 0.131、0.044、「式の形が違う」 | **6.026 / 0.198 / db 0.138、0.054**、判定は同じ |
| imu_x=0.03 | 7.860 / 0.196、0.024、ax の平均 −0.075 | 8.006 / 0.201、0.015、ax の平均 **−0.068** |

15 章の「fb は式の形が違うと判定される」は、新しい同定では**判定が「雑音の範囲」に変わる**（見逃す側に変わる）。本文の読み方（「合っている」と出ても左右差は残る）の見直しが要る。ax の平均が lr で +0.001（前は −0.001）に符号が変わるのは雑音の範囲。

`loop`:

| 行 | 前 | 後 |
| --- | --- | --- |
| HIDDEN の同定 | K=7.87 tau=0.196 db=0.150 | **K=8.01 tau=0.201** |
| HIDDEN の「後」 | tc=0.2 sim 通過率 70 % 整定 0.50 s | **40 %**、整定 0.51 s |
| HIDDEN 電池そのまま tc=0.3 / 0.4 | 整定 0.83 s・定常偏差 0.007 / 1.14 s・0.034（NG） | 0.85 s・0.009 / 1.17 s・0.039（NG） |
| HardPlant の同定 | K=5.75 tau=0.236 db=0.132 | **K=6.05 tau=0.245 db=0.136** |
| HardPlant の「後」 | tc=0.2 通過率 10 % 整定 inf 定常偏差 0.373 | **tc=0.25 通過率 3 %**、整定 inf 定常偏差 0.373 |
| HardPlant 電池を新品に tc=0.2 / 0.3 / 0.4 | 0.93 s・12 %・NG / 0.49 s・0 %・0.017 OK / 0.86 s・NG | 0.88 s・10 %・NG / 0.56 s・0 %・0.019 OK / 0.93 s・NG |
| HardPlant 電池そのまま（3 行） | 整定 inf、定常偏差 0.373 | 同じ |

### 16 章（`16-enclosure.md`）、`python -m physlearn.cad`

出力は**前後で全く同じ**（差分 0 行）。ただし本文の「寸法の食い違い」の節は事実が変わる: numpy `Params`（16 mm / 80 mm）は MJCF（30 mm / 100 mm）に**一本化した**。`cad.dimension()` が表を優先順で読み、`tests/test_cad.py` が `Params`・MJCF・表の一致を固定している。`cad/dimensions.csv` の「sim の今の値 (numpy Params)」の 2 行は値が 16・80 のままで、`note` に「古い」と追記しただけ（値の欄は触らない決めだった。S074 が直すか統括に聞く）。

### その他（章に出ない公開名・CLI の変化）

- `physlearn sim-log --plant hard`、`physlearn loop-demo --real hard` が使える（`-h` の選択肢に出る）。
- `cad.dimension`、`cad.TABLE`、`cad.WHEEL_PARTS`、`cad.to_mjcf(wheel_radius=, track=, table=)`。
- `sysid.identify` の戻りに `drift`（無いこともある）。
- `randomize.SPREAD` の値が tuple に（`motor_gain`・`motor_tau`）。これを読む外のコードは `tests/` と `compare.py` だけ。
- `compare.spread()` の各欄に `lo`・`hi` が増え、`half` は `(hi−lo)/2`。
- `control.run(..., gate=None)`、`link.SerialPlant(..., settle=True)`、`link.SETTLE_N/SETTLE_GZ/SETTLE_S`。
- `link.SerialPlant.reset` が止まるのを待つので、**実機の 1 回の `reset` が約 0.2 s 以上かかる**（停止しているなら 20 サンプル = 0.2 s）。`bringup.md` の手順の所要時間の記述に影響するかもしれない【未確認】。

## 確かめていないこと・残したこと

- 実機・MG24・実際のシリアルポートでは何も走らせていない（偽の XIAO と pty だけ）。`reset` の待ちが実機の IMU でどう働くかは【未確認】。
- 図（`fig/`）は作り直していない。r の変更で変わる図があるかは【未確認】（S077）。
- `mismatch.SAG_T = 13.0` のコメント「同定の実験 1 回分（id_experiment の長さ）」は、実験が 17 s になって事実と合わなくなった。値は 13 のまま（15 章の数字を動かさないため）。コメントを直すか、17 にして 15 章を作り直すかは統括の判断。`mismatch.py` は依頼文の「触ってよいファイル」に入っていたが、数字が動くので触らなかった。
- `drift` は「同じ振幅が 4 回以上ある」ログにだけ出る。13 s の古いログ（実機で既に取ったもの）には欄が出ない。
- `identify` の格子の下限（τ 0.01 s）より速い系、`deadband` が 0.3 を超える系は当てはまらない。
- 偽の XIAO 越しの `link run` の +3.0 が NG のまま残る件（12 章の表）。原因は未調査。
- `cad/dimensions.csv` の numpy 行の値の欄が古いまま（note で断っただけ）。
- 試験の所要時間が 70〜90 s と揺れる。90 s の目安にほぼ達している。重いのは `test_real_loop`（約 17 s）・`test_fakexiao`（約 11 s）・同定を何度も呼ぶ試験。`identify` の格子（粗い格子 31 点）を粗くすれば速くなるが、(b) の精度の条件との引き換え。
