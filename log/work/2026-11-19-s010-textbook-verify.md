# S010 `textbook-verify`

| | |
| --- | --- |
| 日付 | 2026-11-19 |
| ブランチ | `feature/s010-textbook-verify` |
| worktree | `.git-worktree/s010-textbook-verify` |
| セッション記録 | 未作成（統合担当が取る） |

## 依頼

概念の章（00・01・02・09・10・用語集）を、main にある実物（`src/physlearn/`、`firmware/xiao_imu_drive/`、`doc/protocol.md`、調査と ADR）と突き合わせ、食い違いと「要確認」を潰す。コードと他の章は直さず、食い違いは申し送る。

## 決めたこと

- LSM6DS3TR-C の感度は、Seeed Arduino LSM6DS3 2.0.8 のソース（`calcAccel`・`calcGyro`・既定の `settings`）を根拠にした。TR-C のデータシートそのものは取れていないので、±245 / ±250 の表記は【未確認】のまま残した。
- 02 章には、スケッチが範囲を設定しない（ライブラリの既定: 加速度 ±16 g・0.488 mg/LSB、角速度 ±2000 dps・70 mdps/LSB、ともに 416 Hz）ことを書いた。範囲の変更はスケッチ側（03 章の範囲）なので提案にとどめた。
- 04〜07 章と `physlearn sysid` などのコマンドは名前だけの記述なので、そのまま残した。

## やったこと

- `doc/textbook/02-imu.md`: 感度表の要確認を、ライブラリの換算式で裏づけ。スケッチが実際に使う範囲・感度・ODR・単位の表を追加。ログ CSV の形（見出し行、`t,ax,ay,az,gx,gy,gz,left,right`、単位、機体の軸）と `python -m physlearn.link still ... --seconds 60` を追記。出典 4（ライブラリ）を追加。
- `doc/textbook/09-safety.md`: ウォッチドッグの「200 ms（推測）」を実装の値に。いまの実装に入っているゲート（XIAO の `DUTY_MAX = 0.6`、NaN 行の拒否、200 ms のウォッチドッグ、`SerialPlant` の 50 ms ごとの再送と終了時・例外時の停止）と、入っていないもの（変化率の制限、有効化スイッチ）を明記。NaN の注意を追加。
- `doc/textbook/00-overview.md`: ボード（XIAO nRF52840 Sense）・ドライバー（DRV8835）・BOM の価格・Isaac Sim 6.2 / Isaac Lab 3.0.0・mujoco 4.0.1 以上を調査と ADR に合わせた。
- `doc/textbook/glossary.md`: MuJoCo の版、Isaac Sim の要件、ウォッチドッグ 200 ms、duty 上限 0.6 を追記。
- 01・10 章: 突き合わせたが食い違いは無く、変更なし。

## 検証

- 02 章の numpy の例: `python -m physlearn.mujoco_plant --out scratchpad/s010/still.csv` の CSV で実行し、`ax ay az gx gy gz` の平均と標準偏差が出た（`az` 平均 9.8097。sim のログは旋回を含むので `gz` 平均 4.49）。
- 相対リンク: 6 ファイルの相対リンクは全部実在のファイルを指す。04〜07 章へのリンクはもともと無い（章番号の文字だけ）。
- `uv run pytest`: 下のコミット時に実行（文書だけの変更）。
- セッション記録の `--check`・漏洩検査: 実行していない（統合担当に任せる）。

## 確かめていないこと・残したこと

申し送り（直していない食い違い）:

- コード側: `link.encode_command` は NaN を拒否せず、`min(1, max(-1, nan))` で -1 にして送る（Python で確認）。XIAO 側の `isfinite` は効かず、-0.6 で逆転する。NaN を 0 か停止にすべき。
- コード側: スケッチ冒頭と `PIN_*` のコメントが DRV8833 のまま（調査の第一候補は DRV8835。IN/IN の駆動なので結線の意味は同じだが、DRV8835 は MODE ピンを IN/IN 側にする必要がある）。
- コード側: スケッチは IMU の範囲を設定せず ±2000 dps / ±16 g。小さな車には粗いので ±500 dps 程度を検討。
- 残った未確認: TR-C のデータシートでの角速度範囲の表記（±245 / ±250）、温度が落ち着くまでの待ち時間（02 章）、00 章の NVIDIA 記事 2・3 の本文。
