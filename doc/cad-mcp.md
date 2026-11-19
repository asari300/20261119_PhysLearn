# SolidCraft で筐体を設計する: ブラウザー版・CLI・MCP

発注者の使い方は「ブラウザー版が主。GUI で人が設計するのと、Claude Code から MCP で設計させるのと、両方」。この文書は、その 3 つの道具をリポジトリの `cad/` でつなぐ手引き。
調べた日と版: JST 2026-11-19、SolidCraft v0.44.1（`tangency-labs/solidcraft`）。出典の短縮: [gh] = `https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.44.1/`（JST 17:48〜17:52 に取得）。
実行した所には出力を載せた。動かしていない所は【未実行】、確かめていない所は【未確認】。

## 1. 3 つの道具の関係

```
 人 ── ブラウザー版 / Windows のデスクトップ版（GUI）
        │ 保存（設計 JSON）                    ▲ 開く（設計 JSON か .sc）
        ▼                                      │
   solidcraft-cli script ──►  cad/*.design.json（正本）+ cad/*.json（レシピ） ──► solidcraft-cli run --save x.design.json
   （設計 JSON → レシピ。外観は落ちる）  （設計 JSON が正本、レシピを添える）  （レシピ → 設計 JSON）
                                 │   ▲
              ┌──────────────────┤   └── MCP（solidcraft-cli mcp）── Claude Code が読み書き
              ▼                  ▼
   solidcraft-cli run        CI（.github/workflows/cad.yml）
   ├ STEP / URDF              STEP を作り、体積・質量・Izz を
   └ 質量特性 mass.json       cad/expected.csv と比べる
        │
        ▼
   physlearn.solidcraft_props（SI に換算）→ sim（physlearn.cad に渡す）
```

要点は、**中心に置くのはファイル（`cad/*.design.json`）で、画面ではない**こと。人の GUI と Claude の MCP は、同じファイルを順番に開いて直す。

### ブラウザー版は MCP につながるか: つながらない（明記した一文は無く、文書からの読み）

公式の文書の原文（[gh]`docs/browser-api.md`）:

> An agent with JavaScript evaluation access to this tab can make the same calls. The API does not register WebMCP tools or expose a network listener.

**原文が言っていること（事実）**: ブラウザー版が出すのは、タブの中の `window.solidcraft`（JavaScript）で、"does not register WebMCP tools or expose a network listener"。つまり MCP のツールを登録せず、外からつなぐネットワークの待ち受けも持たない。
**原文が言っていないこと**: 「ブラウザー版は MCP につながらない」とそのまま書いた一文は、公式の文書に見つからなかった。MCP の文書（[gh]`docs/mcp.md`）は、アプリにつなぐ形をデスクトップ版の制御の口として説明するだけで、ブラウザー版には触れていない。原文: "The desktop app opens its control channel on `127.0.0.1:27878` (or the next free port when that one is taken) when Preferences > Assistant > Agents through MCP > "Let AI agents connect" is on."、"the server finds the app's control token in the token file the app wrote for that port"（同じ文書の例には `7878` とも書いてあり、番号は文書の中で食い違う。実際はアプリが表示するはず【未確認】）。
**推測（上の 2 つの原文からの読み）**: ブラウザーのタブは待ち受けも、ファイルに token を書くこともできないので、`solidcraft-cli mcp` はブラウザー版につなげない。**結論: MCP に直接つながるのは、窓なしの `solidcraft-cli mcp` と、デスクトップ版（Windows のアプリ）。ブラウザー版は、ファイル（設計 JSON）で受け渡す。** ブラウザー版を MCP につなぐ別の道は見つからなかった。将来の対応は【未確認】。

## 2. `cad/` に置く「正」の形式: 設計 JSON（レシピのコマンド列を添える）

3 つの形式を比べた（同じ `cad/plate_mount.json` から、手元で作って確かめた）。

| 形式 | 大きさ | 差分 | CLI | ブラウザー版・GUI | MCP の `open` |
| --- | --- | --- | --- | --- | --- |
| コマンド列の JSON（`{"commands":[...]}`） | 2.5 KB、22 行 | 1 行 1 コマンド。パラメーター 1 つの変更で 4 行 | `run` が走らせる | File > Open で開くかは【未確認】 | **開けない**（`.sc`・設計 JSON・STEP・メッシュだけ） |
| 設計 JSON（`run --save x.design.json`、`"format": "solidcraft/58"`） | 10.7 KB、505 行 | 同じ変更で 12 行。再保存でバイト一致（`name` 欄はファイル名から決まる） | `run` `eval` が直接開く。`--param-check strict` も通る | File > Open / Save As JSON（[gh]`docs/book/src/guide/files.md`）【未実行】 | 開ける・`save` で書ける（確かめた） |
| `.sc`（コンテナ） | 11.8 KB（zip） | 読めない | 開ける | 開ける | 開ける |

