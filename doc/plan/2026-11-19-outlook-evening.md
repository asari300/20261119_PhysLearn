# 夜の部の展望（S044。昼の [outlook.md](2026-11-19-outlook.md) の続き）

第 1 巡: JST 17:35〜18:00。昼の文書は書き換えない。時刻は JST、日付は 2026-11-19。
外の事実は今日の 17:37〜17:45 に取り直した（URL と時刻は各所）。推測は【推測】、確かめていないことは【未確認】。

## 0. 最初に: 履歴のメールアドレスは、最初の push の前に決める

- `git log --format='%an <%ae> | %cn <%ce>' | sort | uniq -c` の結果は、**139 コミットすべて**の author と committer が個人のメールアドレス（17:37 に走らせた）。`pyproject.toml` の `authors` にも同じものがある。
- `pyproject.toml` を直しても、**履歴の中の古い版と、コミットの author 欄には残る**。push すると、公開リポジトリから誰でも読める。
- GitHub の「Block command line pushes that expose my email」は、**最新のコミットだけ**を見る（GitHub Docs「Blocking command line pushes that expose your personal email address」、17:4x 取得: "GitHub checks the most recent commit on each push"）。履歴の古いコミットは守れない。
- 今の `finish-session` のスキルの説明には「push」「CI の確認」が入っている。**発注者の返事が出るまで、誰も push しない**ことを、統括が全セッションに伝えるのがよい。
- 選択肢（発注者に聞く。2 節の問い 3）:
  - (a) 書き換えて noreply にする。**推薦**（推測）。必要なのは、発注者の noreply アドレス `ID+USERNAME@users.noreply.github.com`（形式は GitHub Docs「Email addresses reference」、17:4x 取得。ID は発注者の GitHub の Settings > Emails に出る。こちらでは分からない）。やるのは**全セッションが main に入った後、20:45 ごろに 1 回**。author/committer の書き換えに加えて、**古い版の `pyproject.toml` の中のメールも消す**（blob の置換が要る）。`git filter-repo` はこの PC に入っていない（17:4x に `which` で確認）。`uvx` で入るかは【未確認】（予行 N1 で確かめる）。ハッシュが全部変わるので、`log/work/` と `outlook.md` に書いた短縮ハッシュ（約 10 ファイル）は対応を失う。
  - (b) そのまま公開する。メールが公開される。
  - (c) 履歴を捨てて 1 コミットで公開する。作業記録の履歴という、このリポジトリの値打ちが減る。
- 今すぐできる小さなこと: 統括が `git config user.email <noreply>` を main のチェックアウトに設定すれば、これからのコミットは増えない（worktree はリポジトリの設定を共有する）。

## 1. 夜の後半（19:00〜20:30）にやる値打ちが高いもの

並べ方は、(1) 取り返しがつかない、または時刻の締め切りがある、(2) 1 周を回す人が実機の日に詰まる、(3) 公開リポジトリとして欠けている、の順。**無いことの確認**は各件の末尾に書いた。

触れないファイル（S070〜S077 と S075 が持つ）: `README.md`、`doc/setup.md`、`doc/bringup.md`、`doc/plan/2026-11-19-plan.md`、`doc/textbook/` 全部。ほかの夜の部（S039 の `.github/workflows/ci.yml` と `.claude/settings.json`、S041 の `sim.py`・`sysid.py`・`randomize.py`・`link.py`・`fakexiao.py`・`cad.py`・`__init__.py`、S046 の `docs_check`、S042 の `cad/`）とも重ならないように、新規ファイルだけにした。

### N1. 公開前の予行（履歴の書き換えと点検）【19:00 着手、30 分、サブエージェント 1 体】

- **なぜ今か**: 取り返しがつかない唯一の作業で、20:45 に本番をやるなら、その前に手順を通して数字で確かめておく必要がある。
- **作るもの**: `doc/publishing.md`（新規）と作業記録。コードは書かない。
- **やること**:
  1. main を**スクラッチ領域に clone** し（元のリポジトリの履歴は触らない）、ダミーの noreply アドレスで、author/committer と全コミットの全 blob のメール文字列を置き換える手順を通す。道具は `uvx git-filter-repo` を試し、だめなら `git filter-branch --env-filter` と `--tree-filter`（遅いが 139 コミットなら足りる、【推測】）。
  2. 数字で確かめる: (i) コミット数が元と同じ、(ii) マージの形（`git log --graph --oneline | wc -l` と親の数）が同じ、(iii) 先端のツリーが元と同一（`git diff --stat 元 書換後` が空。ただしメールを直した `pyproject.toml` の 1 行だけは差が出る）、(iv) `git log --all --format='%ae %ce'` と、`git grep -I <旧メール> $(git rev-list --all)` が **0 件**、(v) 書き換え後の先端で `uv run pytest` が通る、(vi) 全履歴で、ホームのパス・トークンらしい文字列（`CLAUDE.md` の検査と同じ正規表現）が 0 件。
  3. 発注者の決定で履歴から外すもの（2 節の問い 4・5 の「公開しない」）を、同じ書き換えで外す手順（`--invert-paths`）も書く。
  4. GitHub 側の設定（"Keep my email addresses private" と "Block command line pushes that expose my email" を**push の前に**入れる）、push のコマンド、push 後の確認（Actions が有効か、バッジ、リポジトリの説明と topics）。
- **ぶつかり**: なし（新規 2 ファイルだけ。`log/work/` の自分の記録）。
- **無いことの確認**: `git grep -il 'filter-repo\|noreply\|mailmap'` は 0 件。`doc/` に公開の手順の文書は無い。

### N2. 実機の最初の 30 分を機械にする: `hwcheck`【19:00 着手、25〜30 分、1 体】

- **なぜ今か**: `doc/bringup.md` の段 1〜3（`I` 行が流れる、1 秒 100 行、静止の値、**軸の向き**）は今は人が `picocom` と CSV を目で見て確かめる。特に軸の符号は、間違えても動いてしまい、以後の同定が静かに狂う。部品が届く日に一番詰まる所を先に潰す。
- **作るもの**: `src/physlearn/hwcheck.py`（新規、約 120 行）と `tests/test_hwcheck.py`（新規）。`python -m physlearn.hwcheck stream|axes --port ...` の形で、`__init__.py` と `pyproject.toml` は触らない。
  - `check_stream(rows) -> list[(項目, 合否, 基準とその出どころ, 外れたときの次の手)]`: 行数/秒（基準 100、スケッチの `PERIOD_US = 10000`）、欠けた行の数、`# ERR` 行の数、静止時の `az` ≈ +9.81（±0.5 は bringup の「目安（根拠なし）」と同じ印を付ける）、`gz` の平均がバイアスの幅 0.02 rad/s 以内（`randomize.SPREAD`）、雑音の標準偏差。
  - `axes_from_poses(rest, nose_up, left_up) -> "y,-x,z" の形`: 3 つの姿勢の加速度の平均から、機体の x・y・z に対応する基板の軸と符号を出す（bringup 段 3 の 4 つの確かめの前半）。行列式が −1（左右反転）なら「矛盾」と返す。`link.py` の `--axes` の書式を**読むだけ**で再利用する。
  - 対話の `axes`: 「水平に置いて Enter」「鼻を上げて Enter」「左を上げて Enter」と促し、各 2 秒を読んで `--axes` の文字列を表示する。ジャイロの符号は上から見て反時計回りで gz 正（03 章 3.7）を人が確かめる 1 項目を残す。
  - 試験: 偽の XIAO（`fakexiao`、pty）の相手で `check_stream` が全部合格、レートを落とした偽物で不合格になる。`axes_from_poses` は合成の姿勢の 24 通り（軸の置換 × 符号）のうち右手系の 24 通りを全部当てる。
