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
