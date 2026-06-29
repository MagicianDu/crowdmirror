import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_pre_outcome_prediction_trial_or_customer_field_revalidation import (
    R12_PRE_OUTCOME_PREDICTION_TRIAL_OR_CUSTOMER_FIELD_REVALIDATION_SCHEMA_VERSION,
    build_r12_pre_outcome_prediction_trial_or_customer_field_revalidation,
)


def test_r12_pre_outcome_prediction_trial_locks_future_public_trial():
    report = build_r12_pre_outcome_prediction_trial_or_customer_field_revalidation(
        artifact_id=(
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-test"
        ),
        run_id="r12-l17-test",
        r12_independent_hindcast_revalidation=_load_current_l16(),
        r12_external_or_customer_holdout_raw_slice=_load_current_raw_slice(),
        prediction_lock_timestamp="2026-06-27T14:45:00Z",
    )

    assert report["schema_version"] == (
        R12_PRE_OUTCOME_PREDICTION_TRIAL_OR_CUSTOMER_FIELD_REVALIDATION_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_pre_outcome_prediction_trial_locked_outcome_pending_guarded"
    )
    assert report["claim_level"] == (
        "pre_outcome_prediction_trial_locked_not_yet_validated"
    )
    assert report["route_selection"] == {
        "selected_route": "pre_outcome_public_dot_trial",
        "customer_field_revalidation_fallback_enabled": True,
        "customer_field_slice_contract_ready": True,
        "selected_feature_source_artifact_id": (
            "r12-external-or-customer-holdout-raw-slice-current-001"
        ),
        "supporting_hindcast_artifact_id": (
            "r12-independent-hindcast-revalidation-current-001"
        ),
    }
    assert report["trial_summary"] == {
        "trial_id": "r12-dot-atcr-2026-05-pre-outcome-trial-001",
        "prediction_lock_timestamp": "2026-06-27T14:45:00Z",
        "feature_period": "April 2026",
        "target_outcome_period": "May 2026",
        "target_outcome_artifact_present": False,
        "prediction_case_count": 14,
        "prediction_total_basis": 4839,
        "prediction_source_independent_of_target_outcome": True,
        "target_outcome_used_for_prediction_generation": False,
        "prediction_lock_timestamp_pre_target_outcome": True,
        "pre_outcome_revalidation_ready": False,
        "customer_field_slice_present": False,
        "customer_approval_present": False,
    }
    assert report["locked_predictions"][0] == {
        "case_id": "dot_atcr_2026_05_us_airline_american_airlines",
        "source_case_id": "dot_atcr_2026_04_us_airline_american_airlines",
        "carrier": "American Airlines",
        "feature_observed_total": 1341,
        "static_prior_prediction": 0.071429,
        "locked_prediction_share": 0.277123,
        "prediction_interval_low": 0.227123,
        "prediction_interval_high": 0.327123,
        "prediction_basis": "prior_month_official_complaint_share",
    }
    assert report["customer_field_slice_contract"] == {
        "accepted_formats": ["csv", "jsonl"],
        "minimum_case_count": 10,
        "required_fields": [
            "case_id",
            "segment_id",
            "scenario_id",
            "prediction_share_or_score",
            "observed_outcome",
            "outcome_timestamp",
            "customer_approval_reference",
        ],
        "optional_fields": [
            "segment_label",
            "mechanism_label",
            "baseline_prediction",
            "interaction_prediction",
            "decision_cost",
            "review_note",
        ],
        "must_include_customer_approval_reference": True,
        "manual_prompt_or_persona_patch_allowed": False,
    }
    assert report["evaluation_contract"] == {
        "next_required_artifact": (
            "r12_pre_outcome_or_customer_field_outcome_ingestion"
        ),
        "evaluation_metrics": [
            "mean_absolute_error",
            "interval_coverage",
            "risk_ranking_quality",
            "static_prior_miss_recovery",
            "false_alarm_rate",
            "decision_value",
        ],
        "acceptance_requires": [
            "target_outcome_artifact_present=true",
            "target_outcome_used_for_prediction_generation=false",
            "prediction_lock_timestamp_pre_target_outcome=true",
            "false_alarm_non_regression=true",
            "field_or_pre_outcome_revalidation_passed=true",
        ],
    }
    assert report["acceptance_gates"] == {
        "supporting_independent_hindcast_passed": True,
        "pre_outcome_prediction_trial_created": True,
        "prediction_packet_locked": True,
        "prediction_lock_timestamp_present": True,
        "prediction_lock_timestamp_pre_target_outcome": True,
        "prediction_source_independent_of_target_outcome": True,
        "target_outcome_used_for_prediction_generation": False,
        "target_outcome_artifact_present": False,
        "pre_outcome_revalidation_ready": False,
        "customer_field_slice_contract_ready": True,
        "customer_field_slice_present": False,
        "customer_approval_present": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "accept_pre_outcome_trial_lock_keep_validation_and_product_default_blocked_until_outcome_ingestion"
    )
    assert report["next_required_artifact"] == (
        "r12_pre_outcome_or_customer_field_outcome_ingestion"
    )
    assert "pre-outcome outcome revalidation passed" in report["blocked_claims"]
    assert "runtime_default_allowed=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_pre_outcome_prediction_trial_cli_writes_artifact(tmp_path):
    hindcast_path = tmp_path / "r12-l16.json"
    raw_slice_path = tmp_path / "r12-raw-slice.json"
    output = tmp_path / "r12-l17.json"
    hindcast_path.write_text(json.dumps(_load_current_l16(), allow_nan=False))
    raw_slice_path.write_text(json.dumps(_load_current_raw_slice(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            (
                "experiments/"
                "r12_pre_outcome_prediction_trial_or_customer_field_revalidation.py"
            ),
            "--artifact-id",
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-cli",
            "--run-id",
            "r12-l17-test",
            "--r12-independent-hindcast-revalidation-path",
            str(hindcast_path),
            "--r12-external-or-customer-holdout-raw-slice-path",
            str(raw_slice_path),
            "--prediction-lock-timestamp",
            "2026-06-27T14:45:00Z",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == (
        "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": (
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-cli"
        ),
        "output": str(output),
        "status": (
            "r12_pre_outcome_prediction_trial_locked_outcome_pending_guarded"
        ),
    }


def _load_current_l16():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_independent_hindcast_revalidation/"
            "r12-independent-hindcast-revalidation-current-001.json"
        ).read_text()
    )


def _load_current_raw_slice():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_external_or_customer_holdout_raw_slice/"
            "r12-external-or-customer-holdout-raw-slice-current-001.json"
        ).read_text()
    )