**決定: 設計 JSON を正本（`cad/<名前>.design.json`）にし、コマンド列の `cad/<名前>.json` はレシピ（人が読む・Claude が書く出発点）として添える。** `.sc` はコミットしない。理由は 3 つ。

1. **3 つの道具すべてが開けるのは設計 JSON だけ**（上の表）。
2. **人が直した結果を失わない**。`solidcraft-cli script`（設計 → コマンド列）は外観を落とす。CLI 自身が `note: the script leaves out appearances (colours of bodies and faces)` と出し、色を付けた設計 JSON を往復すると `appearances` の 13 行が消えた（確かめた）。部品や関節の落ちは【未確認】。
3. **CI が両方を検査できる**。`cad/expected.csv` に両方の行を書き、レシピと正本が同じ数字になるかを見る。

弱点: 差分が大きめで、形式の番号が版に依存する（`solidcraft/58`）。**ブラウザー版が `cad/*.design.json` を開けるか・書き出せるかは未実行**。決め手がブラウザー版でしか分からないので、確かめ方を [cad/README.md](../cad/README.md) の「どれを正にするか」に書いた。通らなければ当面は「レシピを正、設計 JSON は派生」に戻す。

### 往復と、ブラウザー版での操作（CLI の所は確かめた。ブラウザー版は【未実行】）

```
$ solidcraft-cli run cad/plate_mount.json --save plate_mount.design.json       # レシピ → 設計 JSON
$ solidcraft-cli run plate_mount.design.json --param-check strict --out x.step  # 設計 JSON を直接 run。終了コード 0
$ solidcraft-cli script plate_mount.design.json --out plate_mount.script.json   # 設計 JSON → レシピ（外観は落ちる）
plate_mount.script.json: 12 steps
$ solidcraft-cli run plate_mount.script.json --out x.step --json-out x.json
  total.volume_mm3 = 31111.170273681717        （元の cad/plate_mount.json と同じ値）
```

- ブラウザー版で開く: https://solidcraft.io/app を開き、File > Open（Chrome・Edge・Opera ではブラウザーの開くダイアログ。Firefox・Safari は保存先がブラウザーの中になる。[gh]`docs/book/src/guide/files.md` の "Saving in the web app"）。設計 JSON は `.json` の名前のまま開く（"Opening detects the format from the contents"）【未実行】。
- ブラウザーから出す: File > Save As JSON（"Save As JSON is also available in the File menu on desktop and web"）、または File > Download design【未実行】。出てきた設計 JSON を `cad/<名前>.design.json` に上書きしてコミットする。レシピ（`cad/<名前>.json`）が要るときだけ、上の `script` で作り直す。
- URL で開く道: `?open=<エンコードした HTTPS の URL>` で、公開された `.sc` を開く（[gh]`docs/book/src/guide/getting-started.md`）。設計 JSON（`.sc` は「コンテナまたは JSON の設計」と files.md にある）を `raw.githubusercontent.com` に置いてこれで開けるかは【未確認】。

## 3. CLI の入れ方（この PC = WSL2 で動いた手順、置き場所は C に決まった）

発注者の決定（JST 17:50 頃）: 置き場所は C（GUI は Windows、CLI と MCP は WSL）。候補 A・B・C・D の比較は [doc/research/2026-11-19-solidcraft.md](research/2026-11-19-solidcraft.md) の「CLI の常設の置き場所の候補」。

WSL 側（動いた。S042 と S051 が確かめた）:

```bash
# 公式の Release から、Linux x86_64 の tar.gz。SHA-256 は 3 通りで一致: API の digest、SHA256SUMS.txt、手元の sha256sum
curl -sSfL -O https://github.com/tangency-labs/solidcraft/releases/download/v0.44.1/solidcraft-0.44.1-linux-x86_64.tar.gz
echo "164097743f6ff11c1eeb90a4313964728955e297689052053e4e5d8d20a64229  solidcraft-0.44.1-linux-x86_64.tar.gz" | sha256sum -c -
mkdir -p ~/.local/opt && tar -xzf solidcraft-0.44.1-linux-x86_64.tar.gz -C ~/.local/opt   # 展開すると 469 MB（CLI だけなら bin/solidcraft-cli の 203 MB）
ln -s ~/.local/opt/solidcraft-0.44.1-linux-x86_64/bin/solidcraft-cli ~/.local/bin/solidcraft-cli
solidcraft-cli --version      # solidcraft-cli 0.44.1
```

