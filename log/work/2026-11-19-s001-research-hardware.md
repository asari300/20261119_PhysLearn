# S001 research-hardware 作業記録（2026-11-19）

時間: JST 13:34 開始、13:4x コミット。成果物: `doc/research/2026-11-19-hardware.md`。

## 決めたこと

- 第一候補 XIAO nRF52840 Sense、次点 XIAO MG24 Sense、在庫の保険 XIAO nRF54L15 Sense。
- モータードライバーは DRV8835（秋月 AE-DRV8835-S）を MODE=GND で IN/IN に。DRV8833 は秋月に無かった。
- 車体は Cytron Robo Base キット 2WD（スイッチサイエンス）。タミヤのギヤボックスは秋月で入荷未定。
- BOM: (A) 3,155 円、(B) 7,851 円 ＋ 電池。

## 根拠（取得 13:35〜13:40）

- Seeed の XIAO 比較表で IMU があるのは nRF52840 / MG24 / nRF54L15 / nRF54LM20A の Sense だけ。ESP32 系は無し。
- nRF52840 Sense の IMU 電源と Wire1 のピンは Seeed の variant.h で確認。
- MG24 Sense の IMU は LSM6DS3TR-C、0x6A、PD5 で電源（wiki で確認）。
- 秋月の在庫・価格・技適番号は商品ページで確認。
- DRV8835 の MODE=LOW が IN/IN なのは Pololu のページで確認。

## 確かめていないこと

- スイッチサイエンスのページ直読（429）。Sense Plus と Robo Base の在庫は検索抜粋だけ。
- マルツ・千石・Amazon・Seeed 日本向け。TB6612FNG。電池とコンデンサの価格。
- nRF52840 Sense の I2C アドレス（0x6A と推測）、ライブラリが IMU 電源を自分で上げるか。
- nRF52840 の analogWrite の周波数・分解能。DRV8835 と DRV8833 の真理値表が同じこと（記憶）。
- nRF54L15 Sense を Arduino から使って IMU を読めるか。

## S005 への影響

- ボードの前提はそのまま。ただし秋月の残り 9 個・スイッチサイエンス売り切れで、入手が細い。
- ドライバーは DRV8833 ではなく DRV8835 になる。IN/IN の 4 本 PWM の考え方は同じ（MODE を GND）。
