"""セッション記録フックの伏せ字。切り詰めの境目をまたぐ文字列が漏れないこと（S119 の指摘 1）。"""
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "save_session_log.py"
_spec = importlib.util.spec_from_file_location("save_session_log", _PATH)
hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook)


def _clipped(monkeypatch, secret, fragment):
    monkeypatch.setattr(hook, "_local_names", lambda: {"alicewonder"})
    n = hook.MAX_RESULT_CHARS
    body = "x" * (n - len(fragment)) + secret + " tail" + "y" * 50   # secret が n 字目をまたぐ
    return hook.redact(hook.clip(body, n))


def test_email_across_clip_boundary(monkeypatch):
    out = _clipped(monkeypatch, "foo.bar@example.com", "foo.bar@exam")
    assert "foo.bar" not in out and "@exam" not in out


def test_username_across_clip_boundary(monkeypatch):
    out = _clipped(monkeypatch, "-home-alicewonder-proj", "-home-alice")
    assert "alice" not in out and "wonder" not in out


def test_clip_long_alnum_run_is_fast():
    """切る前の全文に redact を通すと、英数字の連なりで 2 乗の時間（8 万字で 24 秒）になった（S126 #2）。"""
    import time
    n = hook.MAX_RESULT_CHARS
    t = time.perf_counter()
    out = hook.clip("a" * 80_000, n)
    assert time.perf_counter() - t < 2
    assert out.startswith("a" * n) and "残り 79,200 字" in out     # 残りは元の長さから数える


def test_local_names_is_cached():
    """redact の呼び出しごとに /mnt/c/Users を読み直さない（S126 #1）。"""
    hook._local_names.cache_clear()
    hook.redact("x")
    hook.redact("y")
    assert hook._local_names.cache_info().hits >= 1


def test_local_name_is_case_insensitive(monkeypatch):
    """名前の大文字小文字を変えても伏せ字になり、--check にも当たる（S126 #5c）。"""
    monkeypatch.setattr(hook, "_local_names", lambda: {"foobar"})
    assert "FooBar" not in hook.redact("FooBar and FOOBAR wrote this")
    assert hook.leftovers("Dear FOOBAR") == ["foobar"]


def test_no_fragment_when_redaction_shrinks_the_window(monkeypatch):
    """絶対パスの並びで窓が大きく縮むと、窓の末尾の切れたメールが [:n] の中に入った（S127）。"""
    monkeypatch.setattr(hook, "_local_names", lambda: {"alicewonder"})
    n = hook.MAX_RESULT_CHARS
    head = "/home/someuser1234567890/proj/src/a.py\n" * 26
    raw = (head + "x" * 200)[: n + 256 - 12] + "taro.yamada@example.com" + " tail " * 100   # メールが n+256 字目をまたぐ
    out = hook.clip(raw, n)
    assert "taro.yamada" not in out and "@" not in out.split("\n… （残り")[0]


def test_token_longer_than_the_margin_across_the_boundary():
    """窓（1824 字）より長いトークンが n 字目をまたいでも、窓に入った頭 36 字以上でトークンの規則に掛かる。"""
    n = hook.MAX_RESULT_CHARS
    for start in (n - 20, n + 256 - 20):
        out = hook.clip("x" * start + " ghp_" + "A" * 3000 + " tail", n)
        assert "ghp_A" not in out and "AAAA" not in out, start


def test_token_after_a_word_character_is_redacted():
    """トークンの規則に頭の \\b を付けていたので、直前が語の文字（`x`・`KEY_`・`token`）だと掛からなかった（S129、問題 34）。"""
    for tok in ("ghp_" + "A" * 36, "sk-" + "A" * 30, "AKIA" + "A" * 16, "xoxb-" + "1" * 12):
        for text in (tok, "x" + tok, "KEY_" + tok, "token" + tok):
            assert tok not in hook.redact(text), text
            assert hook.leftovers(text) == [tok], text
    assert "AKIA" + "A" * 17 in hook.redact("AKIA" + "A" * 17)       # 末尾の \b は残す（長い大文字の連なりは鍵ではない）
