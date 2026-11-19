# S012 `review` のレビュー（Claude）

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s012-review` |
| 対象 | main `8740b38` 時点の `src/physlearn/`、`firmware/xiao_imu_drive/xiao_imu_drive.ino`、`doc/protocol.md`、`tests/`（差分ではなく全体） |
| レビュアー | Claude Opus 5.5 |
| 依頼の文面 | 今日並列に書かれたコードを、実機の暴走・物理と符号・同定と制御の数値・取り決めの食い違い・試験の穴の順に独立に見る |
| 作業記録 | `log/work/2026-11-19-s012-review.md` |

既知で別の担当が直している事項（sysid の 1 段ログ、SafetyGate 上限 0.8 対 DUTY_MAX 0.6、DRV8833 前提、MG24 未コンパイル）には重ねていない。ただし #2 は上限の食い違いが同定に及ぼす結果で、S008 の修正で一緒に閉じるか確かめてほしい。

再現スクリプト: scratchpad の `s012/r1.py`（#1〜#4・#9）、`s012/r5.py`（#5）。リポジトリには入れていない。

## 指摘（原文のまま）

| # | 重さ | 場所 | 指摘 | 採否 | 理由・直したコミット |
| --- | --- | --- | --- | --- | --- |
| 1 | 高（実機が危ない） | `src/physlearn/link.py:22` `encode_command` | NaN の duty が停止ではなく **-1（全力後退）** になる。`max(-1.0, nan)` が -1.0 を返すため。`Command(nan, nan)` → `b"M -1.000 -1.000\n"`（再現した）。`python -m physlearn.link step --duty nan` でも同じで、`record` は `SafetyGate` を通らないので止める者がいない（MCU は 0.6 に切るだけ）。スケッチ側の `isfinite` は文字列化された後なので効かない。直し方: `encode_command` で非有限なら `STOP` を返す（または `ValueError`）。`main` で `--duty` を `0..DUTY_MAX` に検査。試験 `test_encode_clamps_and_formats` に NaN を 1 行足す。 |  採用 | S019。`STOP` を返す案ではなく `ValueError`（`step` の except が `S` を送る。呼び手の誤りを黙って停止にしない）。NaN・±inf で `M` が 1 行も出ず最後が `S` を試験。`step --duty` の CLI は今の `link.py` に無く、`--dt`・`--seconds` を検査（NaN も弾く） |
| 2 | 高（結果が誤る） | `src/physlearn/link.py:142`（CSV の left/right）、`sim.py:91`（実験に 0.65） | ログの left/right は **PC が頼んだ値**で、MCU が実際に出した値（`DUTY_MAX` 0.6 で切った値）ではない。`id_experiment` には 0.65 の段があるので、実機ログを `sysid` に掛けるとゲインとデッドバンドが下に偏る。0.6 で切る代役 sim で再現: 真 K=6.0・db=0.20 に対し、切らない場合 K=5.90・db=0.200、切る場合 **K=5.01・db=0.168**。直し方: 実験の振幅を `DUTY_MAX` 以下に収める（S008 の 6 段で確認）、かつ `encode_command` が PC 側でも `DUTY_MAX` で切って、ログには実際に送った値を書く。 |  採用 | S019。main（S008）で実験の最大 0.5・ゲート 0.6 になり `link id` は閉じていた。`record` に直に 0.9 を渡すと 0.9 が記録されていた（`test_record_csv` は 0.4 なので穴を固めてはいないが、穴を突いてもいなかった）。`link.DUTY_MAX = 0.6` を置き `encode_command`・`record` の記録を同じ値で切る。スケッチの値との食い違いは試験 `test_duty_max_matches_sketch` が `.ino` を読んで照合 |
| 3 | 中（実機が危ない・推測） | `firmware/xiao_imu_drive/xiao_imu_drive.ino:62,71` | `Serial.println("# ERR ...")` だけが `availableForWrite` の検査なしで書く。PC が読まずに壊れた行を送り続けると（例: 端末から流し込み）、送信バッファが埋まって `println` で止まり、`loop()` のウォッチドッグ判定に戻らず **最後の `M` の duty で回り続ける**おそれ。Adafruit nRF52 の TinyUSB CDC は DTR が立っている間は書き込みで待つはず（読んで追っただけ、未確認）。`sendSample` と imu-not-found は守ってあるので一貫させるだけ。直し方: ERR も `if (Serial.availableForWrite() > 24)` で囲む。 |  採用 | S019。コア 1.1.13 の `Adafruit_USBD_CDC.cpp:224` で、接続中に FIFO が埋まると `yield()` しながら待つことを確かめた（推測が裏づけられた）。`say()` で空きを確かめてから書く。ファームの試験の仕組みが無いので試験なし（コンパイルのみ、実機未確認） |
| 4 | 中（結果が誤る） | `src/physlearn/link.py:84,27-41` | `readline` が 50 ms の timeout で途中まで読んだ行をそのまま返すと、最後の数値が切れていても 8 個そろえば採用される。`b"I 52310 0.012 -0.034 9.806 0.0011 -0.0007 1"`（本来 gz=12.3456）→ `gz=1.0` の Obs（再現した）。gz は制御にも同定にも使う列。直し方: `decode_sample` で行末が `\n` でない行を捨てる（`doc/protocol.md` の「PC が使う行」にも 1 行足す）。 |  採用 | S019。`decode_sample` ではなく `SerialPlant._next` で行末が `\n` でない行を捨てる（`decode_sample` の公開の形と他の呼び手を変えないため）。試験 `test_partial_line_is_dropped` |
| 5 | 中（実機が危ない） | `src/physlearn/link.py:109-111` `SerialPlant.step` | MCU 時刻が戻る（MCU の再起動、`millis()` の 49 日の桁あふれ）と、`obs.t` が負になり `while obs.t < t_target` がサンプルを受け続けるので `TimeoutError` にならず、その間 50 ms ごとに同じ `M` を送り直して **走らせ続ける**。偽ポートで t=50.02 s から 0 に戻すと、0.03 s の step が 6.5 s 返らず `M` を 127 回送った（再現した。実機なら reset 時の MCU 時刻ぶん、数十秒以上）。USB 給電の XIAO の再起動はふつうポートごと消えて例外になるので頻度は低いが、桁あふれと「時刻が飛んだ」場合も同じ道。直し方: `_next` で前のサンプルより `t` が減ったら例外（`step` の except が `S` を送る）。 |  採用 | S019。MCU 時刻が前のサンプルより戻ったら `RuntimeError`（→ `S`）。試験 `test_mcu_time_going_back_stops`（直す前は 1 秒の TimeoutError まで M を送り続けた）。壁時計の上限は足していない: 時刻が戻らなければ各 `_next` の 1 秒の timeout で止まるため |
| 6 | 低（実機） | `firmware/xiao_imu_drive/xiao_imu_drive.ino:46` | 停止は `S` ちょうどだけ。`S `（末尾空白）や `s` は `# ERR bad line` で、止まるのはウォッチドッグの 200 ms 後。`doc/protocol.md` は「区切りは空白 1 個」なので取り決め違反ではないが、端末から手で止める教材の使い方では効く。直し方: `s[0]=='S'` の後を空白と `\r` だけ許す。 |  採用 | S019。`S` の後の空白を許す。`\r` は `readSerial` が既に落としている。小文字 `s` は取り決めに無いので受けない。ファームの試験なし（コンパイルのみ） |
| 7 | 低（物理） | `src/physlearn/sim.py:128-130`、`models/diffdrive.xml:24` | sim と MuJoCo はどちらも IMU を旋回中心（車軸の中点）に置いている。実機の XIAO が中心から d ずれていると、その場旋回で ax に −ω²d（3 rad/s・d=3 cm で −0.27 m/s²）と、角加速度で ay に d·dω/dt が乗る。sysid は加速度を使わないので今は結果に効かないが、加速度を S2R/R2S で比べる章では sim と実機がずれる。直し方: 教材で「IMU は中心にある前提」と明記するか、`Params` に IMU 位置を足す。sim の ay の符号（左旋回で +y）と MuJoCo の座標・gz の符号は正しかった。 |  保留 | S024 の担当 |
| 8 | 低（安全） | `src/physlearn/control.py:49-70` `SafetyGate`、`link.py:136-143` `record` | 実機で走る経路のうち `link.record`（step 実験）はゲートを通らない。gz の上限での停止も変化率の制限も効かない。#1 と合わせて、実機に出る経路はすべてゲートを通す方が筋。 |  実質採用 | S019 の #1・#2 で、`record` の経路でも NaN は送られず duty は 0.6 で切られる。gz の上限での停止と変化率の制限は `record` には無いまま（step 実験は `id` と違い今は CLI から呼ばれない） |
| 9 | 低（評価） | `src/physlearn/control.py:93-104` `metrics` | 目標が負だと行き過ぎが常に 0 になる（`(y.max()-target)/target`）。target=-3 で 30 % 行き過ぎた応答 → `overshoot 0.0`（再現した）。target=0 では 0 除算。今は TARGET=3 固定なので実害なし。直し方: `y` と `target` に `sign(target)` を掛けてから計算。また整定時間は「最後に外れていたサンプルの時刻」で、入った時刻より 1 dt 早い（定義として書けば十分）。 |  保留 | S025 の担当 |

