import os
import subprocess
import sys
from pathlib import Path

import pytest
from webex_test_caller.plan import load_plan


@pytest.mark.parametrize("test_id", ["request-response", "dtmf-menu"])
def test_generic_plan_runs_without_gateway_evidence(test_id: str) -> None:
    root = Path(__file__).resolve().parents[1]
    plan = load_plan(root / "config/contact-center.spec.json")
    selected_test = next(test for test in plan.tests if test.test_id == test_id)

    assert selected_test.require_gateway_events is False


def test_installed_cli_validates_from_outside_checkout(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "webex_test_caller",
            "validate",
            "--config",
            str(root / "config/contact-center.spec.json"),
            "--list",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert "request-response:" in result.stdout
    assert "dtmf-menu:" in result.stdout
