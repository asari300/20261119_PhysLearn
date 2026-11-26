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
