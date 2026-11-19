from physlearn.docs_check import auto_skip, compare, extract, run_file, same, unsafe

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


def test_auto_skip():
    assert auto_skip("uv run python -m physlearn.link id --port /dev/pts/1", False)
    assert auto_skip("uv run --extra mujoco physlearn x", False) and not auto_skip("uv run --extra mujoco physlearn x", True)
    assert auto_skip("uv run physlearn loop-demo", False) is None


def test_integers_must_match_exactly_but_decimals_keep_their_tolerance():
    assert not same("n 12", "n 12.4") and not same("n 3", "n 3.2") and same("n 12", "n 12.0") and same("n 12", "n 12")
    assert same("x 0.12", "x 0.1204") and same("x 1e-3", "x 0.0012")  # 小数・指数の許容は従来どおり


def test_unsafe_commands_for_strict_mode():
    assert unsafe("echo hi") == "uv run 以外" and unsafe("cat a | head") == "uv run 以外"
    for bad in ("uv run x; rm a", "uv run x && y", "uv run x > out", "uv run x $(id)", "uv run x `id`"):
        assert unsafe(bad), bad
    for ok in ('uv run python -c "print(1 > 0); x = 2"', "uv run physlearn sysid a.csv", "uv run x | head -3", "uv run python -c 'print(\"$(x)\")'"):
        assert unsafe(ok) is None, ok


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
