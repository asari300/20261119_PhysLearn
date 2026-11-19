---
name: start-session
description: PhysLearn で新しいセッション（作業）を始める。S 番号と topic を決め、git worktree に feature ブランチを切って uv sync し、作業記録の下書きを作る。「作業を始める」「次のセッション」「worktree を切って」と言われたとき、またはこのリポジトリで実装・文書作成を始める前に使う。
---

# セッションの開始

理由は [CLAUDE.md](../../../CLAUDE.md) の「1. 作業は git worktree の feature ブランチで行う」。

## 1. S 番号と topic を決める

- S 番号は [計画](../../../doc/plan/2026-11-19-plan.md) の表と `log/work/` の最後の番号から決める（3 桁、例 `S009`）。
- topic は英小文字とハイフン。迷うときだけユーザーに確かめる。

## 2. worktree を作る

```bash
MAIN=$(git worktree list --porcelain | awk '/^worktree /{print $2; exit}')
TOPIC=sNNN-<topic>
WT="$MAIN/.git-worktree/$TOPIC"
cd "$MAIN"
git worktree list                 # 同名が無いか
git status --porcelain            # main に未コミットの変更が無いか。あれば止めて伝える
git worktree add -b "feature/$TOPIC" "$WT" main
cd "$WT" && uv sync
```

## 3. 作業記録の下書きを作る

`log/work/<YYYY-MM-DD>-sNNN-<topic>.md` を [log/work/_TEMPLATE.md](../../../log/work/_TEMPLATE.md) から作り、「日付 / ブランチ / worktree / 依頼」まで埋める。

## 4. 以降は worktree の中で作業する

すべての編集とコマンドを `$WT` で行う。カレントディレクトリが戻る環境では絶対パスで `$WT` を指す。終わったら `/finish-session`。
