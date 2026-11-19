# S052 `s052-troubleshooting`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s052-troubleshooting` |
| worktree | `.git-worktree/s052-troubleshooting` |
| セッション記録 | `log/sessions/` に finish-session が入れる（このセッションでは未実施） |

## 依頼

症状から引ける「つまずき集」`doc/troubleshooting.md` を 1 本書く（展望の提案 N4）。新しい事実は作らず、既存の文書とコードのエラーメッセージを症状別に並べる。コードと他の文書は直さない。

## 決めたこと

- 印を 3 つにした: ✔ 再現（偽の XIAO・`sim-log`・短い Python で状況を作って原文を確かめた）、（文書より）（文書かコードを読んだだけ）、【実機では未確認】。
- 動きやすい数字（行数・秒数・試験の本数）は書かない。メッセージの原文は載せる。
- `python -m physlearn.hwcheck`（S050）は「追加予定」と 1 行だけ。

## やったこと

- `doc/troubleshooting.md` を新規作成（環境・Arduino・WSL2/USB・シリアル・軸・IMU・モーター・同定・制御・偽の XIAO・SolidCraft・CI）。
- 再現に使った道具は scratchpad の使い捨てスクリプト（リポジトリには入れていない）。他の担当の偽の XIAO を巻き込まないよう、自分の PID だけ止めた。

## 検証

- `uv run pytest`: 通った（111 passed、44 s。本数は文書に書いていない）。
- 項目数: 約 60 項目のうち ✔ 再現 33 箇所の印（1 項目に複数の再現を含むものあり）、（文書より）は残りの大半、【実機では未確認】はモーター・配線・飽和・`/dev/ttyACM0` まわり。
- 再現した原文: mujoco・matplotlib 無し、`axes ... は回転になっていない`、`substring not found`、`argument --axes: expected one argument`、`有限でない指令`、`MCU の時刻が戻った`、`IMU のサンプルが来ない`（`# ERR imu not found` 付きも）、`# ERR bad line`、`# ERR line too long`、引数の範囲 5 種、`動いたステップが 2 つ未満...`、`最初に静止区間...`、`列が足りない`、`静止区間の雑音が 0`、`安全ゲートが作動した`、`冒頭 0 s にサンプルが無く...`、Permission denied、No such file、loop-demo の NG→OK。
- セッション記録の `--check`・漏洩検査: 統括の finish-session に任せる。ホームのパスは文書に無いことを grep で確認。

## 確かめていないこと・残したこと

- 実機が要る項目は全部。【実機では未確認】の印のまま。
- `fakexiao` の pty 不可メッセージ（Windows 素の Python）、`# ERR imu not found` を本物のスケッチが出す所、`dialout` が原因かどうか、SolidCraft・CI は走らせていない。
- 探す途中で見つけた食い違い・分かりにくい点（直していない）:
  1. `SafetyGate` が作動しても `sim-log`・`link id` は無言で、以後の指令が 0 のログができる。`sysid` は `deadband 0.0`・`motor_tau 0.01` と RankWarning で返す（`sim_log` / `identify`）。
  2. `--axes a,b,c` は `ValueError: substring not found`。`parse_axes` の入力検査が無い。
  3. `--axes -x,y,z` は argparse に拒まれる（`=` が要る）。`protocol.md` の例 `-y,x,z` はこのまま打つと失敗する。
  4. 存在しないポートは生の `SerialException` のトレースバック。ヒント（`ls /dev/ttyACM*`、usbipd、dialout）が無い。
  5. `--dt 0` のエラーは `--dt は 0〜1 秒、--seconds は 0〜3600 秒`。どちらが悪いか分からない。
  6. `python -m physlearn` は `__main__` が無く動かない。14 章などは `physlearn ...` と書く（`uv run` が要る）。
  7. `jog --left 0.3` は 12 章の `-0.419` に対し今回 `-0.395`（`+0.580`／`+0.582` は一致）。長く動かしている偽の XIAO では少しずれる。
  8. `setup.md` の「非 mbed 版で Serial がコンパイルできない → TinyUSB」の行は、今のスケッチ（足していない）と CI が通る事実と並べると当たる条件が不明。
  9. 03 章 3.9 「ウォッチドッグを PC から確かめる口は無い」。12 章 演習 2 の生の `serial` で確かめる道だけ。
