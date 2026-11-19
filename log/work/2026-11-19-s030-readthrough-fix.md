# S030 `readthrough-fix`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s030-readthrough-fix` |
| worktree | `.git-worktree/s030-readthrough-fix` |

## 依頼

展望 (S017) の「9. 通読で見つけた直す所」13 件を、持ち分の章だけ直す。追加で 06 章の演習 2・3（解答集の担当の指摘）。

## やったこと（13 件）

1. 直した（06 章の手順 3 だけ）: 実機の `Plant` の作り方・`max_duty` の誤った手順を消し、`python -m physlearn.link` の閉ループ用コマンド（07 章「実機の経路で 1 周」と 03 章）を指す形に。オプションは書かない。07:94 は残り。
2. 直した: 06 章に PI・積分の説明 2 文、極零相殺 (Kp/Ki = τ、`control.design` と照合)、FF の経緯を 1 文に。用語集に PI 制御・積分・極零相殺・整定時間・行き過ぎ・通過率・安全ゲート・代役（時定数・デッドバンドは既にあった。むだ時間は 14 章だけなので足さない）。
3. 直した: 05 章の `link step` を `link id` に（`--help` で still/id を確認）。
4. 直した: 02 章を `physlearn sim-log --plant mujoco` に。02 章の numpy の例をそのログで走らせて動いた。`fig/README.md` には既に `mujoco_plant` が無かった（既に直っていた）。
5. 直した: 09 章の「入っているもの」に `SafetyGate`（0.6・10 /s・NaN/|gz|>15 で停止）と `SerialPlant` の守り（有限でない指令は例外、`DUTY_MAX = 0.6`、壊れた行を捨てる、MCU の時刻が戻ったら例外）。`control.py`・`link.py` で確認。
6. 一部直した: setup.md の試験の本数を書かない形に、viz の「追加予定」を外した。00 章の表に 11〜16（15 は追加予定）。README・textbook/README は残り。
7. 残り（03 章は持ち分外）。
8. 残り（textbook/README と 00 章の道筋。00 章は今回触らず）。
9. 直した: 05 章に仮の値と `wheel_radius`・`track` の書き換え、16 章への参照。「ヨーには効かない」は `sysid.apply` → `Params.with_yaw_gain`（K_m = K·b/2r）で確認。
10. 直した（持ち分）: 02・08・13・14 章の S0xx を消した。setup.md の S0xx は出典の記録なので残した。03・07 章は残り。
11. 直した: 06 章「動かしてみる」の前に通過率の定義（`randomize.evaluate`・`metrics` と照合）。
12. 直した: 01 章のステップの例にその場旋回の注記。
13. 残り（07 章）。

追加: 06 章の演習 2・3 を書き換えた。2 は公称・t_c=0.08・50 台で試し、時定数 ±60 %・ゲイン ±50 %・デッドバンド ±0.1 はどれも 100 %、バイアス ±0.1 だけ 46 % に落ちた。3 は `SafetyGate(max_rate=2.0)` に直接通して 0.02/step で増えるのを確認。`solutions.md` はこの worktree（14:02 の main）に無いので触っていない。

## 検証

- `uv run pytest`: 走らせていない（文書だけの変更）
- 触った章の相対リンク: 切れ 0 件
- `physlearn sim-log --plant mujoco` + 02 章の例: 動いた

## 確かめていないこと・残したこと

- 残り: 07:94（実機の閉ループの手順）、07:81-84（14 章の診断を材料に）、03・07 章の S0xx、03 章の setup.md との食い違い、README の試験の本数と loop-demo の数字、textbook/README の「追加予定」と XIAO 単体コース、solutions.md の 06 章演習 2・3。
