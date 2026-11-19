# このリポジトリでの作業ルール

PhysLearn は、XIAO と IMU で Physical AI（Sim2Real・Real2Sim）を学ぶ教材とコード（Python と Arduino のスケッチ）。計画は [doc/plan/2026-11-19-plan.md](doc/plan/2026-11-19-plan.md)。

## 1. 作業は git worktree の feature ブランチで行う

`main` の作業ツリーを直接編集しない。1 セッションごとに worktree を切る。手順は `/start-session`、締めは `/finish-session`。

```bash
MAIN=$(git worktree list --porcelain | awk '/^worktree /{print $2; exit}')
cd "$MAIN" && git worktree add -b feature/<topic> .git-worktree/<topic> main
cd .git-worktree/<topic> && uv sync
```

- `<topic>` は `sNNN-<英小文字とハイフン>`（例 `s004-sim-core`）。ブランチは `feature/<topic>`、worktree は `.git-worktree/<topic>`（`.gitignore` 済み）。
- `.venv` を worktree 間で共有・symlink しない。
- main に未コミットの変更があったら、止めてユーザーに伝える。勝手にコミットも stash もしない。
- remote は無い。締めは「main に `--no-ff` でマージ」まで。

## 2. ディレクトリの意味

| 場所 | 意味 |
| --- | --- |
| `src/physlearn/` | Python パッケージ。境界は `api.py` の `Command` / `Obs` / `Plant` |
| `firmware/` | XIAO の Arduino スケッチ |
| `tests/` | pytest の試験 |
| `doc/plan/` | 計画。変えたら同じコミットで直す |
| `doc/research/` | 調査の記録。事実ごとに出典 URL と確認日 |
| `doc/adr/` | 設計判断（状態 / 背景 / 決定 / 結果）。覆すときは消さずに Superseded にする |
| `doc/textbook/` | 教材 |
| `log/work/` | 作業記録（手動、1 セッション 1 枚） |
| `log/sessions/` | 伏せ字にしたセッション記録（finish-session がコピーする） |
| `log/review/` | レビューの指摘と採否（1 レビュー 1 枚） |
| `log/local/` | フックの出力。生ログを含むので**コミットしない** |

## 3. 文書の書き方

- 日本語の平易な文で書く。1 文に 1 つのこと。
- 調べた事実には出典 URL と確認日を付ける。確かめていないことは【未確認】と書き、推測を事実のように書かない。
- 試せなかったこと・通っていない検査は、そう書く。

## 4. ログはすべて残す

- セッション記録（自動）: `.claude/settings.json` の `Stop` / `SessionEnd` フックが [.claude/hooks/save_session_log.py](.claude/hooks/save_session_log.py) を呼び、main のチェックアウトの `log/local/` に整形版（伏せ字済み）と生ログ（`raw/*.jsonl.gz`、伏せ字なし）を書く。
- 公開用は finish-session が `log/sessions/` にコピーし、`python3 .claude/hooks/save_session_log.py --check log/sessions/*.md` で取りこぼし 0 件を確かめてからコミットする。取りこぼしはフックの `REDACTIONS` を直して作り直す。手で直さない。
- 作業記録（手動）: `log/work/<日付>-sNNN-<topic>.md` を [_TEMPLATE](log/work/_TEMPLATE.md) から。何を決めたか・なぜか・検証の数字を残す。
- 詳しくは [log/README.md](log/README.md)。

## 5. 締めのチェックリスト

`/finish-session` に従う。どれかが落ちたら止めて報告する。

1. `uv run pytest` が通る（コードを触ったとき）
2. セッション記録をコピーし、`--check` で取りこぼし 0 件
3. ステージした差分に、メールアドレス・ホームのパス・トークンが 0 件
4. 作業記録を数字で仕上げ、feature ブランチにコミット
5. main に `--no-ff` でマージ
