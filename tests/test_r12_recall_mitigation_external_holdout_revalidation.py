import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_recall_mitigation_external_holdout_revalidation import (
    R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_REVALIDATION_SCHEMA_VERSION,
    build_r12_recall_mitigation_external_holdout_revalidation,
)


def test_r12_external_holdout_revalidation_reports_proxy_metrics_and_blocks_default():
    report = build_r12_recall_mitigation_external_holdout_revalidation(
        artifact_id="r12-recall-mitigation-external-holdout-revalidation-test",
        run_id="r12-l14-test",
        r12_external_or_customer_holdout_raw_slice=_load_current_raw_slice(),
    )

    assert report["schema_version"] == (
        R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_REVALIDATION_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_recall_mitigation_external_holdout_revalidation_blocked_prediction_proxy_only"
    )
    assert report["claim_level"] == (
        "external_holdout_proxy_revalidation_diagnostic_only"
    )
    assert report["revalidation_summary"] == {
        "source_artifact_id": "r12-external-or-customer-holdout-raw-slice-current-001",
        "case_count": 14,
        "observed_total": 4839,
        "high_risk_threshold": 0.071429,
        "top_k_for_risk_ranking": 4,
        "static_prior_prediction_source": "uniform_carrier_share_control",
        "interaction_prediction_source": (
            "same_table_mechanism_composition_proxy"
        ),
        "prediction_source_independent_of_observed_outcome": False,
        "same_table_prediction_leakage_risk": True,
    }
    assert report["metric_comparison"] == {
        "mean_absolute_error": {
            "static_prior": 0.067156,
            "interaction": 0.062827,
            "delta": -0.004329,
        },
        "interval_coverage": {
            "static_prior": 0.285714,
            "interaction": 0.357143,
            "delta": 0.071429,
        },
        "risk_ranking_quality": {
            "static_prior": 0.0,
            "interaction": 0.25,
            "delta": 0.25,
        },
        "static_prior_miss_recovery": {
            "static_prior": 0.0,
            "interaction": 0.8,
            "delta": 0.8,
        },
        "false_alarm_rate": {
            "static_prior": 0.0,
            "interaction": 0.428571,
            "delta": 0.428571,
        },
        "precision": {
            "static_prior": 0.0,
            "interaction": 0.571429,
            "delta": 0.571429,
        },
    }
    assert report["acceptance_gates"] == {
        "raw_external_or_customer_slice_present": True,
        "prediction_fields_generated": True,
        "external_holdout_revalidation_executed": True,
        "mean_absolute_error_improved": True,
        "interval_coverage_non_regression": True,
        "risk_ranking_quality_improved": True,
        "static_prior_miss_recovery_improved": True,
        "false_alarm_non_regression": False,
        "prediction_source_independent_of_observed_outcome": False,
        "same_table_prediction_leakage_risk": True,
        "external_holdout_revalidation_passed": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    first_case = report["case_predictions"][0]
    assert first_case == {
        "case_id": "dot_atcr_2026_04_us_airline_american_airlines",
        "carrier": "American Airlines",
        "observed_outcome": 1341,
        "observed_share": 0.277123,
        "static_prior_prediction": 0.071429,
        "interaction_prediction": 0.079432,
        "mechanism_pressure_score": 0.182685,
        "static_prior_absolute_error": 0.205695,
        "interaction_absolute_error": 0.197691,
        "observed_high_risk": True,
        "static_prior_predicted_high_risk": False,
        "interaction_predicted_high_risk": True,
        "static_prior_miss_recovered": True,
        "interaction_false_alarm": False,
    }
    assert report["top_k_risk_ranking"] == {
        "observed_top_k_carriers": [
            "American Airlines",
            "Delta Air Lines",
            "United Airlines",
            "Frontier Airlines",
        ],
        "interaction_top_k_carriers": [
            "Avelo Airlines",
            "Spirit Airlines",
            "Contour Airlines",
            "American Airlines",
        ],
        "overlap_count": 1,
        "risk_ranking_quality": 0.25,
    }
    assert report["acceptance_decision"] == (
        "reject_product_default_keep_as_proxy_external_revalidation_diagnostic"
    )
    assert report["next_required_artifact"] == (
        "r12_pre_outcome_or_independent_prediction_packet"
    )
    assert (
        "external holdout revalidation passed with independent predictions"
        in report["blocked_claims"]
    )
    assert "runtime_default_allowed=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_external_holdout_revalidation_cli_writes_artifact(tmp_path):
    raw_slice_path = tmp_path / "r12-raw-slice.json"
    output = tmp_path / "r12-external-revalidation.json"
    raw_slice_path.write_text(json.dumps(_load_current_raw_slice(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_recall_mitigation_external_holdout_revalidation.py",
            "--artifact-id",
            "r12-recall-mitigation-external-holdout-revalidation-cli",
            "--run-id",
            "r12-l14-test",
            "--r12-external-or-customer-holdout-raw-slice-path",
            str(raw_slice_path),
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
        "r12-recall-mitigation-external-holdout-revalidation-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": (
            "r12-recall-mitigation-external-holdout-revalidation-cli"
        ),
        "output": str(output),
        "status": (
            "r12_recall_mitigation_external_holdout_revalidation_blocked_prediction_proxy_only"
        ),
    }


def _load_current_raw_slice():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_external_or_customer_holdout_raw_slice/"
            "r12-external-or-customer-holdout-raw-slice-current-001.json"
        ).read_text()
    )
