"""TASK-012: traceable local documentation and automated coverage inventory."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / ".github/futuristic/d40bbe8d-773b-4cba-a51e-cab7ab35cbc4/tests.json"


def test_tc_017_readme_documents_local_setup_and_prototype_limits() -> None:
    """TC-017: documentation must retain the local-only and volatile-state warnings."""
    readme = (ROOT / "README.md").read_text()
    for required in (
        "uv sync --locked --python 3.12",
        "uv run --locked --python 3.12 flask",
        "uv run --locked --python 3.12 python -m compileall -q src tests",
        "uv run --locked --python 3.12 pytest -q",
        "uv run --locked --python 3.12 ruff check .",
        "uv run --locked --python 3.12 ruff format --check .",
        "PASSWORD_RESET_SESSION_SECRET",
        "owner@example.test",
        "peer@example.test",
        "owner_link_outbox",
        "owner-notification sink",
        "Restart",
        "Multiple workers",
        "No real",
        "not production-ready",
    ):
        assert required in readme, f"README missing {required}"
    assert "Session revocation and owner notices are not yet implemented" not in readme
    assert "is production-ready" not in readme


def test_tc_016_all_automated_case_references_collect_under_python_312() -> None:
    """TC-016: inspect actual pytest collection; full execution is the pytest gate."""
    assert sys.version_info[:2] == (3, 12)
    data = json.loads(INVENTORY.read_text())
    assert set(data) == {"schema_version", "test_cases"}
    assert data["schema_version"] == "1.0"
    cases = data["test_cases"]
    assert [case["id"] for case in cases] == [
        f"TC-{number:03d}" for number in range(1, 26)
    ]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    nodes = {line.strip() for line in result.stdout.splitlines() if "::" in line}
    for case in cases:
        if case["status"] == "manual":
            assert set(case) == {"id", "status", "reason"}
            assert case["reason"].strip()
            continue
        assert case["status"] == "automated"
        assert set(case) == {"id", "status", "reference"}
        node = case["reference"]
        assert node.startswith("tests/") and node in nodes, node
        assert case["id"].lower().replace("-", "_") in node.lower(), node
