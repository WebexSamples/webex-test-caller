import json
import stat
from datetime import datetime, timezone
from types import SimpleNamespace

from webex_test_caller.artifacts import redact_destination, write_artifact


def test_redact_destination_preserves_only_suffix() -> None:
    assert redact_destination("tel:+15551234567") == "***4567"
    assert redact_destination("9999") == "***"


def test_artifacts_do_not_overwrite_results_in_the_same_second(tmp_path, monkeypatch):
    frozen = datetime(2026, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(
        "webex_test_caller.artifacts.datetime", SimpleNamespace(now=lambda _tz: frozen)
    )

    first = write_artifact(tmp_path, {"status": "completed"})
    second = write_artifact(tmp_path, {"status": "failed"})

    assert first != second
    assert json.loads(first.read_text()) == {"status": "completed"}
    assert json.loads(second.read_text()) == {"status": "failed"}
    assert stat.S_IMODE(first.stat().st_mode) == 0o600
