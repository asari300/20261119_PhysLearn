# S093 `docs-check-coverage`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s093-docs-check-coverage` |
| worktree | `.git-worktree/s093-docs-check-coverage` |
| セッション記録 | `log/sessions/<日付>-<セッションID>.md`（統括が締めるときに作る） |

## 依頼

章に貼った出力の見張り（`docs_check`）が効いていない 13 章・15 章・解答集を、効くようにする（14 章は S091 が触るので除く）。あわせて MuJoCo が無い環境の分かりにくい失敗 2 つ（16 章の `python -m physlearn.cad` が `ModuleNotFoundError` で止まる、`docs_check` が `--mujoco` なしでそれを「差」と数える）を直す。

## 決めたこと

- 15 章の `mismatch one`・`loop` の出力は、章が断片で貼っている（現象ごとに数行、`loop` は HIDDEN の 6 行を省略）。章を書き換えず、道具に **「直前に `<!-- docs_check: output uv run ... -->` があるブロックを、そのコマンドの出力の抜粋（順序つきの部分列）として見る」** 形 (iii) を足した。同じコマンドは 1 章で 1 回だけ走らせる（`one` は約 20 s）。
- 「`uv run` の付かない `python -m physlearn...`・`physlearn ...` も対象にする」は**入れなかった**。全対象の章を grep すると、そう書いてある行は 14 章（S091 が `uv run` を足している最中）にしか無く、`LOG.csv` のような置き換え用の名前も含むので、既定にしても 13・15・解答集の件数は変わらず、14 章は S091 の変更とぶつかる。
- 13 章の表と数字（K・τ・電池と荷物の表、`motor.simulate` の 8.9946 rad/s など）は、章の中にそれを出すコマンドが無い（`motor.py` に `main` が無く、章は試算を本文に書いている）。見張るにはコマンドを足す必要があり、本文を変えない決まりなので (c) のまま。
- `--mujoco` なしで `ModuleNotFoundError: No module named 'mujoco'`・「mujoco が入っていない」で止まったコマンド、`--plant mujoco`・`--real mujoco` は「飛ばした（mujoco なし）」にした。

## やったこと

- `src/physlearn/docs_check.py`: 形 (iii)（`output` 指定）、同じコマンドの結果の使い回し、mujoco なしの飛ばし。冒頭の説明も更新。
- `src/physlearn/cad.py`: `main` の先頭で `import mujoco` を試み、無ければ `__init__.py` と同じ文面で `SystemExit`（終了コード 1）。MuJoCo がある環境の出力は変えていない（16 章・解答集とも `--mujoco` で一致）。
- `tests/test_docs_check.py`（output 指定の抽出と実行、mujoco なしの飛ばし）、`tests/test_cad.py`（mujoco が無いときの案内 1 本）。
- `doc/textbook/15-mismatch.md`: 断片 6 つの直前に `output` の印、冒頭の「走らせるだけで出力を貼っていない」bash ブロックに skip の印（二重に走らせないため）。**本文・数値・表は無変更**。
- `doc/textbook/solutions.md`: 16 章の `python -m physlearn.cad` の出力ブロックの直前に `output` の印 1 つ。
- `doc/troubleshooting.md`: `No module named 'mujoco'` の項を、cad の直った動きに合わせた。

## 検証

全章の件数（一致 / 差 / 飛ばした）。前 = main の 0b7e35d、後 = このブランチ。どちらも `--mujoco`。

