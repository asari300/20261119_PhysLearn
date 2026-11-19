# 寸法・質量・モーター定数の調査（S045、JST 2026-11-19 17:35〜18:00）

`cad/dimensions.csv` の未確認 14 件と、`13-motor-physics.md` の仮のモーター定数を、公開の図面・データシートで確かめた。
このファイルは調査結果だけで、`cad/dimensions.csv`・コード・章は直していない（後で別の担当が表に写す）。
取得時刻は JST。PDF と設計ファイルは `curl` で原文を取り、文字と図を読んだ（Seeed・秋月・Energizer・Panasonic）。
価格・在庫・付属品は扱わない（S043 の担当）。

## 結論

- **確かめられた（メーカーの図面・データシートの原文）**: XIAO の外形と IMU の位置・軸の向きとピン間隔、AE-DRV8835-S の外形とピン間隔、電池ボックス（SBH-341-1AS）の外形と線の長さ、EIC-801 の外形、単3 アルカリ E91 の質量・外形・電圧、ニッケル水素 BK-3MCC の質量・外形・電圧。
- **確かめられなかった**: **Robo Base 2WD そのもの（板の外形・穴・トレッド・車輪の直径・質量・モーター）**。Cytron のページは自動取得が 403（Cloudflare）で読めず、スイッチサイエンスと The Pi Hut は 429 で読めなかった。公式の図面・STEP も見つけていない。XIAO・DRV8835・電池ボックスの質量、XIAO の全高も公開の資料に無い。
- **車輪半径**: 実物の値は【未確認】。ただし TT モーター用の車輪は直径 65〜67 mm と売られており（検索抜粋、下）、半径は約 32〜33 mm と見込める。**MuJoCo の 30 mm が近く（差 2〜3 mm）、numpy の 16 mm は半分で遠い**。**トレッドは 80 / 100 mm のどちらとも言えない**（根拠が無い）。
- **質量と慣性（見積もり）**: 質量が分かる部品だけで 193 g。分からない部品に仮の値を入れた全体は 0.30〜0.34 kg で、sim（0.29 kg）の 1.05〜1.16 倍。ヨーの慣性は 3.4〜6.4e-4 kg m² で、sim（5.8e-4）の 0.58〜1.10 倍。差の大半は電池の位置とトレッドで決まる。
- **モーター**: Cytron のモーターの数値は取れなかった。同じ種類の TT モーター（1:48）の他社の公開値（Adafruit）から、K ≈ 26 rad/s/duty（6 V）、τ ≈ 30〜80 ms の見積もり。ただし別の販売元の値なので「参考値」。

## 1. 寸法表に写せる行（`cad/dimensions.csv` の形）

列: part, item, value, unit, source, url, fetched_jst, 原文の該当箇所。`source` は提案。
`datasheet` はメーカーの文書、`assumed` のままにするものは「参考値」と書く。