- **ぶつかり**: `link.py` は S041 が触るので**読むだけ**（`--axes` の解析関数を import する。名前が変わったら止めて報告）。bringup.md への 1 行の足しは、S075 の後に統括が行う。
- **無いことの確認**: `git grep -ilE 'doctor|hwcheck|list_ports'` は 0 件（`src/` に `serial.tools.list_ports` の使用なし）。軸の自動判定の道具も無い（bringup 段 3 は手作業）。
- **実機で未確認のまま残るもの**: 合格基準は全部、机上の値。作業記録にそう書く。

### N3. ファームウェアのコンパイルを CI に: `firmware.yml`【19:15 着手、30 分、1 体。下の条件つき】

- **なぜ今か**: 「分かっている問題」5 の MG24 未コンパイルが残っている。昼の S040（在庫と MG24 のコンパイル）は夜の部の一覧に無く、在庫は S043 が見るがコンパイルは誰も見ない。GitHub のランナーなら、コアの 1 GB 級のダウンロードも自分の PC のディスクを使わずに済む。
- **作るもの**: `.github/workflows/firmware.yml`（新規。S039 の `ci.yml` とは別ファイルにして、ぶつけない）。`arduino-cli` で nRF52840 Sense を必須、MG24 Sense を `continue-on-error: true`（落ちてもバッジを赤くしない）。コアとライブラリは版を固定してキャッシュ。FQBN は MG24 のコアを入れたあと `board listall` で確かめる（`doc/setup.md` が【未確認】と書く）。
- **条件**: ローカルで 1 回通してから置く（このセッションの PC に `arduino-cli` が今は無い。入れて 1.6.0 で試した記録が setup.md にある）。**MG24 が落ちたら、直さずに原因を作業記録に書く**（`firmware/` の変更は別の担当。`#if` の切り分けは `xiao_imu_drive.ino` の 12〜19 行目）。ディスクに余裕はある（空き 641 GB、17:4x）。
- **ぶつかり**: `firmware/` は昼以降、誰も触っていない（S047 の監査の直しは文書が主、【推測】。S047 に聞く）。
- **無いことの確認**: `.github/` は今は無い。`git grep -n 'arduino-cli compile'` は `doc/setup.md`・03 章・作業記録だけで、自動の実行は無い。

### N4. つまずき集 `doc/troubleshooting.md`【19:30 着手、20 分、1 体】

- **なぜ今か**: 部品が届いた日、学ぶ人は「症状 → 原因 → 確かめ方」で探す。いまは bringup の各段の「外れたら:」、03 章、setup、09 章に散っている。`git grep -ilE 'トラブル|切り分け|FAQ|困ったとき'` は教材・手順書で 0 件（作業記録 1 件だけ）。
- **作るもの**: `doc/troubleshooting.md`（新規）と `doc/README.md` の表に 1 行。**新しい事実は書かない**。bringup・03 章・setup・protocol・09 章・`link`/`fakexiao` のエラー文から**拾って並べる**だけで、各行に元の場所へのリンクを付ける（元の文書が S075 などで直っても、リンク先で正しくなる）。症状の例: `I` 行が出ない、`# ERR`、書き込めない（ブートローダー）、usbipd でポートが出ない、車輪が逆に回る、`SafetyGate` が作動して例外、同定が `drift` で警告、`仕様 NG`、`--axes` を付け忘れ。実機で確かめていない行は【実機未確認】と付ける。
- **ぶつかり**: `doc/README.md` の 1 行だけ。S075 の割り当てに `doc/README.md` は無い。

### N5. SolidCraft の質量特性を `physlearn` に入れる口と、MCP の依頼文【S042 が報告して S041 が main に入った後、20:00〜、30 分、1 体】

- **なぜ今か**: `cad.py` は「CAD が質量特性を出せるなら Izz を 1 つの部品として渡せばよい」と書くが、**渡す口が無い**（`part_izz` は箱・球・円柱だけ）。公式文書に、出力の形がある（3 節の事実 F6）。S042 が実際の出力を持ってくる。
- **作るもの**:
  - `src/physlearn/solidcraft_props.py`（新規、約 50 行）: SolidCraft の質量特性の JSON から `(質量 [kg], 重心 [m], Izz [kg m²])` を返す。（第 1 巡の記述。実際の形と単位は第 2 巡 5.4 節を正とする: kg·mm² を 1e6 で割る。）`null`（メッシュが閉じていない）なら例外。試験は、**S042 が実際に出した JSON**（無ければ公式文書の形に合わせた手書き）と、**箱の公式 `m(a²+b²)/12`** との突き合わせ（板 1 枚なら 1 % 以内、【推測】）。`cad.py` に繋ぐのは S041 の後に統括が 1 か所。
  - `doc/cad-mcp.md`（新規）: 3 節の「MCP の最小の題材」の依頼文と、人が確かめる表。MCP の登録は発注者の設定の変更なので、**手順だけ書いて、設定ファイルは置かない**。
- **ぶつかり**: `cad.py` は S041・S074 が触るので触らない。`cad/` は S042 の持ち分なので触らない。
- **条件**: S042 が「CLI が WSL2 で動いた」と報告しなかったら、この件は明日に回し、代わりに N4 を厚くする。
- **S039 への連絡**（許可リスト）: MCP のツール名は `mcp__solidcraft__<tool>`（【推測】、サーバー名 `solidcraft` は公式文書の記述、命名規則は Claude Code の仕様）。読むだけの `inspect_design`・`measure`・`list_commands`・`describe_command`・`screenshot` は許可リストに入れてよく、**`execute`・`batch`・`save`・`export`・`open` は入れない**（ファイルを書く）。

### 時刻の目安

| 時刻 | 統括 | サブエージェント |
|---|---|---|
| 〜18:30 | 全員に「push しない」を伝える。発注者に 2 節の問い 1〜5 を送る | |
| 19:00 | | N1・N2・N3 を並行（ファイルは互いに別） |
| 19:30 | S041・S046 の取り込み → S070〜S077 | N4 |
| 20:00 | | N5（S042 の報告後） |
| 20:45 | 全部を main に入れたあと、N1 の手順で書き換え → push | |

## 2. 公開リポジトリとして要るもの（独学用の小さなリポジトリなので、絞る）

| 項目 | 要る？ | 理由（1 行） |
|---|---|---|
| ライセンスの表示 | **要る** | ルートに `LICENSE*` が無く、`pyproject.toml` にも `license` が無い（`git grep -il license` は研究メモと作業記録だけ）。付けないと他人は使えない（【一般知識】、取り直していない） |
| `authors` のメール | **要る（判断）** | 0 節。外すか noreply にする |
| 履歴のメール | **要る（判断）** | 0 節 |
| 参考資料 2 つ（`doc/physical_ai_isaacsim_poc_ja.md`、`..._slides_ja.html`） | **判断** | 問い 4 |
| `log/sessions/`（セッション記録 4,713 行） | **判断** | 問い 5。発注者の指示の全文とサブエージェントへの依頼文が入る。伏せ字の検査は 0 件だが、内容は公開される |
| CI のバッジ | 要る（1 行） | URL は `https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg`（GitHub Docs、17:4x）。OWNER/REPO が決まってから。README は S075 が触るので、S075 の取り込み後に統括が足す |
| Actions の費用 | 心配なし | 公開リポジトリの標準ランナーは無料（GitHub Docs「GitHub Actions billing」、17:4x: "The use of standard GitHub-hosted runners is free" の最初が public repositories） |
| `CONTRIBUTING.md` | 要らない | 個人の学習用。README に「PR は受けない/歓迎」のどちらかを 1 行 |
| Issue テンプレート | 要らない | 受けないなら Issues を閉じるだけ（設定） |
| `SECURITY.md`・`CODE_OF_CONDUCT.md`・`CHANGELOG.md` | 要らない | 日付つきの計画と作業記録が代わりになっている。秘密の値は無い |
| SolidCraft の名前とロゴ | ロゴは使わない | ロゴ・名前は別ライセンス LICENSE-BRAND（SolidCraft README、17:3x 取得）。名前を文章で書くのは今のままでよい（【推測】） |
| Dependabot | 後で | 版を固定しているので急がない |

