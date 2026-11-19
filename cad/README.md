# cad/ 筐体の設計

Cytron Robo Base 2WD の上に載せる取り付け板（またはケース）の設計の置き場。
道具は SolidCraft。CLI は動かして確かめた（下の「走らせ方」）。本家 https://github.com/tangency-labs/solidcraft 、最新の正式版 v0.44.1、2026-11-17 公開、JST 2026-11-19 14:10 に GitHub の API で確認。旧名 `bherbruck/solidcraft` は同じリポジトリ。調査: [doc/research/2026-11-19-solidcraft.md](../doc/research/2026-11-19-solidcraft.md)。
ただし下の要件と寸法表は道具に依らない。

## ファイル

| ファイル | 中身 |
| --- | --- |
| `dimensions.csv` | 部品の外形・質量の表。**寸法の唯一の置き場**。各値に出どころ（`datasheet` / `measured` / `cad` / `assumed`）と URL・取得時刻。届いたら `measured` 欄に測った値を書く |
| `plate.json` | 板だけ（120 × 90 × 3 mm、穴なし）。SolidCraft v0.44.1 の CLI で STEP が書き出せることを確かめた最小の例 |
| `plate_mount.json` | 取り付け板。パラメーター付き。XIAO の窓（datasheet の外形 + 逃げ）と、Robo Base 取付穴の**仮の値**の 4 穴。材料 PLA（密度は SolidCraft の表の値） |
| `plate_mount.design.json` | `plate_mount.json` から `solidcraft-cli run … --save` で作った**設計 JSON**（10.7 KB、505 行、`"format": "solidcraft/58"`）。ブラウザー版・GUI・MCP の `open` が開ける形。**正本（下の「どれを正にするか」）** |
| `plate_mass.json` | 質量特性を読む 1 コマンド（`assembly.mass_properties`）。`--in` で設計に重ねて使う |
| `expected.csv` | ファイルごとの体積・質量・Izz の期待値（手計算）。CI（`.github/workflows/cad.yml`）が `check.sh` で比べる |
| `check.sh` `check_expected.py` | `cad/expected.csv` の各スクリプトを STEP にして数字を比べる。手元は `cad/check.sh`（`solidcraft-cli` が PATH にあること） |
| `README.md` | この文書（要件と走らせ方） |

コミットするもの: 寸法表、設計 JSON（`*.design.json`。正本）、コマンド列の `.json`（レシピ。人が読む・Claude が書く出発点）。
コミットしないもの: 書き出した STEP / STL / 3MF / URDF とそのメッシュ（`.json` から作り直せる。`plate_mount.step` は 29 KB と小さいが、方針は変えない）、`.sc`。
`.sc`（v0.44.1 が書いたものは zip で、`plate_mount` は 11.8 KB）はバイナリなので入れない。設計 JSON と同じ内容なので要らない。

## どれを正にするか（S051 の決定。ブラウザー版での確かめは発注者）

**正本は設計 JSON（`cad/<名前>.design.json`）、コマンド列の `cad/<名前>.json` はレシピ**にする。決め手は、実際に試して分かった 3 つ（v0.44.1、2026-11-19）。

1. **3 つの道具すべてが開けるのは設計 JSON だけ**。ブラウザー版・GUI は File > Open / Save As JSON、MCP の `open`/`save` は `.sc` と設計 JSON を扱う。CLI の `run`/`eval` も設計 JSON をそのまま開く（`--param-check strict` も通った）。コマンド列の JSON は CLI と `mcp --in` だけで、MCP の `open` は開けない（確かめた）。
2. **人がブラウザー版で直した結果を失わない**。設計 → コマンド列（`solidcraft-cli script`）に直すと外観（色）が落ちる。CLI 自身が `note: the script leaves out appearances` と出す。色を付けた設計 JSON を `script` で戻して `run --save` し直すと、`appearances` の 13 行が消えた。部品や関節も同じ型の落ちがあり得る【未確認】。
3. **再保存でバイトが変わらない**（`name` 欄はファイル名から決まるので、同じ名前で保存すること）。差分は大きめ（パラメーター 1 つで 12 行、コマンド列は 4 行）だが、`git diff` で読める。

