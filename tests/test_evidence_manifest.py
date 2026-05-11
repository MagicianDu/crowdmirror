import json

import pytest

from experiments.evidence_manifest import build_run_manifest, write_manifest


def test_build_run_manifest_records_required_fields(tmp_path):
    manifest = build_run_manifest(
        run_id="w3w4-dry-001",
        lane="causal",
        mode="dry-run",
        command=["python", "experiments/w3w4_causal_calibration.py", "--dry-run"],
        config={"max_iterations": 3, "eval_size": 5},
        metrics={
            "initial_loss": 0.30,
            "best_loss": 0.25,
            "final_loss": 0.27,
            "n_iterations": 3,
        },
        artifacts={"result_json": "experiments/results/w3w4_calibration_result.json"},
        notes=["dry-run uses mocked LLM responses"],
    )
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
