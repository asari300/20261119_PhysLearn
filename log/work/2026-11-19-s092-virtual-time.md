# S092 `virtual-time`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s092-virtual-time` |
| worktree | `.git-worktree/s092-virtual-time` |
| セッション記録 | 統括が finish-session でコピーする |

## 依頼

偽の XIAO を使う試験（`tests/test_fakexiao.py`・`test_real_loop.py`・`test_hwcheck.py`）は、偽物を壁時計（実時間の 2 倍速）で回していたので、PC の負荷が高いと間合いがずれて落ちた（レビュー 3 巡目 → S059 が許容差を広げた → 監査 7 巡目が load average 10〜17 で 5 回中 3 回、毎回違う試験が落ちるのを再現: `log/review/2026-11-19-s089-audit7-claude.md`）。CI は `--lf` で失敗した試験だけやり直し、不安定さを隠していた。試験を壁時計に依らない形で回し、許容差を元の厳しさに戻し、CI の再試行を外す。実時間の形（`python -m physlearn.fakexiao`）は変えない。

## 決めたこと

- **選んだ設計: 同じプロセスの中で、pyserial と同じ形の物を渡す（依頼の案 b）。** `FakeXiao(plant, pty=False)` は擬似端末もスレッドも持たず、`f.ser`（`VirtualPort`）が `write`・`readline`・`reset_input_buffer`・`flush`・`close` と `with` を持つ。`SerialPlant(ser=f.ser)` にそのまま渡せる。`write` は届いた時点で偽物が行を解釈し（指令は次のサンプルから効く）、`readline` は出力が空なら偽物の時刻を 1 サンプル (10 ms) 進めてその行を返す。PC が 1 行読むごとに 1 サンプル、の決定論的な握手。偽物の中身（行の解釈・ウォッチドッグ 200 ms・duty 上限・`# ERR`・軸の逆回し）は `feed`（バイト列 → 行）と `tick`（1 サンプル進める）に切り出して、実時間の形（`_run`）と共有した。写し先のスケッチとの対応は変わらない。
- **捨てた設計。** (a) pty のまま偽物の時刻を「PC が読んだぶんだけ進む」にする: pty のバッファとスレッドの切り替えで、指令がどのサンプルから効くかが OS の都合になり、決定論にならない。(c) 壁時計は使うが遅れたら偽物が待つ: PC が読み終わるのを待つ印が pty には無く（バッファに積まれるだけ）、結局 `SerialPlant` の壁時計の再送（50 ms）や時間切れとの相互作用が残る。(b) は試験が速くなり（17 s の実験が、同定まで含めて 2 s ほど）、スレッドも `sleep` も無い。
- **`link.py`・`hwcheck.py` は触っていない。** `SerialPlant` は `ser=` を最初から受け取る。`hwcheck` は `time` と `open_port` をテストの側で差し替えた（下）。
- **hwcheck の「PC 壁時計 周期」（項目 7）。** 実機では USB・OS の遅れを測る意味のある項目なので `hwcheck.py` は変えず残す。仮想の時刻の試験では、`hwcheck.time` を「`monotonic` = 偽物の時刻 `t_ms / 1000`、`sleep` = 何もしない」の物に差し替え、項目は判定に残したまま偽物の時刻で測る。値は 10 ms ちょうどになる（負荷に依らない）ので、これは実機の遅れの検査ではなく、判定の式・基準・表示が通ることの確認。実機の遅れを検出する力は、`test_stream_detects_gap_and_saturation`（欠け・飽和を作ったデータを直に判定に渡す）と、基準が `≤ 50 ms` の項目として表に出ていることで保つ。壁時計そのものを測る試験は無い（測る相手が実機だけ）。
- **擬似端末の形の確認は 1 本だけ残した。** `test_pty_realtime_form_still_works`: 5 サンプルが 10 ms 刻みで来ること（`t_ms` は偽物が数えるので負荷に依らない）と、指令が届くことを、待ちの上限だけ壁時計（5〜10 s）で見る。中身の検査は仮想の時刻の側。`test_stream_timeout_shows_the_err_the_mcu_sent` も pty を使う（スレッドが `# ERR` を流し続ける試験で、偽の XIAO ではない。サンプルが 0 個であることを見るだけなので負荷に依らない）。
- **許容差を戻した。** `motor_tau`: `0.15〜HIDDEN+0.12` → `rel=0.1`（S059 の前は `rel=0.25`。実測 0.201 vs HIDDEN 0.2）。ウォッチドッグ: 範囲 (200, 320) → 210 ちょうど（S059 の前は (200, 220)。200 ms ちょうどの刻みではまだ止まっていないことも、`while duty != 0` で 1 刻みずつ見て確かめる。定数 `WATCHDOG_MS` でなく 210 を直に書き、定数の取り違えも見える）。サンプル数: `180〜203` → `== 200`。`t` の飛び: `abs=0.02` → `abs=1e-6`。軸の入れ替え: `gz` 0.15 → 0.05、`ay`・`ax` 0.1 → 0.05。確かめる中身（同定が `gyro_bias`・`yaw_gain`・`deadband`・`motor_tau` を戻す、200 ms で止まる、duty 上限、壊れた行 5 種 + 長すぎる行 1 本の `# ERR`、軸の入れ替え、前 NG → 後 OK、`hwcheck stream` の診断）は弱めていない。壊れた行の `# ERR bad line` が 5 本・`line too long` が 1 本ちょうどであることも新たに見る。
- **決定論の試験。** `test_same_run_twice_gives_identical_csv`: 同じ偽物を 2 つ作り、`link id` を CLI の `main` 越しに 2 回回して `--out` の CSV がバイト単位で同じ（1701 行）であること。

