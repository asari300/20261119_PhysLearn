# 教材の図

`python -m physlearn.plot` と `physlearn.plot.figures()` で作った PNG。軸ラベルは英語（日本語フォントが無い環境でも文字化けしないため）。
「代役」は `physlearn.HIDDEN` のパラメータの sim（loop-demo と同じ seed）。

| 図 | 何が見えるか | 貼る場所の案 |
| --- | --- | --- |
| `01-sim-nominal.png` | 公称の sim で同定の実験をしたログ。全体で 17 s。静止 1 s のあと、旋回の指令 ±0.2・±0.35・±0.5 を各 1 s（間に 0 を 1 s）、最後に +0.35・−0.35 をもう一度（前後で K が変わったかを `drift` で見るための段。末尾の 2 段）。上が指令の旋回成分、下が gz。指令の段ごとに gz が一次遅れで追う。 | 04 章（sim）の同定の実験の説明 |
| `02-stand-in-vs-nominal.png` | 代役のログに、公称パラメータのモデルを重ねた図。モデルは代役より大きく速く回り、小さい指令 (0.2) では代役はわずかしか回らない（不感帯）。 | 01 章（S2R と R2S）か 05 章（Real2Sim）の冒頭。「sim と実機の差」 |
| `03-stand-in-vs-identified.png` | 同じ代役のログに、同定して直したパラメータのモデルを重ねた図。線がほぼ重なる。 | 05 章（Real2Sim）の同定の結果 |
| `04-step-before-after.png` | 代役での閉ループのステップ応答 (0 → 3 rad/s)。前は公称で決めたゲイン、後は同定したパラメータで決め直したゲイン。前は行き過ぎて目標の少し下に落ち着き、後は目標に揃う。 | 06 章（Sim2Real）か 07 章（1 周）の結果 |
| `05-still.png` | 代役を 5 s 止めたときの gz と、そのヒストグラム。平均（バイアス）と標準偏差を書き込んである。 | 02 章（IMU）のバイアスと雑音 |
| `06-mujoco.png` | MuJoCo の車体（IMU に雑音とバイアスあり）で同じ同定の実験をしたログ。公称の sim より大きく回る。 | 08 章（MuJoCo） |

## 作り直す

sim・同定・制御の中身が変わったら（S077 で S041 の後の main から作り直した。実験は 17 s、寸法は r = 30 mm・b = 0.1 m）、下を実行して PNG をコミットし直す。
`figures()` は公開された関数（`sim_log`・`identify`・`apply`・`tune`・`design`・`run`）を呼ぶだけなので、コードは直さなくてよい。

```bash
uv sync --extra viz --extra mujoco
uv run python -c "from physlearn.plot import figures; figures('doc/textbook/fig')"   # 01〜05（05 は前と同じ）
uv run physlearn sim-log mujoco-id.csv --plant mujoco
uv run python -m physlearn.plot log mujoco-id.csv --out doc/textbook/fig/06-mujoco.png
rm mujoco-id.csv
```

作り直したら、各図を開いて上の「何が見えるか」がまだ正しいか確かめる。

## 自分のログを図にする

```bash
uv run python -m physlearn.plot log run.csv --out run.png --params params.json   # gz にモデルを重ねる
uv run python -m physlearn.plot compare sim.csv real.csv --out cmp.png           # 2 本の gz を重ねる
uv run python -m physlearn.plot still still.csv --out still.png                  # 静止ログのバイアスと雑音
```
