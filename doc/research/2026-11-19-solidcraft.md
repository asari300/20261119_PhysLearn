# SolidCraft の調査（2026-11-19）

発注者の要望「筐体設計は SolidCraft で行えるようにしたい」（JST 2026-11-19 13:51 頃）に応えるため、SolidCraft が何かを調べた。
確認は JST 2026-11-19 13:55〜14:00。Web 検索と、GitHub の README・docs の取得による。
**CLI は JST 17:36 に動かした**（S042）。発注者が 17:30 頃に「この PC で CLI を落として試してよい」と許可した（昼の試みは権限の判定で止められていた）。結果は下の「実際に動かした結果」。動かしていないのは、GUI・ブラウザー版・MCP・Windows 版。
2 巡目の監査（S029、[log/review/2026-11-19-s029-audit2-claude.md](../../log/review/2026-11-19-s029-audit2-claude.md)）を受けて、S035 が本家・版・署名を一次資料で直した（JST 14:10 に GitHub の API と README を取り直した）。

## 結論（確からしさ: 高い。本家・版・ライセンスは一次資料で確かめた）

「SolidCraft」という名前の CAD は実在する。オープンソースのパラメトリック 3D CAD で、Rust で書かれている。
言い違い（SolidWorks など）ではなく、これを指していると考えるのが自然。理由は、同名の CAD がほかに見つからなかったこと（S029 の監査の Web 検索 1 回でも、ほかに見つからなかった。見落としの余地は残る）。
GitHub のリポジトリは `tangency-labs/solidcraft` の 1 つ（https://github.com/tangency-labs/solidcraft 、作成 2026-10-07）。最新の正式版は **v0.44.1**（2026-11-17T19:23Z 公開）。出典: https://api.github.com/repos/tangency-labs/solidcraft と https://api.github.com/repos/tangency-labs/solidcraft/releases/latest （JST 14:10 取得）。

- 公式サイト: https://solidcraft.io （ダウンロード https://solidcraft.io/download 、ブラウザー版 https://solidcraft.io/app 、文書 https://docs.solidcraft.io/ ）
  - 出典: README https://raw.githubusercontent.com/tangency-labs/solidcraft/main/README.md （13:57 に旧名 `bherbruck` の URL で取得。同じリポジトリ）
- 発注者に聞くこと（1〜3 は JST 17:30 頃に返事があった: 「Rust 製 OSS-CAD で合っている。ブラウザー版。両方。CLI 可」= 1 は合っている、2 は主にブラウザー版、3 は人が GUI で設計するのと Claude Code から MCP で設計させるのと両方）:
  1. 「SolidCraft」は https://solidcraft.io （GitHub `tangency-labs/solidcraft`）のオープンソース CAD のことでよいか。ほぼ確実だが、念のため確かめたい。
  2. ブラウザー版・Windows 版・Linux 版（WSL2 の中）のどれで使うか。Windows 版は SmartScreen の警告が出ることがある（下の「署名」）。WSL2 の中で動くかは公式に記載が無い。
  3. 設計は人が GUI で行うか、Claude Code から MCP（`solidcraft-cli mcp`）で行わせるか。MCP にするには Claude Code の設定に登録が要る（`claude mcp add ...`）。設定を変えることなので、発注者が決める。

## わかったこと（出典つき）

