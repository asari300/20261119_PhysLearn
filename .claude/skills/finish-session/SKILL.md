---
name: finish-session
description: PhysLearn のセッションを締める。pytest、伏せ字にしたセッション記録のコピーと漏洩の検査、作業記録の仕上げ、feature ブランチへのコミット、main への --no-ff マージ、push、CI の確認、終わった worktree の片付けまでを順に行う。「作業を終わる」「まとめて」「コミットして」と言われたとき、または一区切りついたときに使う。
---

# セッションの締め

順に通す。**どれかが落ちたら、そこで止めて報告する。** 以下は worktree（`$WT`）で実行する。

```bash
MAIN=$(git worktree list --porcelain | awk '/^worktree /{print $2; exit}')
BRANCH=$(git branch --show-current)
```

## 1. 試験（コードを触ったとき）

```bash
uv run pytest
```

コードの出力が変わる変更をしたときは、先に `uv run python -m physlearn.docs_check --mujoco` を回し、差が出た章を直す（出力は走らせた結果をそのまま貼る。CI の `docs` が main で同じものを見張る）。

## 2. セッション記録をコピーして伏せ字を検査する

フックは main の `log/local/` に書いている。最新に書き直してからコピーする。

```bash
MD=$(python3 .claude/hooks/save_session_log.py --latest --match "$BRANCH")
cp "$MD" log/sessions/
python3 .claude/hooks/save_session_log.py --check log/sessions/*.md
```

- 並列のセッションがあるので `--match "$BRANCH"` で絞る。セッション ID が分かれば `--session <ID>` が確実。
- 取りこぼしは **0 件**であること。あればフックの `REDACTIONS` を直して作り直す。手で直さない。
- `log/local/raw/` は絶対にコミットしない。

## 3. 作業記録を仕上げる

`log/work/<日付>-sNNN-<topic>.md` の「決めたこと / やったこと / 検証 / 残したこと」を埋める。検証は数字で。通っていない項目は「通っていない」と書く。計画を変えたら `doc/plan/` も同じコミットで直す。

## 4. 漏洩を検査してからコミットする

```bash
git add -A && git status --porcelain     # 意図しない差分が無いか読む
# 足した行を、セッション記録と同じ規則（フックの REDACTIONS・ローカルのユーザー名・Windows のプロファイル名）で検査する
F=$(mktemp) && git diff --cached -U0 | grep '^+' | cut -c2- > "$F"  # 行頭の + を落とす（メールの規則に + が入る）
python3 .claude/hooks/save_session_log.py --check "$F" && echo "漏洩の疑い 0 件" || echo "漏洩の疑いあり。止める"
rm -f "$F"
git commit                               # 日本語で「SNNN: 何を・なぜ」
```

## 5. main に --no-ff でマージする

```bash
git -C "$MAIN" status --porcelain        # 未コミットの変更があれば止めて伝える
git merge main                           # 先に最新の main を取り込み、uv run pytest を回し直す
git -C "$MAIN" merge --no-ff -m "Merge $BRANCH: <要約>" "$BRANCH"
```

## 5b. push して CI を見る

```bash
git -C "$MAIN" push origin main
gh run watch --exit-status               # test / docs / firmware は必須。firmware-mg24 は落ちても全体は落ちない
```

- 公開リポジトリ。4 の漏洩検査を省かない。
- CI が落ちたら main に直しを入れる。force push はしない。
- 完全に終わった worktree は、main に取り込み済み（`git branch --merged main` に出る）で `git -C "$WT" status --porcelain` が空と確かめてから片付ける。

```bash
git -C "$MAIN" worktree remove "$WT" && git -C "$MAIN" branch -d "$BRANCH"
```

## 6. 報告する

作ったもの、検査の数字、ブランチと worktree のパス、main のコミット、積み残し。
