# log — 作業とセッションの記録

作業は**すべて記録を残す**。方針は [../CLAUDE.md](../CLAUDE.md) の「4. ログはすべて残す」。

```text
log/
├── local/      フックの出力（git 管理外）。main のチェックアウトにだけできる
│   ├── <日付>-<セッションID>.md             整形版（伏せ字済み）
│   └── raw/<日付>-<セッションID>.jsonl.gz   完全な生ログ（伏せ字なし。絶対にコミットしない）
├── sessions/   公開用のセッション記録。finish-session が local/ からコピーする
├── review/     レビューの指摘と採否（手動。1 レビュー 1 枚）
└── work/       作業記録（手動。1 セッション 1 枚）
```

## 公開と CI

remote は GitHub の公開リポジトリ。`log/sessions/`・`log/work/`・`log/review/` はそのまま公開されるので、コミットの前の `--check` と漏洩検査を省かない。push の後は `gh run watch` で CI（`test` / `firmware` / `firmware-mg24`）を確かめる。

## local/ — 自動、コミットしない

- `.claude/settings.json` の `Stop` / `SessionEnd` フックが [../.claude/hooks/save_session_log.py](../.claude/hooks/save_session_log.py) を呼ぶ。毎ターン上書きするので、途中で落ちても直前まで残る。
- worktree から手で実行しても main の `log/local/` に書く（マージで未追跡ファイルとぶつからないように）。
- `raw/*.jsonl.gz` が完全な記録。`gunzip -c <file> | jq` で辿れる。メールアドレスやローカルのパスがそのまま入っている。

## sessions/ — 公開用、コミットする

- コミットの前に `python3 .claude/hooks/save_session_log.py --check log/sessions/*.md` で取りこぼし 0 件を確かめる。
- 伏せ字にするもの: メールアドレス、ローカルのユーザー名とホームのパス、トークンらしき文字列、LAN のアドレス。
- 取りこぼしはフックの `REDACTIONS` に規則を足して作り直す。手で直さない。

## work/ — 手動

セッション記録が「何が起きたか」の全量、作業記録は「何を決めたか・なぜか」。雛形は [work/_TEMPLATE.md](work/_TEMPLATE.md)。

## review/ — 手動

- 名前は `<日付>-sNNN-<topic>-<レビュアー>.md`。雛形は [review/_TEMPLATE.md](review/_TEMPLATE.md)。
- レビュアーの指摘は原文のまま貼り、採否（採用 / 保留 / 不採用）と理由を実装側が書く。差分そのものは書かない。
- コミットの前に `--check log/review/*.md` で取りこぼし 0 件を確かめる。
