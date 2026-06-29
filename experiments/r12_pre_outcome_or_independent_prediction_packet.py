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
from experiments.r12_external_or_customer_holdout_raw_slice import (
    R12_EXTERNAL_OR_CUSTOMER_HOLDOUT_RAW_SLICE_SCHEMA_VERSION,
)
from experiments.r12_recall_mitigation_external_holdout_revalidation import (
    R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_REVALIDATION_SCHEMA_VERSION,
)


R12_PRE_OUTCOME_OR_INDEPENDENT_PREDICTION_PACKET_SCHEMA_VERSION = (
    "r12-pre-outcome-or-independent-prediction-packet-v1"
)


def build_r12_pre_outcome_or_independent_prediction_packet(
    *,
    artifact_id: str,
    run_id: str,
    r12_recall_mitigation_external_holdout_revalidation: dict[str, Any],
    r12_external_or_customer_holdout_raw_slice: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_l14_revalidation(r12_recall_mitigation_external_holdout_revalidation)
    _validate_raw_slice(r12_external_or_customer_holdout_raw_slice)

    raw_records = r12_external_or_customer_holdout_raw_slice["raw_records"]
    target_carriers = [record["carrier"] for record in raw_records]
    source_records = _dot_atcr_march_2026_prior_month_records()
    source_by_carrier = {record["carrier"]: record for record in source_records}
    matched = [
        source_by_carrier[carrier]
        for carrier in target_carriers
        if carrier in source_by_carrier
    ]
    source_total = sum(record["total"] for record in source_records)
    high_risk_threshold = 1 / len(target_carriers)
    locked_predictions = [
        {
            "case_id": target_record["case_id"],
            "carrier": target_record["carrier"],
            "target_period": "April 2026",
            "feature_period": "March 2026",
            "prediction_input_total": source_by_carrier[
                target_record["carrier"]
            ]["total"],
            "prediction_share": _round6(
                source_by_carrier[target_record["carrier"]]["total"]
                / source_total
            ),
            "high_risk_threshold": _round6(high_risk_threshold),
            "predicted_high_risk": (
                source_by_carrier[target_record["carrier"]]["total"]
                / source_total
                > high_risk_threshold
            ),
            "prediction_source_id": "dot_may_2026_atcr_march_2026_table_3",
            "target_outcome_used_for_prediction_generation": False,
        }
        for target_record in raw_records
    ]
    gates = {
        "external_holdout_proxy_blocked": (
            r12_recall_mitigation_external_holdout_revalidation[
                "acceptance_gates"
            ]["external_holdout_revalidation_passed"]
            is False
        ),
        "independent_feature_source_ingested": True,
        "prediction_packet_generated": True,
        "minimum_case_overlap_met": len(matched) >= 10,
        "prediction_source_independent_of_target_outcome": True,
        "target_outcome_used_for_prediction_generation": False,
        "same_table_prediction_leakage_risk": False,
        "prediction_lock_timestamp_pre_target_outcome": False,
        "hindcast_independent_revalidation_ready": len(matched) >= 10,
        "pre_outcome_revalidation_ready": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    packet = {
        "schema_version": (
            R12_PRE_OUTCOME_OR_INDEPENDENT_PREDICTION_PACKET_SCHEMA_VERSION
        ),
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_pre_outcome_or_independent_prediction_packet_ready_independent_hindcast_not_pre_registered"
        ),
        "claim_level": "independent_feature_prediction_packet_not_revalidation",
        "prediction_packet_summary": {
            "source_revalidation_artifact_id": (
                r12_recall_mitigation_external_holdout_revalidation[
                    "artifact_id"
                ]
            ),
            "target_raw_slice_artifact_id": (
                r12_external_or_customer_holdout_raw_slice["artifact_id"]
            ),
            "target_outcome_period": "April 2026",
            "independent_feature_period": "March 2026",
            "prediction_case_count": len(locked_predictions),
            "source_row_count": len(source_records),
            "matched_case_count": len(matched),
            "prior_month_observed_complaint_cases": source_total,
            "target_outcome_used_for_prediction_generation": False,
            "prediction_source_independent_of_target_outcome": True,
            "prediction_lock_timestamp_pre_target_outcome": False,
            "hindcast_independent_revalidation_ready": (
                gates["hindcast_independent_revalidation_ready"]
            ),
            "pre_outcome_revalidation_ready": False,
        },
        "independent_prediction_source": _independent_prediction_source(),
        "prediction_generation_contract": {
            "prediction_route": "prior_month_complaint_share_hindcast",
            "target_case_axis": "carrier",
            "prediction_unit": "complaint_share",
            "normalization": "share_of_prior_month_total_complaint_cases",
            "uses_target_outcome_counts": False,
            "uses_target_outcome_category_mix": False,
            "prompt_or_persona_manual_patch_allowed": False,
            "revalidation_artifact_required": "r12_independent_hindcast_revalidation",
        },
        "prediction_independence_audit": {
            "uses_target_outcome_counts": False,
            "uses_target_outcome_category_mix": False,
            "uses_prior_month_official_source": True,
            "prediction_source_independent_of_target_outcome": True,
            "same_table_prediction_leakage_risk": False,
            "post_hoc_hindcast_risk": True,
            "pre_registered_before_target_outcome": False,
        },
        "locked_predictions": locked_predictions,
        "acceptance_gates": gates,
        "acceptance_decision": (
            "accept_independent_hindcast_prediction_packet_block_pre_outcome_and_product_default"
        ),
        "next_required_artifact": "r12_independent_hindcast_revalidation",
        "source_refs": [
            r12_recall_mitigation_external_holdout_revalidation["artifact_id"],
            r12_external_or_customer_holdout_raw_slice["artifact_id"],
            "dot_may_2026_atcr_march_2026_table_3",
        ],
        "source_registry": [
            {
                "artifact_id": (
                    r12_recall_mitigation_external_holdout_revalidation[
                        "artifact_id"
                    ]
                ),
                "path": (
                    "experiments/results/"
                    "r12_recall_mitigation_external_holdout_revalidation/"
                    "r12-recall-mitigation-external-holdout-revalidation-current-001.json"
                ),
            },
            {
                "artifact_id": (
                    r12_external_or_customer_holdout_raw_slice["artifact_id"]
                ),
                "path": (
                    "experiments/results/r12_external_or_customer_holdout_raw_slice/"
                    "r12-external-or-customer-holdout-raw-slice-current-001.json"
                ),
            },
            {
                "artifact_id": "dot_may_2026_atcr_march_2026_table_3",
                "path": _independent_prediction_source()["source_pdf_url"],
            },
        ],
        "allowed_claims": [
            (
                "R12 has an independent prior-month official prediction packet "
                "ready for hindcast revalidation."
            ),
            (
                "The packet does not use the April target outcome values or "
                "same-table category mix to generate predictions."
            ),
        ],
        "blocked_claims": [
            "pre-outcome prediction packet locked before target outcome",
            "independent hindcast revalidation passed",
            "R12 Product default high-risk recovery validated",
            "R12 Product core method ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "customer outcome validated",
            "精准预测系统",
        ],
    }
    _validate_prediction_packet(packet)
    assert_strict_json(packet)
    return packet


def write_r12_pre_outcome_or_independent_prediction_packet(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_pre_outcome_or_independent_prediction_packet(**kwargs),
    )


def _validate_l14_revalidation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_REVALIDATION_SCHEMA_VERSION
    ):
        raise ValueError("r12 L14 revalidation schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L14 revalidation acceptance_gates required")
    if gates.get("external_holdout_revalidation_passed") is not False:
        raise ValueError("r12 L15 expects L14 proxy revalidation to be blocked")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L14 revalidation must not allow Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L14 revalidation must not allow runtime default")


