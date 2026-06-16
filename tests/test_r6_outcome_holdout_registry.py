import json
import subprocess
import sys

from experiments.r6_outcome_holdout_registry import build_r6_outcome_holdout_registry


def test_r6_outcome_holdout_registry_marks_missing_independent_holdouts():
    registry = build_r6_outcome_holdout_registry(
        artifact_id="r6-outcome-holdout-registry-test",
        run_id="r6-gap-closure-run",
    )

    assert registry["schema_version"] == "r6-outcome-holdout-registry-v1"
    assert registry["status"] == "holdout_registry_ready_missing_required_slots"
    assert registry["registry_summary"] == {
        "registered_outcome_count": 3,
        "independent_public_proxy_count": 0,
        "field_outcome_count": 0,
        "missing_required_slot_count": 3,
        "in_condition_independent_holdout_available": False,
    }
    by_key = {entry["source_key"]: entry for entry in registry["outcome_entries"]}
    assert by_key["htops_cost_pressure"]["independence_level"] == (
        "out_of_family_non_regression_proxy"
    )
    assert by_key["anes_health_heldout"]["independence_level"] == "source_case_proxy"
    assert by_key["anes_climate_heldout"]["independence_level"] == (
        "same_source_out_of_condition_proxy"
    )
    missing = {slot["slot_id"] for slot in registry["missing_required_slots"]}
    assert missing == {
        "independent_same_family_in_condition_holdout",
        "independent_supported_signal_holdout",
        "real_field_outcome",
    }
    assert registry["acceptance_gates"]["holdout_registry_present"] is True
    assert registry["acceptance_gates"]["independent_holdout_missing_slots_visible"] is True
    assert registry["acceptance_gates"]["field_outcome_validated"] is False
    json.dumps(registry, allow_nan=False)


def test_r6_outcome_holdout_registry_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-outcome-holdout-registry.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_outcome_holdout_registry.py",
            "--artifact-id",
            "r6-outcome-holdout-registry-cli",
            "--run-id",
            "r6-gap-closure-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_text().endswith("\n")
    report = json.loads(output.read_text())
    assert report["schema_version"] == "r6-outcome-holdout-registry-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-outcome-holdout-registry-cli",
        "output": str(output),
        "status": "holdout_registry_ready_missing_required_slots",
    }
