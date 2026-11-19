# S051 `solidcraft-bridge`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s051-solidcraft-bridge` |
| worktree | `.git-worktree/s051-solidcraft-bridge` |
| セッション記録 | 統括が締めで `log/sessions/` にコピーする（このセッション単独では作っていない） |

## 依頼

SolidCraft を (1) sim への受け渡し、(2) CI での検査、(3) 発注者の使い方（ブラウザー版が主、GUI と MCP の両方）の手引き、の 3 点でリポジトリにつなぐ。締め切りは JST 18:35 のコミット。マージと push はしない。MCP の登録と許可リストの変更は自分ではしない。

## 決めたこと

- **正本は設計 JSON（`cad/<名前>.design.json`）、コマンド列の `cad/<名前>.json` はレシピ**。S042 は「コマンド列が正本」、S044 は「設計 JSON」を推した。自分で試した結果、設計 JSON にした。理由は 3 つ。(1) ブラウザー版・GUI・MCP の `open`・CLI の `run` のすべてが開けるのは設計 JSON だけ（MCP の `open` はコマンド列の JSON を開けない。実測）。(2) `solidcraft-cli script`（設計 → コマンド列）は外観を落とす（CLI 自身が note を出し、色を付けた設計 JSON の往復で `appearances` の 13 行が消えた）。(3) CI が両方を検査できる（`expected.csv` に両方の行を書き、ずれを見つける）。弱点は差分の大きさ（パラメーター 1 つで 12 行 対 4 行）と形式の番号（`solidcraft/58`）。ブラウザー版で開く・書き出す所は【未実行】なので、通らなければ「レシピを正」に戻す取り決めと、発注者が確かめる 3 点を `cad/README.md` に書いた。
- `solidcraft_props.py` は `cad.py` を import しない（標準ライブラリだけ）。S041 が `cad.py` を変えても壊れない。CI の `check_expected.py` もこのファイルをパスで読む（パッケージの `__init__` が numpy を要するため）。
- 単位はキーの名前で決める。実際の出力は `inertia_world_kg_mm2`（kg·mm²、÷1e6）。公式の文書は `inertia_g_mm2`（g·mm²、÷1e9）。両方を 1 つの表 `_KEY_TO_SI` で持ち、知らないキーは `KeyError`。
- 許可リストの提案: 読み取りだけの 10 ツールを許可、書く・変える系は確認。提案だけで、設定は変えていない。
- CI の対象は `main` への push（`ci.yml` と同じ）。`continue-on-error` は付けない。

## やったこと

- `src/physlearn/solidcraft_props.py`、`tests/test_solidcraft_props.py`（6 件）、`tests/data/solidcraft/plate_mount.mass.json` と `plate_mount.urdf`（今日の CLI の実際の出力。パスの混入 0 件）。
- `.github/workflows/cad.yml`、`cad/check.sh`、`cad/check_expected.py`、`cad/expected.csv`、`cad/plate_mount.design.json`、`cad/README.md`（正本の取り決めと運用）。
- `doc/cad-mcp.md`（3 つの道具の図、ブラウザー版と MCP の結論、形式の決定、CLI の入れ方、MCP の登録と実測、ツール 22 個の一覧、許可リストの提案、題材、チェックリスト）。

## 検証

- 質量特性: 自分で `run cad/plate_mass.json --in plate_mount.sc --results` を走らせた。質量 38.5779 g、Izz 7.4826e-5 kg m2（S042 の値と一致）。URDF は Izz 7.4828e-5（メッシュ積分で 0.007 % 違う）。手計算との一致は試験にした（rel 1e-3）。
- 試験の単位検査: 慣性を 1e6 倍にすると `check_box` が落ちる。g·mm² の入力は同じ SI になる。知らないキーは落ちる。不可能な慣性（三角不等式）と質量 0 も落ちる。
- `cad/check.sh`（CI と同じ手順。展開済みの CLI で）: 7 行すべて ok。`expected.csv` の質量を 38.9 に壊すと食い違いを出して終了コード 1。
- `actionlint`（`uvx --from actionlint-py`、1.7.12）: 指摘 0 件。
- API の digest を JST 17:48 に取り直した: `164097743f6ff11c1eeb90a4313964728955e297689052053e4e5d8d20a64229`（ワークフローの固定値と同じ）。手元の展開済み CLI の `ldd` で `not found` は 0 件。
- MCP: `solidcraft-cli mcp --headless` に `initialize` → `tools/list`。ツール 22 個、読み取りだけは 10 個。`--allow-path` なしでは `open` が拒否され、付けると `open` → `measure` → `parameters.change` → `save` が通った（scratch のコピーで。リポジトリの `cad/` には書いていない）。
- `uv run --extra mujoco --extra viz pytest -q`: 117 passed。
- 漏洩検査（ホームのパス・ユーザー名）: 追加した 8 ファイルで 0 件（`grep` でホームのパスとユーザー名）。セッション記録の `--check` は統括が行う。