### 試験の穴

- `encode_command` の NaN/inf（#1）、途中で切れた行（#4）、MCU 時刻の逆行（#5）の試験が無い。
- `test_record_csv` は「頼んだ duty がそのまま CSV に出る」ことを確かめており、#2 の誤りを正しいものとして固定している。
- sim の向心加速度 `ay` の符号（左旋回・前進で +）を確かめる試験が無い（MuJoCo 側は gz の符号だけ）。
- `sysid` は理想の sim ログでしか試していない。MCU で切れた duty（#2）や時刻のばらつきの試験は無い。

### 見たが無かった

- スケッチ: `millis()` の桁あふれ（符号なし引き算で正しい）、`micros()` の周期（`(long)` 差で正しい）、長すぎる行（47 文字で切って行末まで捨てる）、`M nan 0`・`M inf 0`・`M 0.3`・`M 0.3 0.3x`（すべて拒否、ウォッチドッグ延長なし）、範囲外（`constrain`）、起動直後（`setup` で停止、`last_cmd_ms=0` なので 200 ms 後からウォッチドッグも効く）、シリアル切断（指令が来ず 200 ms で停止）、`sendSample` の書き込み詰まり（守ってある）。
- PC: 例外・Ctrl-C（`BaseException`）・タイムアウトで `S` を送る経路、`with` の `close`、読めないときに固まらない（readline 50 ms・1 s で `TimeoutError`）。
- 単位: スケッチの g→m/s²・deg/s→rad/s と `link.py`・`Obs` の単位は一致。`t_ms/1000`。`parse_axes` は鏡映と重複を拒否。
- 差動 2 輪の式、一次遅れの厳密離散化、デッドバンド、`design` の極零相殺（閉ループ 1/(tc s+1) になる）、MuJoCo の車輪の回転向き。
- sysid に時刻のばらつき（±4 ms）を足しても推定は変わらない（`first_order` が実際の dt を使う。再現した）。乱数の seed（`evaluate` は tc 間で共通乱数、代役は seed+1000 で重ならない）。

### 小言

- `mujoco_plant.main` と `link.record` は同じ「schedule を回して CSV に書く」処理を別々に持つ（`log.row` / `write_csv` で揃えられる）。
- スケッチは指令が無い間、毎 loop で `setMotors(0,0)`（`analogWrite`）を呼び続ける。害はないが、止めた後 1 回で足りる。
- `SafetyGate` の変化率は呼び手の `dt` を信じる。大きな dt を渡すと制限が実質なくなる。

## 結論

- 採用 ? 件・保留 ? 件・不採用 ? 件（直す担当が埋める）。
- 実機の前に直すべきは #1・#2・#3・#5。#1 と #4 と #5 は数行ずつの修正と試験 1 本ずつで済む。
