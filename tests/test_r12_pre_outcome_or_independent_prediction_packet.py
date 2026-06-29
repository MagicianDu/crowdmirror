import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_pre_outcome_or_independent_prediction_packet import (
    R12_PRE_OUTCOME_OR_INDEPENDENT_PREDICTION_PACKET_SCHEMA_VERSION,
    build_r12_pre_outcome_or_independent_prediction_packet,
)


def test_r12_pre_outcome_or_independent_prediction_packet_uses_prior_month_source():
    packet = build_r12_pre_outcome_or_independent_prediction_packet(
        artifact_id="r12-pre-outcome-or-independent-prediction-packet-test",
        run_id="r12-l15-test",
        r12_recall_mitigation_external_holdout_revalidation=_load_current_l14(),
        r12_external_or_customer_holdout_raw_slice=_load_current_raw_slice(),
    )

    assert packet["schema_version"] == (
        R12_PRE_OUTCOME_OR_INDEPENDENT_PREDICTION_PACKET_SCHEMA_VERSION
    )
    assert packet["status"] == (
        "r12_pre_outcome_or_independent_prediction_packet_ready_independent_hindcast_not_pre_registered"
    )
    assert packet["claim_level"] == (
        "independent_feature_prediction_packet_not_revalidation"
    )
    assert packet["prediction_packet_summary"] == {
        "source_revalidation_artifact_id": (
            "r12-recall-mitigation-external-holdout-revalidation-current-001"
        ),
        "target_raw_slice_artifact_id": (
            "r12-external-or-customer-holdout-raw-slice-current-001"
        ),
        "target_outcome_period": "April 2026",
        "independent_feature_period": "March 2026",
        "prediction_case_count": 14,
        "source_row_count": 14,
        "matched_case_count": 14,
        "prior_month_observed_complaint_cases": 6024,
        "target_outcome_used_for_prediction_generation": False,
        "prediction_source_independent_of_target_outcome": True,
        "prediction_lock_timestamp_pre_target_outcome": False,
        "hindcast_independent_revalidation_ready": True,
        "pre_outcome_revalidation_ready": False,
    }
    assert packet["independent_prediction_source"] == {
        "source_id": "dot_may_2026_atcr_march_2026_table_3",
        "source_name": (
            "May 2026 Air Travel Consumer Report (March 2026 Data)"
        ),
        "source_owner": "U.S. Department of Transportation",
        "source_route": "external_public_official_prior_month_report",
        "source_table": "Table 3. Consumer Complaint Cases: U.S. Airlines",
        "feature_period": "March 2026",
        "target_period": "April 2026",
        "report_page_url": (
            "https://www.transportation.gov/resources/individuals/"
            "aviation-consumer-protection/"
            "may-2026-air-travel-consumer-report-march-and"
        ),
        "source_pdf_url": (
            "https://www.transportation.gov/sites/dot.gov/files/2026-05/"
            "May%202026%20ATCR.pdf"
        ),
        "source_extraction_note": (
            "DOT PDF text lines 2168-2195 report March 2026 Table 3 U.S. "
            "airline consumer complaint cases."
        ),
    }
    assert packet["prediction_generation_contract"] == {
        "prediction_route": "prior_month_complaint_share_hindcast",
        "target_case_axis": "carrier",
        "prediction_unit": "complaint_share",
        "normalization": "share_of_prior_month_total_complaint_cases",
        "uses_target_outcome_counts": False,
        "uses_target_outcome_category_mix": False,
        "prompt_or_persona_manual_patch_allowed": False,
        "revalidation_artifact_required": "r12_independent_hindcast_revalidation",
    }
    assert packet["prediction_independence_audit"] == {
        "uses_target_outcome_counts": False,
        "uses_target_outcome_category_mix": False,
        "uses_prior_month_official_source": True,
        "prediction_source_independent_of_target_outcome": True,
        "same_table_prediction_leakage_risk": False,
        "post_hoc_hindcast_risk": True,
        "pre_registered_before_target_outcome": False,
    }
    assert packet["locked_predictions"][0] == {
        "case_id": "dot_atcr_2026_04_us_airline_american_airlines",
        "carrier": "American Airlines",
        "target_period": "April 2026",
        "feature_period": "March 2026",
        "prediction_input_total": 1716,
        "prediction_share": 0.284861,
        "high_risk_threshold": 0.071429,
        "predicted_high_risk": True,
        "prediction_source_id": "dot_may_2026_atcr_march_2026_table_3",
        "target_outcome_used_for_prediction_generation": False,
    }
    assert packet["acceptance_gates"] == {
        "external_holdout_proxy_blocked": True,
        "independent_feature_source_ingested": True,
        "prediction_packet_generated": True,
        "minimum_case_overlap_met": True,
        "prediction_source_independent_of_target_outcome": True,
        "target_outcome_used_for_prediction_generation": False,
        "same_table_prediction_leakage_risk": False,
        "prediction_lock_timestamp_pre_target_outcome": False,
        "hindcast_independent_revalidation_ready": True,
        "pre_outcome_revalidation_ready": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert packet["acceptance_decision"] == (
        "accept_independent_hindcast_prediction_packet_block_pre_outcome_and_product_default"
    )
    assert packet["next_required_artifact"] == "r12_independent_hindcast_revalidation"
    assert (
        "pre-outcome prediction packet locked before target outcome"
        in packet["blocked_claims"]
    )
    assert "runtime_default_allowed=true" in packet["blocked_claims"]
    json.dumps(packet, allow_nan=False)


def test_r12_pre_outcome_or_independent_prediction_packet_cli_writes_artifact(
    tmp_path,
):
    revalidation_path = tmp_path / "r12-l14.json"
    raw_slice_path = tmp_path / "r12-raw-slice.json"
    output = tmp_path / "r12-l15.json"
    revalidation_path.write_text(json.dumps(_load_current_l14(), allow_nan=False))
    raw_slice_path.write_text(json.dumps(_load_current_raw_slice(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_pre_outcome_or_independent_prediction_packet.py",
            "--artifact-id",
            "r12-pre-outcome-or-independent-prediction-packet-cli",
            "--run-id",
            "r12-l15-test",
            "--r12-recall-mitigation-external-holdout-revalidation-path",
            str(revalidation_path),
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
        "r12-pre-outcome-or-independent-prediction-packet-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-pre-outcome-or-independent-prediction-packet-cli",
        "output": str(output),
        "status": (
            "r12_pre_outcome_or_independent_prediction_packet_ready_independent_hindcast_not_pre_registered"
        ),
    }


def _load_current_l14():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_recall_mitigation_external_holdout_revalidation/"
            "r12-recall-mitigation-external-holdout-revalidation-current-001.json"
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
