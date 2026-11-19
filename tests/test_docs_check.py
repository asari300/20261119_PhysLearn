from physlearn.docs_check import auto_skip, compare, extract, same

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
