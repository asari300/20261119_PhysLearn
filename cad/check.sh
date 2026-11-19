#!/usr/bin/env bash
# cad/expected.csv の各スクリプトを solidcraft-cli で STEP にし、体積・質量・Izz を表と比べる（CI と手元で同じ）。
# 使い方: cad/check.sh [出力フォルダ]   solidcraft-cli は PATH に置く（CI では展開した bin/ を PATH に足す）
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=${1:-cad-out}
mkdir -p "$OUT"
solidcraft-cli --version
tail -n +2 cad/expected.csv | cut -d, -f1 | while read -r script; do
  n=${script%.json}
  # --param-check strict: 引数が各コマンドの契約に合わなければ止まる。--out の STEP は成功しないと書かれない
  solidcraft-cli run "cad/$script" --param-check strict --save "$OUT/$n.sc" --out "$OUT/$n.step" --json-out "$OUT/$n.json"
  solidcraft-cli run cad/plate_mass.json --in "$OUT/$n.sc" --results --json-out "$OUT/$n.mass.json" > /dev/null
done
python3 cad/check_expected.py "$OUT"
