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
**効かない物**: `snapshot` と `gpu` は GPU の無い WSL2 で返らなかった（S042）。`mcp` の `screenshot` も同じ系統のはず【未確認】。形は `measure` の数字で確かめる。

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

### 未解決の点: 許可された folder は main の `cad/` で、worktree の `cad/` ではない

許可は、登録時に書いた**絶対パス**（main のチェックアウトの `cad/`）。ところが `CLAUDE.md` は「main の作業ツリーを直接編集しない。作業は `.git-worktree/<topic>/` の feature ブランチで」と決めている。worktree の `cad/`（`<リポジトリの根>/.git-worktree/<topic>/cad`）は許可の外で、MCP の `open` が拒否される見込み。**これはパスの比較からの推論で、worktree では試していない**（S055 の注意 N-1）。

そのため、今の登録のまま MCP で設計すると、`open` する先は main の `cad/` になり、`save` は main のチェックアウトの作業ツリーを書き換える。決まりと食い違う。案（**設定は変えていない。決めるのは発注者**）:

1. **worktree ごとに `--allow-path` を足して登録し直す。** 設計の作業を始めるとき（`/start-session` の後）に `claude mcp remove solidcraft` → `claude mcp add solidcraft -- solidcraft-cli mcp --allow-path <worktree>/cad`。決まりは守れるが、worktree を切るたびに手間が増え、登録し直した後は Claude Code の再起動が要る【未確認】。
2. **`--allow-path` を `.git-worktree` までに広げる。** `--allow-path <リポジトリの根>/.git-worktree` の 1 回で、どの worktree の `cad/` も開ける（`--allow-path` が配下を許可するかは公式の文書で確かめていない【未確認】）。許可は `.git-worktree` の下の全ファイルに広がる（`cad/` 以外も読み書きできる）。`--allow-any-path` よりは狭い。main の `cad/` を許可に残すかどうかも決める。
3. （参考）設計の作業だけは main の `cad/` で行う例外を決まりに書く。ただし main に未コミットの変更が出るので、`CLAUDE.md` の「main に未コミットの変更があったら止める」と衝突する。おすすめしない。

どれにするかは、MCP を実際に使うセッションで 1 回試してから決めるのがよい。

### MCP のツール一覧（実際に取った）

`solidcraft-cli mcp --headless` を標準入出力で起動し、`initialize` → `tools/list` を送った（JST 17:50。設定は変えていない）。サーバーは `solidcraft 0.44.1`、protocolVersion `2025-06-18`。ツールは **23 個**（自分でも `solidcraft-cli mcp --headless` に `tools/list` を送って数え直した。S055 の監査と同じ）。`annotations` の `readOnlyHint` で分けた:

| 読み取りだけ（`readOnlyHint: true`、10 個） | 説明（原文の要約） |
| --- | --- |
| `version` | 動いている版とモード |
| `list_commands` | コマンドの一覧（id・1 行の引数の説明） |
| `describe_command` | 1 コマンドの引数の説明 |
| `inspect_design` | パラメーター・タイムライン・ボディ・スケッチの全体 |
| `measure` | 体積・面積・重心・外形・面/辺/頂点の数 |
| `body_topology` | 辺と面の一覧（中点・長さ・法線） |
| `crash_reports` | 手元の crash レポート |
| `running` | アプリが今動かしている要求（アプリにつないだとき） |
| `pending` | 時間のかかっている要求の結果 |
| `skill_reference` | 同梱の設計の手引きを読む |

| 設計を変える・ファイルを書く・読む（`readOnlyHint: false`、13 個） | 注意 |
| --- | --- |
| `execute`、`batch` | 任意のコマンドを実行。`destructive: true` |
| `set_parameter`、`check_parameters` | パラメーターの変更（`check_parameters` は試すだけで戻る）。`destructive: false` |
| `undo`、`redo`、`cancel` | 設計の履歴 |
| `new_design`、`open` | 今の設計を捨てる（`destructive: true`） |
| `save`、`export` | ファイルを書く。許可された folder の中だけ（`destructive: true`） |
| `screenshot`、`compare_picture` | 画像を作る。GPU の無い PC では返らない可能性が高い。ファイルも書ける |

### 許可リストの提案（決めるのは発注者。私は設定を変えていない）

- **毎回確認なしに許可してよい**（上の表の読み取りだけの 10 個）: `mcp__solidcraft__version`、`list_commands`、`describe_command`、`inspect_design`、`measure`、`body_topology`、`skill_reference`。`crash_reports` `running` `pending` は使う場面が少ないので外してよい。
- **毎回確認にする**: `execute`、`batch`、`set_parameter`、`new_design`、`open`、`save`、`export`、`screenshot`、`compare_picture`。設計を変えるか、ファイルを書く。`execute` は任意のコマンドを通すので、ファイルを書くコマンドも通る。
- `check_parameters` `undo` `redo` `cancel` は、設計の内容を残さないので許可でもよいが、最初は確認にして様子を見る。
- 許可リストの書き方は `update-config` の手順（`.claude/settings.json`）。許可リストの変更も発注者が決める。

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
- 登録した MCP が、次のセッションで実際にツールを出すこと。worktree の `cad/` が拒否されること（推論のまま）と、案 1・2 が通ること。
- `screenshot` / `compare_picture` / `snapshot`（GPU が要る。この PC では返らなかった）。
- WSL2 の Claude Code から、Windows のデスクトップ版の `127.0.0.1` の制御の口につながるか（WSL2 のネットワーク設定次第）【未確認】。
- GitHub の ubuntu-latest での CLI の実行。
