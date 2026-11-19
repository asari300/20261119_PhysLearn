# S022 `s022-audit-fix-bringup`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s022-audit-fix-bringup` |
| worktree | `.git-worktree/s022-audit-fix-bringup` |
| セッション記録 | 統括がまとめてコピーする（このセッションでは取っていない） |

## 依頼

(1) S016 の監査が見つけたソフトウェア側の文書の誤り（#2〜#4）と、二次的・取り直せなかった項目を、一次資料を取り直して直す。(2) 実機が届いてからの立ち上げ手順書 `doc/bringup.md` を書く。

## 決めたこと

- 監査の言い分も取り直した。PyPI は JSON API（`https://pypi.org/pypi/<名前>/json`）、MuJoCo は GitHub の rst 原文（要約を挟まない）、NVIDIA フォーラムは Discourse の JSON 原文、docs.ros.org は HTML を直接読んだ（JST 13:55〜13:56）。
- 監査の誤り #2〜#4 は 3 件とも原文で裏づけられたので採用。#4 は監査の根拠が検索要約だったが、changelog 原文の 3.5.0 の節で確かめた。
- 「NVIDIA 職員」は原文では Moderator（staff 表示）で、Isaac Sim 5.x の時期（2025-10-31）の回答。「モデレーター」と時期、「6.2 で変わったかは未確認」に直した（software.md・ADR）。
- 「flex の弾性定数」の言い直しは決め手が見つからず保留。
- 手順書の段 8（実機の閉ループ）は、実在するコマンドが無いので「無い」と書いた。コードは触らない約束のため作っていない。

## やったこと

- `doc/research/2026-11-19-software.md`: LeRobot 0.7.0、Genesis 1.4.7、MJWarp は 3.5.0 で正式（PyPI の最新 4.0.1 も）、MJWarp の保守の言い方、ROS 2 Lyrical の GA の裏づけ、Kilted の EOL、フォーラムの回答者。
- `doc/adr/0001-sim-stack.md:10`: フォーラムの回答者の言い方。
- 00・10・90 章は grep で該当の数字が無く、変えていない。
- `log/review/2026-11-19-s016-audit-claude.md`: 末尾に採否の表（原文は変えていない）。
- `doc/bringup.md`（新規、約 110 行）: 段 0〜9 のチェックリスト。止め方とやってはいけないことを段 4 の前に置いた。

## 検証

- コードは触っていないので `uv run pytest` は走らせていない。
- 手順書のコマンドは `uv run physlearn {sysid,eval,loop-demo} --help`、`python -m physlearn.link --help`、`python -m physlearn.imu {still,turn,r2s} --help` で存在とオプションを確かめた。実機では 1 つも走らせていない。
- 手順書のリンク先のファイルが存在することを確かめた（欠け 0）。
- 合格基準のうち「目安（根拠なし）」は 5 件。
- セッション記録の `--check`・漏洩検査: 走らせていない（締めは統括）。

## 確かめていないこと・残したこと

- 手順書は実機で 1 度も通していない。
- 実機で PI の閉ループを回す CLI が無い（`link` は `still` と `id` だけ）。`control.run` に `SerialPlant` を渡す入口が要る。
- モーターの向き・duty 上限・ウォッチドッグを試す専用のコマンドが無く、端末で手打ち（`M 0.3 0.3`）。duty 上限は目視かオシロでしか確かめられない。
- サンプル間隔の揺れを出す道具があるか（`imu still` の出力に含まれるか）は見ていない。
- AE-DRV8835-S のピンの並び、SA0、TI・ST のデータシートは未確認のまま（手順書で実物を見て確かめる段にした）。
- `link.encode_command` が NaN を -1 にする件（S010 の申し送り）が直っているかは見ていない。直っていなければ段 5 の前に直すべき。
- Kilted の公式の EOL 日、「flex の弾性定数」の言い直し。
