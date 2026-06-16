import json
import subprocess
import sys

from experiments.r6_behavioral_update_operator import (
    build_r6_behavioral_update_operator,
)


def test_r6_behavioral_update_operator_generates_structured_blocked_candidate():
    report = build_r6_behavioral_update_operator(
        artifact_id="r6-behavioral-update-operator-test",
        run_id="r6-behavioral-update-operator-run",
    )

    assert report["schema_version"] == "r6-behavioral-update-operator-v1"
    assert report["status"] == "behavioral_update_candidate_blocked_pending_holdout"
    assert report["operator_summary"] == {
        "candidate_update_count": 2,
        "prompt_patch_update_count": 0,
        "runtime_default_allowed_count": 0,
        "structured_operator_update_count": 2,
        "field_outcome_validated": False,
    }
    assert report["acceptance_gates"] == {
        "operator_update_structured": True,
        "prompt_patch_absent": True,
        "runtime_default_allowed": False,
        "operator_holdout_validated": False,
        "product_guard_required": True,
    }
    first = report["candidate_updates"][0]
    assert first["operator_id"] == "damp-rights-rule-over-amplification"
    assert first["update_target"] == "cap_or_damping_rule"
    assert first["runtime_decision"] == "blocked_pending_operator_holdout"
    assert first["derived_from_failure_boundary"] == (
        "interaction_over_amplifies_rejection_risk"
    )
    assert first["prompt_patch_text"] == ""
    assert first["parameter_delta"] == {
        "max_reject_delta_when_static_prior_close": 0.02,
        "static_prior_close_error_threshold": 0.03,
    }
    assert "operator_update_not_runtime_default" in report["risk_flags"]
    json.dumps(report, allow_nan=False)


def test_r6_behavioral_update_operator_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-behavioral-update-operator.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_behavioral_update_operator.py",
            "--artifact-id",
            "r6-behavioral-update-operator-cli",
            "--run-id",
            "r6-behavioral-update-operator-run",
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
    assert report["schema_version"] == "r6-behavioral-update-operator-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-behavioral-update-operator-cli",
        "candidate_update_count": 2,
        "output": str(output),
        "status": "behavioral_update_candidate_blocked_pending_holdout",
    }