### 発注者への問い（そのまま送れる形）

1. **コードのライセンス**: (a) `MIT OR Apache-2.0`（姉妹リポジトリ GlobeMode と同じ。`LICENSE-MIT` と `LICENSE-APACHE` の 2 ファイル、`pyproject.toml` に `license = "MIT OR Apache-2.0"`。GlobeMode の `Cargo.toml`・`pyproject.toml`・README で確認、17:3x）、(b) `MIT` だけ（1 ファイル）、(c) 付けない（他人は使えない）。私の推薦は (a)（【推測】。揃えると判断が 1 つ減る）。
2. **教材の文章**（`doc/` 以下）のライセンス: (a) コードと同じにする（最小）、(b) `CC BY 4.0`（出典を書けば誰でも使える）、(c) `CC BY-SA 4.0`（改変も同じ条件）。Creative Commons は**ソフトウェアに CC を使うことを勧めない**（CC FAQ、17:3x 取得: "We recommend against using Creative Commons licenses for software"）ので、分けるなら**文章だけ**に CC を使う。分けた場合は README に「コード: …、教材（`doc/`）: …」と 1 行書く。私の推薦は (a)（【推測】）。
3. **メールアドレス**: 0 節の (a) 書き換えて noreply にする／(b) そのまま／(c) 履歴を捨てる。(a) なら noreply アドレス（Settings > Emails の `ID+USERNAME@users.noreply.github.com`）を教えてほしい。
4. **参考資料 2 つ**（ChatGPT と作った設計書とスライド、2026-10-22 時点）を公開してよいか。OpenAI の規約は、出力の権利を利用者に渡すと読める（検索結果の要約による。規約の原文は取得が 403 で読めていない【未確認】。要約: "As between you and OpenAI ... you own the Output"、ただし他の利用者に似た出力が出ることがある）。文書の中には販売ページの価格・仕様の引用がある（事実なので問題は小さいと考える【推測】）。公開しないなら N1 の書き換えで履歴からも外す。
5. **`log/sessions/`**（会話の記録）を公開してよいか。公開しないなら `.gitignore` に入れて履歴からも外す。公開するなら、判断材料としては「作業の経緯が全部読める」と「発注者の発言と依頼文が公開される」の両方。

## 3. SolidCraft を S2R / R2S の輪に組み込む道筋

取得は 17:3x〜17:4x。出典の短縮: [docs] = https://docs.solidcraft.io/ 、[gh] = https://raw.githubusercontent.com/tangency-labs/solidcraft/main/ 。

### 3.1 公式の文書で分かったこと（事実）と、まだ無いこと

| # | 事実 | 出典 |
|---|---|---|
| F1 | CLI `solidcraft-cli` は窓なしで `run script.json --out part.step`、`eval`、`snapshot`、`exec` を動かす。`run` に `--json-out`、`--param-check warn\|strict`、`--quality` がある。GPU が無ければ CPU で描く（`SOLIDCRAFT_GPU=cpu`） | [docs]guide/getting-started.html |
| F2 | MCP のツールは 22 個: `list_commands`・`describe_command`・`execute`・`batch`（最初の誤りで巻き戻す）・`inspect_design`・`measure`・`set_parameter`・`check_parameters`・`screenshot`・`export`（STEP・IGES・3MF・メッシュ・GLB・URDF）・`open`・`save`・`undo`・`redo` ほか | [docs]guide/mcp.html |
| F3 | MCP は 2 通り: 窓なし（`solidcraft-cli mcp [--in part.sc]`）と、**起動中のデスクトップ版に接続**（アプリの設定で "Let AI agents connect"、`--connect 127.0.0.1:7878`）。接続は 127.0.0.1 だけ、同じ PC の中だけ。**この頁はデスクトップ版の説明で、ブラウザー版には触れていない** | [docs]guide/mcp.html |
| F4 | **ブラウザー版は MCP につながらない**（書いていない、というだけでなく別の仕組み）。ブラウザー版は、そのタブの `window.solidcraft`（JavaScript）で動かす。"does not register WebMCP tools or expose a network listener"。タブの JavaScript を実行できるエージェントなら同じ呼び出しができる。ファイルのパスはブラウザーの仮想ファイルシステム | [gh]docs/browser-api.md |
| F5 | 設計の保存: `.sc`（バージョンつきの入れ物、または JSON）と、**`.json`（自己完結の平文 JSON）**。`.json` の名前で保存すれば JSON のまま保たれる。開くときは中身で形式を見分ける。Save As JSON はデスクトップにもウェブにもある | [gh]docs/book/src/guide/files.md |
| F6 | 質量特性: 材料の密度つきで、質量・重心・慣性テンソル。**公式文書（main の docs）は `inertia_g_mm2`（g·mm²、10⁹ で割る）と書くが、v0.44.1 の CLI が実際に返す JSON は別の形**だった（第 2 巡 17:50 に確認。5.4 節）: `groups[].mass.{mass_kg, center_of_mass_mm, inertia_world_kg_mm2}`、単位は **kg·mm²（10⁶ で割る）**。丸い物体は標準の品質で約 0.1 %。メッシュが閉じていなければ `null` | [gh]docs/assembly-properties.md、実測 |
| F7 | Linux 版は v0.44.1 に tar.gz（180 MB）・AppImage・deb・rpm・snap・flatpak がある。単体の CLI の zip は macOS だけ。Linux で `solidcraft-cli` がどのパッケージのどこに入っているかは【未確認】（S042 が確かめる） | GitHub API releases/tags/v0.44.1 |
| F8 | 版: v0.44.1 が最新の正式版（2026-11-17）。毎日 nightly（今日 05:41Z に v0.45.0-nightly）が出る。README は "Early but usable for simple parts" | GitHub API、[gh]README.md |
| F9 | ブラウザー版は `?open=<エンコードした HTTPS の URL>` で設計を開ける。`raw.githubusercontent.com` は `access-control-allow-origin: *` を返す（17:38 に `curl -I`）ので、ブラウザーの制約には掛からないはず。**SolidCraft がその URL を受け付けるかは【未確認】** | [docs]guide/getting-started.html |

**まだ無い/確かめていない**:
- ブラウザー版と `solidcraft-cli mcp` の直結（F3・F4）。
- STEP がバイトで同じになる保証（書いていない）。**比べるのは数字**にする。
- WSL2 の中の Claude Code から、Windows 側のデスクトップ版の 127.0.0.1 につながるか（WSL2 のネットワーク設定次第、【未確認】）。
- この PC で CLI が動くか（S042 が確かめている最中）。

### 3.2 「GUI で形を決める → リポジトリ → CLI → sim」は現実的か

**現実的。ただし中心に置くのは、ブラウザーの画面ではなく「ファイル」**。発注者の「ブラウザー版が主・GUI と MCP の両方」は、次の 3 つの道のうち R1 で満たせる。

| 道 | 中身 | 判定 |
|---|---|---|
| **R1 ファイルの受け渡し** | 人がブラウザー版で設計 → JSON を保存（F5）または `timeline.export_script` で出力 → `cad/` にコミット。Claude は窓なしの MCP（`mcp --in cad/xxx.json`）で開いて編集し `save` → コミット。人はブラウザーで開き直して確かめる（F9 が通れば GitHub の URL 1 本で開ける） | **推薦**。今日からできる（CLI が動けば） |
| R2 デスクトップ版 + `mcp` の接続 | 人の画面で Claude の操作がそのまま見える（F3）。ブラウザーが主という要望とは違う。WSL2 の壁（上の【未確認】）がある | 発注者がデスクトップ版でもよいなら、体験は一番よい。【未確認】が 2 つ |
| R3 ブラウザー版を JavaScript で動かす | タブの JavaScript を実行できるエージェントが要る（F4）。MCP ではないので、公式の 22 個のツールは使えず、`solidcraft.execute` を直接呼ぶ | 試験的。今夜はやらない |

