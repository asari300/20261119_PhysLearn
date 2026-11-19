# S031 `mujoco-motor`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s031-mujoco-motor` |
| worktree | `.git-worktree/s031-mujoco-motor` |
| セッション記録 | なし（並列のサブエージェント） |

## 依頼

MuJoCo の車体モデルとモーターの式まわりの 3 件: (1) `motor.mujoco_model()` の負の粘性、(2) MuJoCo が ±0.2 でほとんど回らない、(3) 07 章の「同定後に整定が遅くなる」。xml と mujoco_plant.py は変えない。

## 決めたこと

- (1) b = 0、Kt = Ke = 0.05、R = Kt²/(0.05/30) = 1.5 Ω、V = 0.05·R/Kt = 1.5 V。傾きを全部逆起電力に持たせた。K・τ は不変。
- 依頼は「内部抵抗で K が下がる」を確かめるとあったが、b = 0 では K は V/Ke で R によらない（無負荷で電流 0）。試験は「K が上がらない、τ が延びる」にした。

## やったこと

- `src/physlearn/motor.py`: `mujoco_model()` の置き方。
- `modelica/DCMotorPivot.mo`: 同じ置き方、電池の内部抵抗 `Rbat`（既定 0）。
- `tests/test_motor.py`: `test_mujoco_model_is_physical`（直す前は `b = -8.3e-4` で落ちた）。
- 13 章 5.3 に置き方の 2 文、5.2 に小さい duty も合う 1 文。解答集 08-3・13-3。08 章に「小さい duty でも回るか…」の節。

## 検証

- omc（run.mos）: t = 0.5 s で 8.9946、t = 0.0673 s で 5.6875（直す前と同じ）。
- omc `-override Rbat=0.5`: t = 0.5 s で 8.9657、t = 0.0898 s で 5.6900。motor.py: K 30 → 30、τ 0.0673 → 0.0897。
- MuJoCo 直接（ゲートなし）: duty 0.05/0.1/0.15/0.2/0.3/0.5 → gz 0.898/1.796/2.693/3.591/5.387/8.978（予測 u×18）。車輪関節の qfrc_constraint・qfrc_passive は 0。
- `sim-log --plant mujoco`: ±0.2 の段の後半 0.5 s で 3.611 / −3.571。
- `loop-demo --real mujoco`: 前後とも tc = 0.08、同定 yaw_gain 17.958・tau 0.07・deadband 0.0、整定 0.08 → 0.22 s。
- `uv run --extra mujoco --extra viz pytest -q`: 70 passed / 0 failed

## 確かめていないこと・残したこと

- S026 の「0.047 / −0.007」は再現できなかった。区間の読み違いと推測【未確認】。
- 07 章の「前」が 0.08 s と速い理由（ゲイン過小見積もり 1.5 倍 + 不要な FF 0.05）は定性的。各要素を外して走らせてはいない。
- xml の誤りは見つからなかった。