この PC の実際の置き場所は `~/.local/opt/solidcraft-0.44.1/`（統括が展開済みのものをコピーした）と `~/.local/bin/solidcraft-cli`（symlink）。root・FUSE・GPU は要らない。`ldd` で `not found` は 0 件。
API の digest を JST 17:48 に取り直したら、上の値と同じだった（`https://api.github.com/repos/tangency-labs/solidcraft/releases/tags/v0.44.1`）。
**効かない物**: `snapshot` と `gpu` は GPU の無い WSL2 で返らなかった（S042）。`mcp` の `screenshot` も同じで、75 秒待っても返らなかった（S094）。形は `measure` の数字で確かめる。

Windows 側の GUI（発注者が自分で用意する。公式の README の Download 節、[gh]`README.md`）:

- ブラウザー版: https://solidcraft.io/app 。インストール不要。
- デスクトップ版: インストーラー https://github.com/tangency-labs/solidcraft/releases/latest/download/solidcraft-windows-x64.msi 。署名は SignPath の無料の署名で、本番の証明書が入るまで SmartScreen が警告することがある。そのときは「詳細情報」→「実行」（README の原文: choose **More info**, then **Run anyway**）。
- winget のパッケージ `bherbruck.SolidCraft`（ID は旧名のまま）は第三者の索引で見ただけ【未確認】。公式の README には書かれていない。
- Windows 版を入れたら、WSL の CLI と**版を合わせる**（0.44.1）。`/releases/latest/` は新しい正式版が出ると動く。版を固定するなら `/releases/download/v0.44.1/` の資産名（版つき）を使う【資産名は未確認】。

## 4. MCP: Claude Code から設計させる

### 登録の状態（JST 2026-11-19 17:58 に再登録。S055 が 18:0x に `claude mcp get` で確かめた）

発注者の決定（17:50 頃）で、CLI は `~/.local/opt/solidcraft-0.44.1/` に置き、`~/.local/bin/solidcraft-cli` で呼べる。MCP は統括が 17:58 に次のコマンドで登録し直した（local スコープ。このプロジェクトの、この利用者だけに効く。`.mcp.json` は作っていないので、リポジトリには何も入らない）。`<リポジトリの根>` は main のチェックアウトの場所。

```
claude mcp add solidcraft -- solidcraft-cli mcp --allow-path <リポジトリの根>/cad
claude mcp list
solidcraft: solidcraft-cli mcp --allow-path <リポジトリの根>/cad - ✔ Connected
```

- ツールごとの許可は**未設定**（下の「許可リストの提案」）。
- **次に Claude Code を起動したセッションからツールが出るかは【未確認】**。今動いているセッションには出ない。
- 公式の登録の手順（[gh]`docs/mcp.md`）: `claude mcp add solidcraft -- solidcraft-cli mcp`、または プロジェクトの `.mcp.json`。`solidcraft-cli mcp setup --dry-run` は何を書くか見るだけ（使っていない）。
- チームで共有する project スコープ（`.mcp.json` をコミット）という選択肢はあるが、公開リポジトリで `solidcraft-cli` が無い人には動かないので、local スコープのままにしている。

### なぜ `--allow-path` が要るか（実測）

`solidcraft-cli mcp` は、ファイルの読み書きを「許可された folder」に限る。**作業中の folder は、それだけでは許可されない**（[gh]`docs/mcp.md` "The working folder the server was started in does not count by itself"）。`--allow-path` なしで `open` を呼ぶと拒否された（S051。`cad/` のコピーを scratch に置いて試した）:

```
open  → isError: true
  "…/cadcopy/plate_mount.design.json: outside the folders this agent may use (…/solidcraft/recovery, /tmp/solidcraft-mcp-…); allow another folder with `--allow-path DIR`"
```

`--allow-path` を付けると、同じ操作が通った。`open` → `measure`（体積と重心）→ `execute parameters.change {TBD_robo_hole_d: 4}`（`recomputed: 2, errors: []`）→ `measure` → `save` が全部成功した。`--allow-any-path` は付けていない（許可は `cad/` だけ）。正本が設計 JSON なので、Claude は MCP の `open cad/plate_mount.design.json` → `inspect_design` / `measure` / `set_parameter` / `execute` → `save` で、そのまま正本を読み書きできる。コマンド列のレシピ（`cad/*.json`）は MCP の `open` が開けないので、Claude がファイルとして編集するか、`execute` / `batch` に同じコマンドを渡して作らせる。窓なしの MCP を `--in cad/plate_mount.json` で起動すると、コマンド列から始められると公式の文書にある【未実行】。Claude が設計 JSON を直すと、レシピとずれる。ずれは `cad/expected.csv` の両方の行が同じ数字になるかで CI が見つける。

