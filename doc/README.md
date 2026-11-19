# doc/ の案内

| 場所 | 中身 |
| --- | --- |
| [plan/](plan/2026-11-19-plan.md) | 計画。セッションの一覧、決まったこと、次にやること。展望は [outlook](plan/2026-11-19-outlook.md)、夜の展望と発注者の決定の一覧は [outlook-evening](plan/2026-11-19-outlook-evening.md) |
| [shopping-list.md](shopping-list.md) | 発注リスト。店ごとの品番・価格・在庫、買い方 (A)(B)(C) の合計。車体は Robo Base ミニキット 2WD（寸法は未確認） |
| [bringup.md](bringup.md) | 実機の立ち上げ手順書（机上で作成、実機では未確認） |
| [troubleshooting.md](troubleshooting.md) | つまずき集。症状から原因・確かめ方・直し方を引く |
| [setup.md](setup.md) | 環境構築の手引き（WSL2・arduino-cli・USB） |
| [cad-mcp.md](cad-mcp.md) | SolidCraft（ブラウザー版・CLI・MCP）で `cad/` の筐体を設計する手引き。CLI は動かした、GUI とブラウザー版は未実行 |
| [research/](research/) | 調査の記録（ハードウェア・ソフトウェア・SolidCraft・寸法・エンコーダー・無線化・車体の代案）。事実ごとに出典 URL と取得時刻 |
| [adr/](adr/0001-sim-stack.md) | 設計判断。0001 は sim の構成（numpy 必須・MuJoCo 任意・Isaac Sim は手引きだけ） |
| [protocol.md](protocol.md) | XIAO と PC のシリアルの取り決め |
| [textbook/](textbook/README.md) | 教材。索引から読む。図は [textbook/fig/](textbook/fig/README.md) |
| `physical_ai_isaacsim_poc_ja.md` ほか | 出発点にした 2026-10-22 時点の PoC 設計書とスライド（参考資料。いまの計画とは違う所がある） |

CI は GitHub Actions: [.github/workflows/ci.yml](../.github/workflows/ci.yml)（試験・スケッチのコンパイル 2 種・章の出力の検査 `docs`）と [.github/workflows/cad.yml](../.github/workflows/cad.yml)（`cad/` の設計データの検査）。
ライセンスは [../LICENSE.md](../LICENSE.md)（コードは MIT OR Apache-2.0、文章と図は CC BY 4.0）。