| 章 | 前 | 後 |
| --- | --- | --- |
| 04 | 1 / 0 / 0 | 1 / 0 / 0 |
| 05 | 10 / 0 / 0 | 10 / 0 / 0 |
| 06 | 7 / 0 / 0 | 7 / 0 / 0 |
| 07 | 4 / 0 / 1 | 4 / 0 / 1 |
| 08 | 1 / 0 / 0 | 1 / 0 / 0 |
| 11 | 3 / 0 / 0 | 3 / 0 / 0 |
| 12 | 0 / 0 / 5 | 0 / 0 / 5 |
| 13 | 0 / 0 / 0 | 0 / 0 / 0 |
| 14 | 0 / 0 / 0 | 0 / 0 / 0（S091 の担当） |
| 15 | 0 / 0 / 0 | **6** / 0 / 0 |
| 16 | 1 / 0 / 0 | 1 / 0 / 0 |
| solutions | 0 / 0 / 0 | **1** / 0 / 0 |
| README | 1 / 0 / 0 | 1 / 0 / 0 |
| bringup | 0 / 0 / 0 | 0 / 0 / 0 |
| 合計 | 28 / 0 / 6 | **35** / 0 / 6 |

新しく見張られる 7 つ: 15 章の `mismatch one` の断片 5 つ（遅延・lr・fb・sag・imu_x）、`mismatch loop` の 1 つ、解答集 16 章の `python -m physlearn.cad` の 1 つ。**貼ってある出力が古かった所は無い**（7 つとも走らせ直して一致。解答集 `loop-demo` の基準の数字も走らせて一致を確かめた）。

- `uv run --extra mujoco --extra viz pytest -q`: 169 passed（コミット前の 1 回目）。
- 素の環境（`git clone` の写しで `uv sync` だけ。`/tmp` の作業用の場所、終了後に削除）:
  - `uv run python -m physlearn.cad` は `mujoco が入っていない。`uv sync --extra mujoco` で入れる` を出して終了コード 1。
  - `uv run pytest -q`: 155 passed, 7 skipped。
  - `uv run python -m physlearn.docs_check`（`--mujoco` なし）: 全章で差 0。16 章と解答集の cad は「飛ばした（mujoco なし）」（1 回目は、メッセージの文面を飛ばす条件に入れ忘れて 2 件が「差」だった。直して 0）。05 章の 2 件・07 章の 2 件・08 章の 1 件も mujoco なしの飛ばし（従来どおり）。
- 漏洩の検査: 追加した行にメールアドレス・ホームのパス・ユーザー名は無い（`git diff` を見た）。

## 確かめていないこと・残したこと

**まだ見張りが効かないもの（場所と理由）**

| 場所 | 理由 |
| --- | --- |
| 13 章 全体（表・本文の数字） | 数字を出すコマンドが章に無い（`motor.py` に `main` が無い）。見張るには CLI を足す必要がある |
| 13 章 5.3 の `omc` の bash ブロック | `uv run` でなく、CI に OpenModelica が無い。結果（8.9946 rad/s など）は本文 |
| 14 章 | S091 が `uv run` を足している最中（私は触っていない） |
| 15 章 本文の数字（`drift` の表 −0.0003・−0.156、「通過率 30 台で 0.40」など）、`fb` の負の向きの見込み 8.41 | 出力のブロックでなく本文・表。`drift` の表は `sysid.identify` を呼ぶ別の手順 |
| 15 章 冒頭の `mismatch one`/`loop`（出力なしの bash） | 出力を貼っていないので比べるものが無い（skip の印をつけた） |
| 解答集 のほか全部（`python` ブロック 2 つ、表、本文の数字、`uv run python -m physlearn.cad 0 0.04 -0.04` の結果） | 出力が表・本文。python ブロックは `uv run` が付かず、出力が別の場所。`cad` の x 引数つきの 1 行も、本文中の数字 |
| 12 章の 5 つと `hwcheck stream` | 偽の XIAO（実時間で揺れる）。従来どおり飛ばす |
| `output` の抜粋の比べ方 | 行の部分列としてしか見ない。省略された行が増えても、順序が合っていれば一致になる |

- 実時間で揺れる出力は今回の対象に無かった。`mismatch one`/`loop` は乱数の seed が固定で、3 回走らせて同じ。ただし CI の環境（別の CPU・BLAS）で最後の桁がずれる可能性は、数字の比べ方（最後の桁の半分 + 1e-9）に任せていて、確かめていない。
- 15 章が 24〜30 s 増える（CI の `docs` ジョブの上限 15 分には余裕）。
