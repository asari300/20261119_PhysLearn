# S011 `readme-index`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s011-readme-index` |
| worktree | `.git-worktree/s011-readme-index` |
| セッション記録 | 統括のセッションのサブエージェント（個別のコピーは無し） |

## 依頼

リポジトリの入口になる文書を書く: `README.md`、教材の索引 `doc/textbook/README.md`、`doc/README.md`、計画の更新、S000 の作業記録。締め切りは JST 14:08 までに feature ブランチへコミット。マージと push はしない。

## 決めたこと

- README のコードブロックには、自分で走らせたコマンドだけを載せた（`uv sync`、`uv run pytest`、`uv run physlearn loop-demo`、`uv run physlearn --help`）。
- S008 が変えている CLI のオプション（MuJoCo を選ぶ口など）は README に書かず、計画の表で「作業中」とだけ書いた。
- `doc/setup.md`（S015）と 11 章（S014）は「追加予定」とし、リンクを張らなかった（まだ無いファイルなので）。
- 教材の索引の「実機」の列は、章の題と内容から判断した。各章を全部は読んでいない。
- S016 (audit)・S017 (outlook) は依頼に無いが、ブランチがあったので計画の表に「作業中」として載せた。

## やったこと

- `README.md`: これは何か、できること・できないこと、最短の始め方、買うもの、S2R / R2S の輪の図、地図、教材の入口、作業の進め方、remote と CI。
- `doc/textbook/README.md`: 章の表（00〜11・90・用語集）と 3 つのコース。
- `doc/README.md`: doc/ の案内。
- `doc/plan/2026-11-19-plan.md`: セッション表を S000〜S017 にし状態を付けた。「決まったこと」「次にやること（優先順）」を足した。
- `log/work/2026-11-19-s000-bootstrap.md`: 統括の申告と `git log` から。

## 検証

この worktree（main の `8740b38` から分岐）で実行した。

- `uv sync --extra mujoco`: 成功
- `uv run pytest`: 29 passed
- `uv run physlearn loop-demo`: 前は仕様 NG（定常偏差 0.085 rad/s）、後は仕様 OK（行き過ぎ 0.2 %、定常偏差 0.000 rad/s）
- `uv run physlearn sim-log <csv>` → `uv run physlearn sysid <csv>`: 動いた（1100 行、yaw_gain 12.0028 など）。README には載せていない。
- セッション記録の `--check`: 実行していない（サブエージェントなので統括がまとめて行う）。
- ステージした差分の漏洩検査: 下のコミット前に grep で確かめた。

## 確かめていないこと・残したこと

- main は作業中に S009・S010 が入って進んだ。この worktree はその前から分岐しているので、README の「29 passed」と loop-demo の数値は新しい main では変わりうる。
- 各セッションの状態は 13:47 時点。統括がマージ後に直す。
- 教材の各章の本文と README のリンクの整合は、ファイル名のリンク先が存在することだけ確かめた。