| part | item | value | unit | source | url | fetched_jst | 原文の該当箇所 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| XIAO nRF52840 Sense | board_xy | 20.955 x 17.78 | mm | datasheet | https://files.seeedstudio.com/wiki/XIAO-BLE/Seeed-Studio-XIAO-nRF52840V1.1-KiCad-Project-260105.zip | 2026-11-19 17:39 | 基板ファイル `Seeed Studio XIAO nRF52840 v1.1.kicad_pcb` の Edge.Cuts（`gr_line`・`gr_arc`）の外接: x 138.0236〜158.9786、y 96.1136〜113.8936。Seeed の仕様欄は「21 x 17.8mm」（https://wiki.seeedstudio.com/XIAO_BLE/ 17:38、同じ値）。USB-C の突き出しを含むかは【未確認】 |
| XIAO nRF52840 Sense | thickness_pcb | 1.6 | mm | datasheet | 同上（KiCad） | 17:39 | `(stackup` の層の厚さの和: 銅 0.035 × 4、誘電体 0.48 × 3、マスク 0.01 × 2（≈ 1.6）。**部品・USB-C を含む全高は【未確認】**。Seeed の SOM 資料（https://files.seeedstudio.com/wiki/XIAO/Seeed-Studio-XIAO-Series-SOM-Datasheet.pdf）の「20×17.5×3.5mm」は SAMD21 と RP2040 の表で、nRF52840 の表には無い |
| XIAO nRF52840 Sense | pin_pitch | 2.54（2 列の間隔 15.24、各列 7 ピン） | mm | datasheet | 同上（KiCad） | 17:39 | フットプリント `XIAO-Add-On` のパッド座標: 列内の間隔 2.54、2 列は基板中心から y = ±7.62（端のパッドは ±8.89）。ピン 1 は USB-C 側 |
| XIAO nRF52840 Sense | imu_offset_on_board | 基板中心から USB 側へ +1.59、横へ +4.57（上面） | mm | datasheet | 同上（KiCad） | 17:39 | 部品 `U3`（`LGA14-0.5-2.5X3X0.86MM`、値 `LSM6DS3TR-C`）の `at 150.0886 100.4316 180`、層 F.Cu（USB-C と同じ上面）。基板中心 (148.5011, 105.0036)。座標は KiCad（y が下向き）から「USB-C 側を +x_b、画面の上を +y_b」に直した。基板の端からは、USB の反対の端から 12.07、IMU 側の長辺から 4.32 |
| XIAO nRF52840 Sense | imu_axes | 下の「IMU の軸」 | | datasheet | https://files.seeedstudio.com/wiki/XIAO-BLE/ST_LSM6DS3TR_Datasheet.pdf | 17:40 | データシート p.18（Figure 1. Pin connections）の図と、上の `U3` のパッド座標を重ねて読んだ。**実物での確認はまだ** |
| XIAO nRF52840 Sense | mass | 4 | g | assumed（参考値） | https://www.bastelgarage.ch/seeed-studio-xiao-nrf52840-sense-1-2516 | 17:46 | 販売店（Bastelgarage）の Technical Data「Weight: 4 g」。Seeed の公式ページ（https://www.seeedstudio.com/Seeed-XIAO-BLE-Sense-nRF52840-p-5253.html）には質量の記載が無い。他に Farnell が 0.004 kg（検索抜粋）、Cirkit Designer が 3 g（検索抜粋）。メーカーの値ではない |
| AE-DRV8835-S | board_xy | 10 x 15 | mm | datasheet | https://akizukidenshi.com/goodsaffix/AE-DRV8835-S_20210526.pdf | 2026-11-19 17:42 | マニュアル p.1「外形図（ピン穴 0.9mm）」の寸法線: 横 10、縦 15 |
| AE-DRV8835-S | pin_pitch | 2.54、2 列の間隔 7.62、列の長さ 12.7（6 ピン × 2 列） | mm | datasheet | 同上 | 17:42 | 外形図の寸法線 2.54、7.62、12.7。特徴欄「300mil 幅 2.54mm ピッチ 12 ピン（6x2）の DIP 基板」。穴径 0.9 |
| AE-DRV8835-S | mounting_holes | なし（外形図にピン穴 12 個だけ） | | datasheet | 同上 | 17:42 | 外形図に取付穴は描かれていない（図の読み。厳密には「描いていない」まで） |
| AE-DRV8835-S | mass | 【未確認】 | g | | https://akizukidenshi.com/catalog/g/g109848/ | 17:41 | 商品ページ・マニュアルに質量の記載なし。試した: 商品ページ、マニュアル p.1〜2 |
| 電池ボックス 単3×4 (秋月 100311) | box_xyz | 68 x 65 x 19（フタ側の外形 66） | mm | datasheet | https://akizukidenshi.com/goodsaffix/SBH%20341-1AS.PDF | 17:42 | 図面 S3411AS-1100（SBH-341-1AS）: BOTTOM 横 68±1、縦 65±1、側面 19±0.5、COVER 横 66±1。秋月のページは長辺 68、短辺 65、高さ 19（https://akizukidenshi.com/catalog/g/g100311/ 17:41）。電池 4 本は 68 の向きに並ぶ軸で、65 の方向に 4 列 |
| 電池ボックス 単3×4 (秋月 100311) | lead_length | 150 ± 5 | mm | datasheet | 同上 | 17:42 | 図面の仕様欄「WIRE: UL1007 AWG#26, BLACK & RED 150MM±5MM」 |
| 電池ボックス 単3×4 (秋月 100311) | mass | 【未確認】 | g | | 同上 | 17:44 | 図面・秋月ページに質量なし。販売店の記載も見つからず（検索 1 回）。仮の値を置くなら 30 g 前後だが根拠は無い |
| 単3 アルカリ電池 | mass_each | 23.0（Energizer E91、典型値） | g | datasheet | https://cdn.connectec.uk/Files/Products/Batteries/energizer_batteries/e91_aa_battery_datasheet.pdf | 17:43 | 「Typical Weight: 23.0 grams (0.8 oz.)」。この版は Energizer の様式 EBC-1102-R の転載。Energizer の公式 URL は 404 だった |
| 単3 アルカリ電池 | size | 直径 13.50〜14.50、長さ 49.50〜50.50 | mm | datasheet | 同上 | 17:43 | 図面の寸法欄「14.50 (0.571) / 13.50 (0.531)」「50.50 (1.988) / 49.50 (1.949)」。「Physical values are for reference purposes」の注意書きあり |
| 単3 ニッケル水素電池 | mass_each | 約 27（eneloop BK-3MCC） | g | datasheet | https://www.peak-system.com/produktcd/Tools/PCAN-Diag%20FD/Documentation/Addendum%20Batteries/Panasonic_Cell%20Type%20BK-3MCC.pdf | 17:43 | 「Approx.27g」（チューブ付き）。Panasonic の資料の転載（PEAK-System が配布） |
| 単3 ニッケル水素電池 | size | 14.35 x 50.4 | mm | datasheet | 同上 | 17:43 | 「14.35(D) x 50.4(H) mm」（チューブ付き）。他社の転載では 14.5 / 50.5 とする（検索抜粋）ので、1 本 0.1〜0.15 mm の幅がある |
| ブレッドボード EIC-801 | board_xyz | 84 x 54.3 x 9.4 | mm | datasheet | https://akizukidenshi.com/goodsaffix/0165-40-4-8010(EIC-801).PDF | 17:43 | 図面 0165-40-4-8010: 横 84.00、縦 54.30、高さ 9.40。**同じ図面の文字は「Board:84*54.3*8.5(mm)」で、高さが 9.4 と 8.5 で食い違う**。販売店（Tinytronics）は 9.5。取付穴 2 個 M2.3 × L5.5（裏のねじ穴）の間隔 71.60 |
| ブレッドボード EIC-801 | mass | 36 | g | assumed（参考値） | https://www.tinytronics.nl/en/tools-and-mounting/prototyping-supplies/breadboards/eic-premium-breadboard-400-points | 17:47 | 販売店の記載「Weight [g] 36」。メーカーの値ではない |