## やったこと

- `src/physlearn/fakexiao.py`: `FakeXiao(..., pty=True)` の引数、`feed`・`tick` の切り出し、`VirtualPort`。pty の import は `pty=True` のときだけ（Windows の素の Python でも `pty=False` は使える）。`python -m physlearn.fakexiao` の既定の動き・出力・`--help` のオプションは変えていない。
- `tests/conftest.py`（新規）: `fake_factory`（`FakeXiao(SimPlant(HIDDEN, seed=1), axes, pty=False)`）。3 つの試験ファイルが個別に持っていたスレッドつきの fixture を置き換えた。
- `tests/test_fakexiao.py`・`test_real_loop.py`・`test_hwcheck.py`: 上のとおり。`wait_stopped` は、停止 `S` が write の時点で届くので `duty == (0, 0)` を見るだけになった。
- `.github/workflows/ci.yml`（`test` ジョブだけ）: `|| { ...; pytest --lf; }` を外して `uv run pytest -q` にした。`timeout-minutes` 15 → 10（偽の XIAO の試験が実時間でなくなり、全体で 1 分ほど。`uv sync` を足しても余裕）。`actionlint`（`uvx --from actionlint-py actionlint`）は通る。

## 検証

- `uv run --extra mujoco --extra viz pytest -q`: 168 passed。
- **負荷をかけた 5 回**（`taskset -c 0 uv run ... pytest -q tests/test_fakexiao.py tests/test_real_loop.py tests/test_hwcheck.py` を、同じコアで `taskset -c 0 sh -c 'while :; do :; done'` 2 本を走らせたまま。ほかの担当 4 体が並列で動いていて、始める前から load average 約 10）: 5 回とも 45 passed。所要時間は 12.1・9.3・6.4・7.4・7.3 秒（3 ファイル）。終わりに 2 本とも止めた（自分が立てた PID を指定）。
- **前**（同じ条件、変更前のコード、2 回）: 2 回とも 43 passed、43.5・45.2 秒。この条件（同じコアに 2 本）では旧い試験も落ちなかった。監査 7 巡目が落ちを再現した load average 10〜17 の「多数のプロセスが取り合う」条件を、ここでは作り直していない。前の失敗を再現して「直った」とは言わない。言えるのは、決定論になったこと（スレッド・pty・壁時計の待ちが無く、同じ入力で CSV がバイト単位で同じ）と、同じ負荷のもとで 3 ファイルが約 6 倍速く通ること。
- **所要時間**: 3 ファイル 42.8 s → 5.6 s（静かなとき）。全体 168 本は 55 s（ほかの担当が並列で動いている中での 1 回。`--durations` で見ると残りは `test_sysid`・`test_mismatch`・`test_loop` の 3〜5 s の試験が並ぶ）。**目標の 40 秒以内には届いていない**: 偽の XIAO の試験の分は 43 s → 6 s に減ったが、ほかの試験は触らない範囲。
- **実時間の形**: `python -m physlearn.fakexiao` を 1 回立て（出力 `偽の XIAO: --port /dev/pts/N  (axes=x,y,z speed=1.0 plant=sim)  Ctrl-C で終わる`、変更前と同じ文面）、`link still --seconds 2` をつなぐと 200 行、az の平均 9.809。`--help` のオプションは 4 つ（`--axes`・`--speed`・`--plant`・`--seed`）のまま。
- セッション記録の `--check`・ステージした差分の漏洩検査は統括の finish-session。

## 確かめていないこと・残したこと

- 変更前の失敗（load average 10〜17 で落ちる）を再現していない（上）。
- 実機の経路の壁時計（`SerialPlant` の 50 ms の再送、時間切れ 1 s）は仮想の時刻の試験では効かない: `VirtualPort.readline` は時間切れしない。時間切れ・時刻が戻る例外は `tests/test_link.py` 側の試験の範囲で、ここでは触っていない。
- 全体の所要時間の目標 40 秒は、ほかの遅い試験（sysid・mismatch・loop）を速くしないと届かない。別の担当へ。
- MuJoCo の偽物（`--plant mujoco`）は試験に入っていない（元から）。
