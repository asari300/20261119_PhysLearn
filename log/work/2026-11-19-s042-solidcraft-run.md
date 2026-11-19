# S042 `solidcraft-run`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s042-solidcraft-run` |
| worktree | `.git-worktree/s042-solidcraft-run` |
| セッション記録 | 統括が締めで `log/sessions/` にコピーする（このセッション単独では作っていない） |

## 依頼

SolidCraft の CLI を実際に動かし、`cad/` の設計データから STEP が書き出せることを確かめ、筐体の板の設計を進める。発注者が JST 17:30 頃に「この PC で CLI を落として試してよい」と許可した。締め切りは 18:20 のコミット。マージと push はしない。

## 決めたこと

- 落とす物: v0.44.1 の Linux x86_64 の `tar.gz`（180 MB）。AppImage ではなく tar.gz にした。理由: FUSE が要らず、展開済みで `bin/solidcraft-cli` が入っている。公式の同じ Release の資産で、3 つの手段（API の digest、`SHA256SUMS.txt`、`sha256sum`）が一致。
- 置き場は scratchpad の `s042/`。落とした tar.gz は展開後に消した（`/tmp` の残りのため。展開物 469 MB は残す）。
- STEP / `.sc` はコミットしない（`cad/README.md` の既存の方針どおり。STEP は 29 KB で小さいが、方針は変えない）。
- 板: XIAO の外形（datasheet）だけを窓にした。逃げ 0.3 mm は設計者の仮定。Robo Base の取付穴は `TBD_` 付きのパラメーターで仮置き。実物の板に穴を開けない注意を README に書いた。
- 材料は PLA（SolidCraft の表の 1.24 g/cm3）。板を何で作るかは決めていない。
- MCP の登録（`claude mcp add`、`.mcp.json`、`solidcraft-cli mcp setup`）はしていない。手順と置き場の候補を文書に書いた。

## やったこと

- `cad/plate.json` を修正なしで走らせた（STEP 9,413 バイト、体積 32400 mm3 で手計算と一致）。
- `cad/plate_mount.json`（パラメーター 9 個、窓 1、穴 4、PLA）と `cad/plate_mass.json`（質量特性）を新規に作り、実際に通したものだけを置いた。
- `cad/README.md` に走らせ方、板の設計の根拠、CAD と `cad.py` の比較。
- `doc/research/2026-11-19-solidcraft.md` に「実際に動かした結果」の節。冒頭の「一度も動かしていない」を直した。ブラウザー版の手順（【未実行】）、MCP の登録の手順、CLI の置き場所の候補を追記。
- `doc/textbook/16-enclosure.md` の 3 節（SolidCraft での流れ）だけを、動かした事実に直した。寸法や sim の数値の節は触っていない。

## 検証

- CLI: `run` / `eval` / `commands` は終了コード 0、各 0.1 秒。
- 板の体積: CAD 31111.170 mm3、手計算 3 × (10800 − 21.6 × 18.4 − 4π1.6²) = 31111.170 mm3（一致）。
- Izz: CAD 7.48264e-5、手計算 7.48238e-5 kg m2（差 0.004 %）、`cad.mass_props` の直方体 7.23335e-5（CAD の 0.967 倍）。
- パラメーター変更: dx 100 → 94、径 3.2 → 4 で、STEP の円筒の中心 x が ±50 → ±47、半径 1.6 → 2.0、体積 31056.88 mm3（手計算 31056.9）。
- STEP の読み戻し: `eval plate_mount.step` で体積 31111.17、14 面。
- URDF: `file.export_urdf` で mass 0.0385790 kg、izz 7.48278e-5。STL 227 KB つき（置き場にのみ。コミットしない）。
- `uv run pytest`: 実行していない（`src/` を触っていないため）。
- 差分の漏洩検査: finish-session の検査は統括が行う。この文書にはホームのパスやユーザー名を書いていない（置き場は `<scratchpad>/s042/` のように書いた）。

## 確かめていないこと・残したこと

- GUI・ブラウザー版・Windows 版・MCP の実動作。`snapshot` と `gpu` は GPU 無しの WSL2 で返らず（90 秒で打ち切り）、画像は出していない。
- 板の窓は貫通。基板の厚み・押さえ方は【未確認】。
- `physlearn.cad` は Izz を直接持つ部品を受けない。CAD の出力を渡すには口が要る（`src/` は触っていない。次の担当への提案）。
- 置き場に残した物: `s042/x/solidcraft-0.44.1-linux-x86_64/`（469 MB、CLI は `bin/solidcraft-cli`）、`s042/out/`（STEP・.sc・URDF）、`s042/docs/`（公式の文書 3 本）、`s042/xdg/`。合計約 584 MB、`/tmp` の残り約 2.0 GB。
- 発注者が決めること: CLI の常設の置き場所（A: WSL のホームに展開、B: Windows に MSI / winget、C: 両方）と、MCP の登録をするか。