### 試した結果（旧「未解決の点」）: worktree の `cad/` は、登録のままでは拒否される（推論は当たっていた）

JST 2026-11-19 19:35〜19:50、S094 が `solidcraft-cli mcp`（v0.44.1）を自分で立て、標準入出力に JSON-RPC を送って試した（スクリプトは scratchpad。リポジトリの `cad/` には何も書いていない）。登録と同じ引数は `--allow-path <リポジトリの根>/cad`。`--headless` を付けない形でも、SolidCraft のアプリが見つからないので窓なし（`mode: headless`）で動き、応答に `Note: this is a headless session because the SolidCraft app was not found; …` が付く。以下の応答のパスは `<リポジトリの根>`・`<WT>`（作業用 worktree）・`<SCR>`（scratchpad）に置き換えた。

**登録と同じ引数（`--allow-path <リポジトリの根>/cad`）**

| 呼び出し | 結果 |
| --- | --- |
| `open <リポジトリの根>/cad/plate_mount.design.json` | 通った。`{"errors": 0, "features": 2, "name": "plate_mount.design", …}` |
| `open <WT>/cad/plate_mount.design.json` | **拒否された**（`isError: true`） |

拒否の原文: `<WT>/cad/plate_mount.design.json: design container: <WT>/cad/plate_mount.design.json: outside the folders this agent may use (<SCR>/xdg/data/solidcraft/recovery, /tmp/solidcraft-mcp-…, <リポジトリの根>/cad, <リポジトリの根>/cad); allow another folder with `--allow-path DIR``。起動時の標準エラーは `files limited to …recovery, /tmp/solidcraft-mcp-…, <リポジトリの根>/cad and the folders of designs opened or saved here`。

**理由は 2 つ重なっている**（公式の文書 [gh]`docs/mcp.md` の "Which files the agent can reach"、JST 19:41 に v0.44.1 の原文を取り直して手元の写しと一致を確認）。(1) `--allow-path` は絶対パスで、worktree の `cad/` はその外。(2) 開いた設計の folder が自動で許可に入る決まりもあるが、"not in a hidden folder" の条件があり、`.git-worktree` は先頭が `.` の隠し folder なので入らない。実測: `--in <WT>/cad/plate_mount.design.json` で立てると、設計は読み込まれる（`inspect_design` は成功）が、標準エラーに `the design's folder is left out because it is inside a hidden folder; add it with --allow-path if you mean it` と出て、`save` は拒否された。`/tmp` の下の隠れていない folder の設計を `--in` で立てた場合は、許可なしで同じ folder に `open` できた。

**案を 1 つずつ試した**

| 案 | 登録の引数 | 試した結果 | 開けるようになる範囲 |
| --- | --- | --- | --- |
| 現状 | `--allow-path <リポジトリの根>/cad` | main の `cad/` は開く。**worktree は拒否** | main の `cad/` だけ |
| 1 worktree ごとに足す | `--allow-path <リポジトリの根>/cad --allow-path <WT>/cad` | **動いた**。両方の `open` が通り、別の worktree（S091 の `cad/`）は拒否された | 足した `cad/` だけ |
| 2 `.git-worktree` まで広げる | `--allow-path <リポジトリの根>/.git-worktree` | **動いた**。この worktree と別の worktree（S091）の `cad/` の `open` が通った。許可は配下に及ぶ。ただし main の `cad/` は**拒否された**（main も要るなら `--allow-path <リポジトリの根>/cad` を足す） | `.git-worktree` の下の全ファイル（隠しファイルも） |
| 3 リポジトリの根まで広げる | `--allow-path <リポジトリの根>` | **動いた**。main の `cad/` も worktree の `cad/` も通った。標準エラーは `files limited to …, <リポジトリの根>` | リポジトリの根の下の全部（`.git`・`.venv`・`log/local/` の生ログ・他の worktree を含む） |
| （参考）main を例外にする | 現状のまま | main の `cad/` は開けて、`save` は main の作業ツリーを書き換える（書けることは S051 と、上の scratchpad の試しで確認） | main の `cad/` |

`--allow-path` に glob（`<リポジトリの根>/.git-worktree/*/cad`）を渡すと、`allow-path … ignored: it doesn't exist` と出て無視された。**glob は使えない**。