### 電池の電圧（13 章の仮の値と比べる）

| 項目 | 値 | 出典・原文 |
| --- | --- | --- |
| アルカリ 公称 | 1.5 V | E91 データシート「Nominal Voltage: 1.5 volts」「Designation: ANSI-15A, IEC-LR6」 |
| アルカリ 新品の開放電圧 | 1.6 V | Energizer の Alkaline Handbook（https://data.energizer.com:443/pdfs/alkaline_appman.pdf 17:45）の例の式に「Open circuit voltage = 1.6 Volts」。**例の数字であって、仕様値ではない** |
| アルカリ 使う範囲 | 1.6 V → 0.9 V | 同 Handbook「Most devices are designed to operate within a voltage range (for example from 1.6 volts to 0.9 volts per cell)」 |
| アルカリ 終止 | 0.8 V | 同 Handbook「a minimum voltage cutoff of 0.8 volts per cell」（その時点で使える容量の約 95 % を使い切る）。E91 の放電曲線も 0.8 V まで |
| 内部抵抗（新品） | 150〜300 mΩ | E91「Nominal IR: 150 to 300 milliohms (fresh)」。4 本で 0.6〜1.2 Ω。モーター 1.5 A なら 1〜2 V 落ちる計算で、13 章の電圧の表にこの落ちは入っていない |
| ニッケル水素 公称 | 1.2 V | BK-3MCC「1.2V」。内部抵抗は約 25 mΩ（1 kHz、「Approx. 25mΩ(at 1000Hz)」） |

