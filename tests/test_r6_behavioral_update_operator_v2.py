import json
import subprocess
import sys

from experiments.r6_behavioral_update_operator_v2 import (
    build_r6_behavioral_update_operator_v2,
)


def test_r6_behavioral_update_operator_v2_adds_error_attribution_and_transfer_guards():
    report = build_r6_behavioral_update_operator_v2(
        artifact_id="r6-behavioral-update-operator-v2-test",
        run_id="r6-gap-closure-run",
    )

    assert report["schema_version"] == "r6-behavioral-update-operator-v2"
    assert report["status"] == "operator_v2_structured_blocked_missing_holdout"
    assert report["operator_v2_summary"] == {
        "candidate_update_count": 3,
        "same_case_repair_count": 1,
        "transfer_candidate_count": 2,
        "runtime_default_allowed_count": 0,
        "prompt_patch_update_count": 0,
    }
    assert report["acceptance_gates"]["operator_v2_structured"] is True
    assert report["acceptance_gates"]["operator_v2_runtime_default_allowed"] is False
    assert report["acceptance_gates"]["independent_holdout_available"] is False
    candidate = report["candidate_updates"][0]
    assert candidate["operator_family"] == "over_amplification_damping"
    assert candidate["error_attribution"]["primary_component"] == "over_amplification"
    assert candidate["acceptance_status"] == "blocked_missing_independent_holdout"
    assert candidate["runtime_default_allowed"] is False
    assert candidate["prompt_patch_text"] == ""
    assert "independent_same_family_in_condition_holdout" in candidate[
        "transfer_preconditions"
    ]
    json.dumps(report, allow_nan=False)


def test_r6_behavioral_update_operator_v2_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-behavioral-update-operator-v2.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_behavioral_update_operator_v2.py",
            "--artifact-id",
            "r6-behavioral-update-operator-v2-cli",
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
    assert report["schema_version"] == "r6-behavioral-update-operator-v2"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-behavioral-update-operator-v2-cli",
        "output": str(output),
        "status": "operator_v2_structured_blocked_missing_holdout",
    }