**許可の中で Claude が書ける範囲（ここが危なさの中身）** 許可された folder の中では、`save` が**既存のファイルを拡張子に関係なく上書きできた**。scratchpad の許可 folder で、`notes.txt`・`run.sh` に設計を `save` したら、中身が設計のコンテナ（zip）に置き換わった（元の中身は `<名前>.bak` に残った）。新しい `newfile.py`・`Makefile`・`.hidden.json` も作れた。`export` は stl・obj・step・3mf・glb・urdf・sc の拡張子だけ（`run.sh` は `unsupported format` で拒否）。上書きするとき、元のファイルは `<名前>.bak` として隣に残る。**`*.bak` は `.gitignore` に無いので、`cad/` の設計を `save` で上書きすると `git status` に `cad/plate_mount.design.json.bak` が出る**（コミットしないよう注意）。つまり案 2・3 は「Claude が worktree や根の下の任意のファイル（`src/*.py` など）を設計のバイト列で壊せる」範囲を作る。git で戻せるが、未コミットの変更は `.bak` にしか残らない。

| 案 | Claude が書ける範囲 | 「main を直接編集しない」との折り合い |
| --- | --- | --- |
| 1 | その worktree の `cad/` だけ（最も狭い） | 合う。ただし worktree を切るたびに `claude mcp remove`・`add` と Claude Code の再起動が要る【再起動が要ることは未確認】 |
| 2 | `.git-worktree` の下のすべて（他セッションの worktree も） | 合う（main の `cad/` は許可の外なので、MCP は main を書けない）。登録は 1 回 |
| 3 | リポジトリの根の下のすべて（main の作業ツリーと `.git` を含む） | **合わない**（MCP が main の作業ツリーを書ける）。広すぎる |
| main を例外 | main の `cad/` | 決まりを変える必要があり、`CLAUDE.md` の「main に未コミットの変更があったら止める」と衝突する |

### symlink・相対パス・`..`・hard link で許可の外に出られるか: symlink・`..`・相対パスは出られなかった。hard link は出られる

scratchpad に許可 folder `allowed/` と外の `outside/` を作って `--allow-path <SCR>/sym/allowed` で試した。

| 試し | 結果 |
| --- | --- |
| `allowed/` の中の symlink（相対・絶対）が、外のファイルを指す | **拒否**（`outside the folders this agent may use`） |
| `allowed/` の中の symlink が、外の folder を指す（`link_dir/secret.design.json`） | **拒否** |
| `allowed/../outside/…` | **拒否** |
| 相対パス（サーバーの作業 folder が許可の中。`../outside/…`） | **拒否**。相対パスは絶対に直して比べる |
| `allowed/` の中の **hard link**（外のファイルと同じ実体） | **開けた**（文書の注意どおり。hard link は見分けられない）。`save` は新しいファイルに置き換えて書くので、外のファイルは変わらなかった（隣に `.bak` として hard link が残る） |

hard link は `ln` で人が作るもの。許可 folder に hard link を置かなければ問題にならない（`execute` が hard link を作れるかは試していない【未試】）。

`execute`・`batch` 経由の書き込みも同じ検査を通った。`file.save_as`・`file.export_step`・`file.export_urdf`（メッシュの `y-base.stl` の書き出し先で拒否）・`file.save_mesh` は、許可の外では拒否され、中では書けた。`batch` の引数は `steps` ではなく `commands`。`doc.open`・`file.insert_step`・`compare_picture` の `reference` も、許可の外は拒否された。`file.send_to_slicer`・`sketch.text` のフォント指定など、ほかのファイルを触る命令は試していない【未試】。

### `--require-allow-path`・`--allow-any-path` の意味

- `--allow-path DIR`: DIR を丸ごと許可する（配下の隠しファイルも）。存在しない DIR は `allow-path … ignored: it doesn't exist` を出して**無視され、サーバーは起動する**（実測。終了コード 0）。
- `--require-allow-path`: **すべての** `--allow-path` が使えないとき、起動を拒否する（実測: `--allow-path /nonexistent` と組み合わせると `error: mcp: every --allow-path folder is missing or unusable` で終了コード 1）。`--allow-path` を 1 つも付けずに `--require-allow-path` だけでは、拒否されず起動した（終了コード 0）。つまり「`--allow-path` の 1 つ目が打ち間違いで、許可なしで黙って起動する」ことを防ぐ用途。登録に付けるなら `--allow-path` の綴りが確実なときだけでよい。
- `--allow-any-path`: 許可の限りを外す（文書の原文は "no limit (the behaviour before this option existed)"）。**使わない**。試していない。

### MCP のツール一覧（実際に取った。S094 が 10 個の「読み取りだけ」を実際に呼んで確かめた）

`solidcraft-cli mcp --headless` を標準入出力で起動し、`initialize` → `tools/list` を送った（JST 17:50 に S051、19:3x に S094 が取り直し）。サーバーは `solidcraft 0.44.1`、protocolVersion `2025-06-18`。ツールは **23 個**。`annotations` の `readOnlyHint` で分けた:

| 読み取りだけ（`readOnlyHint: true`、10 個。**実際に呼んでも、scratchpad の写しのファイルの一覧・大きさ・更新時刻は変わらなかった**） | 説明（原文の要約）と試した呼び出し |
| --- | --- |
| `version` | 動いている版とモード。`{"mode": "headless", "version": "0.44.1", …}` |
| `list_commands` | コマンドの一覧 |
| `describe_command` | 1 コマンドの引数の説明（`id: solid.extrude`） |
| `inspect_design` | パラメーター・タイムライン・ボディ・スケッチの全体 |
| `measure` | 体積・面積・重心・外形（`summary: true` も） |
| `body_topology` | 辺と面の一覧（`body: plate`） |
| `crash_reports` | 手元の crash レポート（一覧は `reports: []`） |
| `running` | アプリが今動かしている要求（窓なしでは `running: []`） |
| `pending` | 時間のかかっている要求の結果（窓なしでは `pending: null`） |
| `skill_reference` | 同梱の設計の手引きを読む。`file` に `../…`・絶対パス・scratchpad の設計を渡すと `Unknown file … Available files: SKILL.md, reference.md` で拒否（任意のファイルは読めない）。`skill` に `/etc` も拒否 |

確かめ方: `open` の後、10 個を 1 つずつ呼び、呼ぶたびに scratchpad の写しの folder・XDG の folder・サーバーの scratch folder（`/tmp/solidcraft-mcp-*`）の全ファイルの（相対パス、大きさ、更新時刻）を比べた。**どの呼び出しの前後でも差は 0 件**。呼んだ後の設計ファイルの SHA-256 も、リポジトリの `cad/plate_mount.design.json` と一致した。`open` 自体もファイルを書かなかった（ロックファイルも出ない）。`check_parameters`（試すだけで戻る）も差は 0 件だったが、`readOnlyHint: false` なので分類は変えない。

**10 個はすべて「読み取りだけ」のままでよい。外すものは無い。** ただし「ファイルを書かない」ことであって、「機密を読めない」ことではない: `inspect_design`・`measure` などは `open` した設計の中身を返す。窓なしの形での試しで、アプリにつないだ形（`--connect`、デスクトップ版）での `running`・`pending`・`crash_reports` の動きは【未確認】。

| 設計を変える・ファイルを書く・読む（`readOnlyHint: false`、13 個） | 注意 |
| --- | --- |
| `execute`、`batch` | 任意のコマンドを実行。`destructive: true`。ファイルを書く命令（`file.save_as` など）も通るが、許可 folder の外は拒否される（実測） |
| `set_parameter`、`check_parameters` | パラメーターの変更（`check_parameters` は試すだけで戻る）。`destructive: false`。ファイルは書かない |
| `undo`、`redo`、`cancel` | 設計の履歴 |
| `new_design`、`open` | 今の設計を捨てる（`destructive: true`）。`open` は許可の外を拒否する |
| `save`、`export` | ファイルを書く。許可された folder の中だけ。**中では既存ファイルを拡張子に関係なく上書きする**（`.bak` を残す） |
| `screenshot`、`compare_picture` | 画像を作る。この PC（GPU なし）では `screenshot` が **75 秒待っても返らず**、サーバーが詰まって次の呼び出しにも返らなくなった（標準エラーは `libEGL warning: failed to open /dev/dri/…: Permission denied`）。`path` が許可の外なら先に拒否される。`compare_picture` の `reference` が許可の外なら先に拒否される |

### 許可リストの提案（決めるのは発注者。私は設定を変えていない）

- **毎回確認なしに許可してよい**（読み取りだけの 10 個、実際に呼んで確かめた）: `mcp__solidcraft__version`、`mcp__solidcraft__list_commands`、`mcp__solidcraft__describe_command`、`mcp__solidcraft__inspect_design`、`mcp__solidcraft__measure`、`mcp__solidcraft__body_topology`、`mcp__solidcraft__skill_reference`、`mcp__solidcraft__crash_reports`、`mcp__solidcraft__running`、`mcp__solidcraft__pending`。使う場面が少ない `crash_reports`・`running`・`pending` は外してもよい（7 個にしても困らない）。
- **毎回確認にする**: `execute`、`batch`、`set_parameter`、`new_design`、`open`、`save`、`export`、`screenshot`、`compare_picture`。`screenshot` は GPU の無いこの PC で詰まるので、許可しない。
- `check_parameters` `undo` `redo` `cancel` は、ファイルを書かない（`check_parameters` は実測）。最初は確認にして様子を見てよい。
- 書式（公式の文書 `https://code.claude.com/docs/en/permissions` の "MCP" 節、JST 19:41 に WebFetch で取得）: 1 つのツールは `mcp__<サーバー名>__<ツール名>`（例 `mcp__puppeteer__puppeteer_navigate`）、サーバー全体は `mcp__<サーバー名>__*`。この登録のサーバー名は `solidcraft`。許可は `.claude/settings.json`（または `settings.local.json`）の `permissions.allow` の配列に書く。`mcp__solidcraft__*` で全部を許可するのは**しない**（書く系が入る）。読み取りの名前に共通の接頭辞が無いので、個々のツール名を並べる。配列の書式 `{"permissions": {"allow": ["mcp__solidcraft__measure", …]}}` は文書の例から【`allow` の配列の例を原文では確かめていない。`update-config` の手順で確かめてから書く】。