**R1 で「正」にするもの**【推測】: コマンドの列（`cad/plate.json` のような `{"commands": [...]}` のスクリプト、`parameters.add` で寸法を名前つきにする）。理由: (i) 人が読めて差分が取れる、(ii) `run --param-check strict` で CI が検査できる、(iii) `timeline.export_script` でブラウザーの設計から取り出せる（公式文書: "In the app and over MCP"）。`.json`/`.sc` の設計ファイルはその写し。**どちらを正にするかは S042 が実際に動かした結果で決める。**

質量特性から sim への道（F6 → N5）: 設計 → `run` で窓なしに質量特性を出す → `inertia_g_mm2` の zz 成分（z 上の設計のとき、鉛直軸まわり = ヨーの慣性）を kg m² にする → `cad.py` の `mass_props` の Izz に入れる → MuJoCo の車体と 13 章の τ の式に使う。**CAD の座標が「z 上」であること、世界座標のテンソルであることを、依頼文で固定する**。

### 3.3 CI で `cad/` を検査する案の是非

**作る価値はある。ただし明日、S042 が手元で通してから**（今夜は N5 の条件が揃えば、その後で）。
- やること: `cad/**` が変わったときだけ動く**別のワークフロー**（`cad.yml`。pytest の CI と分け、バッジを赤くしない）。CLI を**版を固定して**取る（nightly は毎日変わる）、同じリリースの `SHA256SUMS.txt` で検査、キャッシュ。`run --param-check strict` が 0 で終わり、質量・重心・外形が `cad/expected.json` の値の許容内（STEP のバイト比較はしない）。
- 守りたいもの: **MCP で Claude が JSON を書き換えたとき**に、コマンドが壊れていないこと・質量が桁で変わっていないこと。人が見落としやすい所。
- 費用と危険: 毎回 180 MB のダウンロード（キャッシュで緩和）、0.x の版の仕様変更、GPU の無いランナーで `run` が動くか【未確認】（F1 は描画の CPU 代替を言うだけ）。【推測】で「失敗しても main を止めない」設定から始める。

### 3.4 MCP で Claude に設計させる最小の題材と、人が確かめること

**題材: 「XIAO の基板の中心を旋回中心（左右の車軸の中点）の真上に置く取り付け板」**。`cad/README.md` の要件 2 と同じ。
- 依頼文の骨子（N5 の `doc/cad-mcp.md` に書く）: 座標は x 前・y 左・z 上、原点は車軸の中点、単位 mm。板は長さ × 幅 × 厚さをパラメーター（`parameters.add`）にする。XIAO 用の穴/ポケットの中心を原点に置く。基板の外形は 21 × 17.8 mm（`dimensions.csv` の値、datasheet）。**Robo Base の取付穴は未確認なので、穴は開けない**（`cad/README.md` の注意）。材料と密度を指定。書き出しは STEP と質量特性。最後に `set_parameter`/`check_parameters` で長さを変えても壊れないことを確かめさせる。
- **IMU の位置は基板の中心とは違う**。基板上の位置は【未確認】（`dimensions.csv`）。題材の学びはここ: 「中心に置いた」つもりでも d が数 mm 残り、それは旋回中の ax から逆算できる（16 章、R2S）。
- **人が確かめる表**（Claude の自己申告や screenshot を証拠にしない）:

| # | 確かめること | 方法 |
|---|---|---|
| 1 | 寸法が `dimensions.csv` の値と一致 | 別の道具で測る（`measure` の数字と表を人が突き合わせる） |
| 2 | XIAO の穴の中心が原点 | `inspect_design` ではなく人が画面で頂点の座標を読む |
| 3 | 座標の向き（x が前） | 16 章の約束と、板の切り欠きの向きを画面で |
| 4 | 質量・重心・Izz の桁 | 板 1 枚なら `m(a²+b²)/12`（`cad.py` の箱の公式）と 1 % 以内か。密度の単位と値を材料の公称値と照合 |
| 5 | パラメーターを変えても壊れない | `check_parameters`（元に戻る）を人が 1 回見る |
| 6 | 実物に合うか | 原寸の紙に印刷して XIAO とベースに当てる。穴の位置は**ノギスで測ってから**。**実機で未確認** |
| 7 | 保存した JSON の差分が読める | `git diff` で、意図しない変更が無いか |

- **MCP の安全**: `--allow-any-path` を付けない（公式: 読み書きは許可されたフォルダーの中だけ）。`claude mcp add` は発注者の設定の変更なので、発注者が決める。公開リポジトリに、自分のインストール先の入った `.mcp.json` を置かない。

## 4. 明日以降の並びの見直し（昼の outlook.md の 8 節に印をつける）

| 昼の番号 | 夜の状態 | 見直し |
|---|---|---|
| S040 stock-and-compile | 在庫は S043 が一部。**MG24 のコンパイルは N3 に移した** | 明朝は、在庫と価格の再確認と、発注の判断材料の 1 枚だけ（発注者の判断待ち） |
| S041 numbers-once | 夜に実行中 | そのまま |
| S042 solidcraft-run | 夜に実行中 | 結果で 3.2 の「正」を決める。N5 と `cad.yml` が続く |
| S043 solutions-2 | 昼の割り当てでは S076 に入った | 昼の番号 S043 は夜に別の用（監査 4）に使われた。**番号を呼び直す**（S076 のまま） |
| S044 sim-checks | 夜の S044 はこの展望の役 | 番号を **S078** に付け替え（seed 違いの `loop-demo`、numpy と MuJoCo の比較、MuJoCo の描画）。S070〜S077 の後 |
| S045 fake-vs-sketch | 夜の S045 は寸法調査 | 内容は**未着手**。番号を **S079** に付け替え。S041 の後（`fakexiao.py`・`link.py` を触る） |
| S050〜S053 実機 | 部品が届くまで止まる | **N2（hwcheck）が先に入っていると S050 が短くなる**。S052 エンコーダーの前提は変わらない |
| S060 remote-ci | S039 が CI を作る。**push は 0 節の返事を待つ** | N1 の手順で書き換えてから push。バッジは S075 の後 |
| 新規 | | **S080 公開の仕上げ**: ライセンスの文書、README の License 節とバッジ、`authors` の直し、`doc/publishing.md` の反映（S075 の後。README を触るので） |

夜の部で**済みそうなもの**: S041・S042（CLI の実行まで）・S046・S070〜S077・N1〜N4。済みそうにないもの（明日へ）: `cad.yml`、N5 の `cad.py` への接続、S078・S079、発注。

## 確かめていないこと

- `uvx git-filter-repo` が動くか。書き換えの手順は未実行（N1 の仕事）。
- GitHub の「Block command line pushes」が、**書き換え後**の先頭コミットに何を言うか。
- OpenAI の規約の原文（403 で読めていない。検索の要約だけ）。
- SolidCraft: F4 の「別の仕組み」は browser-api.md の記述による。実際にタブから呼んではいない。`?open=` に GitHub の raw URL を渡して開くかは未試験。F7 の Linux の CLI の場所。
- MCP ツール名 `mcp__solidcraft__*` の形（Claude Code の規則からの推測）。
- `firmware/` を S047 が触るかどうか（S047 に聞く）。
- 所要時間（20〜30 分）はすべて推測。

---

# 第 2 巡（JST 17:45〜18:15）

第 1 巡の採否（統括）: 0 節は履歴の書き換えで進む（N1 は統括が済ませた。`doc/publishing.md` は不要）。N3 は S039 の `ci.yml` に入った。N2・N4・N5 は採用。番号は統括が予約する。この文書では仮に **S081 hwcheck、S082 troubleshooting、S083 solidcraft-props** と呼ぶ。
S042 が main に入った（CLI は WSL2 で動いた）ので、N5 の「CLI が動いた場合」は現実になった。両方を書く。

