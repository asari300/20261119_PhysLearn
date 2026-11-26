# S127 `review-fixes`

| | |
| --- | --- |
| 日付 | 2026-11-27 |
| ブランチ | `feature/s127-review-fixes` |
| worktree | `.git-worktree/s127-review-fixes` |
| セッション記録 | 統括が `log/sessions/` にコピーする（この担当はコピーしない） |

## 依頼

S126 のレビュー（`log/review/2026-11-27-s126-review-night.md`、指摘 10 件）を、統括の採否の表どおりに直す。最小の変更で、新しい抽象・オプション・依存は足さない。

## 決めたこと

統括の採否のまま。この担当で判断したのは次の点。

- #2 の窓: 最初は `redact(s[:n+256])[:n]` にしたが、統括が「`redact` は縮むので、絶対パスが 12 行ほど並ぶと、窓の末尾（生の文字列を切った所）の断片が `[:n]` の中に入る」を再現した（メールの頭 `taro.yamada@` が残り、`leftovers` は 0 件）。そこで決まりを「`redact` を通した結果が `n + SECRET_MAX`（256）字以上あるか、全文を通し終えたときだけ `[:n]` で切る」にし、窓は `n + 1024` から 2 倍ずつ、最後は全文にした。長い英数字の連なりは縮まないので 1 回で済む（8 万字で 0.024 秒）。
- #3 の文書: `--dt` の範囲を書いた所は `doc/troubleshooting.md` の 1 行（実際の断りの文の「原文」）と `--help` だけ。`doc/protocol.md`・`doc/bringup.md`・教材の章には無かった（`git grep` で確認）。
- #5b の形: `[ -s "$F" ] && 検査 && echo 0 件 || echo 止める` にして、空のとき「0 件」が出ない形にした。追加の行を出すだけだと、続く検査が「0 件」と出してしまう。
- #7: `turn` は 1 行でも通る（積分 0 度）ので、見出しだけ（0 行）を断る文は他と同じ「サンプルが 2 行未満」を使った（文が少し広い）。
- #9 は不採用（下）。

## やったこと

| # | 変えた場所 | 試験 | 前後の数字 |
| --- | --- | --- | --- |
| 1 | `.claude/hooks/save_session_log.py` `_local_names` に `functools.lru_cache` | `test_local_names_is_cached` | 14 MB の記録で `--transcript` の保存 15.37 秒 → 0.66 秒（窓の直しの後も 0.66 秒）。4.8 MB（この統括セッション）で 6.12 秒 → 0.30 秒。既存の monkeypatch（`setattr(hook, "_local_names", ...)`）は効き続ける（試験 2 件が通る） |
| 2 | 同 `clip`: `len(s) <= n` なら全文を `redact`。それ以外は頭の窓（`n + 1024` 字、結果が `n + SECRET_MAX` 字未満なら 2 倍、最後は全文）に `redact` を通して `[:n]`。「残り N 字」は元の長さから | `test_clip_long_alnum_run_is_fast`（8 万字の `a`、2 秒未満、残り 79,200 字）、`test_no_fragment_when_redaction_shrinks_the_window`（統括の再現。旧 clip の写しで落ちる）、`test_token_longer_than_the_margin_across_the_boundary`。境目の既存 2 件も通る | 8 万字の連なりで 24 秒 → 0.024 秒（試験は 2 秒未満を見る）。絶対パス 8000 行は 0.0014 秒 |
| 3 | `src/physlearn/link.py` `--dt` を `0.01 <= dt <= 0.1`、断りの文、`--help` の文。`doc/troubleshooting.md` の原文の行 | `test_args_rejected` に `--dt 0.5` を足した | `jog --seconds 1.0 --dt 0.66` が 1.32 s まで超えた抜け道を塞いだ（超過は dt/2 = 0.05 s 以内） |
| 4 | `tests/test_real_loop.py::test_args_rejected` が、`error:` の後ろに悪い引数の名前が出ることを見る（usage の行にも `--dt` が出るので、後ろだけを見る） | 同 | 直しを外した写しで確かめた: `--dt` の確認を消す → 落ちる、上限を `< 1` に戻す（`--dt 0.5` が通ってポートの断りになる）→ 落ちる。最初の形（`err` 全体に名前があるか）は外しても通ったので、`error:` の後ろに直した |
| 5a | `.claude/skills/finish-session/SKILL.md` の 4 に、止まったときの手順（場所を探す 1 行、例の値なら理由を書いて進める、本物なら止める） | - | - |
| 5b | 同、足した行のファイルが空なら「0 件」と出さず止める | スキルのブロックを抜き出して実行（空のファイルは「止める」、通常は「0 件」） | - |
| 5c | フック `redact`（`re.I`）と `leftovers`（`lower()` の比較）。ローカルの名前の大文字小文字を区別しない | `test_local_name_is_case_insensitive`（例の名前は `foobar`） | `FooBar`・`FOOBAR` が `<user>` になり、`--check` にも当たる |
| 6 | `link.run_loop`: 各回の最後に `np.abs(y) <= gate.gz_limit`（自前の閾値なし）。理由は「`|gz| > 15.0（最後のサンプル）`」 | `test_run_loop_checks_the_last_sample`（1 回目の最後だけ gz=100 の代役） | 直す前は理由 ""・2 回目に進む。直しを外した写しで落ちる |
| 7 | `imu.py` `main`: `turn` は 1 行未満、他は 2 行未満で断る | `test_stats_refuses_short_log_with_a_sentence` に `turn` の見出しだけを 1 ケース足した | IndexError のトレースバック → 1 行の文 |
| 8 | `compare.load` が `ValueError` に `path: ` を足す。`holdout` の文面と `main` の 1 行化は変えない | `test_cli_refusal_is_one_line_for_fit_holdout_spread` の `spread` の期待を「ファイル名: 文」に | `spread short.csv p.json` の断りにファイル名が出る |
| 9 | 変えない（下） | - | - |
| 10 | `run_loop` の docstring を事実に（ゲートの作動では投げない。通信の例外は上がり、その回の行は返らない） | - | コードは変えていない |

