# 作業記録 S002 research-software（2026-11-19）

- ブランチ: `feature/s002-research-software`
- 作業時間: JST 13:34〜13:40 ごろ

## 決めたこと

- 計画どおり「sim は numpy 必須・MuJoCo 任意・Isaac Sim は手引きだけ」を ADR 0001 に採用として書いた。

## 根拠

- Isaac Sim 6.2 の最小要件は RTX 4080 (VRAM 16GB)・RAM 32GB。この PC は GPU 無し・RAM 7 GiB・WSL2。
- MuJoCo 4.0.1 は CPU で動き、この PC で動作を確かめた。
- MJX / MuJoCo Warp / Newton / Isaac Lab は GPU 前提で、単一の小さな sim には向かない。

## 確かめたこと（この PC で実行）

- `which nvidia-smi` → 無し。`free -g` → 7 GiB。`nproc` → 16。Python 3.12.14、numpy 2.5.5。
- `uv run --extra mujoco` で mujoco 4.0.1 を入れて import、10,000 step を 0.038 秒。uv.lock は変わらなかった。

## 確かめていないこと

- 文書の出典は WebFetch / WebSearch の要約経由で、原文を全部読んではいない。
- Isaac Sim 6.3 の有無・公開日、ライセンスの細目、AWS の単価、Brev での Isaac Sim の実費。
- Genesis・LeRobot・MuJoCo Playground の版の一次確認。Genesis の CPU 動作。
- micro-ROS の XIAO 対応（公式表に XIAO は無い）。
- MuJoCo の描画（viewer / Studio）が WSL2 で動くか。
- 手引き（90 章）の手順と API 名は一切実行していない。

## 発注者の参考リンク

- ChatGPT の共有リンクは 13:35 JST に 1 回 WebFetch したが、本文は読めなかった。