| 項目 | 内容 | 出典 |
| --- | --- | --- |
| 種類 | パラメトリック 3D CAD。スケッチ → 拘束・寸法 → 押し出しなどの特徴をタイムラインに並べる。寸法を変えると作り直す | README（上記） |
| 成熟度 | README 自身が「Early but usable for simple parts」と書く。サーフェス・図面・CAM・解析は未対応とする紹介記事もある | README、https://smartscope.blog/en/blog/solidcraft-try-free-open-source-3d-cad-your-2026/ |
| ライセンス | `MIT OR Apache-2.0`。ロゴなどは別の LICENSE-BRAND。費用は無料 | README |
| 対応 OS | Windows（MSI）、macOS、Linux（AppImage、`sudo snap install solidcraft`）、ブラウザー版 | README |
| WSL2 | README に記載なし。Linux 版 CLI（tar.gz から展開）は WSL2・GPU なしで動いた（下の「実際に動かした結果」）。GUI は試していない | 実測（S042） |
| GPU | 表示のメッシュ作成に GPU を使い、だめなら CPU に戻る、とある | https://raw.githubusercontent.com/tangency-labs/solidcraft/main/docs/capabilities.md |
| ファイル形式 | STEP・IGES・3MF・STL・OBJ・glTF の読み書き（「where supported」）、URDF の書き出し。独自形式は `.sc`（旧 `.solidcraft`） | README |
| スクリプト | 「JSON list of the same commands the UI runs」。`solidcraft-cli run script.json --out part.step` で GUI なしに走らせて書き出す | https://raw.githubusercontent.com/tangency-labs/solidcraft/main/docs/scripts.md |
| コマンド名の例 | `sketch.create`（`plane`）、`sketch.rectangle.two_point`（`p0`,`p1`）、`solid.extrude`（`distance`）、`sketch.circle.center`、`solid.hole`、`parameters.add`、`file.export_step`、`file.export_stl`、`inspect.measure`、`assembly.mass_properties` | scripts.md、https://raw.githubusercontent.com/tangency-labs/solidcraft/main/docs/features.md |
| 引数の詳しい形 | 公開のコマンド表に引数がある。たとえば `sketch.circle.center` は `center: [x,y]`、`solid.hole` は `position: [x,y,z]`（面の上）など（S029 の監査が 14:04 に取得）。`book/src/reference/commands.md` は生成物でリポジトリには無い | https://docs.solidcraft.io/reference/commands.html |
| MCP | `solidcraft-cli mcp` で MCP サーバー。Claude Code には `claude mcp add solidcraft -- solidcraft-cli mcp` | README |
| 質量特性 | CLI の測定で体積・面積・**重心**。アセンブリで材料つきの質量特性。URDF の書き出しで各リンクの**質量・重心・重心回りの慣性テンソル**（メッシュと材料の密度から。同じリンクの物体は平行軸の定理で合成） | capabilities.md、https://raw.githubusercontent.com/tangency-labs/solidcraft/main/docs/urdf.md |
| URDF の書き出し | `file.export {"path": "robot.urdf"}`、または `solidcraft-cli run script.json --out robot.urdf` | urdf.md |

## 食い違い・怪しいところ

- GitHub のリポジトリは 1 つ。本家は `tangency-labs/solidcraft`。`bherbruck/solidcraft` は同じリポジトリの旧名で、`https://api.github.com/repos/bherbruck/solidcraft` は `301` で `repositories/1409246014`に転送される（JST 14:10 に取り直した）。その ID が `tangency-labs/solidcraft` であることは S029 の監査が確かめた。持ち主が個人から組織に移ったもの。公式サイトの GitHub のリンクも `tangency-labs` だけ（S029 の監査）。
- 版: 最新の正式版は **v0.44.1**（2026-11-17T19:23Z 公開、https://github.com/tangency-labs/solidcraft/releases/tag/v0.44.1 、JST 14:10 に API で取り直した）。その後に試験版 v0.45.0-rc（rc.4 は 2026-11-19T01:11Z、S029 の監査）。「公式のダウンロードの頁は v0.22.0、GitHub の Releases は v0.42.0」とする記事（smartscope.blog、上記）は、二次資料の古い時点の数字で、今の版ではない。毎日のように版が上がるので、教材では版を書いて固定するのがよい。
- 「Fusion 360 のクリーンルーム再実装」「参照部品 76 件中 76 件が一致」は集約サイト（https://aiindigo.com/tool/solidcraft ）の言い方。capabilities.md 自身は「75 of 76」と書き、「完全な同等性を示すものではない」と断っている。
- 署名: Windows のインストーラーは SignPath.io の無料のコード署名で署名されている（証明書は SignPath Foundation）。本番の証明書が入るまでは SmartScreen が警告することがあり、そのときは「詳細情報」→「実行」を選ぶ、と公式の README が書く（Download 節、https://raw.githubusercontent.com/tangency-labs/solidcraft/main/README.md 、JST 14:10 取得）。「署名が無い」とした記事（smartscope.blog）は誤り。
- その他の紹介: https://www.fabbaloo.com/?p=241350 （Fusion の STEP を読めたという試用記）、https://alternativeto.net/software/solidcraft/about/ 、winget のパッケージ `bherbruck.SolidCraft`（https://winget.ragerworks.com/package/bherbruck.SolidCraft 。ID は旧名のままだが、0.44.1 の取得先は `tangency-labs` の Releases、と S029 の監査が確かめた）。