def _validate_raw_slice(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_EXTERNAL_OR_CUSTOMER_HOLDOUT_RAW_SLICE_SCHEMA_VERSION
    ):
        raise ValueError("r12 raw slice schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 raw slice acceptance_gates required")
    if gates.get("raw_external_or_customer_slice_present") is not True:
        raise ValueError("r12 raw slice must be present")
    if gates.get("actual_public_data_ingested") is not True:
        raise ValueError("r12 raw slice must ingest actual public data")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 raw slice must not allow Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 raw slice must not allow runtime default")


def _validate_prediction_packet(packet: dict[str, Any]) -> None:
    predictions = packet["locked_predictions"]
    carriers = [row["carrier"] for row in predictions]
    if len(carriers) != len(set(carriers)):
        raise ValueError("r12 L15 prediction carriers must be unique")
    if any(row["target_outcome_used_for_prediction_generation"] for row in predictions):
        raise ValueError("r12 L15 predictions must not use target outcome")


def _independent_prediction_source() -> dict[str, str]:
    return {
        "source_id": "dot_may_2026_atcr_march_2026_table_3",
        "source_name": "May 2026 Air Travel Consumer Report (March 2026 Data)",
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


def _dot_atcr_march_2026_prior_month_records() -> list[dict[str, Any]]:
    return [
        _raw_record("American Airlines", 425, 76, 114, 47, 622, 185, 86, 46, 9, 12, 1, 93, 1716),
        _raw_record("Alaska Airlines", 38, 14, 21, 4, 47, 36, 21, 10, 1, 2, 1, 23, 218),
        _raw_record("Allegiant Air", 20, 1, 9, 3, 16, 9, 8, 7, 2, 2, 1, 6, 84),
        _raw_record("Avelo Airlines", 6, 0, 4, 4, 24, 4, 2, 3, 1, 1, 0, 4, 53),
        _raw_record("Breeze Airways", 12, 2, 3, 3, 11, 19, 4, 5, 0, 0, 0, 2, 61),
        _raw_record("Contour Airlines", 2, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 5),
        _raw_record("Delta Air Lines", 269, 39, 71, 30, 210, 199, 60, 26, 13, 5, 2, 75, 999),
        _raw_record("Frontier Airlines", 178, 74, 69, 25, 208, 106, 43, 16, 10, 3, 0, 40, 772),
        _raw_record("JetBlue", 94, 11, 22, 9, 106, 35, 22, 9, 5, 0, 1, 19, 333),
        _raw_record("Southwest Airlines", 54, 13, 21, 8, 51, 32, 39, 26, 3, 5, 1, 15, 268),
        _raw_record("Sun Country Airlines", 9, 4, 1, 2, 1, 5, 1, 2, 1, 0, 0, 1, 27),
        _raw_record("Spirit Airlines", 226, 33, 42, 21, 189, 27, 40, 8, 4, 2, 2, 30, 624),
        _raw_record("United Airlines", 200, 25, 67, 24, 272, 92, 65, 37, 6, 10, 1, 56, 855),
        _raw_record("Other U.S. Airline", 2, 0, 1, 1, 2, 1, 0, 0, 0, 0, 0, 2, 9),
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


def _round6(value: float) -> float:
    return round(float(value), 6)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--r12-recall-mitigation-external-holdout-revalidation-path",
        required=True,
    )
    parser.add_argument("--r12-external-or-customer-holdout-raw-slice-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_pre_outcome_or_independent_prediction_packet(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_recall_mitigation_external_holdout_revalidation=load_json_artifact(
            args.r12_recall_mitigation_external_holdout_revalidation_path
        ),
        r12_external_or_customer_holdout_raw_slice=load_json_artifact(
            args.r12_external_or_customer_holdout_raw_slice_path
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
