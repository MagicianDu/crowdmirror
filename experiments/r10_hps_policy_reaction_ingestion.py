from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)


R10_HPS_POLICY_REACTION_INGESTION_SCHEMA_VERSION = (
    "r10-hps-policy-reaction-ingestion-v1"
)
R10_HPS_SOURCE_URL = (
    "https://www2.census.gov/programs-surveys/demo/datasets/hhp/2026/"
    "topical/HTOPS_HPS_2603_CSV.zip"
)
R10_HPS_OUTCOME_COLUMNS = ["PRICECHANGE", "PRICESTRESS", "PRICECONCERN"]
R10_HPS_SEGMENT_COLUMNS = [
    "REGION",
    "METRO_STATUS",
    "RHHINCOME",
    "RRACETH",
    "TAGE",
    "ESEX",
]
R10_HPS_WEIGHT_COLUMNS = ["PWEIGHT", "HWEIGHT"]
R10_HPS_MISSING_VALUES = {"", "-88", "-99", "-66", "-77"}
R10_HPS_CLAIM_BOUNDARY = (
    "R10 HPS policy reaction ingestion artifact. It proves a source-backed "
    "public-use microdata slice was read and profiled for guarded method "
    "development only; it is not field validation, not method superiority, "
    "and not runtime default authorization."
)