弱点は、読みやすさと版への依存。設計 JSON の形式は版ごとに番号が変わる（`solidcraft/58`）。新しい版の形式を古い版で開くと警告が出る（公式の文書）。CI は版を固定している。
**運用**:
- 設計は、人がブラウザー版（または GUI）で直して Save As JSON し、`cad/<名前>.design.json` に上書きしてコミットする。
- コマンド列（レシピ）を直したら、`solidcraft-cli run cad/<名前>.json --save cad/<名前>.design.json` で作り直す。**人が色などを付けていたら、これは上書きで失われる**ので、先に設計 JSON の差分を見る。
- 設計 JSON から読めるレシピを作るには `solidcraft-cli script cad/<名前>.design.json --out cad/<名前>.json`（外観は落ちる）。
- `expected.csv` には**両方**の行を書く。同じ数字になることで、レシピと正本のずれを CI が見つける。
- 発注者が確かめる点（ブラウザー版でしか分からない。自分たちでは【未実行】）: (a) https://solidcraft.io/app で `cad/plate_mount.design.json` を File > Open で開けるか、(b) 少し直して Save As JSON したファイルが `solidcraft-cli run` で通るか、(c) `git diff` が読めるか。(a) か (b) が通らなければ、当面の取り決めは「レシピを正、設計 JSON は派生」に戻す。

## 走らせ方（v0.44.1 の Linux 版 CLI で確かめた。JST 2026-11-19 17:36〜17:43、WSL2・GPU なし）

CLI は GitHub Releases の `solidcraft-0.44.1-linux-x86_64.tar.gz`（SHA-256 `164097743f6ff11c1eeb90a4313964728955e297689052053e4e5d8d20a64229`、公式の `SHA256SUMS.txt` と API の digest に一致）を展開した `bin/solidcraft-cli`（約 203 MB の 1 本）。FUSE も GPU も要らない。以下の `solidcraft-cli` はそのパス。

```bash
solidcraft-cli run cad/plate.json --out plate.step                       # 板だけ。体積 32400 mm3
solidcraft-cli run cad/plate_mount.json --save plate_mount.sc --out plate_mount.step
solidcraft-cli eval cad/plate_mount.json                                 # 体積・質量・重心・bbox を JSON で
solidcraft-cli run cad/plate_mass.json --in plate_mount.sc --results --json-out mass.json   # 質量・重心・慣性
```

CLI は 0.1 秒で終わる。設定は書かない。STEP を読むと読み込みのキャッシュを `$XDG_DATA_HOME/solidcraft/imports/` に作る。
**効かなかったもの**: `snapshot` と `gpu` は、GPU の無いこの環境（`/dev/dri` の権限なし）で 90 秒以上返らず、画像は出なかった。`render` も同じ系統で、試していない。形は `eval` の数値と、STEP の中身で確かめる。

**運用**: `plate*.json` のパラメーターや形を変えたら、`cad/check.sh` を走らせて、`cad/expected.csv` の値も手計算で直す（落ちたら CI が食い違いを全部出す）。
スクリプトを足したら、`expected.csv` に 1 行足す（足さないと CI の対象にならない）。

### パラメーターを変える（パラメトリック設計）

`plate_mount.json` の先頭のパラメーターを変えて再計算できる。仮の値は名前が `TBD_` で始まる。Robo Base が届いて測ったら、`TBD_robo_hole_dx` `TBD_robo_hole_dy` `TBD_robo_hole_d` の 3 つの数字を直す。

```bash
echo '{"commands":[{"command":"parameters.change","params":{"changes":{"TBD_robo_hole_dx":"94","TBD_robo_hole_d":"4"}}}]}' > change.json
solidcraft-cli run change.json --in plate_mount.sc --out changed.step
```

確かめた結果: 穴の中心が x = ±50 → ±47、径 3.2 → 4.0 になり、体積は 31111.17 → 31056.88 mm3（手計算 31056.9）。

### 板の設計（`plate_mount.json`）の根拠

| 要素 | 値 | 出どころ |
| --- | --- | --- |
| XIAO の窓 | (21 + 2 × 0.3) × (17.8 + 2 × 0.3) mm、板の中心 | 外形は `datasheet`。逃げ 0.3 mm は設計者の仮定（`xiao_clearance`）。XIAO には取付穴が無いので、窓で位置を決める枠にした。基板の厚み・押さえる方法は【未確認】で、窓は貫通 |
| 4 つの穴 | 間隔 100 × 60 mm、径 3.2 mm | **仮の値（`TBD_`）**。Robo Base の取付穴は【未確認】。**届く前に実物の板に穴を開けない** |
| 板 | 120 × 90 × 3 mm | `assumed`（MJCF の車体に合わせた） |
| 材料 | PLA 1.24 g/cm3 | SolidCraft の材料表の値。板を何で作るかは決めていない |