13 章の表（アルカリ 新品 1.6、公称 1.5、ニッケル水素 1.2、消耗 1.1）との差: 1.6 は例の数字で裏づく、1.5・1.2 は一致。「消耗 1.1」は出典に無い（使う範囲の下端は 0.9、終止 0.8）。**表に無い効果: 内部抵抗による電圧降下（アルカリ 4 本で 1〜2 V）**。

### Robo Base 2WD（確かめられなかった行）

| part | item | value | source | 試したこと・手がかり |
| --- | --- | --- | --- | --- |
| Cytron Robo Base 2WD | plate_xy | 【未確認】 | | Cytron（www / my / sg.cytron.io の商品・チュートリアル 5 ページ）は curl・WebFetch とも 403。スイッチサイエンス 10708 は 429（3 回、間隔を空けても同じ）、The Pi Hut も 429。第三者の商品ページ（eitkw.com、makerph.com）には寸法なし。GitHub・Printables に図面・STEP なし。分かったのは「板は厚さ 1.6 mm の基板材（The Pi Hut の説明、検索抜粋）、取付穴は M3、スペーサーは 10・15・20・25・30 mm」まで |
| Cytron Robo Base 2WD | wheel_radius | 【未確認】。参考値 32.5〜33.5 | assumed（参考値） | 下の「車輪半径」 |
| Cytron Robo Base 2WD | track | 【未確認】 | | 手がかりなし。下の「トレッド」 |
| Cytron Robo Base 2WD | axle_to_caster_x | 【未確認】 | | キャスターは W420 ボールキャスター（eitkw.com の同梱品リスト）。取り付けは 25 mm のスペーサー（Cytron のチュートリアルの記述、検索抜粋）。位置の寸法は取れず |
| Cytron Robo Base 2WD | mass | 【未確認】 | | 同梱品: TT モーター 2、車輪 2、ブラケット 2、W420 キャスター 1（スイッチサイエンス、検索抜粋）。質量の記載なし。Cytron の TT モーター＋車輪セットは「net weight 65 g」という検索抜粋があるが、本文を読めていない |

### 車輪半径とトレッド

**車輪半径** — 付属の「プラスティックホイール」の直径はどの資料にも無かった。近い品の値（**すべて検索の要約の抜粋。Cytron のページ本文は 403 で読めていない**）:

| 品 | 直径 | 出典（検索結果の URL、2026-11-19 17:36〜17:40） |
| --- | --- | --- |
| Cytron TT Motor Wheel Kit の黒い車輪 | 66 mm（厚さ 25 mm） | https://www.cytron.io/p-tt-motor-plus-wheel-kit |
| Cytron TT 用ゴム車輪 | 65 mm × 15 mm（商品名は 63 mm）、36 g | https://www.cytron.io/p-rubber-wheel-for-tt-motor-63mmx15mm |
| Cytron 2WD Smart Robot Car Chassis | 67 mm | https://www.cytron.io/p-2wd-smart-robot-car-chassis |
| Elmwood / myduino の TT モーター＋車輪 | 66 mm（厚さ 25 mm） | https://elmwoodelectronics.ca/products/tt-motor-wheel-kit |
| BC Robotics の 65 mm 車輪 | 65 mm（幅 26 mm） | https://bc-robotics.com/shop/plastic-wheel-tire/ |

直径 65〜67 mm なら半径 32.5〜33.5 mm。sim の 30 mm との差は 2.5〜3.5 mm（約 10 %）、16 mm との差は 16.5〜17.5 mm（約 2 倍）。**30 mm の方が近い**。ただし Robo Base 付属の車輪が TT 用の標準品かは確かめていない。届いたら測る。

**トレッド** — 80 / 100 mm のどちらにも根拠が無い。弱い手がかりだけ（推測）: 車輪の幅が約 25 mm なら、接地中心の間隔 80 mm だと車輪の内側の隙間は 55 mm で、100 mm なら 75 mm。TT モーターは Adafruit 版で本体が 70 × 22 × 18 mm なので、2 個を車輪の間に置くなら 100 mm の方が収まりやすい。置き方は図が無く分からないので、決め手にはならない。