## 5. 依頼文（そのまま渡せる形）

### 5.1 3 本に共通の決まり

昼の outlook.md の 12.0 の「決まり」をそのまま貼る。加えて次を貼る。

- 触ってよいのは依頼文に列挙したファイルだけ。S041 が `src/physlearn/` の `sim.py`・`sysid.py`・`control.py`・`link.py`・`randomize.py`・`cad.py`・`__init__.py` を、S070〜S077 が `README.md`・教材の全章・索引・計画・解答集・図・`doc/bringup.md`・`doc/setup.md` を触る。**これらは読むだけ**。
- `README.md`・`doc/README.md`・`doc/textbook/README.md`・`doc/bringup.md`・`cad.py`・`pyproject.toml` に 1 行足したいときは、**直さずに作業記録の「統括が最後に足す」の節に、足す場所と文面を書く**。
- 今の main の最新を `git -C <main> log --oneline -10` で確かめてから始める。S047 が 03・09 章の電流・電圧の記述を直した（DRV8835 は 1 ch 連続 1.5 A、3V3 のレギュレーターは 250 mA、秋月の説明書でピン表が読めた）。古い記憶で書かない。
- 実機では何も確かめていない。合格基準は、出どころ（スケッチの定数、データシート、`randomize.SPREAD`）を書き、根拠の無いものは「目安（根拠なし）」と書く（bringup と同じ流儀）。

### 5.2 S081 `hwcheck`（1 体、25〜30 分、新規ファイルだけ）

> あなたはセッション S081 (hwcheck) の担当。PhysLearn（XIAO と IMU の 2 輪車で Sim2Real と Real2Sim を学ぶ教材とコード）に、**実機が届いた日の最初の 30 分を機械にする道具** `python -m physlearn.hwcheck` を足す。`doc/bringup.md` の段 1〜3（`I` 行が流れる、1 秒 100 行、静止の値、軸の向き）は今は人が `picocom` と CSV を目で見て確かめる。軸の符号は、間違えても動いてしまい、以後の同定が静かに狂うので、特に機械にしたい。
>
> **場所と決まり**: worktree `.git-worktree/s081-hwcheck`、ブランチ `feature/s081-hwcheck`（`/start-session`）。共通の決まりは 5.1。
>
> **先に読む**: `CLAUDE.md`、`doc/bringup.md` の段 1〜3 と「止め方」、`doc/textbook/03-hardware-firmware.md` の 3.5〜3.7、`doc/protocol.md`、`src/physlearn/link.py`（`decode_sample`・`parse_axes`・`SerialPlant`）、`src/physlearn/imu.py`（`stats`・`yaw_deg`）、`src/physlearn/fakexiao.py`、`tests/test_fakexiao.py`（偽の XIAO を試験で使う型）、`src/physlearn/log.py`。
>
> **触ってよいファイル**: `src/physlearn/hwcheck.py`（新規、約 150 行）、`tests/test_hwcheck.py`（新規）、`log/work/2026-11-19-s081-hwcheck.md`。
> **触らないファイル**: 5.1 の一覧。`link.py`・`imu.py`・`fakexiao.py` は**読むだけ、import して使うだけ**。名前が変わっていたら止めて報告する。`__init__.py` と `pyproject.toml` に登録しない（`python -m physlearn.hwcheck` で呼ぶ）。
>
> **やること**
> 1. **`check_stream(log) -> list[Check]`**。`log` は `log.as_log` が返す列の辞書（`t,ax,ay,az,gx,gy,gz`）。`Check` は (項目, 合否 `"ok"|"ng"|"目安"`, 実測, 基準, 基準の出どころ, 外れたときの次の手) の 6 つ。項目:
>    - 行数/秒: `imu.stats` の `dt_mean` から。基準 100 Hz ±5 %（スケッチの `PERIOD_US = 10000`）。
>    - 欠けた行: `diff(t) > 1.5 × 0.01` の数。基準 0 件（根拠なし。「目安」）。`# ERR` の行は `SerialPlant` が読み捨てるので数えない（その旨を結果の注に書く）。
>    - 静止の重力: `|a|` の平均と `G = 9.80665` の差。基準 ±0.5 m/s²（bringup 段 2 の「目安（根拠なし）」と同じ印）。
>    - `gz` の平均（バイアス）: 基準 |平均| ≤ 0.02 rad/s（`randomize.SPREAD["gyro_bias"]` を **import して**使う。数を二重に書かない）。
>    - `gz` の標準偏差: 基準なし。0.01 rad/s 前後（sim の公称 `gyro_noise`、`sim.Params` から）と並べて表示するだけ（合否なし）。
>    外れたときの次の手は bringup の該当の段への案内（例「bringup 段 1: 書き込みをやり直す」）。**段の番号は S075 が直すかもしれないので、文字は「bringup の『XIAO 単体』の段」のように見出しの語で書く**。
> 2. **`axes_from_poses(rest, nose_up, left_up) -> AxesResult`**。引数は各姿勢で静止させたときの基板の加速度 (ax, ay, az) の平均（3 要素）と、そのときの `|gyro|` の平均と `|a|` の標準偏差。
>    - **式**: 機体座標への回転を R（`link.parse_axes` が返す 3×3、`v_body = R @ v_board`）とする。姿勢 k では機体の軸 k が真上を向くので、`R @ a_board = g·e_k`。したがって、基板の加速度 `a_board` の絶対値が最大の成分が j、その符号が s なら、`R[k, j] = s`（他の列は 0）。つまり軸の文字列の k 番目の語は `s` と `"xyz"[j]`。姿勢は rest = 水平（機体 z が上、k = z）、nose_up = 鼻を真上（k = x）、left_up = 左側を真上（k = y）。
>    - **断る条件**（どれも `AxesResult(ok=False, 理由, 次の手)` を返し、**文字列を作らない**）: (i) `|a|` が G の ±15 % の外（動いている、または単位が違う）、(ii) 姿勢中の `|a|` の標準偏差が 0.3 m/s² 超か、`|gyro|` の平均が 0.1 rad/s 超（手で持って揺れている）、(iii) **重力がどの軸にも乗り切らない**: `max|a_j| / |a| < 0.94`（真上から約 20° 以上ずれている。0.94 は cos 20° で、根拠は「目安（根拠なし）」と書く）、(iv) 3 姿勢で選ばれた基板の軸が重なる（置換になっていない）、(v) 組み立てた R の行列式が −1（鏡映。**IMU のチップの軸は右手系なので、実機で鏡映になるのは姿勢の取り違え、たいていは左右の取り違え**。その旨を理由に書く）。
>    - ok のときは `spec`（`"y,-x,z"` の形）を返し、`link.parse_axes(spec)` が通ることを確かめてから返す。`R` の外積による検算（`R[z] == R[x] × R[y]`）も行う。
> 3. **対話のコマンド**: `python -m physlearn.hwcheck stream --port P [--seconds 5] [--axes x,y,z]`（`SerialPlant` で読み、`check_stream` の表を出す。終了コードは 1 つでも ng があれば 1）。`python -m physlearn.hwcheck axes --port P`（「水平に置いて Enter」「鼻を真上に立てて Enter」「左側を真上に立てて Enter」と促し、各 2 秒読む。断られたら**同じ姿勢をやり直させる**。ok なら `--axes <spec>` を表示し、続けて「上から見て反時計回りに机の上で約 90° 手で回して Enter」と促し、`imu.yaw_deg` に R を掛けた gz を積分して符号が正（+30° 以上）かを示す。負なら「ジャイロの符号が合わない。基板の軸の読み違い」）。**モーターは動かさない**（`SerialPlant` に指令は `S`/`M 0 0` しか送らない）。
> 4. **試験**（速いものだけ）: (a) 偽の XIAO（`FakeXiao`、`tests/test_fakexiao.py` の `fake_factory` と同じ型）を相手に `check_stream` が全部 ok。偽物の `--speed` を落とす（または `PERIOD_MS` が変わった偽物）と行数/秒が ng。 (b) `axes_from_poses`: **右手系の 24 通りの符号つき置換**すべてについて、`R[k,:]·g` から合成した 3 姿勢（雑音 0.05 m/s²）が元の `spec` に戻る。 (c) 断る 5 条件を 1 つずつ（傾き 30°、動き、重なり、左右を入れ替えた鏡映、`|a|` = 5）。 (d) `FakeXiao(axes="y,-x,z")` の**水平の姿勢だけ**が R の z の行を当てる（偽の XIAO は重力の向きを変えられない。鼻上げ・左上げは合成の値で試す、と試験の docstring に書く）。
>
> **受け入れ条件**: `uv run pytest tests/test_hwcheck.py` が通り、全体の `uv run pytest` も通る。24 通りが全部戻る。断る 5 条件が全部断る。`uv run python -m physlearn.hwcheck stream --help` と `axes --help` が出る。
> **確かめ方**: 偽の XIAO（`uv run python -m physlearn.fakexiao` で出る `/dev/pts/N`）に `stream --port /dev/pts/N --seconds 3` をつないで、表を作業記録に貼る。
> **終わりに**: 作業記録（検証の数字、「統括が最後に足す」の節）。**S075（bringup を直す担当）への申し送り**として、作業記録に次を書く: 「段 1 の『`I` 行が流れる』の次に `python -m physlearn.hwcheck stream --port ...` を足す。段 2 の『静止ログ』は `stream` の結果で置き換えられる。段 3 の『軸の向き』は `python -m physlearn.hwcheck axes --port ...` で `--axes` の文字列が出る（4 つの確かめのうち、水平・鼻上げ・左上げ・反時計回りの 4 つを対話で行う）。実機では未確認。」所要 25〜30 分（推測）。収まらなければ 3 の `axes` の対話の「回して確かめる」の部分を残して止め、そう書く。

