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
  - `src/physlearn/solidcraft_props.py`（新規、約 50 行）: SolidCraft の質量特性の JSON から `(質量 [kg], 重心 [m], Izz [kg m²])` を返す。`inertia_g_mm2` を 1e9 で割って kg m² にする（公式の式）。`null`（メッシュが閉じていない）なら例外。試験は、**S042 が実際に出した JSON**（無ければ公式文書の形に合わせた手書き）と、**箱の公式 `m(a²+b²)/12`** との突き合わせ（板 1 枚なら 1 % 以内、【推測】）。`cad.py` に繋ぐのは S041 の後に統括が 1 か所。
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
| F6 | 質量特性: 材料の密度つきで、質量・重心・`inertia_g_mm2`（全体の重心まわり、世界座標、g·mm²。kg·m² にするには 10⁹ で割る）・主慣性モーメント。丸い物体は標準の品質で約 0.1 %。メッシュが閉じていなければ `null` | [gh]docs/assembly-properties.md |
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
