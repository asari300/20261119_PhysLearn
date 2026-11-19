# S020 `motor-physics`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s020-motor-physics` |
| worktree | `.git-worktree/s020-motor-physics` |
| セッション記録 | 未コピー（マージは別担当） |

## 依頼

「sim のパラメータは物理のどこから来るのか」の章（13 章）と、裏づけの小さなモデル。DC モーターの式から一次遅れの K・τ を導き、MuJoCo の定数から予測して MuJoCo で検算、Modelica (omc) でも同じモデルを走らせる。電圧・荷物での K・τ の幅から `SPREAD` に示唆を出す（直さない）。

## 決めたこと

- `motor.py` は Motor（V・R・L・Kt・n・b）と、K・τ の計算、2 階の式の積分（電流だけ陰的）、`to_params`、`mujoco_model()` だけ。
- MuJoCo の「トルク = 0.05·u − 0.05/30·ω」は V=R=n=1、Kt=0.05 と置き、傾きの差を b で合わせた（Kt² ≠ 0.05/30 なので）。
- Modelica は MSL の部品をつなぐ形にした（「部品をつなぐだけ」を見せるため）。

## やったこと

- `src/physlearn/motor.py`、`tests/test_motor.py`、`modelica/DCMotorPivot.mo`・`run.mos`、`doc/textbook/13-motor-physics.md`。

## 検証

- 予測: 定常ヨー 9.000 rad/s、τ 0.0673 s（J_eff 1.122e-4 kg m²）。2 階の式の数値解 8.995 / 0.0672 s。
- MuJoCo（0.002 s 刻み）: 8.978 rad/s、0.0720 s。慣性は `body_inertia` と手計算が一致。ずれは接触の柔らかさと刻み（solref 0.004・dt 0.0005 で 8.999 / 0.0685 s）。
- omc 1.27.2 + MSL 4.1.0: yaw(0.5) = 8.9946、yaw(0.0673) = 5.6875（比 0.632）。
- L/R = 0.005 s でも 63% 時刻の差は 4% 以内（0.0651 対 0.0673）。
- `uv run --extra mujoco pytest -q tests/test_motor.py`: 3 passed。全体: 39 passed, 1 skipped。
- セッション記録の `--check`・漏洩検査: このセッションではしていない（マージ担当に任せる）。

## 確かめていないこと・残したこと

- Robo Base のモーター定数（無負荷回転数・停動トルク・定格電圧）は未確認。MuJoCo の値は仮。
- 電池の電圧（1.6 / 1.5 / 1.2 / 1.1 V）は仮定で出典なし。
- DRV8835 の fast decay での PWM と平均電圧の関係は出典で確かめていない（近似と明記）。
- 床の摩擦係数 5 で τ が 0.116 s に延びた理由は調べていない。
- `SPREAD` の提案（gain −30%〜+10%、tau −10%〜+60%）は報告のみ。`randomize.py` は触っていない。
