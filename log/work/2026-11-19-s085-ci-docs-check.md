# S085 `ci-docs-check`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s085-ci-docs-check` |
| worktree | `.git-worktree/s085-ci-docs-check` |
| セッション記録 | 統括が写す |

## 依頼

章に貼った出力が今のコードの出力と合っているかを CI で見張る。あわせて、教材の相対リンクが切れていないかの検査を足す。

## 決めたこと

- ジョブ `docs` は `if: push または workflow_dispatch` のときだけ。`docs_check` は章のコマンドを `shell=True` で実行するので、将来 `pull_request` が足されても第三者の章が走らない形にした。`permissions` は `contents: read` のまま、シークレット無し。
- `docs_check` は全体の件数を出さない（章ごとの行だけ）。道具は直さず、ワークフローで表を `tee` し、`awk` で一致・差・飛ばしの合計を最後に 1 行出す。終了コードは道具のものをそのまま返す。
- `timeout-minutes: 15`（ローカルで全章 23〜37 秒、並列で負荷が高いと 100 秒）。
- リンク検査は `pytest` に入れる（`test` ジョブで毎回走る）。対象外は `log/sessions/`、`log/work/2026-*`、`log/review/2026-*`、`.git-worktree/`、`.venv/` など。`doc/plan/` と `doc/research/` は対象に含めた。

## やったこと

- `.github/workflows/ci.yml`: ジョブ `docs`。
- `tests/test_links.py`: 標準ライブラリだけ。コードブロックと `コード` の中は見ない。`path#anchor` は `path` だけ見る。
- `CLAUDE.md`、`.claude/skills/finish-session/SKILL.md`: CI の説明と締めのチェックリストに `docs_check` を足した。

## 検証

- `uv run --extra mujoco --extra viz pytest -q`: 163 passed（84 s、負荷が高い時間帯）。
- `python -m physlearn.docs_check --mujoco`（全章）: 一致 28 / 差 0 / 飛ばした 6、終了コード 0、99 s（並列で他の担当が動いていた）。
- 章のコピー（11 章）の出力を 1 文字変えると、差 1・終了コード 1。ワークフローの `run` ブロックを抜き出して `bash -e` で回して確かめた（合計の行も出る）。
- `actionlint`（`uvx --from actionlint-py actionlint`）: 指摘 0 件。
- リンク検査: 52 ファイル・約 294 リンク、切れ 0 件、0.07 s。仮ファイルで、切れたリンクを行つきで検出すること、コードブロックとコード片の中を見ないことを確かめた。

## 確かめていないこと・残したこと

- GitHub 上で `docs` が動くか（ランナーの遅さ、`uv sync` の時間）は push 後に見る。
- `docs_check` が 13・14 章と `solutions.md` で 0 件（一致も飛ばしも 0）なのは、対象の書き方に合うブロックが無いため。見落としかは未確認。
- README のバッジと CI の説明は触っていない。
