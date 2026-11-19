"""章に貼った「実際に走らせた出力」を走らせ直して比べる（数値を動かす作業の最後に手で回す。pytest には入れない）。

    uv run python -m physlearn.docs_check [章のファイル ...] [--mujoco]

対象の書き方（章のコードブロックの形）:
  (i)  `$ ` で始まる行から始まるブロック: `$ ` の行がコマンド、次の `$ ` の行かブロックの終わりまでが期待する出力。
       引用符が閉じるまでを 1 つのコマンドとする（複数行の python -c）。
  (ii) ```bash / ```sh のブロックの `uv run` で始まる行がコマンド。直後（間に見出し・空行・「…:」で終わる行だけ）の
       言語指定なしのブロックが期待する出力。言語指定が `text` のブロックは「抜粋」で、行を順に含んでいれば一致とする。
飛ばす: ブロックの直前に `<!-- docs_check: skip 理由 -->`。印が無くても `--port`・`fakexiao`・`pytest` は飛ばし、
       それが書くファイルを読む後続のコマンドも飛ばす。`--extra mujoco` は `--mujoco` のときだけ走らせる。
比較: 数字は期待の最後の桁の半分 + 1e-9 以内で一致、数字以外は完全一致、`...` を含む期待の行は飛ばす、空行は無視。
"""

import argparse
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from itertools import zip_longest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGETS = [*(sorted(ROOT.glob(f"doc/textbook/{n}-*.md"))[0] for n in
             ("04", "05", "06", "07", "08", "11", "12", "13", "14", "15", "16")),
           ROOT / "doc/textbook/solutions.md", ROOT / "README.md", ROOT / "doc/bringup.md"]
NUM = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
SKIP_MARK = re.compile(r"<!--\s*docs_check:\s*skip\b(.*?)-->")


@dataclass
class Unit:
    line: int            # コマンドの先頭行（ファイル内、1 始まり）
    cmds: list
    expected: list       # None なら期待する出力が無い（準備のコマンド。走らせるだけ）
    excerpt: bool = False
    skip: str = None


def _commands(lines):
    """行の並びから、引用符が閉じるまでを 1 つにしたコマンドを (先頭の添字, 文字列, 次の添字) で返す。"""
    i = 0
    while i < len(lines):
        cmd, j = lines[i], i + 1
        while True:
            try:
                shlex.split(cmd)
                break
            except ValueError:
                if j >= len(lines):
                    break
                cmd += "\n" + lines[j]
                j += 1
        yield i, cmd, j
        i = j


def extract(text):
    """Markdown の文字列から Unit の一覧を作る。"""
    lines = text.split("\n")
    blocks, i = [], 0  # (開きの添字, 言語, 中身, 閉じの添字, 飛ばす理由)
    while i < len(lines):
        m = re.match(r"\s*```(\w*)\s*$", lines[i])
        if not m:
            i += 1
            continue
        j = i + 1
        while j < len(lines) and not lines[j].lstrip().startswith("```"):
            j += 1
        k = i - 1
        while k >= 0 and not lines[k].strip():
            k -= 1
        s = SKIP_MARK.search(lines[k]) if k >= 0 else None
        blocks.append((i, m.group(1), lines[i + 1:j], j, s and (s.group(1).strip() or "理由なし")))
        i = j + 1
    units = []
    for n, (start, lang, body, end, skip) in enumerate(blocks):
        first = next((l for l in body if l.strip()), "")
        if lang in ("", "text") and first.startswith("$ "):  # (i)
            cmds = [(a, c[2:] if c.startswith("$ ") else None, j) for a, c, j in _commands(body)]
            starts = [a for a, c, _ in cmds if c is not None]
            for a, c, j in cmds:
                if c is None:
                    continue
                nxt = next((b for b in starts if b > a), len(body))
                units.append(Unit(start + 2 + a, [c], body[j:nxt], skip=skip))
        elif lang in ("bash", "sh"):  # (ii)
            cmds = [(a, c) for a, c, _ in _commands(body) if c.startswith("uv run")]
            if not cmds:
                continue
            exp, excerpt = None, False
            if n + 1 < len(blocks):
                s2, l2, b2, _, _ = blocks[n + 1]
                between = lines[end + 1:s2]
                f2 = next((l for l in b2 if l.strip()), "")
                if l2 in ("", "text") and not f2.startswith("$ ") and all(
                        not l.strip() or l.startswith("#") or l.rstrip().endswith((":", "：")) for l in between):
                    exp, excerpt = b2, l2 == "text"
            units.append(Unit(start + 2 + cmds[0][0], [c for _, c in cmds], exp, excerpt, skip))
    return units


