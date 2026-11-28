# S130 `docs-check-no-shell`

| | |
| --- | --- |
| 日付 | 2026-11-27 |
| ブランチ | `feature/s130-docs-check-no-shell` |
| worktree | `.git-worktree/s130-docs-check-no-shell` |
| セッション記録 | 統括が `log/sessions/` にコピーする（この担当はコピーしない） |

## 依頼

リポジトリの状況を確認し、そのまま進める（発注者の「リポジトリの状況を確認」「進めて」）。
計画の「残り」はどれも部品か発注者の入力を待つので、コードだけで閉じられる最後の 1 件、
問題 2 の `docs_check` の `shell=True` をやめた（S059・S100 が案だけ書いて残していた）。

## 決めたこと

- `shell=True` をやめる形は、S100 の案の「`uv run` 以外を既定で飛ばす」ではなく、**引数に分けて `shell=False` で走らせる**にした。理由は 05 章の `head -3 real.csv`・`cat fixed.json` を残すため。S059 は「`uv run` 以外を既定で飛ばすと 05 章が 一致 10 → 8、飛ばした 0 → 2」を理由に既定を狭めなかった。引数に分ける形なら、この 2 つはそのまま動く（章の出力は 50・0・6 のまま）。
- 引用符の外にシェルの記号（`;`・`|`・`>`・`&`・`$`・バッククォート・改行）がある行は「飛ばした」にする。`shell=False` では意味が変わるので、黙って違う物を走らせない。**引用符の中は記号ではない**（`python -c "print(1 > 0); x = 2"` は今までどおり走る）。
- 行末の `# 注釈` は落とす。シェルの動きに合わせて「語の先頭の `#` から行末まで」とし、引用符の中の `#` と語の途中の `#` は残す（章には `# 表示された /dev/pts/N を使う` のような注釈がある）。`shlex.split(..., comments=True)` は語の途中の `#` でも切る（`a#b` が `a` になる）ので使わず、引用符を外してから `#` を探す小さな関数にした。
- `--strict` は変えない（`uv run` 以外を飛ばす・終了コードを見る）。既定の判定を変えないので、章の「一致」は増減しない。
- シェルの記号の判定は、引用符を外した文字列に対する小さな走査にした。生の行を正規表現で見ると、`python -c "print(1 > 0)"` の `>` を誤って拾うため。
- 試験で使う一時フォルダーは `tempfile.mkdtemp()` にした。`tmp_path` は `/tmp/pytest-of-<user>/...` で名前に `pytest` が入り、`auto_skip` の「試験は回さない」（`\bpytest\b`）に当たって、記号の判定より先に飛んでしまう（試験を書いていて気づいた既存の癖）。

## やったこと

| # | 変えた場所 | 中身 |
| --- | --- | --- |
| 1 | `src/physlearn/docs_check.py` | `SHELL_OP`・`outside_quotes()`・`shell_op()`・`strip_comment()` を足した。`run_file` はコマンドを `shlex.split(strip_comment(cmd))` で引数に分け、`subprocess.run(argv, ...)`（`shell=False`）で走らせる。`uv run` で始まる物には今までどおり `--quiet --project <root>` を挿す。引用符の外の記号がある行と、分けた結果が空の行は「飛ばした」。`unsafe()` は `uv run` 以外の判定だけにした（記号の判定は既定に移した）。冒頭の説明を直した |
| 2 | `tests/test_docs_check.py` | `test_shell_operators_are_detected_only_outside_quotes`（引用符の中の `>`・`;`・`$(...)` は記号ではない）、`test_strict_skips_commands_other_than_uv_run`、`test_shell_operators_are_skipped_and_not_run`（リダイレクトの行と、パイプで `head -1` につなぐ行が「飛ばした」になり、リダイレクト先のファイルができない）、`test_comment_at_the_end_of_a_command_is_dropped`、`test_plain_commands_still_run_without_a_shell`（`head -1 a.csv` は動く）。`test_unsafe_commands_for_strict_mode` は上の 2 本に分けた |
| 3 | `CLAUDE.md` | `docs` ジョブの説明から `shell=True` を外した（章に書いたコードはそのまま走る、は変えない） |
| 4 | `doc/plan/2026-11-19-plan.md` | 問題 2 に S130 の結果（`shell=True` をやめた。残りは終了コードと抜粋の部分列）と、S130 の行・次の番号 S131・件数 |
| 5 | `doc/plan/2026-11-20-start-here.md` | 件数（195 passed）と `shell=True` をやめたこと、次の番号 S131 |

## 検証

- `uv run pytest -q`（`uv sync --all-extras` の後）: **195 passed**（main は 191。足したのは 4 件）。42 秒。
- `uv run python -m physlearn.docs_check --mujoco`: **一致 50・差 0・飛ばした 6**。章ごとの内訳も直す前と同じ（04: 1、05: 10、06: 7、07: 4（飛ばし 1）、08: 1、11: 3、12: 0（飛ばし 5）、13: 4、14: 6、15: 7、16: 1、solutions: 5、README: 1、bringup: 0）。章ごとに表示された所要の合計は 105.5 秒（直す前の同じ計測は 101.0 秒。15 章と solutions が数秒ずつ動く）。
- 章ごとの「比べる対象」の数は変えていない（`test_chapters_keep_their_checked_blocks` が通る）。
- 直す前の版に新しい試験を当てると、`shell_op` が無いので import の時点で落ちる（`ImportError: cannot import name 'shell_op'`）。
- ステージした差分の漏洩検査: 0 件（メールアドレス・ホームのパス・トークン）。
- セッション記録の `--check`: この担当は `log/sessions/` にコピーしない（統括がやる）。

## 確かめていないこと・残したこと

- 章のコマンドで `|`（パイプ）・`>`（リダイレクト）・`$VAR` の展開・`$(...)` はもう使えない。使うと「飛ばした」になり、**赤くはならない**ので、章を書いた人は `docs_check` の出力の「飛ばした」を見る必要がある。今の章には無い。
- 終了コードを既定で見る直し（問題 2 の残り）はしていない。
- `auto_skip` の `\bpytest\b` は、コマンドに `pytest` を含むパス（`/tmp/pytest-of-...`）でも当たる。既存の癖で、今回は直していない。
- 実機・Windows は無い。`shell=False` の動きはこの PC の Linux でだけ確かめた。
