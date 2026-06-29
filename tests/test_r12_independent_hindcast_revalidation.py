import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_independent_hindcast_revalidation import (
    R12_INDEPENDENT_HINDCAST_REVALIDATION_SCHEMA_VERSION,
    build_r12_independent_hindcast_revalidation,
)


def test_r12_independent_hindcast_revalidation_scores_locked_predictions():
    report = build_r12_independent_hindcast_revalidation(
        artifact_id="r12-independent-hindcast-revalidation-test",
        run_id="r12-l16-test",
        r12_pre_outcome_or_independent_prediction_packet=_load_current_l15(),
        r12_external_or_customer_holdout_raw_slice=_load_current_raw_slice(),
    )

    assert report["schema_version"] == (
        R12_INDEPENDENT_HINDCAST_REVALIDATION_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_independent_hindcast_revalidation_passed_guarded_not_pre_outcome"
    )
    assert report["claim_level"] == (
        "independent_hindcast_positive_guarded_not_pre_outcome_validation"
    )
    assert report["hindcast_summary"] == {
        "prediction_packet_artifact_id": (
            "r12-pre-outcome-or-independent-prediction-packet-current-001"
        ),
        "target_raw_slice_artifact_id": (
            "r12-external-or-customer-holdout-raw-slice-current-001"
        ),
        "target_outcome_period": "April 2026",
        "feature_period": "March 2026",
        "case_count": 14,
        "observed_total": 4839,
        "prediction_source_independent_of_target_outcome": True,
        "prediction_lock_timestamp_pre_target_outcome": False,
        "hindcast_independent_revalidation_ready": True,
        "pre_outcome_revalidation_ready": False,
    }
    assert report["metric_comparison"] == {
        "mean_absolute_error": {
            "static_prior": 0.067156,
            "independent_hindcast": 0.004206,
            "delta": -0.062951,
        },
        "interval_coverage": {
            "static_prior": 0.285714,
            "independent_hindcast": 1.0,
            "delta": 0.714286,
        },
        "risk_ranking_quality": {
            "static_prior": 0.0,
            "independent_hindcast": 1.0,
            "delta": 1.0,
        },
        "static_prior_miss_recovery": {
            "static_prior": 0.0,
            "independent_hindcast": 1.0,
            "delta": 1.0,
        },
        "false_alarm_rate": {
            "static_prior": 0.0,
            "independent_hindcast": 0.0,
            "delta": 0.0,
        },
        "precision": {
            "static_prior": 0.0,
            "independent_hindcast": 1.0,
            "delta": 1.0,
        },
        "decision_value": {
            "static_prior": -0.357143,
            "independent_hindcast": 0.357143,
            "delta": 0.714286,
        },
    }
    assert report["top_k_risk_ranking"] == {
        "observed_top_k_carriers": [
            "American Airlines",
            "Delta Air Lines",
            "United Airlines",
            "Frontier Airlines",
        ],
        "independent_hindcast_top_k_carriers": [
            "American Airlines",
            "Delta Air Lines",
            "United Airlines",
            "Frontier Airlines",
        ],
        "overlap_count": 4,
        "risk_ranking_quality": 1.0,
    }
    assert report["case_results"][0] == {
        "case_id": "dot_atcr_2026_04_us_airline_american_airlines",
        "carrier": "American Airlines",
        "observed_outcome": 1341,
        "observed_share": 0.277123,
        "static_prior_prediction": 0.071429,
        "independent_hindcast_prediction": 0.284861,
        "static_prior_absolute_error": 0.205695,
        "independent_hindcast_absolute_error": 0.007738,
        "observed_high_risk": True,
        "static_prior_predicted_high_risk": False,
        "independent_hindcast_predicted_high_risk": True,
        "static_prior_miss_recovered": True,
        "independent_hindcast_false_alarm": False,
    }
    assert report["acceptance_gates"] == {
        "prediction_packet_generated": True,
        "prediction_source_independent_of_target_outcome": True,
        "target_outcome_used_for_prediction_generation": False,
        "same_table_prediction_leakage_risk": False,
        "prediction_lock_timestamp_pre_target_outcome": False,
        "hindcast_independent_revalidation_executed": True,
        "hindcast_independent_revalidation_passed": True,
        "mean_absolute_error_improved": True,
        "interval_coverage_non_regression": True,
        "risk_ranking_quality_improved": True,
        "static_prior_miss_recovery_improved": True,
        "false_alarm_non_regression": True,
        "decision_value_improved": True,
        "pre_outcome_revalidation_ready": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "accept_independent_hindcast_positive_keep_product_default_blocked_until_pre_outcome_or_field_validation"
    )
    assert report["next_required_artifact"] == (
        "r12_pre_outcome_prediction_trial_or_customer_field_revalidation"
    )
    assert "pre-outcome validation passed" in report["blocked_claims"]
    assert "runtime_default_allowed=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_independent_hindcast_revalidation_cli_writes_artifact(tmp_path):
    packet_path = tmp_path / "r12-l15.json"
    raw_slice_path = tmp_path / "r12-raw-slice.json"
    output = tmp_path / "r12-l16.json"
    packet_path.write_text(json.dumps(_load_current_l15(), allow_nan=False))
    raw_slice_path.write_text(json.dumps(_load_current_raw_slice(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_independent_hindcast_revalidation.py",
            "--artifact-id",
            "r12-independent-hindcast-revalidation-cli",
            "--run-id",
            "r12-l16-test",
            "--r12-pre-outcome-or-independent-prediction-packet-path",
            str(packet_path),
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
    assert artifact["schema_version"] == "r12-independent-hindcast-revalidation-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-independent-hindcast-revalidation-cli",
        "output": str(output),
        "status": (
            "r12_independent_hindcast_revalidation_passed_guarded_not_pre_outcome"
        ),
    }


def _load_current_l15():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_pre_outcome_or_independent_prediction_packet/"
            "r12-pre-outcome-or-independent-prediction-packet-current-001.json"
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