### #9 を採らなかった理由

S100 が「`...` を含む行が 1 つでも実のある行なら従来どおり」と決めて試験にしている。章の抜粋の書き方に関わるので、変えるなら計画の持ち主が決める。`foo ...` だけの抜粋が何も確かめない穴は残る（今の章には無い。数の試験が一致 50 を守っている）。

## 検証

- `uv run pytest -q`（`--all-extras`）: 189 passed（main は 183。足したのは 6 件: フックの 5 件、`run_loop` の最後のサンプル 1 件。`test_args_rejected`・`test_stats_...`・`test_cli_refusal_...` は既存の試験を書き換えた）
- `uv run python -m physlearn.docs_check --mujoco`: 一致 50、差 0、飛ばした 6（04: 1、05: 10、06: 7、07: 4（飛ばし 1）、08: 1、11: 3、12: 0（飛ばし 5）、13: 4、14: 6、15: 7、16: 1、solutions: 5、README: 1、bringup: 0。合計 50 / 0 / 6）。所要 1 分 11 秒
- フックの実行時間: 上の表のとおり（15.37 秒 → 0.66 秒、6.12 秒 → 0.30 秒）。出来た整形版（14 MB・4.8 MB の両方）の `--check`: 取りこぼし 0 件（検査 2 件）
- ステージした差分の漏洩検査: 窓の直しの前のコミットは 0 件。窓の直しのコミットは 2 件当たった。どちらも `tests/test_session_log_hook.py` の例の値（統括の再現にある架空のパス `/home/someuser1234567890` と、`example.com` のメールアドレス）で、本物ではない。`git diff --cached | grep -nF` で場所を確かめ、finish-session の手順どおり理由を書いて進めた

## 確かめていないこと・残したこと

- 残した指摘: なし（#9 は不採用）。
- #2 の限界: `SECRET_MAX`（256）字より長い 1 つの秘密が境目をまたぐ場合。メール・トークン・名前は 256 字より短いと仮定している。長いトークンは確かめた: `ghp_` + 3000 字の `A` が n 字目と n+256 字目をまたぐ場合、窓（1824 字）に頭の 36 字以上が入るので、`ghp_` のトークンの規則で全体が `<redacted>` になる（試験 `test_token_longer_than_the_margin_across_the_boundary`）。ただし `\bghp_` は直前が語の文字だと掛からない（`x` の直後など）。これは `redact` 全体の規則の性質で、clip の窓とは関係ない。【残り】トークンの規則に掛からない、256 字より長い秘密（規則が無い形式）はこの限りでない。
- フックを本物の Claude Code から起動したときの所要時間は計っていない（`--transcript`・`--latest` の直接実行で計った）。
- 実機は無い。#3・#6 は偽の XIAO と代役でだけ確かめた。
