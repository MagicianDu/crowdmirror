import json
import subprocess
import sys

import pytest

from experiments.r6_behavioral_update_operator import (
    build_r6_behavioral_update_operator,
)


REQUIRED_CANDIDATE_KEYS = {
    "operator_id",
    "update_target",
    "parameter_delta",
    "affected_segments",
    "source_dynamic_paths",
    "derived_from_failure_boundary",
    "expected_repair",
    "new_false_alarm_risk",
    "runtime_decision",
    "runtime_default_allowed",
    "prompt_patch_text",
}


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
    assert [update["operator_id"] for update in report["candidate_updates"]] == [
        "damp-rights-rule-over-amplification",
        "boost-service-access-memory-activation",
    ]
    for candidate in report["candidate_updates"]:
        assert set(candidate) == REQUIRED_CANDIDATE_KEYS
        assert candidate["prompt_patch_text"] == ""
        assert candidate["runtime_decision"] == "blocked_pending_operator_holdout"
        assert candidate["runtime_default_allowed"] is False
        assert candidate["affected_segments"]
        assert candidate["source_dynamic_paths"]

    first = report["candidate_updates"][0]
    assert first["operator_id"] == "damp-rights-rule-over-amplification"
    assert first["update_target"] == "cap_or_damping_rule"
    assert first["runtime_decision"] == "blocked_pending_operator_holdout"
    assert first["derived_from_failure_boundary"] == (
        "interaction_over_amplifies_rejection_risk"
    )
    assert first["prompt_patch_text"] == ""
    assert {
        path["path_type"] for path in first["source_dynamic_paths"]
    } == {"peer_amplified_risk_diffusion"}
    assert first["parameter_delta"] == {
        "max_reject_delta_when_static_prior_close": 0.02,
        "static_prior_close_error_threshold": 0.03,
    }
    second = report["candidate_updates"][1]
    assert second["operator_id"] == "boost-service-access-memory-activation"
    assert second["update_target"] == "activation_threshold"
    assert second["derived_from_failure_boundary"] == (
        "static_prior_miss_under_interaction_diffusion"
    )
    assert {
        path["path_type"] for path in second["source_dynamic_paths"]
    } == {"memory_threshold_activation"}
    assert "operator_update_not_runtime_default" in report["risk_flags"]
    json.dumps(report, allow_nan=False)


def test_r6_behavioral_update_operator_rejects_missing_explicit_trace_paths():
    with pytest.raises(
        ValueError,
        match="propagation_trace lacks required dynamic paths for behavioral update operator",
    ):
        build_r6_behavioral_update_operator(
            artifact_id="r6-behavioral-update-operator-empty-trace",
            run_id="r6-behavioral-update-operator-run",
            propagation_trace={"artifact_id": "empty-trace", "case_traces": []},
        )


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
