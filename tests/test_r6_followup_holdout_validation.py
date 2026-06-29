import json
import subprocess
import sys

from experiments.r6_followup_holdout_validation import (
    build_r6_followup_holdout_validation,
)


def test_r6_followup_holdout_validation_blocks_global_update_when_same_family_holdout_misses_cap_condition():
    report = build_r6_followup_holdout_validation(
        artifact_id="r6-followup-holdout-validation-test",
        run_id="r6-followup-holdout-validation-run",
    )

    assert report["schema_version"] == "r6-followup-holdout-validation-v1"
    assert report["status"] == "holdout_validation_partial"
    assert report["validation_design"] == {
        "mechanism_cap_source_proxy_key": "anes_health_heldout",
        "cross_proxy_holdout_proxy_key": "htops_cost_pressure",
        "same_family_holdout_proxy_key": "anes_climate_heldout",
        "validation_scope": "same_family_condition_coverage_and_cross_proxy_non_regression",
    }
    assert report["acceptance_gates"] == {
        "mechanism_cap_source_failure_fixed": True,
        "mechanism_cap_cross_proxy_non_regression": True,
        "mechanism_cap_same_family_holdout_available": True,
        "mechanism_cap_same_family_cap_condition_covered": False,
        "mechanism_cap_same_family_validation_passed": False,
        "outcome_feedback_cross_case_transfer_available": False,
        "third_public_proxy_connected": True,
        "global_update_accepted": False,
    }
    assert report["mechanism_cap_validation"] == {
        "upgrade_status": "partial_pass_needs_in_condition_same_family_holdout",
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
        "same_family_holdout": {
            "target_case_id": "generic-rights-rule-change",
            "source_proxy_key": "anes_climate_heldout",
            "observed_reject_proxy": 0.25,
            "static_prior_error": 0.06,
            "original_prior_anchored_error": 0.13,
            "capped_prior_anchored_error": 0.13,
            "cap_condition_met": False,
            "cap_applied": False,
            "validation_status": "available_but_condition_not_exercised",
        },
        "missing_holdout": "in_condition_same_family_rights_rule_public_or_real_proxy",
    }
    assert report["outcome_feedback_validation"] == {
        "upgrade_status": "blocked_same_case_only",
        "accepted_for_global_update": False,
        "same_case_feedback_improved_count": 3,
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
            {
                "target_case_id": "generic-rights-rule-change",
                "source_proxy_key": "anes_climate_heldout",
                "prior_anchored_error": 0.13,
                "outcome_feedback_error": 0.05,
                "same_case_feedback_improved": True,
                "global_update_status": "blocked_same_case_only",
            },
        ],
    }
    assert report["recommended_next_data"] == [
        "in_condition_same_family_rights_rule_holdout_proxy",
        "real_or_field_outcome_proxy",
        "outcome_feedback_cross_case_transfer_protocol",
    ]
    assert "partial_holdout_not_runtime_acceptance" in report["risk_flags"]
    assert "same_family_holdout_condition_not_covered" in report["risk_flags"]
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