### 5.3 S082 `troubleshooting`（1 体、20 分、新規ファイル 1 本）

> あなたはセッション S082 (troubleshooting) の担当。部品が届いた日に、学ぶ人が「症状 → 原因 → 確かめ方 → 次の手」で探せる一覧 `doc/troubleshooting.md` を作る。**新しい事実は書かない**。今ある文書とコードのエラー文から拾って並べるだけ。
>
> **場所と決まり**: worktree `.git-worktree/s082-troubleshooting`、ブランチ `feature/s082-troubleshooting`。共通の決まりは 5.1。
>
> **先に読む**: `doc/bringup.md`（各段の「外れたら」）、`doc/textbook/03-hardware-firmware.md`、`09-safety.md`、`12-fake-xiao.md`、`doc/setup.md`、`doc/protocol.md`、`doc/research/2026-11-19-hardware.md`、`log/review/2026-11-19-s036-audit3-claude.md` と `log/work/2026-11-19-s047-audit3-fix.md`（電流・電圧の最新の値）。エラー文は `grep -rn 'raise \|SystemExit\|p.error\|# ERR\|print(.*警告\|TimeoutError' src/physlearn firmware` で拾う。
>
> **触ってよいファイル**: `doc/troubleshooting.md`（新規）、`log/work/2026-11-19-s082-troubleshooting.md`。**`doc/README.md` への 1 行（表に「troubleshooting.md: つまずき集」）は統括が最後に足す**（作業記録に文面を書く）。
>
> **やること**
> 1. 表を段ごとに作る: 書き込み（ブートローダー、FQBN、`adafruit-nrfutil`）、USB（usbipd、`/dev/ttyACM0` が出ない、権限）、IMU（`I` 行が出ない、`# ERR imu not found`、0x6A/0x6B、軸の向き）、モーター（逆に回る、回らない、デッドバンド、熱い）、安全（ウォッチドッグで止まる、`SafetyGate` の作動、`|gz| > 15`）、同定（`drift`、時定数が範囲外、ばらつきの外）、閉ループ（`仕様 NG`、振動）、PC 側（`uv sync`、`mujoco` の extra、`pty` が無い）。**20〜30 行**。
> 2. 各行: 症状（画面に出る文字そのままを `コード書式` で）／考えられる原因（**出どころのファイルと節を文字で**。例「03 章 3.4」）／確かめ方（実際のコマンド）／次の手／**実機で確かめたか**（全部「いいえ（机上）」。偽の XIAO で再現できたものは「偽の XIAO で再現」）。
> 3. 見出しへのリンク（`#anchor`）は使わない。S070〜S077 が見出しを直すかもしれないので、**ファイル名と節の番号を文字で書く**。ファイルへの相対リンクだけは付ける。
> 4. 最後に「それでも分からないとき」の節: 止め方（bringup の「止め方」の 3 つを要約。電池ボックスのスイッチに手が届くこと）、作業記録に何を書いておくと後で読めるか（`log/work/` の雛形）。
>
> **受け入れ条件**: (1) 症状の欄の画面の文字列は、すべて `src/physlearn`・`firmware` に**そのまま**ある（`grep -F` で全部 1 件以上。作業記録に件数を書く）。(2) 相対リンクがすべて存在するファイルを指す（使い捨ての確認スクリプトをスクラッチ領域で走らせ、結果を記録。コミットしない）。(3) 電流・電圧の数字は S047 の値（DRV8835 は 1 ch 連続 1.5 A、3V3 は 250 mA）と食い違わない。 (4) 新しい断定がない（原因の欄はすべて出どころつき。無いものは【推測】）。
> **確かめ方**: 偽の XIAO で再現できるもの 3 つ以上（例: `# ERR bad line`、時間切れ、ウォッチドッグ）を実際に起こして、出る文字を表と照合する。
> **終わりに**: 作業記録に「統括が最後に足す」（`doc/README.md` の 1 行）。所要 20 分（推測）。

### 5.4 S083 `solidcraft-props`（1 体、30 分、新規ファイルが中心）