AE-DRV8835-S・電池ボックス・ブレッドボードの置き場は、寸法が【未確認】なので、まだ描いていない。

### 測った値と `physlearn.cad` の比較

| | SolidCraft（`assembly.mass_properties`） | 手計算（板 − 窓 − 4 穴） | `cad.mass_props`（同じ質量の直方体 120 × 90 × 3） |
| --- | --- | --- | --- |
| 質量 | 38.578 g | 38.578 g | （入力） |
| 重心 | (0, 0, 1.5) mm | 同じ | 同じ |
| Izz | 7.4826e-5 kg m2 | 7.4824e-5 | 7.2333e-5（CAD の 0.967 倍） |

質量は体積と一致、Izz は手計算と 4 桁で一致（差 0.004 %、円のメッシュ化の差と思われる【未確認】）。
窓と穴の分だけ材料が外側に寄るので、直方体の近似は Izz を 3.4 % 低く見積もる。板が車体の慣性に占める割合は小さいが、**CAD → sim は、直方体の近似の代わりに CAD の出力を渡せる**。
`physlearn.cad.mass_props` は Izz を直接持つ部品を受けないので、今は比べるだけにした。CAD の出力ファイルを SI で読む口は `physlearn.solidcraft_props`（`python -m physlearn.solidcraft_props mass.json`）。URDF の書き出し（`file.export_urdf`）も動き、同じ板の `<inertial>` は mass 0.0385790、izz 7.48278e-5（STL のメッシュから積分した値で、上の厳密な値と 0.007 % 違う）。


## 要件

1. **固定するもの**: XIAO nRF52840 Sense（ブレッドボードに挿す）、AE-DRV8835-S、ブレッドボード、単3×4 の電池ボックス。走行中の振動で動かないこと。IMU の値が板の揺れを拾うので、XIAO の周りは固く留める。
2. **IMU の置き場所: 旋回中心（左右の車軸の中点）の真上**。
   - 中心から前へ d ずらすと、旋回中の加速度 x に向心加速度 −ω²d が乗る（下の計算と 16 章）。角加速度があれば y に接線成分 α·d も乗る。
   - ジャイロ（角速度）は置き場所に依らない。困るのは加速度だけ。
   - 向き: 基板の軸を機体の軸（x 前・y 左・z 上、`api.py`）に合わせる。合わないときは `physlearn link --axes` で対応を書く（例 `-y,x,z`）。基板上の IMU の位置と軸の向きは【未確認】。
3. **USB ケーブル**: 繋いだまま回すとケーブルがねじれる。その場旋回の実験では、ケーブルを上から吊るして逃がすか、回転の合計を 1〜2 回に抑える。USB-C の口の前に指が入る空き（10 mm 程度、目安）を残す。
4. **電池**: 一番重い部品。旋回中心に近いほどヨーの慣性が小さく、応答が速い（下の計算では 4 cm ずらすと τ が約 15 % 延びた）。交換できるよう蓋が開く向きに置く。
5. **配線の逃げ**: モーターの線（15 cm）が板を通る穴か切り欠き。ジャンパー線が車輪に触れない。
6. **作り方を選ばない形**: 平板 1 枚 + 穴 + 結束バンドの穴、を基本にする。3D プリント、レーザー加工（アクリル・MDF）、手加工（プラ板・段ボールにドリル）のどれでも作れる。

## 寸法について

`dimensions.csv` の部品の寸法・質量は、XIAO の外形（21 × 17.8 mm）以外すべて【未確認】。
**Robo Base の上板の取付穴の位置は確かめていない。届く前に穴を開けない。** 届いたらノギスと秤で測って `measured` 欄を埋める。

sim の車輪半径とトレッドは numpy（`sim.Params`: 16 mm・80 mm）と MuJoCo（`diffdrive.xml`: 30 mm・100 mm）で食い違っている。どちらも測った値ではない（`assumed`）。今回は直していない。

## CAD → sim

`python -m physlearn.cad` が、部品（直方体・球・円柱）の足し合わせと平行軸の定理で質量・重心・ヨーの慣性 Izz を出し、`diffdrive.xml` を書き換えて MuJoCo で走らせる。
SolidCraft の質量特性（`assembly.mass_properties`）と URDF の `<inertial>`（質量・重心・慣性テンソル）は、板で動くことを確かめた（上の「測った値と比較」）。その値は `mass_props` に 1 つの部品として渡したいが、Izz を直接持つ部品の形は今は無い。要るときに足す。