## 2. IMU の軸

データシート p.18 の図（Figure 1）は、パッケージを上から見た 3D 図で、ピン 1 の印（丸）が左の角にある。X の矢印は手前の右（印の角から 3 mm の辺に沿う）、Y は奥の右（2.5 mm の辺に沿う）、Z は上。右側の底面図は、ピン 1 が右上で、1〜4 が右の列。つまり、**上から見てピン 1 を左上に置くと、X はピン 1→4 の向き（下）、Y は右、Z は手前**。右手系で、X × Y = Z になる。

Seeed の基板では U3 は上面（USB-C と同じ面）で、パッドの座標から、上から見て（USB-C を右に置く）次のとおり:

- ピン 1〜4 は USB 側の列（+x_b = 2.787）で、ピン 1 は y_b = +3.82（基板の中心寄り）、ピン 4 は y_b = +5.32（長辺寄り）。ピン 5〜7 が長辺側、8〜11 が USB の反対の列、12〜14 が中心側。番号は上から見て反時計回りで、データシートの底面図と合う。
- よって **X_imu = +y_b（USB-C を前としたとき、機体の左）、Y_imu = −x_b（機体の後ろ）、Z_imu = +z（上）**。

機体の軸（x 前・y 左・z 上、`api.py`）に直すと、**USB-C を前に向けて、部品面を上にして置いたとき: 機体 x = −Y_imu、機体 y = +X_imu、機体 z = +Z_imu**。`link --axes` の書き方に直すと、機体の軸ごとにセンサの軸を書く形で `-y,x,z`（`cad/README.md` の例と同じ形）。
**図の矢印の向きの読み取りと、Arduino のライブラリが軸を入れ替えていないかは、実機で確かめる**（下の一覧）。

## 3. モーター定数

Robo Base 付属の TT モーターの数値は取れなかった（Cytron のページが読めない）。**参考値は Adafruit 製品 3777（TT モーター 1:48、https://www.adafruit.com/product/3777 、2026-11-19 17:44 取得）**。Cytron のモーターと同じ品かは確かめていない。

| 項目 | 参考値（Adafruit 3777） | 13 章・MuJoCo の仮の値 | 差 |
| --- | --- | --- | --- |
| 定格電圧 | 3〜6 V（「Rated Voltage: 3~6V」） | 6 V と置いた（電池 4 本の公称） | 新品アルカリ 4 本の 6.4 V は定格の上限を 0.4 V 超える |
| 減速比 | 1:48（「Gear Ratio: 1:48」） | n = 1（車輪軸の値だけで書く） | 13 章は軸の換算。n = 48 でも K は同じで、τ は回転子の慣性（未確認）で変わる |
| 無負荷回転数 | 6 V で 200 ± 10 % rpm（最小の規格）、Adafruit の実測 約 250 rpm（6 V）、3 V で 約 120 rpm | 30 rad/s（286 rpm） | 実測 250 rpm = 26.2 rad/s は 13 %低い。規格の最小 200 rpm = 20.9 rad/s なら 30 % 低い |
| 無負荷電流 | 150 mA ± 10 % | （無し） | |
| 停動トルク | 6 V で 0.8 kg·cm = 0.0785 N m（3 V で 0.4 kg·cm） | 0.05 N m | 参考値が 1.6 倍 |
| 停動電流 | Adafruit の実測 1.5 A（6 V）、1.1 A（3 V） | （無し） | DRV8835 の 1 チャンネル 1.5 A と同じで、余裕が無い |
| 質量 | 30.6 g（本体 70 × 22 × 18 mm） | 車輪 20 g × 2 のみ | |

### `motor.py` の式から出る K・τ

6 V（アルカリ 4 本の公称）で `uv run python` で計算した（スクリプトはリポジトリに入れていない。使った関数: `motor.Motor`、`motor.first_order`、`motor.yaw_inertia_on_wheel`、`motor.mujoco_model`）。

