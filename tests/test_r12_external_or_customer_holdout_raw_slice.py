import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_external_or_customer_holdout_raw_slice import (
    R12_EXTERNAL_OR_CUSTOMER_HOLDOUT_RAW_SLICE_SCHEMA_VERSION,
    build_r12_external_or_customer_holdout_raw_slice,
)


def test_r12_external_or_customer_raw_slice_ingests_dot_atcr_rows_for_revalidation():
    report = build_r12_external_or_customer_holdout_raw_slice(
        artifact_id="r12-external-or-customer-holdout-raw-slice-test",
        run_id="r12-l13-test",
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            _load_current_l12_contract()
        ),
    )

    assert report["schema_version"] == (
        R12_EXTERNAL_OR_CUSTOMER_HOLDOUT_RAW_SLICE_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_external_or_customer_holdout_raw_slice_ready_external_dot_atcr_revalidation_pending"
    )
    assert report["claim_level"] == "official_external_raw_outcome_slice_only"
    assert report["slice_selection"] == {
        "selected_source_id": "dot_air_travel_consumer_report_complaint_candidate",
        "selected_source_name": (
            "June 2026 Air Travel Consumer Report (April 2026 Data)"
        ),
        "source_route": "external_public_official_report_slice",
        "source_owner": "U.S. Department of Transportation",
        "reporting_period": "April 2026",
        "report_issue_month": "June 2026",
        "source_table": "Table 3. Consumer Complaint Cases: U.S. Airlines",
        "report_page_url": (
            "https://www.transportation.gov/resources/individuals/"
            "aviation-consumer-protection/"
            "june-2026-air-travel-consumer-report-april-2026"
        ),
        "source_pdf_url": (
            "https://www.transportation.gov/sites/dot.gov/files/2026-06/"
            "June%202026%20ATCR.pdf"
        ),
        "source_extraction_note": (
            "DOT PDF text lines 1608-1635 report April 2026 Table 3 U.S. "
            "airline consumer complaint cases."
        ),
    }
    assert report["raw_slice_summary"] == {
        "entity_type": "us_airline",
        "source_row_count": 15,
        "case_count": 14,
        "total_observed_complaint_cases": 4839,
        "excluded_by_source_footnote_count": 1,
        "minimum_case_count_required": 10,
        "minimum_case_count_met": True,
        "prediction_fields_present": False,
        "ready_for_revalidation": False,
    }
    assert report["source_excluded_records"] == [
        {
            "case_id": "dot_atcr_2026_04_us_airline_hawaiian_airlines",
            "carrier": "Hawaiian Airlines",
            "total": 38,
            "exclusion_reason": (
                "DOT footnote states Hawaiian Airlines consumer complaint data "
                "is combined with and attributed to Alaska Airlines."
            ),
        }
    ]
    assert len(report["raw_records"]) == 14
    assert report["raw_records"][0] == {
        "case_id": "dot_atcr_2026_04_us_airline_american_airlines",
        "carrier": "American Airlines",
        "flight_problems": 336,
        "denied_boarding": 66,
        "reservations_ticketing_boarding": 101,
        "fees_fares": 44,
        "refunds": 391,
        "baggage": 148,
        "customer_service": 91,
        "disability": 57,
        "advertising": 14,
        "discrimination": 10,
        "animals": 2,
        "other": 81,
        "total": 1341,
    }
    assert sum(row["total"] for row in report["raw_records"]) == 4839
    for row in report["raw_records"]:
        category_sum = sum(
            row[key]
            for key in [
                "flight_problems",
                "denied_boarding",
                "reservations_ticketing_boarding",
                "fees_fares",
                "refunds",
                "baggage",
                "customer_service",
                "disability",
                "advertising",
                "discrimination",
                "animals",
                "other",
            ]
        )
        assert category_sum == row["total"]

    assert len(report["normalized_holdout_cases"]) == 14
    first_case = report["normalized_holdout_cases"][0]
    assert first_case == {
        "case_id": "dot_atcr_2026_04_us_airline_american_airlines",
        "scenario_family": "air_travel_service_complaint",
        "segment_column": "carrier",
        "segment_value": "American Airlines",
        "observed_outcome": 1341,
        "outcome_metric": "consumer_complaint_case_count",
        "outcome_window_start": "2026-04-01",
        "outcome_window_end": "2026-04-30",
        "source_ref": "dot_air_travel_consumer_report_complaint_candidate",
        "customer_approval_id": "official_public_source",
        "segment_sensitivity_level": "low_sensitive_business_entity",
        "static_prior_prediction": None,
        "interaction_prediction": None,
        "mechanism_tags": [
            "refund_pressure",
            "flight_schedule_disruption",
            "baggage_handling_friction",
        ],
    }
    assert report["acceptance_gates"] == {
        "l12_contract_present": True,
        "selected_source_matches_l12_preferred": True,
        "official_external_source": True,
        "actual_public_data_ingested": True,
        "raw_external_or_customer_slice_present": True,
        "minimum_case_count_met": True,
        "customer_slice_used": False,
        "customer_approval_present": False,
        "prediction_fields_present": False,
        "external_holdout_revalidation_ready": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "accept_raw_external_slice_for_revalidation_keep_product_default_blocked"
    )
    assert report["next_required_artifact"] == (
        "r12_recall_mitigation_external_holdout_revalidation"
    )
    assert "external holdout revalidation completed" in report["blocked_claims"]
    assert "actual public data ingestion has completed" not in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_external_or_customer_raw_slice_cli_writes_artifact(tmp_path):
    contract_path = tmp_path / "r12-l12-contract.json"
    output = tmp_path / "r12-external-or-customer-raw-slice.json"
    contract_path.write_text(json.dumps(_load_current_l12_contract(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_external_or_customer_holdout_raw_slice.py",
            "--artifact-id",
            "r12-external-or-customer-holdout-raw-slice-cli",
            "--run-id",
            "r12-l13-test",
            "--r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-path",
            str(contract_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r12-external-or-customer-holdout-raw-slice-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-external-or-customer-holdout-raw-slice-cli",
        "output": str(output),
        "status": (
            "r12_external_or_customer_holdout_raw_slice_ready_external_dot_atcr_revalidation_pending"
        ),
    }


def _load_current_l12_contract():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice/"
            "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-current-001.json"
        ).read_text()
    )