## この PC（WSL2・GPU なし・RAM 7 GiB）で使えるか

- （13:52〜13:56 の時点。17:36 に CLI を一時の置き場へ展開した。常設ではない。）この PC には入っていない（`which solidcraft` なし。モノレポにも名前・文書の言及なし。`C:\Program Files*` の直下にも CAD らしい名前なし。13:52〜13:56 に確認）。
- 入れずに使う道: **ブラウザー版**（https://solidcraft.io/app ）。Windows 側のブラウザーで開く。動作は【未確認】。
- Windows 側に入れる道: MSI または winget。WSL から CLI を呼ぶ形は【未確認】（17:36 に WSL 側の Linux 版 CLI は動いた）。古いインストーラーは `solidcraft-cli` を PATH に入れないので、`"C:\Program Files\SolidCraft\solidcraft-cli.exe"` と書く、と README にある（S029 の監査）。
- WSL2 の Linux に入れる道: `snap` は WSL2 では systemd の設定次第で動かないことがある。AppImage は FUSE が要る。どちらも試していない。**tar.gz を展開するだけの道が動いた**（root も FUSE も要らない。下の節）。
- 費用: 無料（MIT OR Apache-2.0）。

## このリポジトリでの使い方の案

- 寸法は `cad/dimensions.csv` を正とする。SolidCraft のスクリプト（JSON）はこの表から作れる。確かな寸法（datasheet / measured）だけを穴にし、未確認の寸法は `TBD_` のパラメーターで仮置きした（`cad/plate_mount.json`、[cad/README.md](../../cad/README.md)）。
- SolidCraft で作った形の質量特性（URDF の `<inertial>` 相当）は、`physlearn.cad` の同じ口（質量・重心・ヨーの慣性）に入れて `diffdrive.xml` と比べる。詳しくは `doc/textbook/16-enclosure.md`。
- 書き出した STEP / STL はリポジトリに入れない方針（`cad/README.md`）。

## 実際に動かした結果（S042、JST 2026-11-19 17:35〜17:45）

### 落としたもの

GitHub API `https://api.github.com/repos/tangency-labs/solidcraft/releases/tags/v0.44.1`（正式版、prerelease でない、2026-11-17T19:23:15Z 公開）の資産一覧から、Linux x86_64 向けの 1 つだけを落とした。第三者のサイトと rc は使っていない。

| 資産名 | 大きさ | 照合 |
| --- | --- | --- |
| `solidcraft-0.44.1-linux-x86_64.tar.gz` | 179,977,960 バイト | SHA-256 `164097743f6ff11c1eeb90a4313964728955e297689052053e4e5d8d20a64229`。API の `digest` と、同じ Release の `SHA256SUMS.txt` の行と、落としたファイルの `sha256sum` の 3 つが一致 |
| `SHA256SUMS.txt` | 5,112 バイト | 公式が出しているチェックサム表（照合に使った） |