def same(exp, act):
    if "..." in exp:
        return True
    if NUM.split(exp) != NUM.split(act):
        return False
    e, a = NUM.findall(exp), NUM.findall(act)
    if len(e) != len(a):
        return False
    for x, y in zip(e, a):
        mant, _, ex = x.lower().partition("e")
        dec = len(mant.split(".")[1]) if "." in mant else 0
        if abs(float(x) - float(y)) > 10 ** (int(ex or 0) - dec) / 2 + 1e-9:
            return False
    return True


def compare(expected, actual, excerpt=False):
    """一致なら None、食い違えば最初の (期待の行, 実際の行)。"""
    exp = [l.rstrip() for l in expected if l.strip()]
    act = [l.rstrip() for l in actual if l.strip()]
    if excerpt:  # shortcut: 抜粋は順序つきの部分列で見る。行の途中の省略には対応しない
        i = 0
        for e in exp:
            while i < len(act) and not same(e, act[i]):
                i += 1
            if i == len(act):
                return e, "(見つからない)"
            i += 1
        return None
    for e, a in zip_longest(exp, act):
        if e is None or a is None or not same(e, a):
            return e or "(なし)", a or "(なし)"
    return None


def auto_skip(cmd, mujoco):
    if "--port" in cmd or "fakexiao" in cmd:
        return "擬似端末かポートが要る"
    if re.search(r"\bpytest\b", cmd):
        return "試験は回さない"
    if "--extra mujoco" in cmd and not mujoco:
        return "mujoco なし"


def run_file(path, mujoco):
    """[(行, 先頭行の文字列, 結果, 詳細)] を返す。"""
    rows, missing = [], set()  # missing: 飛ばしたコマンドが書くはずのファイル
    env = {**os.environ, "PYTHONHASHSEED": "0"}
    with tempfile.TemporaryDirectory() as d:
        for u in extract(Path(path).read_text()):
            out, why, ran, head = [], None, False, u.cmds[0].split("\n")[0]
            for cmd in u.cmds:
                toks = cmd.split()
                r = u.skip or auto_skip(cmd, mujoco) or ("前のコマンドを飛ばした" if missing & set(toks) else None)
                if r:
                    why = why or r
                    missing |= {t for t in toks if re.fullmatch(r"[\w./-]+\.(csv|json)", t) and not (Path(d) / t).exists()}
                    continue
                if cmd.startswith("uv run"):
                    cmd = f"uv run --quiet --project {shlex.quote(str(ROOT))}" + cmd[len("uv run"):]
                p = subprocess.run(cmd, shell=True, cwd=d, env=env, text=True, capture_output=True, timeout=900)
                if p.returncode and "FileNotFoundError" in p.stderr:  # 章の中に入力ファイルを作る手順が無い
                    why = why or "入力ファイルが無い"
                    continue
                out += (p.stdout + p.stderr).split("\n")
                head = head if ran else cmd.split("\n")[0].replace(f" --quiet --project {shlex.quote(str(ROOT))}", "")
                ran = True
            if u.expected is None:
                continue
            if not ran:
                rows.append((u.line, head, "飛ばした", why))
                continue
            diff = compare(u.expected, out, u.excerpt)
            rows.append((u.line, head, "一致" if diff is None else "差", diff))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="*", help="章のファイル（無ければ対象の章すべて）")
    ap.add_argument("--mujoco", action="store_true", help="`--extra mujoco` のブロックも走らせる")
    a = ap.parse_args(argv)
    files = [Path(f) for f in a.files] or TARGETS
    n_diff, summary = 0, []
    for f in files:
        t0 = time.time()
        rows = run_file(f, a.mujoco)
        for line, head, res, detail in rows:
            label = f"{res}（{detail}）" if res == "飛ばした" else res
            print(f"{f.name}:{line}\t{label}\t{head[:70]}")
            if res == "差":
                print(f"    期待: {detail[0]}\n    実際: {detail[1]}")
        c = [sum(r[2] == k for r in rows) for k in ("一致", "差", "飛ばした")]
        n_diff += c[1]
        summary.append(f"{f.name}\t一致 {c[0]}\t差 {c[1]}\t飛ばした {c[2]}\t{time.time() - t0:.1f} s")
    print("\n" + "\n".join(summary))
    return 1 if n_diff else 0


if __name__ == "__main__":
    sys.exit(main())
