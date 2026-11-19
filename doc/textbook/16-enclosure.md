# 16. 筐体を設計して、sim に戻す

## この章でわかること

- 筐体（部品を載せる板）を設計するときに、何を決めればよいか。
- 部品の寸法と質量から、sim の値（質量・重心・ヨーの慣性・IMU の位置）を計算する方法。
- IMU を旋回中心からずらすと、加速度に何が乗るか。
- 作った後に測って、表と sim を直す流れ（Real2Sim）。

## 1. 要件

要件の全文は [cad/README.md](../../cad/README.md)。大事なのは 2 つ。

1. **IMU は旋回中心（左右の車軸の中点）の真上に置く。** 理由は 4 節。
2. **電池（一番重い部品）はなるべく中心に置く。** 理由は 5 節。

## 2. 寸法の表を読む

寸法は [cad/dimensions.csv](../../cad/dimensions.csv) の 1 か所にまとめる。
1 行が 1 つの値で、`source` 欄が出どころを表す。

| source | 意味 |
| --- | --- |
| `datasheet` | メーカーの資料（URL と取得時刻つき） |
| `measured` | 自分でノギスや秤で測った値 |
| `cad` | CAD が計算した値 |
| `assumed` | 置いただけの値。測っていない |

今の表には、調査（[doc/research/2026-11-19-dimensions.md](../research/2026-11-19-dimensions.md)、JST 2026-11-19 17:36〜17:47）で読んだ部品の値を写した。メーカーの文書の値（XIAO の外形 20.955 × 17.78 mm と IMU の位置、AE-DRV8835-S の外形 10 × 15 mm、電池ボックス 68 × 65 × 19 mm、ブレッドボード 84 × 54.3 × 9.4 mm、単3 アルカリ 23 g）は `datasheet`。販売店の値（XIAO の質量 4 g、ブレッドボードの質量 36 g）は `assumed`（参考値）。**どれも実物では測っていない。** 質量が見つからなかった AE-DRV8835-S と電池ボックスは【未確認】のまま。

**車体は Cytron の Robo Base ミニキット 2WD（スイッチサイエンス 10530）に決まった**（発注者の決定、JST 18:20 頃。元の Robo Base 2WD は売り切れ）。ミニの板の外形・取付穴・トレッド・車輪径・質量は数字がどこにも見つからず、表の行は全部【未確認】。構成（TT モーター 2、車輪 2、板 2 枚、キャスター 1、スタンド）も検索の要約で、商品ページを直接読んだものではない。穴の位置を間違えると部品を壊すので、届いて測るまで穴は開けない。**届いたら最初にトレッドと車輪の径を測り、表と sim を直す。** ミニは 2WD よりトレッドが狭い可能性があり、80 mm 以下だとその場旋回がジャイロの範囲（±1000 dps = 17.5 rad/s）を超えるおそれがある（調査の見積もり。そのときは duty の上限の見直しが要る）。元の 2WD の行は、コードと試験が名前を使うので消さずに残し、「売り切れ。使わない」と注記した。

寸法の食い違いは**一本化した**（S041）。以前は numpy の `sim.Params` が 16 mm・80 mm、MuJoCo の `diffdrive.xml` が 30 mm・100 mm だったが、今は両方とも **車輪半径 30 mm・トレッド 100 mm**。表の「sim の今の値 (MJCF)」の行が正で、`Params` の既定値・MJCF・表の値が一致することを試験が固定している。ただしこの 30 mm と 100 mm は**実物を測った値ではない**（`assumed`）。ミニを測ってから、表を正として両方を直す。表の「sim の今の値 (numpy Params)」の行は、値を 30・100 に直したが、コードは読まない（読むのは MJCF の行）。

## 3. SolidCraft での流れ

SolidCraft はオープンソースのパラメトリック CAD（https://solidcraft.io 、GitHub は https://github.com/tangency-labs/solidcraft 。最新の正式版は v0.44.1、2026-11-17 公開、JST 2026-11-19 14:10 に GitHub の API で確認。調査は [doc/research/2026-11-19-solidcraft.md](../research/2026-11-19-solidcraft.md)）。
**どこまで確かめたか（JST 2026-11-19 18:20 時点）**:

- **CLI は動いた。** v0.44.1 の Linux 版（WSL2・GPU なし）で、17:36 に S042 が、18:0x に監査 5 巡目（S055）が、この章のコマンドを走らせ直して出力が合った。`~/.local/bin/solidcraft-cli` で呼べる。落とした物・コマンド・出力は [調査](../research/2026-11-19-solidcraft.md) の「実際に動かした結果」。
- **GUI・ブラウザー版は【未実行】。** 発注者が確かめる点は [cad/README.md](../../cad/README.md) の「どれを正にするか」。
- **MCP は登録済み**（統括が 17:58 に実施。local スコープ、`--allow-path` 付き、`claude mcp list` で Connected）。**ツールごとの許可は未設定。次に Claude Code を起動したセッションからツールが出るかは【未確認】。** 許可された folder は main の `cad/` で、worktree の `cad/` は拒否される見込み（推論）。この進め方は未解決で、[doc/cad-mcp.md](../cad-mcp.md) の「未解決の点」に案を書いた。
- 手引きは [doc/cad-mcp.md](../cad-mcp.md)。**正本は設計 JSON（`cad/plate_mount.design.json`）、コマンド列の `cad/plate_mount.json` はレシピ**。ブラウザー版は MCP につながらず、ファイル（設計 JSON）で受け渡す。

1. ブラウザー版（https://solidcraft.io/app ）を開くか、Windows 側にインストールする【未実行】。Windows のインストーラーは SignPath で署名されているが、本番の証明書が入るまでは SmartScreen の警告が出ることがある、と公式の README が書く。版が毎日のように上がるので、使った版を記録しておく。
2. XY 平面にスケッチを作り、長方形を描いて、押し出す。スクリプトにすると [cad/plate.json](../../cad/plate.json) の形になる（120 × 90 × 3 mm の板。大きさは今の MJCF の車体に合わせた `assumed` の値で、ミニの板の寸法ではない）。
   ```bash
   solidcraft-cli run cad/plate.json --out plate.step   # 動いた。STEP は 9,413 バイト、体積 32400 mm3
   ```
3. 穴は、同じスケッチに円（`sketch.circle.center`）を描いて押し出すと、内側の輪が穴になる。寸法は**パラメーター**（`parameters.add`）にして、式で参照する。実際に通した例が [cad/plate_mount.json](../../cad/plate_mount.json)。XIAO の外形（20.955 × 17.78 mm）を窓にし、未確認の取付穴と板の外形（`TBD_robo_hole_*`・`TBD_plate_w`・`TBD_plate_d`）は仮の値で `TBD_` から始まる名前にした。取付穴の 100 × 60 mm は 2WD を想定した値で、ミニの穴ではない。ミニが届いて測ったら、その数字だけを直して作り直す。

   **この板は「SolidCraft の流れを通す試し」であって、そのまま作る設計ではない。** 要件は XIAO を**ブレッドボードに挿す**だが、今の窓は貫通で XIAO を支えない（目印にすぎない）。XIAO をどう固定するかは決めていない。ミニは板が 2 枚付くので、上の板に部品を直接載せられるなら、この取り付け板そのものが要らないかもしれない。**板が要るかは、ミニの実物を見てから決める。**
   ```bash
   solidcraft-cli run cad/plate_mount.json --save plate_mount.sc --out plate_mount.step
   ```
   `TBD_robo_hole_dx` を 100 → 94、`TBD_robo_hole_d` を 3.2 → 4 に変えて再計算すると、穴の中心が x = ±50 → ±47 になり、体積が手計算どおりに変わった（31114.95 → 31060.66 mm3）。詳しくは [cad/README.md](../../cad/README.md)。
4. STL で書き出して 3D プリントする（`file.export_stl`）【未実行】。書き出したファイルはリポジトリに入れない。
5. 質量特性: `assembly.mass_properties` で質量・重心・慣性テンソルが読めた（上の板を PLA として 38.5825 g、重心 (0, 0, 1.5) mm、Izz 7.4827e-5 kg m2）。URDF の書き出し（`file.export_urdf`）でも同じ `<inertial>` が書けた。読んだ値を SI に直すのが `physlearn.solidcraft_props` で、見本は `tests/data/solidcraft/` にある（実際の出力。XIAO の外形を 21 × 17.8 から直す**前**の板なので、Izz は 7.4826e-5）。`cad.py` の直方体の近似（同じ質量の 120 × 90 × 3 mm）は Izz を 7.2342e-5 と出し、CAD より 3.3 % 低い。窓と穴で材料が外側に寄るため。
   ```bash
   uv run python -m physlearn.solidcraft_props tests/data/solidcraft/plate_mount.mass.json
   ```
   ```
   質量 0.0385779 kg（38.5779 g）
   重心 [m] -5.2454e-17 -4.4568e-18 +1.5000e-03
   慣性 [kg m^2] +2.6999e-05 -1.1548e-21 +9.3826e-22
   慣性 [kg m^2] -1.1548e-21 +4.7886e-05 -3.6087e-23
   慣性 [kg m^2] +9.3826e-22 -3.6087e-23 +7.4826e-05
   Izz 7.4826e-05 kg m^2、回転半径 44.04 mm
   ```
   単位の注意: 公式の文書は慣性を `inertia_g_mm2`（g·mm²）と書くが、実際の `assembly.mass_properties` の出力のキーは `inertia_world_kg_mm2`（kg·mm²）。3 桁違うので、`solidcraft_props` はキーの名前で単位を決める。`cad.py` の `mass_props` に Izz を直接持つ部品として渡す口は、まだ無い（今は比べるだけ）。

