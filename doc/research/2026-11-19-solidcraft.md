# SolidCraft の調査（2026-11-19）

発注者の要望「筐体設計は SolidCraft で行えるようにしたい」（JST 2026-11-19 13:51 頃）に応えるため、SolidCraft が何かを調べた。
確認は JST 2026-11-19 13:55〜14:00。Web 検索と、GitHub の README・docs の取得による。**この PC では一度も動かしていない。**

## 結論（確からしさ: 高い。ただし発注者に 1 点確認したい）

「SolidCraft」という名前の CAD は実在する。オープンソースのパラメトリック 3D CAD で、Rust で書かれている。
言い違い（SolidWorks など）ではなく、これを指していると考えるのが自然。理由は、同名の CAD がほかに見つからなかったこと。

- 公式サイト: https://solidcraft.io （ダウンロード https://solidcraft.io/download 、ブラウザー版 https://solidcraft.io/app 、文書 https://docs.solidcraft.io/ ）
  - 出典: README https://raw.githubusercontent.com/bherbruck/solidcraft/main/README.md （13:57 取得）
- 発注者に聞くこと:
  1. 「SolidCraft」は https://solidcraft.io のオープンソース CAD のことでよいか。
  2. デスクトップ版（Windows 側に入れる）とブラウザー版のどちらで使う想定か。
  3. 設計は人が GUI で行うか、Claude Code から MCP（`solidcraft-cli mcp`）で行わせたいか。

## わかったこと（出典つき）

| 項目 | 内容 | 出典 |
| --- | --- | --- |
| 種類 | パラメトリック 3D CAD。スケッチ → 拘束・寸法 → 押し出しなどの特徴をタイムラインに並べる。寸法を変えると作り直す | README（上記） |
| 成熟度 | README 自身が「Early but usable for simple parts」と書く。サーフェス・図面・CAM・解析は未対応とする紹介記事もある | README、https://smartscope.blog/en/blog/solidcraft-try-free-open-source-3d-cad-your-2026/ |
| ライセンス | `MIT OR Apache-2.0`。ロゴなどは別の LICENSE-BRAND。費用は無料 | README |
| 対応 OS | Windows（MSI）、macOS、Linux（AppImage、`sudo snap install solidcraft`）、ブラウザー版 | README |
| WSL2 | README に記載なし。【未確認】 | — |
| GPU | 表示のメッシュ作成に GPU を使い、だめなら CPU に戻る、とある | https://raw.githubusercontent.com/bherbruck/solidcraft/main/docs/capabilities.md |
| ファイル形式 | STEP・IGES・3MF・STL・OBJ・glTF の読み書き（「where supported」）、URDF の書き出し。独自形式は `.sc`（旧 `.solidcraft`） | README |
| スクリプト | 「JSON list of the same commands the UI runs」。`solidcraft-cli run script.json --out part.step` で GUI なしに走らせて書き出す | https://raw.githubusercontent.com/bherbruck/solidcraft/main/docs/scripts.md |
| コマンド名の例 | `sketch.create`（`plane`）、`sketch.rectangle.two_point`（`p0`,`p1`）、`solid.extrude`（`distance`）、`sketch.circle.center`、`solid.hole`、`parameters.add`、`file.export_step`、`file.export_stl`、`inspect.measure`、`assembly.mass_properties` | scripts.md、https://raw.githubusercontent.com/bherbruck/solidcraft/main/docs/features.md |
| 引数の詳しい形 | `sketch.circle.center`・`solid.hole`・`parameters.add` の引数名は上の文書に無い（コマンド表 `book/src/reference/commands.md` にあるとされる）。【未確認】 | features.md |
| MCP | `solidcraft-cli mcp` で MCP サーバー。Claude Code には `claude mcp add solidcraft -- solidcraft-cli mcp` | README |
| 質量特性 | CLI の測定で体積・面積・**重心**。アセンブリで材料つきの質量特性。URDF の書き出しで各リンクの**質量・重心・重心回りの慣性テンソル**（メッシュと材料の密度から。同じリンクの物体は平行軸の定理で合成） | capabilities.md、https://raw.githubusercontent.com/bherbruck/solidcraft/main/docs/urdf.md |
| URDF の書き出し | `file.export {"path": "robot.urdf"}`、または `solidcraft-cli run script.json --out robot.urdf` | urdf.md |

## 食い違い・怪しいところ

- GitHub のリポジトリが 2 つ見つかった: `bherbruck/solidcraft` と `tangency-labs/solidcraft`。README の中身はほぼ同じ。どちらが本家かは【未確認】（移った可能性があるが、README に移転の記述は見当たらなかった）。
- 版: 「公式のダウンロードの頁は v0.22.0、GitHub の Releases は v0.42.0」とする記事がある（smartscope.blog、上記）。今の版は【未確認】。
- 「Fusion 360 のクリーンルーム再実装」「参照部品 76 件中 76 件が一致」は集約サイト（https://aiindigo.com/tool/solidcraft ）の言い方。capabilities.md 自身は「75 of 76」と書き、「完全な同等性を示すものではない」と断っている。
- Windows のインストーラーは署名が無く SmartScreen の警告が出る、とする記事がある（smartscope.blog）。【未確認】
- その他の紹介: https://www.fabbaloo.com/?p=241350 （Fusion の STEP を読めたという試用記）、https://alternativeto.net/software/solidcraft/about/ 、winget のパッケージ `bherbruck.SolidCraft`（https://winget.ragerworks.com/package/bherbruck.SolidCraft ）。

## この PC（WSL2・GPU なし・RAM 7 GiB）で使えるか

- この PC には入っていない（`which solidcraft` なし。モノレポにも名前・文書の言及なし。`C:\Program Files*` の直下にも CAD らしい名前なし。13:52〜13:56 に確認）。
- 入れずに使う道: **ブラウザー版**（https://solidcraft.io/app ）。Windows 側のブラウザーで開く。動作は【未確認】。
- Windows 側に入れる道: MSI または winget。WSL から CLI を呼ぶ形は【未確認】。
- WSL2 の Linux に入れる道: `snap` は WSL2 では systemd の設定次第で動かないことがある。AppImage は FUSE が要る。どちらも【未確認】で、今回は入れていない（入れない決まり）。
- 費用: 無料（MIT OR Apache-2.0）。

## このリポジトリでの使い方の案

- 寸法は `cad/dimensions.csv` を正とする。SolidCraft のスクリプト（JSON）はこの表から作れる。
- SolidCraft で作った形の質量特性（URDF の `<inertial>` 相当）は、`physlearn.cad` の同じ口（質量・重心・ヨーの慣性）に入れて `diffdrive.xml` と比べる。詳しくは `doc/textbook/16-enclosure.md`。
- 書き出した STEP / STL はリポジトリに入れない方針（`cad/README.md`）。
