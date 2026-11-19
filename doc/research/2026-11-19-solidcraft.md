# SolidCraft の調査（2026-11-19）

発注者の要望「筐体設計は SolidCraft で行えるようにしたい」（JST 2026-11-19 13:51 頃）に応えるため、SolidCraft が何かを調べた。
確認は JST 2026-11-19 13:55〜14:00。Web 検索と、GitHub の README・docs の取得による。**この PC では一度も動かしていない。**
2 巡目の監査（S029、[log/review/2026-11-19-s029-audit2-claude.md](../../log/review/2026-11-19-s029-audit2-claude.md)）を受けて、S035 が本家・版・署名を一次資料で直した（JST 14:10 に GitHub の API と README を取り直した）。

## 結論（確からしさ: 高い。本家・版・ライセンスは一次資料で確かめた）

「SolidCraft」という名前の CAD は実在する。オープンソースのパラメトリック 3D CAD で、Rust で書かれている。
言い違い（SolidWorks など）ではなく、これを指していると考えるのが自然。理由は、同名の CAD がほかに見つからなかったこと（S029 の監査の Web 検索 1 回でも、ほかに見つからなかった。見落としの余地は残る）。
GitHub のリポジトリは `tangency-labs/solidcraft` の 1 つ（https://github.com/tangency-labs/solidcraft 、作成 2026-10-07）。最新の正式版は **v0.44.1**（2026-11-17T19:23Z 公開）。出典: https://api.github.com/repos/tangency-labs/solidcraft と https://api.github.com/repos/tangency-labs/solidcraft/releases/latest （JST 14:10 取得）。

- 公式サイト: https://solidcraft.io （ダウンロード https://solidcraft.io/download 、ブラウザー版 https://solidcraft.io/app 、文書 https://docs.solidcraft.io/ ）
  - 出典: README https://raw.githubusercontent.com/tangency-labs/solidcraft/main/README.md （13:57 に旧名 `bherbruck` の URL で取得。同じリポジトリ）
- 発注者に聞くこと:
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
| WSL2 | README に記載なし。【未確認】 | — |
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

- この PC には入っていない（`which solidcraft` なし。モノレポにも名前・文書の言及なし。`C:\Program Files*` の直下にも CAD らしい名前なし。13:52〜13:56 に確認）。
- 入れずに使う道: **ブラウザー版**（https://solidcraft.io/app ）。Windows 側のブラウザーで開く。動作は【未確認】。
- Windows 側に入れる道: MSI または winget。WSL から CLI を呼ぶ形は【未確認】。古いインストーラーは `solidcraft-cli` を PATH に入れないので、`"C:\Program Files\SolidCraft\solidcraft-cli.exe"` と書く、と README にある（S029 の監査）。
- WSL2 の Linux に入れる道: `snap` は WSL2 では systemd の設定次第で動かないことがある。AppImage は FUSE が要る。どちらも【未確認】で、今回は入れていない（入れない決まり）。
- 費用: 無料（MIT OR Apache-2.0）。

## このリポジトリでの使い方の案

- 寸法は `cad/dimensions.csv` を正とする。SolidCraft のスクリプト（JSON）はこの表から作れる。
- SolidCraft で作った形の質量特性（URDF の `<inertial>` 相当）は、`physlearn.cad` の同じ口（質量・重心・ヨーの慣性）に入れて `diffdrive.xml` と比べる。詳しくは `doc/textbook/16-enclosure.md`。
- 書き出した STEP / STL はリポジトリに入れない方針（`cad/README.md`）。