> あなたはセッション S083 (solidcraft-props) の担当。SolidCraft が出す質量特性（質量・重心・慣性）を `physlearn` の言葉（kg・m・kg m²、機体座標 z 上のヨーの慣性 Izz）に読み替える口と、**Claude が MCP で設計するときの依頼文と人の確かめ方**の文書を作る。`cad.py` は Izz を直接持つ部品を受けない（S042 の積み残し）ので、`cad.py` を触らずに、受け手を別のモジュールに作る。
>
> **場所と決まり**: worktree `.git-worktree/s083-solidcraft-props`、ブランチ `feature/s083-solidcraft-props`。共通の決まりは 5.1。
>
> **先に読む**: `CLAUDE.md`、`cad/README.md`、`cad/plate_mount.json`、`cad/plate_mass.json`、`log/work/2026-11-19-s042-solidcraft-run.md`、`doc/research/2026-11-19-solidcraft.md`（S042 が追記した節）、`doc/textbook/16-enclosure.md` の 3・4 節、`src/physlearn/cad.py`（`mass_props` の `(質量, 重心, 重心まわりの Izz)` の返し方と平行軸の合成）、`doc/plan/2026-11-19-outlook-evening.md` の 3 節と 6 節（この文書）。
>
> **触ってよいファイル**: `src/physlearn/solidcraft_props.py`（新規、約 80 行）、`tests/test_solidcraft_props.py`（新規）、`tests/data/solidcraft_mass_plate_mount.json`（新規。CLI の実出力）、`doc/cad-mcp.md`（新規）、`log/work/2026-11-19-s083-solidcraft-props.md`。
> **触らないファイル**: `cad.py`（S041・S074 が触る）、`cad/` の全部（S042 の持ち分。足したい設計は作業記録に書く）、`.claude/`・`.mcp.json`（**許可リストと MCP の登録は発注者が決めること。設定は変えない**）、5.1 の一覧。
>
> **実際の出力の形**（v0.44.1 の CLI、JST 17:50 に走らせて確かめた）:
> ```bash
> solidcraft-cli run cad/plate_mount.json --save pm.sc
> solidcraft-cli run cad/plate_mass.json --in pm.sc --results --json-out mass.json
> ```
> `mass.json` は**リスト**で、`[0]["groups"][i]["mass"]` に `mass_kg`、`center_of_mass_mm`（x,y,z）、`inertia_world_kg_mm2`（3×3、**単位は kg·mm²**）、`inertia_local_kg_mm2`。板（`plate_mount`）の値: `mass_kg` 0.03857785113936533、`center_of_mass_mm` = (≈0, ≈0, 1.5)、`inertia_world_kg_mm2[2][2]` = 74.82637350671482。**公式文書（main）の `inertia_g_mm2`（g·mm²）とは名前も単位も違う**。版が上がると変わりうるので、版を固定し、読み取りは**実際の形で書き、見つからなければ名前を出して例外にする**。
>
> **やること**
> 1. **`CLI が動いた場合`（今の状態）**
>    - `solidcraft_props.py`: `MassProps(mass_kg, com_m, inertia_kgm2)`（com は m、慣性は kg m² の 3×3）。`load(path_or_obj)` が上の形を読む（`groups` が 2 つ以上なら、全体の合成を平行軸で自分で出すのではなく**例外にして「`groups` を 1 つにするか `combine` を使う」と言う**）。換算は `kg·mm² × 1e-6 = kg·m²`、`mm × 1e-3 = m`。`izz` は `inertia[2][2]`（世界座標で z 上のとき鉛直軸まわり）。`combine(parts: list[MassProps]) -> MassProps` は、質量で重みづけた重心と、`Σ(I_i + m_i·(d_i² 1 − d_i d_iᵀ))`（3×3 の平行軸の定理）。`yaw_inertia_about(p, x, y)`（鉛直軸を (x, y) に移したときの Izz）。**CAD の座標が機体座標（x 前・y 左・z 上、原点は車軸の中点）であることは呼び出す側の約束**で、`load` は黙って信じない: 引数 `expect_z_up=True` のとき、慣性の対角が正で、非対角が対角の 1e-3 倍以内（板のように軸に揃った物）でないと警告を返す。
>    - 試験: (a) `tests/data/` の実出力（3 KB 程度に刈ってよい）で `mass_kg`・`izz` が上の数字に一致（相対 1e-9）。 (b) 直方体の公式 `m(a²+b²)/12`（`cad.part_izz("box", ...)` を呼ぶ）と、一様な板の合成値が一致（SolidCraft で別の板を作れば 1 % 以内、作らなければ `combine` の自己検算だけ）。 (c) `combine` が 2 枚の板を並べた値を、片側にずらした 1 枚の `part_izz` + 平行軸と 1e-9 で一致。 (d) `null` を含む入力・キーが無い入力・単位の取り違え（`inertia_g_mm2` という旧い名前）で、分かる文で例外。
> 2. **`CLI が動かなかった場合`（別の PC や版が変わったとき。試験は (c)(d) だけ、(a)(b) は手書きの値）**: ブラウザー版の Inspect → Measure → Properties の窓にある **Copy matrix**（公式: 3 行のタブ区切りで、表示の単位のまま）をクリップボードから貼って読む `from_clipboard(text, mass_g, com_mm, unit)`（`unit` は `"g mm2"` か `"kg mm2"` を**引数で必ず指定**。既定を持たない）。この口は CLI が動くときも、ブラウザーの数字と CLI の数字を突き合わせるのに使う。
> 3. **`doc/cad-mcp.md`**（新規。次の 6 節を持つ）:
>    - (a) 経路 R1（この文書の 3.2 節）の手順。設計の正は **設計 JSON（`Save As JSON`）**、スクリプトは種（第 2 巡 6.3）。
>    - (b) MCP の登録の仕方（`claude mcp add solidcraft -- solidcraft-cli mcp`、公式 README の 1 行）。**設定は変えない。発注者が決める**と明記。CLI の置き場所は S042 の文書にある 3 案。
>    - (c) **発注者への提案**として、許可リストに入れてよい読み取り系のツール（`list_commands`・`describe_command`・`inspect_design`・`measure`・`body_topology`・`version`・`screenshot`）と、入れない書き込み系（`execute`・`batch`・`set_parameter`・`open`・`save`・`new_design`・`export`・`undo`・`redo`）。ツール名の出どころは公式の MCP の頁（17:46 取得）。Claude Code の許可の書式（`mcp__solidcraft__<tool>`）は【未確認】と書く。`--allow-any-path` は付けない。
>    - (d) 題材「XIAO の基板の中心を旋回中心の真上に置く取り付け板」の**依頼文の雛形**（座標は x 前・y 左・z 上・原点は車軸の中点・単位 mm、材料と密度を**明示**（指定しないと既定の材料の密度が使われる）、パラメーター名、穴は開けない／`TBD_` の穴は仮、書き出しは設計 JSON と質量特性）。`cad/plate_mount.json` を出発点にする。
>    - (e) 人が確かめる表（第 1 巡 3.4 の 7 項目に、**CLI の質量と Properties の質量が一致するか**を足す）。
>    - (f) `solidcraft_props` の使い方（試験で通った例だけ）。
>
> **受け入れ条件**: `uv run pytest` が全部通る。実出力から Izz = 7.4826e-5 kg m² が出る（S042 の記録 7.48264e-5 と 1e-5 以内）。`doc/cad-mcp.md` のコマンドは、書いたものを**実際に走らせた**（CLI のパスは S042 の置き場、またはこのセッションで落とし直した場所）。走らせていないものは【未実行】。
> **確かめ方**: 実出力を `load` に通す。`cad/plate_mount.json` のパラメーターを変えた設計（S042 の README の方法）でも質量が合理的に動く（板厚 3 → 4 mm で質量が 4/3 倍）ことを 1 回。
> **終わりに**: 作業記録の「統括が最後に足す」に、(1) `cad.py` の `mass_props` が `MassProps` を部品として受ける 1 か所（S041・S074 の後）、(2) `doc/README.md` に `cad-mcp.md` の 1 行、(3) `cad/README.md` の「正本」の記述の直し（6.3 の推薦を採るなら）。所要 30 分（推測）。収まらなければ 2 と 3(b)〜(f) の一部を残す。

## 6. SolidCraft のブラウザー版の裏取り（1 段深く）

取得は 17:39〜17:50。【未実行】は自分で動かしていないもの。ブラウザー版は一度も開いていない（この環境にブラウザーの操作手段が無い）。

### 6.1 結論の原文

結論: **公式の文書は、`solidcraft-cli mcp` をブラウザー版につなぐ方法を書いていない。ブラウザー版を外から動かす口は、そのタブの `window.solidcraft`（JavaScript）だけ。** 「つながらない」と明記した文はなく、下の 2 つの記述から読み取れる結論（私の推測）。

| 文 | 出典と取得 |
|---|---|
| "An agent with JavaScript evaluation access to this tab can make the same calls. The API does not register WebMCP tools or expose a network listener." | https://raw.githubusercontent.com/tangency-labs/solidcraft/main/docs/browser-api.md 、17:39 取得 |
| "Bridged, the server finds the app's control token in the token file the app wrote for that port" | https://docs.solidcraft.io/guide/mcp.html 、17:46 取得（HTML から本文を取り出した） |
| "Bridged screenshots are written to a temporary file by the app and read back by the server, so both must run on the same machine." | 同上 |
| 接続の起動: `solidcraft --control 7878 &` のあと `solidcraft-cli mcp --connect 127.0.0.1:7878`。アプリの設定は "Preferences › AI › Agents through MCP" | 同上 |

