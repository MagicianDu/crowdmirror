import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_pre_outcome_or_customer_field_outcome_revalidation import (
    R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_REVALIDATION_SCHEMA_VERSION,
    build_r12_pre_outcome_or_customer_field_outcome_revalidation,
)


def test_r12_pre_outcome_or_customer_field_outcome_revalidation_fails_closed_without_outcome():
    report = build_r12_pre_outcome_or_customer_field_outcome_revalidation(
        artifact_id=(
            "r12-pre-outcome-or-customer-field-outcome-revalidation-test"
        ),
        run_id="r12-l19-test",
        r12_pre_outcome_or_customer_field_outcome_ingestion=_load_current_l18(),
        revalidation_requested_at="2026-06-27T15:05:00Z",
    )

    assert report["schema_version"] == (
        R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_REVALIDATION_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_pre_outcome_or_customer_field_outcome_revalidation_blocked_no_outcome"
    )
    assert report["claim_level"] == "revalidation_harness_ready_no_outcome"
    assert report["revalidation_summary"] == {
        "ingestion_artifact_id": (
            "r12-pre-outcome-or-customer-field-outcome-ingestion-current-001"
        ),
        "trial_artifact_id": (
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-current-001"
        ),
        "target_outcome_period": "May 2026",
        "prediction_case_count": 14,
        "prediction_lock_timestamp": "2026-06-27T14:45:00Z",
        "revalidation_requested_at": "2026-06-27T15:05:00Z",
        "target_outcome_artifact_present": False,
        "customer_field_slice_present": False,
        "field_or_pre_outcome_revalidation_ready": False,
        "metrics_computed": False,
    }
    assert report["metric_execution_plan"] == [
        {
            "metric": "mean_absolute_error",
            "required_inputs": [
                "locked_prediction_share_or_score",
                "observed_outcome",
            ],
            "acceptance_threshold": "mechanism_update_mae <= static_prior_mae",
        },
        {
            "metric": "interval_coverage",
            "required_inputs": [
                "locked_prediction_interval",
                "observed_outcome",
            ],
            "acceptance_threshold": "coverage >= static_prior_coverage",
        },
        {
            "metric": "risk_ranking_quality",
            "required_inputs": [
                "locked_risk_rank",
                "observed_outcome_rank",
            ],
            "acceptance_threshold": "ranking_quality >= static_prior_ranking_quality",
        },
        {
            "metric": "static_prior_miss_recovery",
            "required_inputs": [
                "static_prior_prediction",
                "mechanism_update_prediction",
                "observed_outcome",
            ],
            "acceptance_threshold": "recovery_count > 0",
        },
        {
            "metric": "false_alarm_rate",
            "required_inputs": [
                "locked_risk_alert",
                "observed_outcome",
            ],
            "acceptance_threshold": "false_alarm_rate <= static_prior_false_alarm_rate",
        },
        {
            "metric": "decision_value",
            "required_inputs": [
                "locked_decision_action",
                "observed_outcome",
                "decision_cost_model",
            ],
            "acceptance_threshold": "decision_value >= static_prior_decision_value",
        },
    ]
    assert report["acceptance_gates"] == {
        "pre_outcome_trial_locked": True,
        "prediction_lock_timestamp_pre_target_outcome": True,
        "target_outcome_artifact_present": False,
        "customer_field_slice_present": False,
        "field_or_pre_outcome_revalidation_ready": False,
        "metrics_computed": False,
        "field_or_pre_outcome_revalidation_passed": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "reject_revalidation_without_outcome_keep_product_default_blocked"
    )
    assert report["next_required_artifact"] == (
        "r12_target_outcome_or_customer_field_slice_arrival"
    )
    assert "May 2026 DOT ATCR target outcome artifact" in report[
        "blocked_revalidation_reason"
    ]["missing_inputs"]
    assert "metrics_computed=true" in report["blocked_claims"]
    assert "field_or_pre_outcome_revalidation_passed=true" in report[
        "blocked_claims"
    ]
    json.dumps(report, allow_nan=False)


def test_r12_pre_outcome_or_customer_field_outcome_revalidation_cli_writes_artifact(
    tmp_path,
):
    ingestion_path = tmp_path / "r12-l18.json"
    output = tmp_path / "r12-l19.json"
    ingestion_path.write_text(json.dumps(_load_current_l18(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_pre_outcome_or_customer_field_outcome_revalidation.py",
            "--artifact-id",
            "r12-pre-outcome-or-customer-field-outcome-revalidation-cli",
            "--run-id",
            "r12-l19-test",
            "--r12-pre-outcome-or-customer-field-outcome-ingestion-path",
            str(ingestion_path),
            "--revalidation-requested-at",
            "2026-06-27T15:05:00Z",
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
        "r12-pre-outcome-or-customer-field-outcome-revalidation-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": (
            "r12-pre-outcome-or-customer-field-outcome-revalidation-cli"
        ),
        "output": str(output),
        "status": (
            "r12_pre_outcome_or_customer_field_outcome_revalidation_blocked_no_outcome"
        ),
    }


def _load_current_l18():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_pre_outcome_or_customer_field_outcome_ingestion/"
            "r12-pre-outcome-or-customer-field-outcome-ingestion-current-001.json"
        ).read_text()
    )
