from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pytest

from experiments.evidence_manifest import build_run_manifest, write_manifest


def _manifest_kwargs(**overrides):
    kwargs = {
        "run_id": "w3w4-dry-001",
        "lane": "causal",
        "mode": "dry-run",
        "command": ["python", "experiments/w3w4_causal_calibration.py", "--dry-run"],
        "config": {"max_iterations": 3, "eval_size": 5},
        "metrics": {
            "initial_loss": 0.30,
            "best_loss": 0.25,
            "final_loss": 0.27,
            "n_iterations": 3,
        },
        "artifacts": {"result_json": "experiments/results/w3w4_calibration_result.json"},
        "notes": ["dry-run uses mocked LLM responses"],
    }
    kwargs.update(overrides)
    return kwargs


def test_build_run_manifest_records_required_fields(tmp_path):
    manifest = build_run_manifest(**_manifest_kwargs())
    assert manifest["schema_version"] == "circe-evidence-v1"
    assert manifest["run_id"] == "w3w4-dry-001"
    assert manifest["lane"] == "causal"
    assert manifest["mode"] == "dry-run"
    assert manifest["metrics"]["best_loss"] == 0.25
    assert manifest["claim_boundary"] == "dry-run plumbing evidence only"


def test_write_manifest_creates_parent_directory(tmp_path):
    manifest = build_run_manifest(
        run_id="w5w6-local-001",
        lane="emergence",
        mode="local",
        command=["python", "experiments/w5w6_emergence_calibration.py", "--local"],
        config={"n_agents": 5, "n_steps": 3},
        metrics={"initial_edm": 0.12, "best_edm": 0.08, "final_edm": 0.09},
        artifacts={},
        notes=[],
    )
    path = tmp_path / "nested" / "manifest.json"
    write_manifest(path, manifest)
    assert json.loads(path.read_text())["run_id"] == "w5w6-local-001"


def test_manifest_rejects_unknown_lane():
    with pytest.raises(ValueError, match="lane"):
        build_run_manifest(
            run_id="bad",
            lane="other",
            mode="dry-run",
            command=["python"],
            config={},
            metrics={},
            artifacts={},
            notes=[],
        )


def test_manifest_rejects_unknown_status_typo():
    with pytest.raises(ValueError, match="status"):
        build_run_manifest(**_manifest_kwargs(status="complete"))


def test_manifest_rejects_malformed_timestamp():
    with pytest.raises(ValueError, match="started_at"):
        build_run_manifest(**_manifest_kwargs(started_at="yesterday morning"))


def test_manifest_rejects_naive_timestamp():
    with pytest.raises(ValueError, match="started_at"):
        build_run_manifest(**_manifest_kwargs(started_at="2026-05-11T10:00:00"))


def test_manifest_rejects_completion_before_start():
    with pytest.raises(ValueError, match="completed_at"):
        build_run_manifest(
            **_manifest_kwargs(
                started_at="2026-05-11T10:00:00+00:00",
                completed_at="2026-05-11T09:59:59+00:00",
            )
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("config", {"input_path": Path("experiments/data/input.json")}),
        ("metrics", {"recorded_at": datetime(2026, 5, 11, tzinfo=timezone.utc)}),
        ("notes", ["dry-run", np.int64(7)]),
    ],
)
def test_manifest_rejects_non_json_serializable_inputs(field, value):
    with pytest.raises(TypeError, match=f"{field} must be JSON serializable"):
        build_run_manifest(**_manifest_kwargs(**{field: value}))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("config", {"temperature": float("nan")}),
        ("config", {"temperature": float("inf")}),
        ("metrics", {"best_loss": float("nan")}),
        ("metrics", {"best_loss": float("-inf")}),
    ],
)
def test_manifest_rejects_non_finite_json_numbers(field, value):
    with pytest.raises(TypeError, match=f"{field} must be JSON serializable"):
        build_run_manifest(**_manifest_kwargs(**{field: value}))


def test_write_manifest_rejects_non_json_serializable_artifacts(tmp_path):
    manifest = build_run_manifest(**_manifest_kwargs())
    manifest["artifacts"]["result_json"] = Path("experiments/results/result.json")

    with pytest.raises(TypeError, match="artifacts must be JSON serializable"):
        write_manifest(tmp_path / "manifest.json", manifest)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("config", {"temperature": float("inf")}),
        ("metrics", {"best_loss": float("nan")}),
    ],
)
def test_write_manifest_rejects_non_finite_json_numbers(tmp_path, field, value):
    manifest = build_run_manifest(**_manifest_kwargs())
    manifest[field] = value

    with pytest.raises(TypeError, match=f"{field} must be JSON serializable"):
        write_manifest(tmp_path / "manifest.json", manifest)
