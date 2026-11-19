"""教材・文書の相対リンク `[..](path)` と画像 `![..](path)` が、実在のファイルを指すことを確かめる。

対象は、リポジトリ内の `.md`。除くもの:
  - `log/sessions/`（会話記録の写し）、`log/work/2026-*`・`log/review/2026-*`（その時点の記録。後で動いたファイルを指していてよい）
  - `.git-worktree/`・`.venv/` など作業用の場所
見ないもの: `http(s):`・`mailto:` などの URL、`#` だけのリンク、コードブロックと `コード` の中。`path#anchor` は `path` の存在だけ見る。
"""

import os
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".git-worktree", ".venv", "node_modules", "__pycache__", "sessions", "cad-out"}
SKIP_RECORDS = re.compile(r"^log/(work|review)/2026-")
LINK = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^)]*)?\)")
CODE_SPAN = re.compile(r"`[^`\n]*`")
URL = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")  # http: https: mailto: など


def _md_files():
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            p = Path(d) / f
            rel = p.relative_to(ROOT).as_posix()
            if f.endswith(".md") and not SKIP_RECORDS.match(rel):
                yield p


def broken_links():
    bad = []
    for md in _md_files():
        fence = None
        for n, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            m = re.match(r"\s*(`{3,}|~{3,})", line)
            if m:
                fence = None if fence and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) else (fence or m.group(1))
                continue
            if fence:
                continue
            for target in LINK.findall(CODE_SPAN.sub("", line)):
                path = unquote(target.split("#", 1)[0])
                if not path or URL.match(target):
                    continue
                base = ROOT if path.startswith("/") else md.parent
                if not (base / path.lstrip("/")).exists():
                    bad.append(f"{md.relative_to(ROOT)}:{n}: {target}")
    return bad


def test_relative_links_exist():
    bad = broken_links()
    assert not bad, f"切れた相対リンク {len(bad)} 件:\n" + "\n".join(bad)
