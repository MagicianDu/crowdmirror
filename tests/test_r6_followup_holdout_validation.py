import json
import subprocess
import sys

from experiments.r6_followup_holdout_validation import (
    build_r6_followup_holdout_validation,
)


def test_r6_followup_holdout_validation_blocks_global_update_without_same_family_holdout():
    report = build_r6_followup_holdout_validation(
        artifact_id="r6-followup-holdout-validation-test",
        run_id="r6-followup-holdout-validation-run",
    )

    assert report["schema_version"] == "r6-followup-holdout-validation-v1"
    assert report["status"] == "holdout_validation_partial"
    assert report["validation_design"] == {
        "mechanism_cap_source_proxy_key": "anes_health_heldout",
        "cross_proxy_holdout_proxy_key": "htops_cost_pressure",
        "validation_scope": "cross_proxy_non_regression_not_global_acceptance",
    }
    assert report["acceptance_gates"] == {
        "mechanism_cap_source_failure_fixed": True,
        "mechanism_cap_cross_proxy_non_regression": True,
        "mechanism_cap_same_family_holdout_available": False,
        "outcome_feedback_cross_case_transfer_available": False,
        "global_update_accepted": False,
    }
    assert report["mechanism_cap_validation"] == {
        "upgrade_status": "partial_pass_needs_same_family_holdout",
        "accepted_for_runtime": False,
        "source_case": {
            "target_case_id": "generic-rights-rule-change",
            "source_proxy_key": "anes_health_heldout",
            "original_prior_anchored_error": 0.05,
            "capped_prior_anchored_error": 0.0,
            "failure_fixed": True,
        },
        "cross_proxy_holdout": {
            "target_case_id": "generic-public-service-policy-change",
            "source_proxy_key": "htops_cost_pressure",
            "cap_applied": False,
            "original_prior_anchored_error": 0.11,
            "capped_prior_anchored_error": 0.11,
            "non_regression_passed": True,
        },
        "missing_holdout": "same_family_rights_rule_public_or_real_proxy",
    }
    assert report["outcome_feedback_validation"] == {
        "upgrade_status": "blocked_same_case_only",
        "accepted_for_global_update": False,
        "same_case_feedback_improved_count": 2,
        "cross_case_transfer_available": False,
        "case_results": [
            {
                "target_case_id": "generic-public-service-policy-change",
                "source_proxy_key": "htops_cost_pressure",
                "prior_anchored_error": 0.11,
                "outcome_feedback_error": 0.04,
                "same_case_feedback_improved": True,
                "global_update_status": "blocked_same_case_only",
            },
            {
                "target_case_id": "generic-rights-rule-change",
                "source_proxy_key": "anes_health_heldout",
                "prior_anchored_error": 0.05,
                "outcome_feedback_error": 0.02,
                "same_case_feedback_improved": True,
                "global_update_status": "blocked_same_case_only",
            },
        ],
    }
    assert report["recommended_next_data"] == [
        "same_family_rights_rule_holdout_proxy",
        "third_public_or_real_proxy",
        "outcome_feedback_cross_case_transfer_protocol",
    ]
    assert "partial_holdout_not_runtime_acceptance" in report["risk_flags"]
    json.dumps(report, allow_nan=False)


def test_r6_followup_holdout_validation_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-followup-holdout-validation.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_followup_holdout_validation.py",
            "--artifact-id",
            "r6-followup-holdout-validation-cli",
            "--run-id",
            "r6-followup-holdout-validation-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    report = json.loads(output.read_text())
    assert report["schema_version"] == "r6-followup-holdout-validation-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-followup-holdout-validation-cli",
        "global_update_accepted": False,
        "output": str(output),
        "status": "holdout_validation_partial",
    }