同じ Release の Linux 向けには、ほかに AppImage（163,842,552 バイト）・deb・rpm・snap・flatpak・pkg.tar.zst・aarch64 版があり、ブラウザー版の配布用 `solidcraft-web-0.44.1.zip`（61,634,177 バイト）もある。AppImage は FUSE の心配があるので、展開済みの形の tar.gz を選んだ（どれも 600 MB 未満）。展開後は 469 MB（うち CLI `bin/solidcraft-cli` が 203 MB、GUI `bin/solidcraft`、文書とライセンス）。sudo・snap・apt・ビルドは使っていない。設定の向き先は `XDG_CONFIG_HOME` `XDG_CACHE_HOME` `XDG_DATA_HOME` を置き場の下にした。

### 走らせたコマンドと出力

```
$ solidcraft-cli --version
solidcraft-cli 0.44.1
$ solidcraft-cli run cad/plate.json --out plate.step --results     # 17:36、終了コード 0
$ head -c 200 plate.step      # ISO-10303-21; ... FILE_SCHEMA(AP242_MANAGED_MODEL_BASED_3D_ENGINEERING_MIM_LF ...  （9,413 バイト）
$ solidcraft-cli eval cad/plate.json
  volume_mm3 32400.0、mass_g 41.796（既定材料 1.29 g/cm3）、center_of_mass (0, 0, 1.5)、bbox (-60,-45,0)-(60,45,3)、faces 6、closed true
```

`cad/plate.json` は**修正なしで通った**。コマンド名と引数は公式のコマンド表と一致していた。手計算 120 × 90 × 3 = 32400 mm3、重心の高さ 1.5 mm と一致。書き出した STEP を `solidcraft-cli eval plate_mount.step` で読み戻すと体積 31111.17、14 面で、書いた形と同じ。

穴つきの板（`cad/plate_mount.json`）、質量特性、URDF、パラメーターの変更の結果は [cad/README.md](../../cad/README.md) に書いた。要点: 体積 31111.17 mm3（手計算と同じ）、PLA で 38.578 g、Izz 7.4826e-5 kg m2。URDF は `file.export_urdf` で書けて、`<inertial>` に質量・重心・慣性テンソルが入る（メッシュの STL 227 KB も同時に書かれる）。

### WSL2 での動き・つまずき

- 動いた: `run` `eval` `commands` `--help` `--version`。0.1 秒で終わる。ライブラリ不足なし（`ldd` で not found なし）。1 本の実行ファイルで、FUSE も GPU も不要。`run` `eval` は設定を書かない。STEP を読むと、読み込みのキャッシュを `$XDG_DATA_HOME/solidcraft/imports/` に作る（`solidcraft-cli` の `file.import_cache_clear` で消せる）。
- 動かなかった: `snapshot`（画像）と `gpu`。stderr に `libEGL warning: failed to open /dev/dri/renderD128: Permission denied` と出て、90 秒たっても返らず、画像は出なかった（`timeout` で止めた）。GPU の無い WSL2 では、画像の書き出しは頼れない。`render` は試していない。
- `solidcraft-cli mcp setup` は Claude Code などの設定を書き換えるので、実行していない。
- `solidcraft-cli commands` は 673 のコマンドを JSON で出す（引数の文字列つき）。公式の文書の表より手元で引ける。
- 最初のつまずきは無し。パラメーターの式（`TBD_robo_hole_dx/2` など）は、スケッチの座標・直径・押し出しの距離にそのまま書けた。

### 発注者の使い方（ブラウザー版が主、GUI と MCP の両方）に合わせた手順

**(i) ブラウザー版で `cad/` の設計データを開く・書き出す【未実行】**（自分では動かせない。公式の文書で確かめた操作だけ）

