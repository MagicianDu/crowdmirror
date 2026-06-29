from __future__ import annotations

import argparse
import csv
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
from experiments.r12_pre_outcome_or_customer_field_outcome_revalidation import (
    R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_REVALIDATION_SCHEMA_VERSION,
)


R12_TARGET_OUTCOME_OR_CUSTOMER_FIELD_SLICE_ARRIVAL_SCHEMA_VERSION = (
    "r12-target-outcome-or-customer-field-slice-arrival-v1"
)
REQUIRED_CUSTOMER_FIELD_SLICE_FIELDS = [
    "case_id",
    "segment_id",
    "scenario_id",
    "prediction_share_or_score",
    "observed_outcome",
    "outcome_timestamp",
    "customer_approval_reference",
]
MINIMUM_CUSTOMER_FIELD_CASE_COUNT = 10


def build_r12_target_outcome_or_customer_field_slice_arrival(
    *,
    artifact_id: str,
    run_id: str,
    r12_pre_outcome_or_customer_field_outcome_revalidation: dict[str, Any],
    arrival_checked_at: str,
    customer_field_slice_path: str | Path | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    arrival_checked_at = non_empty_string(
        arrival_checked_at,
        field="arrival_checked_at",
    )
    _validate_l19_revalidation(
        r12_pre_outcome_or_customer_field_outcome_revalidation
    )

    l19 = r12_pre_outcome_or_customer_field_outcome_revalidation
    summary = l19["revalidation_summary"]
    slice_validation = _customer_field_slice_validation(customer_field_slice_path)
    customer_slice_ready = (
        slice_validation["case_count"] >= MINIMUM_CUSTOMER_FIELD_CASE_COUNT
        and not slice_validation["missing_required_fields"]
        and slice_validation["customer_approval_present"] is True
    )
    outcome_source_arrived = customer_slice_ready
    gates = {
        "revalidation_harness_ready": True,
        "outcome_source_arrived": outcome_source_arrived,
        "target_outcome_artifact_present": False,
        "customer_field_slice_present": customer_slice_ready,
        "customer_approval_present": slice_validation[
            "customer_approval_present"
        ],
        "field_or_pre_outcome_revalidation_ready": customer_slice_ready,
        "metrics_computed": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    if customer_slice_ready:
        status = (
            "r12_target_outcome_or_customer_field_slice_arrival_ready_customer_field_slice"
        )
        claim_level = "customer_field_slice_arrived_revalidation_ready"
        acceptance_decision = (
            "accept_customer_field_slice_arrival_enable_revalidation_not_product_default"
        )
        next_required_artifact = (
            "r12_pre_outcome_or_customer_field_outcome_revalidation_with_arrived_outcome"
        )
        allowed_claims = [
            (
                "Customer-approved field slice has arrived and can trigger "
                "outcome revalidation."
            ),
            (
                "R12 remains Product-default blocked until revalidation metrics "
                "are computed and reviewed."
            ),
        ]
    else:
        status = "r12_target_outcome_or_customer_field_slice_arrival_pending_no_source"
        claim_level = "outcome_source_arrival_pending"
        acceptance_decision = (
            "keep_waiting_for_target_outcome_or_customer_field_slice"
        )
        next_required_artifact = (
            "r12_target_outcome_or_customer_field_slice_arrival"
        )
        allowed_claims = [
            (
                "R12 has a source-arrival gate ready for future target outcome "
                "or customer field slice."
            )
        ]

    report = {
        "schema_version": (
            R12_TARGET_OUTCOME_OR_CUSTOMER_FIELD_SLICE_ARRIVAL_SCHEMA_VERSION
        ),
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "claim_level": claim_level,
        "arrival_summary": {
            "revalidation_artifact_id": l19["artifact_id"],
            "target_outcome_period": summary["target_outcome_period"],
            "prediction_case_count": summary["prediction_case_count"],
            "prediction_lock_timestamp": summary["prediction_lock_timestamp"],
            "arrival_checked_at": arrival_checked_at,
            "target_outcome_artifact_path_provided": False,
            "customer_field_slice_path_provided": (
                customer_field_slice_path is not None
            ),
            "validated_customer_field_case_count": slice_validation["case_count"],
        },
        "public_target_outcome_availability": _public_target_outcome_availability(),
        "customer_field_slice_validation": slice_validation,
        "acceptance_gates": gates,
        "acceptance_decision": acceptance_decision,
        "next_required_artifact": next_required_artifact,
        "source_refs": [
            l19["artifact_id"],
            "dot_air_travel_consumer_reports_index_current",
            "dot_airconsumer_latest_news_current",
            *(
                [f"customer_field_slice:{slice_validation['slice_path']}"]
                if slice_validation["slice_path"]
                else []
            ),
        ],
        "source_registry": [
            {
                "artifact_id": l19["artifact_id"],
                "path": (
                    "experiments/results/"
                    "r12_pre_outcome_or_customer_field_outcome_revalidation/"
                    "r12-pre-outcome-or-customer-field-outcome-revalidation-current-001.json"
                ),
            },
            {
                "artifact_id": "dot_air_travel_consumer_reports_index_current",
                "path": (
                    "https://www.transportation.gov/individuals/"
                    "aviation-consumer-protection/air-travel-consumer-reports"
                ),
            },
            {
                "artifact_id": "dot_airconsumer_latest_news_current",
                "path": "https://www.transportation.gov/airconsumer/latest-news",
            },
            *(
                [
                    {
                        "artifact_id": (
                            f"customer_field_slice:{slice_validation['slice_path']}"
                        ),
                        "path": slice_validation["slice_path"],
                    }
                ]
                if slice_validation["slice_path"]
                else []
            ),
        ],
        "allowed_claims": allowed_claims,
        "blocked_claims": [
            *(
                ["outcome_source_arrived=true"]
                if not outcome_source_arrived
                else []
            ),
            "metrics_computed=true",
            "field_or_pre_outcome_revalidation_passed=true",
            "field_outcome_validated=true",
            "Product default can use R12 outcome source by default",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_target_outcome_or_customer_field_slice_arrival(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_target_outcome_or_customer_field_slice_arrival(**kwargs),
    )


def _validate_l19_revalidation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_REVALIDATION_SCHEMA_VERSION
    ):
        raise ValueError("r12 L19 outcome revalidation schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L19 outcome revalidation acceptance_gates required")
    if gates.get("pre_outcome_trial_locked") is not True:
        raise ValueError("r12 L19 requires locked pre-outcome trial")
    if gates.get("metrics_computed") is not False:
        raise ValueError("r12 L19 must not have computed metrics yet")
    if gates.get("field_or_pre_outcome_revalidation_passed") is not False:
        raise ValueError("r12 L19 must not be passed without outcome")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L19 must block runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L19 must block Product default")


def _customer_field_slice_validation(
    customer_field_slice_path: str | Path | None,
) -> dict[str, Any]:
    if customer_field_slice_path is None:
        return {
            "accepted_formats": ["csv", "jsonl"],
            "minimum_case_count": MINIMUM_CUSTOMER_FIELD_CASE_COUNT,
            "required_fields": REQUIRED_CUSTOMER_FIELD_SLICE_FIELDS,
            "slice_path": None,
            "case_count": 0,
            "missing_required_fields": [],
            "customer_approval_present": False,
        }
    path = Path(customer_field_slice_path)
    rows = _read_customer_field_slice(path)
    present_fields = set(rows[0].keys()) if rows else set()
    missing = [
        field
        for field in REQUIRED_CUSTOMER_FIELD_SLICE_FIELDS
        if field not in present_fields
    ]
    approval_present = bool(rows) and all(
        str(row.get("customer_approval_reference", "")).strip()
        for row in rows
    )
    return {
        "accepted_formats": ["csv", "jsonl"],
        "minimum_case_count": MINIMUM_CUSTOMER_FIELD_CASE_COUNT,
        "required_fields": REQUIRED_CUSTOMER_FIELD_SLICE_FIELDS,
        "slice_path": str(path),
        "case_count": len(rows),
        "missing_required_fields": missing,
        "customer_approval_present": approval_present,
    }


def _read_customer_field_slice(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".csv":
        with path.open(newline="") as fh:
            return [dict(row) for row in csv.DictReader(fh)]
    if path.suffix == ".jsonl":
        rows = []
        for line in path.read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows
    raise ValueError("customer field slice must be csv or jsonl")


def _public_target_outcome_availability() -> dict[str, Any]:
    return {
        "expected_public_report": (
            "July 2026 Air Travel Consumer Report (May 2026 Data)"
        ),
        "latest_available_report": (
            "June 2026 Air Travel Consumer Report (April 2026 Data)"
        ),
        "official_reports_index_url": (
            "https://www.transportation.gov/individuals/aviation-consumer-protection/air-travel-consumer-reports"
        ),
        "latest_news_url": "https://www.transportation.gov/airconsumer/latest-news",
        "target_report_found": False,
        "target_outcome_artifact_path": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--r12-pre-outcome-or-customer-field-outcome-revalidation-path",
        required=True,
    )
    parser.add_argument("--arrival-checked-at", required=True)
    parser.add_argument("--customer-field-slice-path")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_target_outcome_or_customer_field_slice_arrival(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_pre_outcome_or_customer_field_outcome_revalidation=load_json_artifact(
            args.r12_pre_outcome_or_customer_field_outcome_revalidation_path
        ),
        arrival_checked_at=args.arrival_checked_at,
        customer_field_slice_path=args.customer_field_slice_path,
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