- **(a) 停動トルクと無負荷回転数の直線から**（`mujoco_model()` と同じ流儀で n = 1、Kt = Ke、b = 0）: 傾き 0.0785 / 26.18 = 0.00300 N m s/rad から Kt = 0.2292、R 相当 = 17.5 Ω。**K = 26.2 rad/s/duty**。電圧との比例は 4.4 V で 19.2、4.8 V で 20.9、6.4 V で 27.9。
- **(b) 電流から**（R = 6 V / 1.5 A = 4.0 Ω、n·Ke = (6 − 4.0 × 0.15) / 26.18 = 0.206、n = 48 と置く）: K = 29.1。ただし停動トルクが 0.309 N m と出て、**規格の 0.0785 N m の 3.9 倍**で合わない。減速機の効率が低い（トルクを食う）ためとみられる（推測）。(a) の方が規格に合う。
- **τ = J_eff / 傾き**。J_eff は 3 節の車体の見積もりから `yaw_inertia_on_wheel` で出した（車輪を中実円盤として 0.5·m·r²、r = 33 mm）。(a) の傾き 0.003 で、トレッド 80 mm のとき τ = 42〜79 ms、100 mm のとき 28〜53 ms。(b) の傾き 0.0106 なら 8〜22 ms。
- 比較: MuJoCo の仮の値は K = 30、τ = 67 ms（J_eff = 1.12e-4、`motor.mujoco_model()`）。参考値の (a) は **K が 13 % 低く、τ は同じ桁**。numpy の既定の motor_gain 30、motor_tau 0.08 とも大きくは外れない。
- 車体の旋回ゲイン 2·r·K / トレッド は 17〜22 rad/s/duty（r = 33 mm、K = 26.2、トレッド 100 / 80 mm）。12.0 節の「公称 `yaw_gain` 12」より大きい。ただし、r、トレッド、K のどれも実物では測っていないので、見直しの根拠にはしない。

## 4. 車体全体の質量とヨーの慣性の見積もり

`physlearn.cad.mass_props`（部品の足し合わせ、平行軸の定理。読んで使い方を確かめた）で計算した。

**質量が出典で分かる部品**: TT モーター 2 個 61.2 g（Adafruit の値）、単3 アルカリ 4 本 92.0 g（E91）、EIC-801 36 g（販売店）、XIAO 4 g（販売店）。合計 **193.2 g**。ニッケル水素（約 27 g × 4）なら電池が 108 g になり、合計 +16 g。
**質量が出典に無い部品（仮の値）**: 車輪 2 個（20 g または 36 g × 2。36 g は Cytron のゴム車輪の検索抜粋）、Robo Base の板（40 g と仮定）、電池ボックス（30 g と仮定）、DRV8835（2〜3 g）、配線・ねじ・キャスター。

位置も仮定: 車軸が x = 0、モーターは車輪の内側 30 mm（y = ±(トレッド/2 − 30 mm)）、板は sim の箱と同じ 120 × 90 mm、EIC-801 と XIAO は x = +30 mm、電池は x = 0 か x = −40 mm（後ろ）。r = 33 mm、車輪の幅 25 mm。

| 車輪の質量 | トレッド | 電池の位置 | 質量 | sim 比 | Izz | sim 比 |
| --- | --- | --- | --- | --- | --- | --- |
| 20 g | 80 mm | x = 0 | 0.303 kg | 1.05 | 3.37e-4 | 0.58 |
| 20 g | 80 mm | x = −40 mm | 0.303 | 1.05 | 4.92e-4 | 0.84 |
| 20 g | 100 mm | x = 0 | 0.303 | 1.05 | 3.91e-4 | 0.67 |
| 20 g | 100 mm | x = −40 mm | 0.303 | 1.05 | 5.47e-4 | 0.94 |
| 36 g | 80 mm | x = 0 | 0.335 | 1.16 | 3.99e-4 | 0.68 |
| 36 g | 80 mm | x = −40 mm | 0.335 | 1.16 | 5.58e-4 | 0.96 |
| 36 g | 100 mm | x = 0 | 0.335 | 1.16 | 4.82e-4 | 0.83 |
| 36 g | 100 mm | x = −40 mm | 0.335 | 1.16 | 6.41e-4 | 1.10 |