## 確かめていないこと・残したこと

- ブラウザー版・デスクトップ版の操作は全部【未実行】。File > Open が設計 JSON を開くか、コマンド列を開くか。
- **CI で初めて分かること**: `ubuntu-latest` に CLI の共有ライブラリが足りるか（WSL2 では `ldd` で不足 0）。180 MB のダウンロードの時間。`--param-check strict` の挙動の同じさ。落ちたら `ldd` の手順が名前を出す。
- 登録した MCP が次のセッションでツールを出すか。登録のままでは `cad/` を開けない（`--allow-path` が要る）ので、再登録は発注者の判断。
- `screenshot` / `snapshot`（GPU）。URDF を sim に入れた結果。複数の部品・関節の設計で `script` が何を落とすか。
- 公式の文書に「ブラウザー版は MCP につながらない」と書いた一文は無い。`browser-api.md` の原文と、MCP の文書の制御の口の説明からの読み（doc に原文と推測を分けて書いた）。

## 申し送り

**`cad.py`（S041 の持ち分）**: 今の main の形は `mass_props(parts)`、`parts = [(shape, 質量 kg, (x, y, z) m, size)]`、`part_izz(shape, m, size)`。CAD の出力を受けるには `part_izz` に `shape == "izz"`（`size = (Izz,)` をそのまま返す）を足し、`solidcraft_props.load(path)` の `MassProps` から `("izz", p.mass, p.com, (p.izz,))` を作る。重心は設計のローカル座標（板の下面が z = 0、中心が x, y = 0）なので、車体座標に置く位置は呼ぶ側で足す。Izz は重心回り・鉛直軸（設計が z 上のとき）。S041 が `part_izz` や `parts` の形を変えたら、この申し送りを直す。

**16 章（別の担当が作り直す）**: 3 節に (a) 正本は設計 JSON（`cad/plate_mount.design.json`）、(b) 手引き `doc/cad-mcp.md` へのリンク、(c) ブラウザー版は MCP につながらない（ファイルで受け渡す）の 3 点。4 節の「渡す口が無い」を `solidcraft_props` に差し替え、`python -m physlearn.solidcraft_props` の出力（Izz 7.4826e-5）を貼る（`docs_check` の対象にするなら実行可能な形で）。質量特性の単位の注意（実際の欄名は `inertia_world_kg_mm2`、kg·mm²）を 1 文。

**README**: 「cad/ の手引き」として `doc/cad-mcp.md` を 1 行。CI の節に `cad.yml`（CAD の検査）を 1 行。

**索引（`doc/` の一覧、`doc/research/2026-11-19-solidcraft.md`）**: 研究記録の「確かめていないこと」を、このセッションで確かめた分（MCP のツール一覧、`--allow-path` の実測、設計 JSON の往復、公式の文書と実出力の欄名の違い）で更新。`cad/README.md` の「CAD → sim」節の末尾は、この対応に差し替え済み（1 文）。

**発注者が決めること**: (1) MCP の再登録（`claude mcp remove solidcraft` → `claude mcp add solidcraft -- solidcraft-cli mcp --allow-path <リポジトリ>/cad`）。(2) 許可リストに読み取りだけの 7〜10 ツールを入れるか。(3) 正本を設計 JSON にしてよいか（ブラウザー版で `cad/plate_mount.design.json` を開いて確かめた後）。(4) 登録を project スコープ（`.mcp.json`）にするか。
