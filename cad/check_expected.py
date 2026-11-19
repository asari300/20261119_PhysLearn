"""check.sh の後半: 出力フォルダの結果を cad/expected.csv と比べる。落ちたら食い違いを全部出して終了コード 1。"""

import csv
import json
import importlib.util
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
# パッケージ経由だと __init__ が numpy を要る。標準ライブラリだけの 1 ファイルなので、パスで読む
spec = importlib.util.spec_from_file_location("solidcraft_props", root / "src" / "physlearn" / "solidcraft_props.py")
props = importlib.util.module_from_spec(spec)
sys.modules["solidcraft_props"] = props  # dataclass が要る
spec.loader.exec_module(props)
from_mass_json = props.from_mass_json

out = Path(sys.argv[1])
bad = []
for row in csv.DictReader((root / "cad" / "expected.csv").open(encoding="utf-8")):
    n = row["file"].removesuffix(".json")
    tol = float(row["rel_tol"])
    total = json.loads((out / f"{n}.json").read_text())["total"]
    p = from_mass_json(json.loads((out / f"{n}.mass.json").read_text()))
    got = {"volume_mm3": total["volume_mm3"], "mass_g": total["mass_g"], "izz_kg_m2": p.izz}
    step = (out / f"{n}.step").read_bytes()
    if not step.startswith(b"ISO-10303-21") or len(step) < 1000:
        bad.append(f"{n}: STEP が壊れている（{len(step)} バイト）")
    for k, v in got.items():
        want = float(row[k])
        ok = abs(v - want) <= tol * abs(want)
        print(f"{'ok ' if ok else 'NG '} {n:12s} {k:11s} 得た {v:.6g}  期待 {want:.6g}  許容 {tol:.0e}")
        if not ok:
            bad.append(f"{n}: {k} 得た {v:.6g} 期待 {want:.6g}")
if bad:
    print("\n".join(["", "食い違い（パラメーターを変えたなら cad/expected.csv も直す）:", *bad]))
    sys.exit(1)