sim（MuJoCo、`cad.mass_props(DEFAULT_PARTS)`）: 質量 0.290 kg、Izz 5.83e-4 kg m²（箱 0.25 kg が 120 × 90 mm、車輪 0.02 kg × 2 が y = ±0.05）。

読み方:

- 質量は 0.30〜0.34 kg で sim の +5〜+16 %。**ほぼ合う**。ただし sim の箱 0.25 kg は「車体の全部」で、実物は電池・板・モーターに分かれる。
- Izz は sim の 0.58〜1.10 倍。**電池が車軸の真上（x = 0）だと小さく、後ろへ 40 mm ずらすと 3 割増える**（`cad/README.md` の「4 cm ずらすと τ が約 15 % 延びた」と同じ向き）。トレッドが広いほど大きい。
- 慣性は、板の外形・モーターの置き方・電池の位置という、**どれも測っていない値が支配している**。表の幅（0.58〜1.10）は、測るまでこれ以上は絞れない。
- 見積もりは、モーター側の回転子の慣性（減速比 48 の 2 乗 = 2304 倍で効く）を入れていない。回転子の慣性は公開の資料に無く、`J_eff` を過小に見積もっている可能性がある（推測）。

## 5. 届いたら測る一覧（公開の資料では分からなかったもの）

| 項目 | 測り方 |
| --- | --- |
| Robo Base の板の外形と取付穴の位置・径 | ノギスで外形、穴の中心から 2 辺までの距離、穴径。写真に定規を置いて残す |
| 車輪の直径・幅 | ノギスで直径を 3 方向。接地した状態の半径は、床から車軸の中心までの高さ（キャスターで水平にして定規） |
| トレッド | 左右の車輪の接地中心の間隔（床に墨をつけて走らせて跡の間隔、または車輪の幅の中心どうしをノギス） |
| 車軸からキャスターまでの距離 | 車軸の中心とキャスターの球の中心の水平距離 |
| 質量 | 台所秤（0.1 g）で、部品ごと（板+モーター+車輪、電池ボックス、ブレッドボード、XIAO、DRV8835）と全体。電池の有無で 2 回 |
| 電池ボックスの質量、DRV8835、XIAO の質量 | 同上 |
| XIAO の全高（USB-C 込み）、USB-C の突き出し | ノギス |
| IMU の軸の向き | `physlearn link --axes` で、前へ押す・左へ傾ける・水平に回す、の 3 回で符号と軸を決め、上の `-y,x,z` と比べる |
| 無負荷回転数 | 車輪を浮かせ、duty 1.0 で回し、車輪に印をつけて動画で数える（電池の電圧を同時にテスターで測る） |
| 停動トルク | 車輪の縁にバネばかりをつけて停動まで引く。電流もテスターで（DRV8835 の 1.5 A を超えないよう短時間） |
| モーターの K・τ | その場旋回のステップ応答（5 章、13 章 8 節）。J_eff を 4 節の式から出し、傾き = J_eff / τ から停動トルクを求めて、上の規格と比べる |
| 電池の電圧と内部抵抗 | 新品の開放電圧と、duty 1.0 で回している間の端子電圧をテスターで。差 ÷ 電流で内部抵抗 |
| モーターの型番・定格 | モーターの側面の印字とラベルを写真に残す（Cytron の仕様と突き合わせる） |

## 6. この調査の弱いところ

- Cytron の資料は 1 件も原文で読めていない。「車輪の直径 65〜67 mm」と「Cytron の TT モーター 1:48」は、いずれも検索の要約の抜粋（要約はモデルが作る文で、原文と違う可能性がある）。原文は 403 で確かめていない。
- モーターの数値は Adafruit 3777 の公開値で、Cytron の品と同じとは限らない。
- 質量の表のうち、板・電池ボックス・車輪・DRV8835 は仮の値。位置も仮定。
- IMU の軸は図の読み取りで、実機で未確認。
- 記憶は根拠にしていない。上の数字はすべて、取得した文書・設計ファイル・計算結果。
