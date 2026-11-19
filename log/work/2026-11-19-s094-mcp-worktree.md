# S094 `mcp-worktree`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s094-mcp-worktree` |
| worktree | `.git-worktree/s094-mcp-worktree` |
| セッション記録 | 統括が finish-session で追加 |

## 依頼

SolidCraft の MCP サーバーについて、推論のまま残っていた 3 点（worktree の `cad/` が拒否されるか／登録した MCP が新しいセッションでツールを出すか／「読み取りだけ」の 10 個が本当にファイルを書かないか）を、`solidcraft-cli mcp` を自分で立てて試し、`doc/cad-mcp.md` を書き直す。Claude Code の登録・許可リスト・`cad/` の設計データは変えない。

## 決めたこと

- 試しは小さな Python（`subprocess` で `solidcraft-cli mcp`、標準入出力の JSON-RPC）。スクリプトと写しは scratchpad の `s094/` で、リポジトリには入れない。`XDG_CONFIG_HOME`・`XDG_CACHE_HOME`・`XDG_DATA_HOME` を scratchpad に向けた（標準エラーの `recovery` の場所が scratchpad の下になったことで効いたと確認）。
- 書く側の試しは scratchpad に写した設計データ（`fake/`、`sym/`、`ext/`、`ro/`）だけ。リポジトリの `cad/` は `open` で読んだだけ。
- 推薦は案 2（`.git-worktree` まで）にした。決めるのは発注者で、設定は変えていない。

## やったこと（試した呼び出しと応答の要点。パスは伏せた）

1. 登録と同じ引数（`--allow-path <根>/cad`）: main の `cad/plate_mount.design.json` の `open` は通った（`features: 2, errors: 0`）。この worktree の同じファイルは `isError: true`、`outside the folders this agent may use (…recovery, /tmp/solidcraft-mcp-…, <根>/cad); allow another folder with --allow-path DIR`。**推論は当たっていた**。理由は絶対パスの外であることに加え、文書の「開いた設計の folder は、隠し folder の中なら許可に入らない」（`.git-worktree` は隠し folder）。`--in <WT>/cad/…` では設計は読めるが、標準エラーに `the design's folder is left out because it is inside a hidden folder`、`save` は拒否。
2. 案: (i) `<根>/cad` + `<WT>/cad` → 両方通る、別の worktree は拒否。(ii) `<根>/.git-worktree` → この worktree と別の worktree の `cad/` が通る（配下に及ぶ）、main の `cad/` は拒否。(iii) `<根>` → すべて通る。glob は `ignored: it doesn't exist` で無視。
3. symlink（相対・絶対・folder）、`..`、相対パスは全部拒否。hard link は外のファイルを開けた（文書の注意どおり）。`save` は置き換えて書くので外のファイルは変わらなかった。
4. 書く側: 許可の中の `save` / `export` / `execute file.save_as` / `file.save_mesh` / `batch` は書けて、外は拒否（`file.export_urdf` は付随の `y-base.stl` の所で拒否）。**中では既存の `.txt`・`.sh` を設計のバイト列で上書きでき、元は `.bak` に残る**。`.gitignore` に `*.bak` は無い。
5. 読み取りだけの 10 個: 1 つずつ呼び、呼ぶ前後で scratchpad の写し・XDG・サーバーの scratch folder の（相対パス、大きさ、更新時刻）を比べて差 0 件。設計ファイルの SHA-256 はリポジトリのものと一致。`skill_reference` の `file` に `../`・絶対パスを渡すと `Unknown file`。10 個すべて残る。
6. `screenshot`: 許可内の `path` でも 75 秒返らず（GPU なし。標準エラーは `libEGL warning`）、サーバーが詰まって後続も返らなかった。許可外の `path` や `compare_picture` の許可外の `reference` は先に拒否。
7. `--require-allow-path`: 全部の `--allow-path` が無効なら終了コード 1。`--allow-path` なしの `--require-allow-path` は起動した（終了コード 0）。
8. 公式の文書: `docs/mcp.md` を v0.44.1 の raw から取り直し（JST 19:41）、S051 の写しと一致。Claude Code の許可の書式は `https://code.claude.com/docs/en/permissions`（WebFetch、JST 19:41）の「`mcp__<server>__<tool>` と `mcp__<server>__*`」。
9. `~/.claude.json` の `projects` で `mcpServers` を持つのは、リポジトリの根だけ（中身は読まず、キーの有無だけ見た）。

変更したファイル: `doc/cad-mcp.md`（「未解決の点」を「試した結果」に、ツール一覧と許可リストの提案、推薦、次のセッションの確かめ手順、7 節）。

## 検証

- 試しは scratchpad のスクリプト。上の各項は応答の原文を見て書いた。
- 立てた MCP サーバーは各スクリプトの終了時に自分で止めた。終了後に `ps` で `solidcraft-cli` が 0 件。
- `git status --short`: 自分の 2 ファイルだけ。
- ステージした差分の漏洩検査（ホームのパスとユーザー名）: 0 件（コミット前に確認）。
- `uv run pytest`: 実行していない（コードを変えていない）。

## 確かめていないこと・残したこと

- **登録した MCP が新しいセッションでツールを出すか**: 試せない（【未確認】のまま）。手順 2 行を `doc/cad-mcp.md` に書いた。
- local スコープの登録は folder ごと。worktree の folder で直接 `claude` を起動すると登録が見えない可能性（【未確認】）。
- アプリにつないだ形（`--connect`）での許可の動き。`file.send_to_slicer`・`sketch.text` のフォントなど、ほかのファイルを触る命令。`--allow-any-path` の実測。
- 試しの途中で、案 (i)・(ii) の確認のため、別の worktree（S091）の `cad/plate_mount.design.json` を `open` で**読んだ**（書いていない）。
- 他のファイルで「未解決の点」を指している所がある（`doc/textbook/16-enclosure.md` の 42 行、`doc/plan/2026-11-20-start-here.md` の 23 行、`log/review/2026-11-19-s055-audit5-claude.md` の N-1）。見出しは「試した結果（旧「未解決の点」）」にしたが、本文の更新（拒否は確認済み、推薦は案 2）は統括の判断で。