### 推薦（決めるのは発注者）: 案 2「`.git-worktree` まで広げる」。ただし main の `cad/` は許可に残さず、書く系のツールは毎回確認にする

```
claude mcp remove solidcraft
claude mcp add solidcraft -- solidcraft-cli mcp --allow-path <リポジトリの根>/.git-worktree --require-allow-path
```

理由:

1. 試して動いたのは案 1・2・3。案 3 は main の作業ツリーと `.git` に書けるので「main を直接編集しない」と合わない。
2. 案 1 は最も狭いが、worktree を切るたびに登録し直しが要る。並列のセッションが 5 つ動くこのリポジトリでは、切るたびの手間と、登録の食い違い（前の worktree の許可が残る・足りない）が起きやすい。
3. 案 2 は 1 回の登録で、どの worktree の `cad/` も開ける。main の `cad/` が許可の外なので、MCP が main を書くことはなく、決まりと合う。
4. 案 2 の弱点は、**書ける範囲が `.git-worktree` の下のすべて**になること（`save` が `.py` などを上書きできる）。そのため `save`・`export`・`execute`・`batch`・`open` は許可リストに入れず、毎回確認にして、保存先のパスを人が見る。上書きされても、追跡されたファイルは git で戻せる（未コミットの変更は `<名前>.bak` に残る）。

別の worktree（他のセッションの作業）にも書けるので、**並列のセッションが動いている間は、設計に使う worktree 以外の `cad/` に触らない**と決めておく。登録のスコープ（local は `~/.claude.json` の `projects` の下に、登録した folder ごとに入る。`mcpServers` を持つのはリポジトリの根だけだった）の都合で、**worktree の folder で直接 `claude` を起動すると、登録が見えない可能性がある**【未確認。リポジトリの根で起動して worktree へ `cd` する運用なら関係しない】。

### 発注者が次のセッションで確かめる手順（【未確認】のまま）

1. 登録したあとに Claude Code を起動し直し、`/mcp` で `solidcraft` が `connected` と出るか、ツール名（`mcp__solidcraft__measure` など）が使えるかを見る。
2. 使えたら Claude に `open` させて worktree の `cad/plate_mount.design.json` を開かせ、拒否されないことと、`measure` の体積が 31114.95 mm3 前後であることを確かめる。

### Claude に設計させる最小の題材

**「XIAO の基板の中心を旋回中心（左右の車軸の中点）の真上に置く取り付け板」**（`cad/plate_mount.json` がその最初の版。`cad/README.md` の要件 2）。依頼文の骨子:

1. 座標は x 前・y 左・z 上、原点は車軸の中点、単位 mm。
2. 板の長さ・幅・厚さを `parameters.add` にし、`comment` に出どころ（`datasheet` / `measured` / `assumed`）を書く。
3. XIAO の窓の中心を原点に置く。基板の外形は 20.955 × 17.78 mm（`cad/dimensions.csv` の `datasheet`）。
4. 取付穴は未確認（車体は Robo Base Mini 2WD に決まったが、板の穴は実物を測ってから）。`TBD_` を付けた仮のパラメーターにとどめ、**実物の板に開けない**。
5. 材料は PLA。最後に `assembly.mass_properties` を呼ぶ。
6. 手計算（体積・質量）を先に書かせ、`execute` の `expect`（`volume_mm3` と `tol`）で自己検査させる。

**IMU の位置は基板の中心とは違う**（基板上の位置は【未確認】）。「中心に置いた」つもりでも d が数 mm 残る。それは旋回中の ax から逆算できる（16 章）。

### 人が確かめるチェックリスト（Claude の自己申告や画像を証拠にしない）

