import pathlib
import shutil
import tempfile

from physlearn.docs_check import auto_skip, compare, extract, run_file, same, shell_op, strip_comment, unsafe

I = '''text
<!-- docs_check: skip 長いので -->
```
$ uv run python -c "
print(1)
"
1
$ uv run physlearn x a.csv
a.csv: 3 行
```
```
$ echo hi
hi
```
'''

II = '''```bash
uv run python -m foo   # 注釈
uv run pytest
```

### 出力

説明:

```
結果 1.50
```

```bash
uv run bar
```

別の説明の文。

```
関係のない図
```
'''


def test_extract_dollar_blocks():
    u = extract(I)
    assert [(x.line, x.cmds, x.expected, x.skip) for x in u] == [
        (4, ['uv run python -c "\nprint(1)\n"'], ["1"], "長いので"),
        (8, ["uv run physlearn x a.csv"], ["a.csv: 3 行"], "長いので"),
        (12, ["echo hi"], ["hi"], None)]


def test_extract_bash_blocks_pair_with_next_plain_block_only():
    u = extract(II)
    assert u[0].cmds == ["uv run python -m foo   # 注釈", "uv run pytest"] and u[0].expected == ["結果 1.50"]
    assert u[1].cmds == ["uv run bar"] and u[1].expected is None  # 間に説明の文があれば組にしない


def test_same_uses_last_printed_digit():
    assert same("x 0.0804 y", "x 0.08044 y") and not same("x 0.0804 y", "x 0.0810 y")
    assert not same("K 12", "K 12.7") and same("5.831e-04", "5.8314e-04")
    assert not same("OK 1", "NG 1") and not same("1 2", "1")


def test_compare_ellipsis_blank_and_excerpt():
    assert compare(["a 1", "", "b ... c"], ["a 1.0", "b zzz c"]) is None
    assert compare(["a 1", "b"], ["a 1"]) == ("b", "(なし)")
    assert compare(["a 1", "c"], ["a 1", "b", "c"], excerpt=True) is None
    assert compare(["c", "a 1"], ["a 1", "c"], excerpt=True) == ("a 1", "(見つからない)")


def test_empty_excerpt_is_a_diff_not_a_match(tmp_path):
    assert compare([], ["a"], excerpt=True) and compare(["", "..."], ["a"], excerpt=True)
    assert compare(["a ..."], ["a 1"], excerpt=True) is None  # ... を含む行が 1 つでも実のある行なら従来どおり
    md = tmp_path / "c.md"
    md.write_text("<!-- docs_check: output uv run python -c \"print('a 1')\" -->\n```\n```\n\n"
                  "<!-- docs_check: output uv run python -c \"print('a 1')\" -->\n```\n...\n```\n")
    assert [r[2] for r in run_file(md, False)] == ["差", "差"]


def test_auto_skip():
    assert auto_skip("uv run python -m physlearn.link id --port /dev/pts/1", False)
    assert auto_skip("uv run --extra mujoco physlearn x", False) and not auto_skip("uv run --extra mujoco physlearn x", True)
    assert auto_skip("uv run physlearn loop-demo", False) is None


def test_integers_must_match_exactly_but_decimals_keep_their_tolerance():
    assert not same("n 12", "n 12.4") and not same("n 3", "n 3.2") and same("n 12", "n 12.0") and same("n 12", "n 12")
    assert same("x 0.12", "x 0.1204") and same("x 1e-3", "x 0.0012")  # 小数・指数の許容は従来どおり


def test_shell_operators_are_detected_only_outside_quotes():
    assert shell_op("uv run x | head -3") == "|" and shell_op("uv run x; rm a") == ";"
    assert shell_op("uv run x > out") == ">" and shell_op("uv run x $(id)") == "$" and shell_op("uv run x `id`") == "`"
    assert shell_op('uv run python -c "print(1 > 0); x = 2"') is None  # 引用符の中は記号ではない
    assert shell_op("uv run python -c 'print(\"$(x)\")'") is None
    assert shell_op('uv run python -c "print(1)"  # 注釈') is None


def test_strict_skips_commands_other_than_uv_run():
    assert unsafe("echo hi") == "uv run 以外" and unsafe("cat a | head") == "uv run 以外"
    assert unsafe("uv run physlearn sysid a.csv") is None


