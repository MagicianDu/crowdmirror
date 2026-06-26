from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    assert_strict_json,
    load_json_artifact,
    non_empty_string,
    write_json_artifact,
)
from experiments.r12_recall_mitigation_external_holdout_ingestion_or_customer_slice import (
    R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_INGESTION_OR_CUSTOMER_SLICE_SCHEMA_VERSION,
)


R12_EXTERNAL_OR_CUSTOMER_HOLDOUT_RAW_SLICE_SCHEMA_VERSION = (
    "r12-external-or-customer-holdout-raw-slice-v1"
)


def build_r12_external_or_customer_holdout_raw_slice(
    *,
    artifact_id: str,
    run_id: str,
    r12_recall_mitigation_external_holdout_ingestion_or_customer_slice: dict[
        str, Any
    ],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_l12_contract(
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice
    )

    raw_records = _dot_atcr_april_2026_raw_records()
    source_excluded_records = _dot_atcr_april_2026_source_excluded_records()
    normalized_cases = _normalized_holdout_cases(raw_records)
    total_observed = sum(row["total"] for row in raw_records)
    minimum_case_count = (
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice[
            "customer_slice_contract"
        ]["minimum_case_count"]
    )
    gates = {
        "l12_contract_present": True,
        "selected_source_matches_l12_preferred": True,
        "official_external_source": True,
        "actual_public_data_ingested": True,
        "raw_external_or_customer_slice_present": True,
        "minimum_case_count_met": len(raw_records) >= minimum_case_count,
        "customer_slice_used": False,
        "customer_approval_present": False,
        "prediction_fields_present": False,
        "external_holdout_revalidation_ready": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    report = {
        "schema_version": R12_EXTERNAL_OR_CUSTOMER_HOLDOUT_RAW_SLICE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_external_or_customer_holdout_raw_slice_ready_external_dot_atcr_revalidation_pending"
        ),
        "claim_level": "official_external_raw_outcome_slice_only",
        "slice_selection": _slice_selection(),
        "raw_slice_summary": {
            "entity_type": "us_airline",
            "source_row_count": len(raw_records) + len(source_excluded_records),
            "case_count": len(raw_records),
            "total_observed_complaint_cases": total_observed,
            "excluded_by_source_footnote_count": len(source_excluded_records),
            "minimum_case_count_required": minimum_case_count,
            "minimum_case_count_met": gates["minimum_case_count_met"],
            "prediction_fields_present": gates["prediction_fields_present"],
            "ready_for_revalidation": gates["external_holdout_revalidation_ready"],
        },
        "source_excluded_records": source_excluded_records,
        "raw_records": raw_records,
        "normalized_holdout_cases": normalized_cases,
        "acceptance_gates": gates,
        "acceptance_decision": (
            "accept_raw_external_slice_for_revalidation_keep_product_default_blocked"
        ),
        "next_required_artifact": "r12_recall_mitigation_external_holdout_revalidation",
        "source_refs": [
            r12_recall_mitigation_external_holdout_ingestion_or_customer_slice[
                "artifact_id"
            ],
            "dot_air_travel_consumer_report_complaint_candidate",
        ],
        "source_registry": [
            {
                "artifact_id": (
                    r12_recall_mitigation_external_holdout_ingestion_or_customer_slice[
                        "artifact_id"
                    ]
                ),
                "path": (
                    "experiments/results/"
                    "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice/"
                    "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-current-001.json"
                ),
            },
            {
                "artifact_id": "dot_air_travel_consumer_report_complaint_candidate",
                "path": _slice_selection()["source_pdf_url"],
            },
        ],
        "allowed_claims": [
            (
                "A DOT Air Travel Consumer Report raw complaint slice has been "
                "ingested for R12 external holdout preparation."
            ),
            (
                "The raw slice can feed revalidation once static-prior and "
                "interaction predictions are generated for the same cases."
            ),
        ],
        "blocked_claims": [
            "external holdout revalidation completed",
            "prediction fields present for DOT raw slice",
            "R12 Product default high-risk recovery validated",
            "R12 Product core method ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "customer outcome validated",
            "精准预测系统",
        ],
    }
    _validate_raw_records(raw_records)
    assert_strict_json(report)
    return report


def write_r12_external_or_customer_holdout_raw_slice(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_external_or_customer_holdout_raw_slice(**kwargs),
    )


def _validate_l12_contract(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_INGESTION_OR_CUSTOMER_SLICE_SCHEMA_VERSION
    ):
        raise ValueError("r12 L12 external/customer contract schema_version is invalid")
    if artifact.get("next_required_artifact") != (
        "r12_external_or_customer_holdout_raw_slice"
    ):
        raise ValueError("r12 L12 contract must request raw slice artifact")
    route = artifact.get("route_selection")
    if not isinstance(route, dict):
        raise ValueError("r12 L12 contract route_selection required")
    if route.get("preferred_external_source_id") != (
        "dot_air_travel_consumer_report_complaint_candidate"
    ):
        raise ValueError("r12 L12 contract must prefer DOT ATCR for this slice")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L12 contract acceptance_gates required")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L12 contract must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L12 contract must block runtime default")