| # | 確かめること | 方法 |
| --- | --- | --- |
| 1 | 寸法の出どころが `assumed` でない | 設計 JSON の `params[].comment`（またはレシピの `parameters.add` の `comment`）を読む。`datasheet` か `measured` だけが確かな寸法。`TBD_` が残っていたら実物に穴を開けない |
| 2 | 窓と穴の位置 | 別の道具（ブラウザー版）で開いて頂点の座標を読む。XIAO の窓の中心が原点。穴の位置は**ノギスで測ってから** |
| 3 | 座標の向き（x が前） | 16 章の約束と、板の窓の向きを画面で |
| 4 | 質量特性が sim に入ったか | `python -m physlearn.solidcraft_props <mass.json>` の質量・Izz が、手計算 `m(a²+b²)/12` と 1 % 以内か。`cad.py` に渡した後は 16 章の表で確かめる（`physlearn.solidcraft_props` で SI に直せる。`cad.py` の `mass_props` に渡す口は無い。5 節） |
| 5 | パラメーターを変えても壊れない | `cad/check.sh`、または MCP の `check_parameters`（試すだけで戻る） |
| 6 | 保存したファイルの差分が読める | `git diff cad/`。意図しない変更が無いか。`cad/expected.csv` も直したか |
| 7 | 実物に合うか | 原寸の紙に印刷して XIAO とベースに当てる。**実機で未確認** |

## 5. 質量特性を sim に渡す

```
$ solidcraft-cli run cad/plate_mount.json --save plate_mount.sc --out plate_mount.step      # 終了コード 0、STEP 28.9 KB
$ solidcraft-cli run cad/plate_mass.json --in plate_mount.sc --results --json-out mass.json  # 終了コード 0
$ python -m physlearn.solidcraft_props mass.json
質量 0.0385779 kg（38.5779 g）
重心 [m] -5.2454e-17 -4.4568e-18 +1.5000e-03
慣性 [kg m^2] +2.6999e-05 …
慣性 [kg m^2] … +7.4826e-05
Izz 7.4826e-05 kg m^2、回転半径 44.04 mm
```

- この出力と 2 節の往復の体積は、S079 が XIAO の外形を 21 × 17.8 → 20.955 × 17.78 mm に直す**前**の板のもの（体積 31111.17 mm3、Izz 7.4826e-5）。直した後は 31114.95 mm3、質量 38.5825 g、Izz 7.4827e-5（`cad/check.sh` で確かめた）。
- 単位の注意: 公式の文書（[gh]`docs/assembly-properties.md`）は `inertia_g_mm2`（g·mm²、"For kg·m², divide by 10⁹"）と書く。**実際の `assembly.mass_properties` の出力のキーは `inertia_world_kg_mm2` / `inertia_local_kg_mm2`（kg·mm²、SI にするには 10⁶ で割る）で、質量は `mass_kg`、重心は `center_of_mass_mm`**。3 桁違うので、`physlearn.solidcraft_props` はキーの名前で単位を決め、知らない名前は読まずに落とす。URDF の `<inertial>` は m・kg・kg m² で、そのまま読める（Izz 7.4828e-5、mass 0.038579。メッシュ積分で 0.002〜0.003 % 違う）。
- 世界座標のテンソルなので、**設計が z 上のとき、鉛直軸まわり（ヨー）の慣性が Izz**。板を寝かせて作った設計を渡すと軸が入れ替わる。依頼文で z 上を固定する。
- 見本は `tests/data/solidcraft/`（実際の出力）、試験は `tests/test_solidcraft_props.py`。

## 6. CI

`.github/workflows/cad.yml`: `cad/**` が変わった main への push と手動実行で動く。公式の tar.gz を落として SHA-256 を固定の値と照合し、`cad/check.sh` で `cad/expected.csv` の各ファイル（設計 JSON とレシピ）を STEP にして、体積・質量・Izz を 0.1 % 以内で比べる。STEP と JSON は artifact に残る。`ubuntu-latest` で共有ライブラリが足りるかは、CI で初めて分かる【未確認】。落ちたら `ldd` の `not found` が出る。

## 7. 確かめていないこと

- ブラウザー版・デスクトップ版（GUI）での操作は全部【未実行】。File > Open が `cad/*.design.json` を開くか、Save As JSON の結果が `solidcraft-cli run` で通るか。File > Open がコマンド列（`cad/*.json`）を開くかも【未確認】。
- 登録した MCP が、次のセッションで実際にツールを出すこと（上の「次のセッションで確かめる手順」）。アプリにつないだ形（`--connect`）での許可の動きと、デスクトップ版が動いているときの窓なしの形の動き（応答の Note は「次の呼び出しでアプリにつなぐ」と言う）。
- `screenshot` / `compare_picture` / `snapshot`（GPU が要る。この PC では返らなかった。`screenshot` は 75 秒待っても返らず、サーバーが詰まった）。
- WSL2 の Claude Code から、Windows のデスクトップ版の `127.0.0.1` の制御の口につながるか（WSL2 のネットワーク設定次第）【未確認】。
- GitHub の ubuntu-latest での CLI の実行。