- https://solidcraft.io/app を開く。インストール不要。
- 公式の文書にある、ブラウザー版へ命令を送る道は、開発者コンソールで `window.solidcraft.execute(コマンド名, 引数)`（https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.44.1/docs/browser-api.md ）。`cad/plate_mount.json` の `commands` を 1 つずつ `await solidcraft.execute(command, params)` で流せば、同じ設計ができるはず【未実行】。JSON ファイルをそのまま読み込む GUI の操作は、文書で見つけていない【未確認】。
- 確実な道: 手元の CLI で `.sc`（設計ファイル。パラメーターと履歴を持つ）を作り（`run cad/plate_mount.json --save plate_mount.sc`）、ブラウザー版で開く【未実行】。開く画面の操作は【未確認】。
- 書き出しは GUI の書き出し（STEP は `file.export_step`、STL は `file.export_stl` と同じ機能）。ブラウザー版が保存先を選ばせるかは【未確認】。
- 配布の `solidcraft-web-0.44.1.zip` は、ブラウザー版を自分で置くためのものらしい。落としていない【未確認】。

**(ii) MCP で Claude Code から設計させる【未実行】**。登録は Claude Code の設定の変更なので、発注者が決めてから行う。

- 公式の手順（`docs/mcp.md`）: `claude mcp add solidcraft -- solidcraft-cli mcp`、または プロジェクトの `.mcp.json` に `{"mcpServers": {"solidcraft": {"command": "solidcraft-cli", "args": ["mcp"]}}}`。`solidcraft-cli mcp setup --client claude-code` という自動の登録もある（`--dry-run` で何を書くか見られる。使っていない）。
- `solidcraft-cli mcp` は GUI なしの設計セッションを開く（`--headless`）。動いているアプリがあれば、そこにつなげて、人が画面で見ながら Claude Code に作らせることもできる（`--connect`。アプリ側の設定 Preferences > Assistant > Agents through MCP > "Let AI agents connect" が要る。新規のインストールでは切れている）。人が GUI で設計するのと Claude Code が MCP で設計するのを**両方**やるなら、この「アプリにつなぐ」形が合う。ただし GUI のアプリが動く場所が要る。
- 書き込める場所は `--allow-path DIR` で絞れる。リポジトリの `cad/` だけ許すなら、`claude mcp add solidcraft -- <CLI のパス> mcp --allow-path <リポジトリ>/cad` の形になる【未実行。引数は mcp.md のとおり】。
- 画像（スクリーンショット）は GPU で描くので、この PC の WSL2 では上の `snapshot` と同じ理由で返らない可能性が高い【未確認】。形の確認は `eval` の数値で行う。

**CLI の常設の置き場所の候補**（発注者が選ぶ）

| 候補 | 中身 | 良い点 | 悪い点 |
| --- | --- | --- | --- |
| A. WSL 側にホームの下へ展開 | `~/.local/opt/solidcraft-0.44.1/` に tar.gz を展開し、`~/.local/bin/solidcraft-cli` を張る | 動くと確かめた。root 不要。MCP も WSL の Claude Code から直に呼べる。版を名前に入れて固定できる | GUI は WSL では画面が無い。展開で 469 MB（CLI だけなら 203 MB） |
| B. Windows 側に MSI / winget | `winget install bherbruck.SolidCraft`（ID は旧名のまま）か、`solidcraft-0.44.1-windows-x64.msi` | GUI も入る。人が使う本命。署名あり | WSL の Claude Code から呼ぶ形は【未確認】（`solidcraft-cli.exe` のフルパスが要る）。SmartScreen の警告 |
| C. 両方 | GUI は Windows、CLI と MCP は WSL | 目的ごとに最適 | 版が 2 つになるので、版を合わせる |
| D. snap / AppImage | 公式の入れ方 | 公式の道 | snap は WSL2 で systemd 次第、AppImage は FUSE が要る。どちらも試していない |

置き場の候補の推薦（作者の意見）: C。ブラウザー版が主なので、まず GUI 相当はブラウザーで足りる。MCP と CLI は A で足りる。

### 確かめていないこと

GUI・ブラウザー版・Windows 版・MCP・`snapshot` / `render`・URDF を sim に入れた結果・他の版との差。`cad.py` に手を入れたくなった点: Izz を直接持つ部品（CAD の出力を `mass_props` に渡す口）。