つまり MCP の「アプリ」は、**制御の口（ポートとトークンのファイル）を開くデスクトップ版**。ブラウザーのタブはファイルも待ち受けのポートも作れない。`mcp.html` に "browser" が出る箇所は、すべて `browser.visibility` などのコマンド名か画面の「Browser（部品の木）」の意味で、ブラウザー版のことではない（本文を全文で調べた）。

### 6.2 ブラウザー版で読み込む・書き出す操作（公式の文書にある範囲）

| 操作 | 文書の記述 | 出典 |
|---|---|---|
| 開く | File → Open（Chrome・Edge・Opera はブラウザーの開くダイアログ）。URL から: `?open=<エンコードした HTTPS の URL>` は "a hosted `.sc` design" を未保存の写しとして開く。ホストは CORS を許す必要がある | guide/files.md「Saving in the web app」、getting-started.md「Design links and embeds」 |
| 形式の見分け | 開くときは中身で形式を見分ける。`.json`（自己完結の平文 JSON）と `.sc` のどちらも読み書きする | files.md |
| 保存 | Chromium 系: Save As が実ファイルを選んだフォルダーに書く（`.sc`）。**Save As JSON は File メニューにデスクトップにもウェブにもある**。Firefox・Safari: ブラウザー内の保管のみ。どのブラウザーでも File → Download design で書き出せる | files.md |
| コマンド列（スクリプト）を読み込む | **画面の操作としては書かれていない**（`ui-tour.md` に該当なし）。`solidcraft.execute(command, params)` を JavaScript のコンソールから呼ぶ道だけ | browser-api.md |
| 設計をコマンド列にする | `timeline.export_script`（"In the app and over MCP"）。画面のどの項目かは【未確認】。CLI の `solidcraft-cli script design --out repro.json` も同じものを出す。ただし**外観・フォルダー・名前つき視点・構成が落ち、部品（component）や関節のある設計は未対応** | getting-started.md |

17:50 に CLI で確かめたこと（ブラウザーでは未実行）: `plate_mount.json`（22 行のスクリプト）を `run --save pm.sc` → `file.save_as {format: "json"}` で設計 JSON（505 行、`"format": "solidcraft/58"`）→ `solidcraft-cli script pm.design.json --out repro.json`（12 ステップ、533 行）→ `eval` の体積 31111.170273681717 mm³・質量 38.57785113936533 g が元と一致。同じ `.sc` から設計 JSON を 2 回保存するとバイトで同一。`.sc` から作ったスクリプトと設計 JSON から作ったスクリプトは、設計名の 1 行（`"design": "pm"` と `"pm.design"`）だけが違う。

### 6.3 `cad/` に置く「正」の形式の推薦

| | 手書きのスクリプト `.json`（今の `plate_mount.json`） | 設計 `.json`（Save As JSON） | `.sc` |
|---|---|---|---|
| 行数・差分 | 22 行。読める | 505 行。パラメーターが先頭に名前つきで並び、読めるが長い | zip。読めない（11.8 KB） |
| ブラウザー版で開く | 画面の操作は無い（JS だけ） | File → Open。`?open=` は `.sc` と書いてある。`.json` が通るかは【未確認】 | File → Open、`?open=` |
| CLI | `run` | `run --in`、`script`、`eval`（確かめた） | 同じ |
| MCP | `execute`/`batch` で流せる | `open`/`save`（`.json` の名前で保存すれば JSON のまま、files.md） | 同じ |
| GUI で直した結果が戻るか | **戻らない**（設計 → スクリプトは外観・構成などが落ち、部品や関節は未対応） | 戻る | 戻る |
| 決定性 | 決定的（手書き） | 同じ入力から 2 回保存してバイト同一 | 【未確認】 |

**推薦（推測を含む）: 正本は設計 JSON**（`cad/<名前>.design.json`）。理由は 1 つに絞れる: **人がブラウザーで直した結果を、失わずにリポジトリに戻せる形式が、これだけ**だから（上の行「GUI で直した結果が戻るか」。出どころは getting-started.md の「落ちるもの」の記述）。手書きのスクリプト（今の `plate_mount.json`）は、**ゼロから作る種**として残す（`cad/README.md` の「設計の正本」という記述は、S042 が書いたもの。統括が採否を決める。直す場合の文面は S083 の作業記録に出る）。`.sc` はコミットしない（今の方針どおり）。版は `"format": "solidcraft/58"` に出るので、CI でその版が期待と違えば警告にできる【推測】。

### 6.4 発注者がブラウザー版で最初にやる 5 手順（公式の文書の操作だけ。【未実行】）

1. **Chrome か Edge で https://docs.solidcraft.io/app/ を開く。** Chromium 系なら Save がフォルダーの実ファイルに書く。Firefox・Safari は保管がブラウザー内だけ（files.md）。
2. **開始画面の "Sample Plate" をクリックして、画面の読み方を見る**（`?sample` でも開く。getting-started.md）。
3. **新しい設計で板を 1 枚作る**: New Sketch → Top（XY）の平面 → Rectangle で 1 点目を原点に置いて辺を打つ（例 `120`、Tab、`90`）→ Finish Sketch → Extrude（sketching.md「Step by step」）。寸法の欄には `plate_w = 120` のように名前を付けて入れると、後から数字を変えても作り直される（design-approach.md）。
4. **Inspect → Measure → Properties を開き、質量・重心・慣性を読む。** 材料を指定しないと既定の材料の密度が使われる（assembly-properties.md）ので、先に材料を決める。材料を指定する画面の操作は文書の該当の頁を読んでいない【未確認】。
5. **File → Save As JSON で `.json` に保存する**（Chromium なら保存先に WSL のフォルダーを選べるかは【未確認】。選べなければ File → Download design で落としてから置く）。置いた設計に対して `solidcraft-cli run cad/plate_mass.json --in <その設計.json> --results --json-out mass.json` を走らせ、CLI の質量が手順 4 の画面の数字と一致するかを見る。

この 5 手順で、ブラウザー版 → ファイル → CLI の最初の往復が確かめられる。MCP は、そのあと R1 の「Claude が窓なしで同じファイルを開く」で足す。

## 7. 明日の最初の 1 時間（案）

1. 最初の 10 分: 公開後の CI（`test`・`firmware`・`firmware-mg24`）の結果を見て、赤なら直す。MG24 の結果が、次点を選ぶ材料になる。
2. 次の 10 分: 部品の在庫と価格を取り直し（秋月・スイッチサイエンス）、発注者に BOM (A)/(B) の判断を仰ぐ。nRF52840 が無ければ MG24 の CI 結果を添える。
3. 次の 15 分: 発注者のブラウザー版の 5 手順（6.4）。設計 JSON が 1 本できれば、S083 の `solidcraft_props` で CLI と画面の質量を突き合わせる。
4. 次の 15 分: S081 の `hwcheck` と S082 のつまずき集の取り込み。S078（sim-checks）・S079（fake-vs-sketch）を起動。
5. 最後の 10 分: 実機が届く前の持ち物の確認（テスター・ノギス・秤・結束バンド。bringup の段 0・4・5 が要る）と、`doc/bringup.md` の【未確認】を消す順の最終確認。

## 確かめていないこと（第 2 巡）

- ブラウザー版そのものの操作（開いていない）。`?open=` に `.json` の設計や GitHub の raw URL が通るか。Chromium の Save As で WSL のフォルダーを選べるか。材料を指定する画面。`timeline.export_script` の画面上の項目。
- `solidcraft-cli mcp` の実際のツール一覧（公式の頁の記述のみ。自分では MCP を起動していない）。
- Claude Code の許可リストでの MCP ツールの書式（`mcp__solidcraft__<tool>`）。
- `script` の出力の「落ちるもの」が、`plate_mount` の設計でどう出たか（12 ステップ、体積と質量は一致したが、落ちた項目の一覧は見ていない）。
- 所要時間は推測。