## 4. CAD → sim の受け渡し

`src/physlearn/cad.py` は、部品を直方体・球・円柱で近似し、足し合わせる。

- 質量 m = Σ mᵢ
- 重心 c = Σ mᵢ rᵢ / m
- ヨーの慣性 Izz = Σ（部品自身の Izz + mᵢ × 重心からの水平距離²）（平行軸の定理）

そして `diffdrive.xml` の IMU の位置を変えたり、電池の箱を足したりした MJCF を作り、MuJoCo で走らせる。

```bash
uv run python -m physlearn.cad
```

実際に走らせた出力（JST 2026-11-19 13:59）:

```
既定の車体: 質量 0.290 kg、重心 x +0.000 m、Izz 5.831e-04 kg m^2
電池 0.1 kg を x=+0.00 m: Izz 6.431e-04、MuJoCo の τ(63%) 0.078 s
電池 0.1 kg を x=+0.04 m: Izz 7.621e-04、MuJoCo の τ(63%) 0.090 s
電池なし: MuJoCo の τ(63%) 0.072 s
IMU を x=+0.00 m: ω 10.77 rad/s、ax +0.000 m/s^2、-ω²d -0.000
IMU を x=+0.04 m: ω 10.77 rad/s、ax -4.643 m/s^2、-ω²d -4.643
```

どの値がどこに入るか:

| 計算した値 | numpy の `sim.Params` | MuJoCo の MJCF |
| --- | --- | --- |
| 車輪半径 | `wheel_radius` | 車輪の `geom size` |
| トレッド | `track` | 車輪の `body pos` の y × 2 |
| 質量・重心・Izz | 直接の欄は無い。`motor_tau` に効く | 各 `geom` の `mass` と位置（MuJoCo が慣性を計算） |
| IMU の位置 | 無い（numpy の sim は IMU を中心に置いたものとして扱う） | `site name="imu"` の `pos` |

τ(63%) は、その場旋回（duty 0.6）でヨー角速度が定常値の 63 % に届くまでの時間。
MuJoCo のモーターは逆起電力でトルクが落ちる形なので、τ は慣性に比例して伸びる。
電池 0.1 kg を中心から 4 cm ずらすと、τ は 0.078 → 0.090 s（約 +15 %）。
質量と慣性から τ を式で出す方法は 13 章（`motor.py`）が扱う。

## 5. IMU を中心からずらすと何が起きるか

一定の角速度 ω で回る車体の上で、中心から前へ d の点は、中心へ向かう加速度 ω²d を受ける。
機体座標の x は前向きなので、加速度センサーの ax には −ω²d が出る。

上の出力では、ω = 10.77 rad/s・d = 0.04 m で ax = −4.643 m/s²、式の −ω²d も −4.643 m/s²。
ω = 3 rad/s なら −0.36 m/s² で、sim の加速度の雑音（`accel_noise` = 0.05 m/s²）よりずっと大きい。
回り始め（角加速度 α がある間）は、横の ay にも α·d が乗る。
ジャイロ（角速度）は置き場所に依らない。困るのは加速度だけ。

この加速度を「車体が前に進もうとしている」と読み違えると、推定が狂う。
だから IMU は中心の真上に置く。置けないなら d を測って、−ω²d を差し引く。

## 6. 作った後に測って直す（Real2Sim）

1. 部品と筐体を秤で量り、ノギスで測って `dimensions.csv` の `measured` 欄を埋める。
2. 車輪半径とトレッドを測る（**ミニが届いたら最初にやる**）。表の「Cytron Robo Base Mini 2WD」の行の `measured` に入れ、`sim.Params` と `diffdrive.xml` の 30 mm・100 mm を直す。トレッドが 80 mm 以下なら、その場旋回の角速度がジャイロの範囲を超えないか（duty の上限）も見直す。なお `cad.dimension()` がミニの行を読むには、コードの `WHEEL_PARTS` にミニの名前を足す必要がある。
3. IMU の中心からのずれ d を測る。MJCF の `imu` の `pos` に入れる。
4. 同定（05 章）の τ と、表から計算した慣性で出る τ を比べる。大きく違えば、モーターの値か慣性のどちらかが違う。

## 演習

1. 電池を中心から後ろへ 4 cm（x = −0.04 m）ずらすと Izz と τ はどうなるか。`main()` の値を変えて確かめよ。前にずらした時と比べよ。
2. IMU を左へ 2 cm（y = 0.02）ずらしてその場旋回させると、ax と ay のどちらに何が出るか。式で予想してから sim で確かめよ。
3. 電池をトレッドの外側（車輪より外）に置くと何が困るか。慣性と、車輪にかかる重さの両方から考えよ。