def build_r10_hps_policy_reaction_ingestion(
    *,
    artifact_id: str,
    run_id: str,
    input_zip_path: str | Path,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    input_zip = Path(input_zip_path)
    profile = _profile_hps_zip(input_zip)
    artifact = {
        "schema_version": R10_HPS_POLICY_REACTION_INGESTION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r10_hps_policy_reaction_ingestion_ready_guarded",
        "source_dataset": {
            "source_owner": "U.S. Census Bureau",
            "source_name": "HTOPS Household Pulse March 2026 PUF CSV",
            "release_window": "March 13, 2026 - March 30, 2026",
            "source_url": R10_HPS_SOURCE_URL,
        },
        "claim_boundary": R10_HPS_CLAIM_BOUNDARY,
        "ingestion_contract": {
            "source_backed_only": True,
            "actual_public_data_ingested": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
            "customer_visible": False,
        },
        "data_inventory": profile["data_inventory"],
        "data_profile": profile["data_profile"],
        "outcome_label_contract": {
            "outcome_family": "policy_or_price_reaction_survey_proxy",
            "outcome_columns": R10_HPS_OUTCOME_COLUMNS,
            "interpretation": {
                "PRICECHANGE": "reported price change exposure or perception",
                "PRICESTRESS": "reported stress from price changes",
                "PRICECONCERN": "reported concern about price changes",
            },
            "missing_values": sorted(R10_HPS_MISSING_VALUES),
        },
        "outcome_summary": profile["outcome_summary"],
        "segment_coverage": profile["segment_coverage"],
        "route_input_mapping": {
            "route_a_evidence_constrained_mechanism_operator": {
                "mechanism_priors": [
                    "economic_stress",
                    "price_sensitivity",
                    "policy_salience",
                ],
                "outcome_signal_columns": R10_HPS_OUTCOME_COLUMNS,
            },
            "route_b_semantic_precedent_retrieval": {
                "scenario_family": "policy_reaction_survey",
                "semantic_tags": [
                    "price_pressure",
                    "household_survey",
                    "public_use_microdata",
                ],
                "source_url": R10_HPS_SOURCE_URL,
            },
            "route_c_constrained_multi_agent_rollout": {
                "affected_segments": R10_HPS_SEGMENT_COLUMNS,
                "risk_observation_window": "March 13, 2026 - March 30, 2026",
            },
        },
        "acceptance_gates": {
            "official_public_zip_read": True,
            "puf_csv_detected": True,
            "minimum_rows_present": profile["data_profile"]["row_count"] > 0,
            "outcome_columns_present": all(
                column in profile["data_profile"]["columns"] for column in R10_HPS_OUTCOME_COLUMNS
            ),
            "segment_columns_present": all(
                column in profile["data_profile"]["columns"] for column in R10_HPS_SEGMENT_COLUMNS
            ),
            "actual_public_data_ingested": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "allowed_claims": [
            "R10 L1 ingested and profiled the official HPS/HTOPS March 2026 PUF CSV.",
            "The artifact can provide guarded survey outcome proxy inputs for R10 routes.",
        ],
        "blocked_claims": [
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "runtime default ready",
            "R10 validated",
            "R10 supports Product core method by default",
            "HPS survey proxy equals customer field outcome",
            "accuracy superiority",
            "精准预测系统",
        ],
    }
    assert_strict_json(artifact)
    return artifact


def write_r10_hps_policy_reaction_ingestion(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r10_hps_policy_reaction_ingestion(**kwargs),
    )


def _profile_hps_zip(input_zip: Path) -> dict[str, Any]:
    with zipfile.ZipFile(input_zip) as archive:
        members = archive.namelist()
        puf_member = _find_puf_csv_member(members)
        with archive.open(puf_member) as raw_file:
            reader = csv.DictReader(io.TextIOWrapper(raw_file, encoding="utf-8-sig"))
            if reader.fieldnames is None:
                raise ValueError("PUF CSV must include a header row")
            columns = list(reader.fieldnames)
            outcome_counts = {column: Counter() for column in R10_HPS_OUTCOME_COLUMNS}
            outcome_weighted_counts = {column: Counter() for column in R10_HPS_OUTCOME_COLUMNS}
            segment_values = {column: set() for column in R10_HPS_SEGMENT_COLUMNS}
            segment_non_missing = Counter()
            row_count = 0
            for row in reader:
                row_count += 1
                weight = _float_or_zero(row.get("PWEIGHT"))
                for column in R10_HPS_OUTCOME_COLUMNS:
                    value = _normalized_value(row.get(column))
                    if value is None:
                        continue
                    outcome_counts[column][value] += 1
                    outcome_weighted_counts[column][value] += weight
                for column in R10_HPS_SEGMENT_COLUMNS:
                    value = _normalized_value(row.get(column))
                    if value is None:
                        continue
                    segment_non_missing[column] += 1
                    segment_values[column].add(value)
    return {
        "data_inventory": {
            "input_zip_path": str(input_zip),
            "zip_member_count": len(members),
            "zip_members": members,
            "puf_csv_member": puf_member,
            "replicate_weight_members": [
                member for member in members if "REPWGT" in member.upper()
            ],
            "data_dictionary_members": [
                member for member in members if "DICTIONARY" in member.upper()
            ],
        },
        "data_profile": {
            "row_count": row_count,
            "column_count": len(columns),
            "columns": columns,
            "outcome_columns_present": [
                column for column in R10_HPS_OUTCOME_COLUMNS if column in columns
            ],
            "segment_columns_present": [
                column for column in R10_HPS_SEGMENT_COLUMNS if column in columns
            ],
            "weight_columns_present": [
                column for column in R10_HPS_WEIGHT_COLUMNS if column in columns
            ],
        },
        "outcome_summary": {
            column: _outcome_summary(
                counts=outcome_counts[column],
                weighted_counts=outcome_weighted_counts[column],
            )
            for column in R10_HPS_OUTCOME_COLUMNS
        },
        "segment_coverage": {
            column: {
                "present": column in columns,
                "non_missing_count": int(segment_non_missing[column]),
                "unique_value_count": len(segment_values[column]),
            }
            for column in R10_HPS_SEGMENT_COLUMNS
        },
    }


def _find_puf_csv_member(members: list[str]) -> str:
    candidates = [
        member
        for member in members
        if member.upper().endswith("_PUF.CSV") and "REPWGT" not in member.upper()
    ]
    if len(candidates) != 1:
        raise ValueError(f"expected exactly one main PUF CSV member, got {candidates}")
    return candidates[0]


def _normalized_value(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if normalized.endswith(".0"):
        normalized = normalized[:-2]
    if normalized in R10_HPS_MISSING_VALUES:
        return None
    return normalized


def _float_or_zero(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _outcome_summary(*, counts: Counter, weighted_counts: Counter) -> dict[str, Any]:
    valid_response_count = sum(counts.values())
    weighted_valid_total = round(sum(weighted_counts.values()), 6)
    if weighted_valid_total <= 0:
        distribution = {}
    else:
        distribution = {
            value: round(weight / weighted_valid_total, 6)
            for value, weight in sorted(weighted_counts.items())
        }
    return {
        "valid_response_count": int(valid_response_count),
        "weighted_valid_total": weighted_valid_total,
        "response_distribution": distribution,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--input-zip", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r10_hps_policy_reaction_ingestion(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        input_zip_path=args.input_zip,
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
