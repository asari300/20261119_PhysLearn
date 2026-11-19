# S086 `firmware-format`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s086-firmware-format` |
| worktree | `.git-worktree/s086-firmware-format` |
| セッション記録 | 統括が締めで作る |

## 依頼

XIAO のスケッチが IMU の行を作るときの数値の書式を、`%f` に頼らず、どちらのボード（nRF52840 Sense・MG24 Sense）でも確実に出る形に直す。S053 の指摘 5 の裏取りと採否も。行の形（項目の数・順・単位・桁）は変えない。

## 決めたこと

- **自前の固定小数関数**（`put_fixed`、整数演算）にした。`dtostrf` は MG24 のコアにあるか未確認（コアを入れていない）で、あっても丸めと桁の挙動が揃う保証が無いため。`-u _printf_float` を MG24 に足す案は、スケッチからはリンクの設定を変えられないので使えない。
- 関数は Arduino に依存しない小さな `fixed_fmt.h` に分け、PC の g++ でそのまま試せるようにした。テストの `main` はリポジトリに入れていない（scratchpad）。ヘッダは `#include` されたときだけ Arduino のビルドに入る。
- NaN は 0、絶対値は 999 で頭打ち。999 にしたのは float で 999×10^4 が正確に表せ（最初 99999 にしたら `99999.0016` と出た）、センサーの範囲（±157 m/s^2・±17.5 rad/s）の外で、バッファが小さく収まるため。
- 負号は丸めた値が 0 でないときだけ（`-0.000` を出さない。元の `%.3f` は出していた。PC はどちらも 0 として読む）。
- 丸めは四捨五入（`lroundf(x * 10^N)`）。`%.Nf` と比べ境界で最後の桁が 1 違いうる。

## やったこと

- 指摘 5 の裏取り（出典つき）:
  - MG24: `SiliconLabs/arduino` のタグ `5.0.0`（CI が入れる版）の `boards.txt` を `raw.githubusercontent.com` から読んだ。`xiao_mg24` の 5 つの protocol_stack すべての `build.ld_flags` が `-mcpu=... -mfloat-abi=hard --specs=nano.specs -Xlinker -Map ... -Wl,--gc-sections -Wl,--wrap=_free_r ...` で `-u _printf_float` が無い。`platform.txt:32` の `compiler.ldflags={build.ld_flags} -Wl,--no-warn-rwx-segments`、`:74` のリンクの recipe にも無い。`printf_float` の語は両ファイルで 0 件。`xiao_mg24.build.float_flags=` は空。よってリンク設定の上では指摘どおり。コアのコンパイル済みライブラリ（precompiled_gsdk）が別の `printf` を持つ可能性は読めていない。
  - nRF52: ローカルの Seeeduino:nrf52@1.1.13 の `platform.txt:57` が `build.float_flags=... -u _printf_float`、`:52` の `compiler.ldflags` が `{build.float_flags}` を含む。
- `firmware/xiao_imu_drive/fixed_fmt.h` を新設、`xiao_imu_drive.ino` の `sendSample` を `snprintf("I %lu")` + `put_fixed` ×6 + `\n` に。最長 70 文字で `out[128]` に収まる。
- `doc/protocol.md`（状態の行と、書式の説明に 1 行）、`doc/textbook/03-hardware-firmware.md`（MG24 の記述に 1 文）、`log/review/2026-11-19-s053-review3-claude.md`（指摘 5 の採否の欄だけ。原文は変えず）。

## 検証

- PC の g++（`-Wall -Wextra` で警告 0）で `fixed_fmt.h` を試した:
  - 代表値（0、-0.0、±0.0004、±0.0005、±0.001、±9.80665、±17.45329、±156.9064、丸めの境界 0.00005・0.99995・9.9995・99.9995、±1e6、±1e30、±inf、NaN）の行 26 本と、4 バイト整数の最大の時刻 `4294967295` を `decode_sample` が全部読めた。行の最長は 70 文字未満。
  - 代表値 + 乱数の 600 行を `decode_sample` で読み戻し、元の値との差が最後の桁の 0.5073 倍以内（float の掛け算の丸めで 0.5 を僅かに超える）。項目 8 個・空白 1 つ区切り・`-0.000` 無し。時刻も一致。
  - 乱数 400 万値を `snprintf("%.3f"/"%.4f")` と突き合わせ: 15,764 個（0.39%）が違い、すべて最後の桁が 1 違い。`-0.000` は 0 件。
- nRF52840 Sense 向けコンパイル（`Seeeduino:nrf52:xiaonRF52840Sense`、`--warnings default`）: 通った。**60,652 バイト（7%）**、グローバル 7,860 バイト（3%）。前は 58,172 バイト（+2,480）。警告 0（前も 0）。増えた理由は調べていない。
- `uv run --extra mujoco --extra viz pytest -q tests/test_link.py tests/test_fakexiao.py`: 62 passed。

## 確かめていないこと・残したこと

- **MG24 でのコンパイル・動作**（push 後の CI の `firmware-mg24`、実機は無い）。`put_fixed` は標準の `math.h` の `lroundf` と整数だけを使うので通る見込み。
- nRF52840 の実機でも未確認（コンパイルのみ）。
- 100 Hz の時間の余裕は測っていない（整数の割り算 12 回ほどで、`%f` より軽い見込み）。
- `fakexiao.py` は `%.3f`・`%.4f` のまま（`src/` は触らない担当）。両者は最後の桁が稀に 1 違うだけで、PC は数値として読む。
