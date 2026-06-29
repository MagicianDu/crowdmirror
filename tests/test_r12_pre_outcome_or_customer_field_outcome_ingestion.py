import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_pre_outcome_or_customer_field_outcome_ingestion import (
    R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_INGESTION_SCHEMA_VERSION,
    build_r12_pre_outcome_or_customer_field_outcome_ingestion,
)


def test_r12_pre_outcome_or_customer_field_outcome_ingestion_records_pending_target():
    report = build_r12_pre_outcome_or_customer_field_outcome_ingestion(
        artifact_id="r12-pre-outcome-or-customer-field-outcome-ingestion-test",
        run_id="r12-l18-test",
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=(
            _load_current_l17()
        ),
        availability_checked_at="2026-06-27T14:55:00Z",
    )

    assert report["schema_version"] == (
        R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_INGESTION_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_pre_outcome_or_customer_field_outcome_ingestion_pending_no_target_outcome"
    )
    assert report["claim_level"] == (
        "target_outcome_ingestion_pending_customer_field_contract_ready"
    )
    assert report["ingestion_summary"] == {
        "trial_artifact_id": (
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-current-001"
        ),
        "trial_id": "r12-dot-atcr-2026-05-pre-outcome-trial-001",
        "feature_period": "April 2026",
        "target_outcome_period": "May 2026",
        "prediction_case_count": 14,
        "prediction_lock_timestamp": "2026-06-27T14:45:00Z",
        "availability_checked_at": "2026-06-27T14:55:00Z",
        "target_outcome_artifact_present": False,
        "customer_field_slice_present": False,
        "customer_approval_present": False,
    }
    assert report["public_source_availability"] == {
        "target_public_source_id": "dot_atcr_2026_05_target_outcome_candidate",
        "expected_public_report": (
            "July 2026 Air Travel Consumer Report (May 2026 Data)"
        ),
        "official_reports_index_url": (
            "https://www.transportation.gov/individuals/aviation-consumer-protection/air-travel-consumer-reports"
        ),
        "latest_news_url": "https://www.transportation.gov/airconsumer/latest-news",
        "latest_available_report": "June 2026 Air Travel Consumer Report (April 2026 Data)",
        "target_report_found": False,
        "target_pdf_url": None,
        "target_table_available": False,
    }
    assert report["customer_field_ingestion_contract"] == {
        "contract_ready": True,
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
        "customer_slice_path_provided": False,
        "manual_prompt_or_persona_patch_allowed": False,
    }
    assert report["evaluation_readiness"] == {
        "field_or_pre_outcome_revalidation_ready": False,
        "missing_inputs": [
            "May 2026 DOT ATCR target outcome artifact",
            "customer-approved field outcome slice",
        ],
        "next_required_artifact": (
            "r12_pre_outcome_or_customer_field_outcome_revalidation"
        ),
        "metrics_to_compute_when_available": [
            "mean_absolute_error",
            "interval_coverage",
            "risk_ranking_quality",
            "static_prior_miss_recovery",
            "false_alarm_rate",
            "decision_value",
        ],
    }
    assert report["acceptance_gates"] == {
        "pre_outcome_trial_locked": True,
        "prediction_lock_timestamp_pre_target_outcome": True,
        "target_outcome_used_for_prediction_generation": False,
        "target_public_outcome_available": False,
        "target_outcome_artifact_present": False,
        "customer_field_slice_contract_ready": True,
        "customer_field_slice_present": False,
        "customer_approval_present": False,
        "field_or_pre_outcome_revalidation_ready": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "accept_outcome_ingestion_pending_keep_validation_and_product_default_blocked"
    )
    assert report["next_required_artifact"] == (
        "r12_pre_outcome_or_customer_field_outcome_revalidation"
    )
    assert "target outcome artifact present" in report["blocked_claims"]
    assert "field_or_pre_outcome_revalidation_ready=true" in report[
        "blocked_claims"
    ]
    json.dumps(report, allow_nan=False)


def test_r12_pre_outcome_or_customer_field_outcome_ingestion_cli_writes_artifact(
    tmp_path,
):
    trial_path = tmp_path / "r12-l17.json"
    output = tmp_path / "r12-l18.json"
    trial_path.write_text(json.dumps(_load_current_l17(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_pre_outcome_or_customer_field_outcome_ingestion.py",
            "--artifact-id",
            "r12-pre-outcome-or-customer-field-outcome-ingestion-cli",
            "--run-id",
            "r12-l18-test",
            "--r12-pre-outcome-prediction-trial-or-customer-field-revalidation-path",
            str(trial_path),
            "--availability-checked-at",
            "2026-06-27T14:55:00Z",
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
        "r12-pre-outcome-or-customer-field-outcome-ingestion-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-pre-outcome-or-customer-field-outcome-ingestion-cli",
        "output": str(output),
        "status": (
            "r12_pre_outcome_or_customer_field_outcome_ingestion_pending_no_target_outcome"
        ),
    }


def _load_current_l17():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_pre_outcome_prediction_trial_or_customer_field_revalidation/"
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-current-001.json"
        ).read_text()
    )
