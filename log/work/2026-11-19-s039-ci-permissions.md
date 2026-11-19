# S039 `ci-permissions`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s039-ci-permissions` |
| worktree | `.git-worktree/s039-ci-permissions` |
| セッション記録 | 未作成（統括が締めで作る。このセッションでは push もマージもしない） |

## 依頼

GitHub Actions の CI を入れる（test / firmware / firmware-mg24 の 3 ジョブ）。S003 が移して統括が外した `.claude/settings.json` の許可リストを戻す。remote が GitHub になったので CLAUDE.md・finish-session・start-session・log/README.md を直す。

## 決めたこと

- アクションの版は `gh api .../releases/latest` で今日の最新を確かめ、タグで固定: `actions/checkout@v7.0.1`、`astral-sh/setup-uv@v10.3.3`、`actions/setup-python@v7.1.0`、`arduino/setup-arduino-cli@v2.1.0`。コミット SHA 固定にはしていない（タグ固定まで）。
- arduino-cli は 1.6.0（ローカルと同じ。最新も 1.6.0）。nRF52 コアは `Seeeduino:nrf52@1.1.13`、ライブラリは `Seeed Arduino LSM6DS3@2.0.8`、`adafruit-nrfutil==0.5.3.post16`（コンパイルの最後に `python` と共に PATH に要る。`actions/setup-python` で `python` を用意）。
- 試験の不安定さへの備えは「失敗したらもう 1 回だけ回す」と `timeout-minutes: 15` の 2 つ。pty を 2 倍速で使う試験を除外はしていない。
- MG24 の FQBN は `SiliconLabs:silabs:xiao_mg24:protocol_stack=none`。出典: パッケージ索引 https://siliconlabs.github.io/arduino/package_arduinosilabs_index.json （コア 5.0.0 の板名 "Seeed Studio XIAO MG24 (Sense)"）と、コア 5.0.0 の `boards.txt`（`xiao_mg24.*`、`-DARDUINO_XIAO_MG24` を定義、メニュー `protocol_stack` に none がある）。確認日 2026-11-19。Seeed wiki 自体は FQBN を載せていない。`none` は無線を使わない最小のスタックとして選んだ。
- 許可リストは S003 の 9 件だけを戻し、足していない（広げるのは発注者が決める）。
- README には触っていない（バッジは別の担当）。

## やったこと

- `.github/workflows/ci.yml`（新規）、`.claude/settings.json`（`permissions.allow`）、`CLAUDE.md`、`.claude/skills/finish-session/SKILL.md`、`.claude/skills/start-session/SKILL.md`、`log/README.md`。

## 検証

- `uv sync --locked --extra mujoco --extra viz && MPLBACKEND=Agg uv run pytest -q`: 106 passed / 0 failed（30 秒）。
- 文法: PyYAML で読み込み OK。`actionlint` 1.7.12 で指摘 0 件。
- 3 つのアクションの `action.yml` を取得し、使った入力名（`version` など）が存在することを確かめた。
- `.claude/settings.json` を JSON として読み込み OK。
- 漏洩検査（ステージした差分）: 0 件。

## 確かめていないこと・残したこと

- **GitHub 上での実行は未確認**（push しないため）。特に次の 3 点は CI で初めて分かる。
  1. `firmware`: コア 1.1.13 とライブラリ 2.0.8 の組が runner で通るか（ローカルでは通っている）。
  2. `firmware-mg24`: コア 5.0.0 のインストールと、スケッチの `#if`・D0..D3 の PWM が通るか。ディスクとタイムアウト（45 分）も未確認。
  3. `test`: pty を使う試験が共有ランナーで安定か。再実行の警告が出たら不安定の兆候。
- `gh workflow list` は空（まだ push していないため）。
- README に足す 1 行（別の担当）: CI バッジ `![CI](https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg)`。