def _slice_selection() -> dict[str, str]:
    return {
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


def _dot_atcr_april_2026_raw_records() -> list[dict[str, Any]]:
    return [
        _raw_record("American Airlines", 336, 66, 101, 44, 391, 148, 91, 57, 14, 10, 2, 81, 1341),
        _raw_record("Alaska Airlines", 25, 9, 16, 6, 39, 25, 20, 6, 0, 2, 2, 11, 161),
        _raw_record("Allegiant Air", 6, 0, 0, 6, 11, 7, 4, 4, 1, 3, 0, 2, 44),
        _raw_record("Avelo Airlines", 3, 1, 5, 4, 28, 5, 2, 2, 0, 0, 0, 0, 50),
        _raw_record("Breeze Airways", 11, 2, 4, 1, 13, 14, 7, 4, 1, 1, 0, 3, 61),
        _raw_record("Contour Airlines", 0, 0, 0, 0, 2, 3, 0, 1, 0, 0, 0, 0, 6),
        _raw_record("Delta Air Lines", 157, 30, 73, 30, 170, 180, 41, 25, 5, 10, 3, 45, 769),
        _raw_record("Frontier Airlines", 125, 49, 72, 24, 161, 96, 47, 17, 12, 9, 0, 47, 659),
        _raw_record("JetBlue", 68, 13, 17, 11, 63, 26, 26, 24, 2, 5, 0, 15, 270),
        _raw_record("Southwest Airlines", 25, 11, 24, 10, 35, 30, 28, 22, 2, 6, 0, 25, 218),
        _raw_record("Sun Country Airlines", 2, 0, 0, 1, 1, 2, 4, 0, 0, 1, 0, 3, 14),
        _raw_record("Spirit Airlines", 138, 28, 33, 18, 162, 39, 21, 11, 1, 2, 0, 22, 475),
        _raw_record("United Airlines", 149, 18, 57, 31, 243, 99, 61, 25, 11, 8, 2, 55, 759),
        _raw_record("Other U.S. Airline", 4, 0, 0, 1, 1, 1, 1, 1, 0, 2, 0, 1, 12),
    ]


def _dot_atcr_april_2026_source_excluded_records() -> list[dict[str, Any]]:
    return [
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


def _raw_record(
    carrier: str,
    flight_problems: int,
    denied_boarding: int,
    reservations_ticketing_boarding: int,
    fees_fares: int,
    refunds: int,
    baggage: int,
    customer_service: int,
    disability: int,
    advertising: int,
    discrimination: int,
    animals: int,
    other: int,
    total: int,
) -> dict[str, Any]:
    return {
        "case_id": f"dot_atcr_2026_04_us_airline_{_slug(carrier)}",
        "carrier": carrier,
        "flight_problems": flight_problems,
        "denied_boarding": denied_boarding,
        "reservations_ticketing_boarding": reservations_ticketing_boarding,
        "fees_fares": fees_fares,
        "refunds": refunds,
        "baggage": baggage,
        "customer_service": customer_service,
        "disability": disability,
        "advertising": advertising,
        "discrimination": discrimination,
        "animals": animals,
        "other": other,
        "total": total,
    }


def _normalized_holdout_cases(
    raw_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "case_id": record["case_id"],
            "scenario_family": "air_travel_service_complaint",
            "segment_column": "carrier",
            "segment_value": record["carrier"],
            "observed_outcome": record["total"],
            "outcome_metric": "consumer_complaint_case_count",
            "outcome_window_start": "2026-04-01",
            "outcome_window_end": "2026-04-30",
            "source_ref": "dot_air_travel_consumer_report_complaint_candidate",
            "customer_approval_id": "official_public_source",
            "segment_sensitivity_level": "low_sensitive_business_entity",
            "static_prior_prediction": None,
            "interaction_prediction": None,
            "mechanism_tags": _mechanism_tags(record),
        }
        for record in raw_records
    ]


def _mechanism_tags(record: dict[str, Any]) -> list[str]:
    ranked = sorted(
        [
            ("refund_pressure", record["refunds"]),
            ("flight_schedule_disruption", record["flight_problems"]),
            ("baggage_handling_friction", record["baggage"]),
            ("service_quality_friction", record["customer_service"]),
            ("accessibility_or_rights_friction", record["disability"]),
        ],
        key=lambda item: (-item[1], item[0]),
    )
    return [tag for tag, value in ranked[:3] if value > 0]


def _validate_raw_records(records: list[dict[str, Any]]) -> None:
    seen = set()
    for record in records:
        case_id = record["case_id"]
        if case_id in seen:
            raise ValueError(f"duplicate raw slice case_id: {case_id}")
        seen.add(case_id)
        category_sum = sum(
            record[key]
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
        if category_sum != record["total"]:
            raise ValueError(f"raw slice category total mismatch for {case_id}")


def _slug(value: str) -> str:
    return value.lower().replace(" ", "_")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-path",
        required=True,
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_external_or_customer_holdout_raw_slice(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            load_json_artifact(
                args.r12_recall_mitigation_external_holdout_ingestion_or_customer_slice_path
            )
        ),
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