def test_shell_operators_are_skipped_and_not_run():
    d = pathlib.Path(tempfile.mkdtemp(prefix="s130-"))  # 名前に pytest が入ると auto_skip（試験は回さない）に当たる
    try:
        pwned = d / "pwned"
        md = d / "c.md"
        md.write_text(f'```\n$ uv run python -c "print(1)" > {pwned}\n1\n'
                      f'$ uv run python -c "print(1)" | head -1\n1\n```\n')
        r = run_file(md, False)
        assert [x[2] for x in r] == ["飛ばした", "飛ばした"]
        assert all("シェルの記号" in x[3] for x in r) and not pwned.exists()
    finally:
        shutil.rmtree(d)


def test_comment_at_the_end_of_a_command_is_dropped(tmp_path):
    assert strip_comment("uv run x a#b # c") == "uv run x a#b "  # 語の途中の # は残す（シェルと同じ）
    assert strip_comment('uv run python -c "print(\'# x\')"') == 'uv run python -c "print(\'# x\')"'
    md = tmp_path / "c.md"
    md.write_text('```\n$ uv run python -c "print(1)"  # 注釈\n1\n```\n')
    assert [x[2] for x in run_file(md, False)] == ["一致"]


def test_plain_commands_still_run_without_a_shell(tmp_path):
    md = tmp_path / "c.md"
    md.write_text('```\n$ uv run python -c "open(\'a.csv\', \'w\').write(\'1\\n2\\n\')"\n'
                  "$ head -1 a.csv\n1\n```\n")
    assert [x[2] for x in run_file(md, False)] == ["一致", "一致"]


def test_strict_flags_nonzero_exit_and_missing_file(tmp_path):
    md = tmp_path / "c.md"
    md.write_text(
        "```\n$ uv run python -c \"print(0.12); raise SystemExit(3)\"\n0.12\n```\n\n"
        "```\n$ uv run python -c \"open('nope.csv')\"\nok\n```\n"
    )
    assert [r[2] for r in run_file(md, False)] == ["一致", "飛ばした"]  # 従来の判定（誤りを含む）は既定のまま
    r = run_file(md, False, strict=True)
    assert r[0][2] == "差" and "終了コード 3" in r[0][3][1]
    assert r[1][2] == "差"  # 飛ばしたコマンドの出力でない FileNotFoundError は本物のバグ


def test_output_directive_checks_fragments_as_excerpts_and_runs_the_command_once(tmp_path):
    md = tmp_path / "c.md"
    md.write_text(
        "<!-- docs_check: output uv run python -c \"import time; print('a 1'); print('b 2'); print('c 3', time.time() > 0)\" -->\n"
        "```\na 1\nc 3 True\n```\n\n"
        "<!-- docs_check: output uv run python -c \"import time; print('a 1'); print('b 2'); print('c 3', time.time() > 0)\" -->\n"
        "```\nb 9\n```\n"
    )
    u = extract(md.read_text())
    assert [(x.excerpt, x.expected) for x in u] == [(True, ["a 1", "c 3 True"]), (True, ["b 9"])]
    assert [r[2] for r in run_file(md, False)] == ["一致", "差"]


def test_commands_that_need_mujoco_are_skipped_without_it(tmp_path):
    assert auto_skip("uv run physlearn loop-demo --real mujoco", False) and auto_skip("uv run physlearn sim-log --plant=mujoco a.csv", False)
    assert not auto_skip("uv run physlearn loop-demo --real mujoco", True)
    md = tmp_path / "c.md"
    md.write_text("```\n$ uv run python -c \"import mujoco_nowhere\"\n1\n$ uv run python -c \"import sys; sys.stderr.write(\\\"No module named 'mujoco'\\\")\"\n1\n```\n")
    r = run_file(md, False)
    assert [x[2] for x in r] == ["差", "飛ばした"] and r[1][3] == "mujoco なし"
    md.write_text("```\n$ uv run python -c \"raise SystemExit('mujoco が入っていない。x')\"\n1\n```\n")
    assert run_file(md, False)[0][2] == "飛ばした"


def test_chapters_keep_their_checked_blocks():
    """章ごとの「比べる対象」の数。文を直して出力のブロックがコマンドから外れると（行末の「:」を「。」にするなど）、
    差は 0 のまま黙って減る。数を変えたら、意図したものか確かめてここを直す。"""
    from physlearn.docs_check import TARGETS

    n = {f.name: sum(u.expected is not None for u in extract(f.read_text())) for f in TARGETS}
    assert n == {"04-sim.md": 1, "05-real2sim.md": 10, "06-sim2real.md": 7, "07-loop.md": 5, "08-mujoco.md": 1,
                 "11-imu-lab.md": 3, "12-fake-xiao.md": 5, "13-motor-physics.md": 4, "14-fit-check.md": 6,
                 "15-mismatch.md": 7, "16-enclosure.md": 1, "solutions.md": 5, "README.md": 1, "bringup.md": 0}
