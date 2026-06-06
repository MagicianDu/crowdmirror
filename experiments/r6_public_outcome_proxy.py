from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    load_json_artifact,
    non_empty_string,
    write_json_artifact,
)


R6_PUBLIC_OUTCOME_PROXY_SCHEMA_VERSION = "r6-public-outcome-proxy-v1"
DEFAULT_PUBLIC_INGESTION_PATH = (
    "experiments/results/policy_reaction_benchmark/"
    "policy-reaction-htops-2506-public-ingestion-001.json"
)
DEFAULT_SOURCE_INTAKE_PATH = "experiments/results/policy_data_intake/hps-htops-food-cost-intake.json"
TARGET_CASE_ID = "generic-public-service-policy-change"


def build_r6_public_outcome_proxy(
    *,
    artifact_id: str,
    run_id: str,
    public_ingestion_path: str | Path = DEFAULT_PUBLIC_INGESTION_PATH,
    source_intake_path: str | Path = DEFAULT_SOURCE_INTAKE_PATH,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    ingestion = load_json_artifact(public_ingestion_path)
    source_intake = _load_optional_json(source_intake_path)
    observed = ingestion["observed_policy_reaction_summary"]
    overall = observed["overall"]
    weighted_reaction = overall["weighted_mean_policy_reaction"]
    observed_reject_proxy_raw = weighted_reaction["baseline_no_new_support"]
    by_segment = _segment_proxy(observed["by_segment"])
    data_quality_flags = [
        "public_proxy_not_field_outcome",
        "proxy_metric_not_direct_attitude_truth",
        "same_dataset_proxy_not_cross_case_validation",
    ]
    risk_flags = [
        "not_field_validation",
        "not_accuracy_superiority_evidence",
        "public_proxy_requires_claim_boundary",
    ]
    source_refs = [
        ingestion["artifact_id"],
        str(public_ingestion_path),
        str(source_intake_path),
    ]
    proxy = {
        "schema_version": R6_PUBLIC_OUTCOME_PROXY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "public_proxy_ready",
        "target_case_id": TARGET_CASE_ID,
        "target_case_type": "public_service_policy_change",
        "public_source": {
            "source_artifact_id": ingestion["artifact_id"],
            "source_schema_version": ingestion["schema_version"],
            "source_url": source_intake.get("source_url", "unknown_public_source_url"),
            "dataset_access_mode": source_intake.get("dataset_access_mode", "public_proxy_slice"),
            "puf_row_count": ingestion["data_profile"]["puf_row_count"],
            "usable_row_count": ingestion["data_profile"]["usable_row_count"],
            "skipped_row_count": ingestion["data_profile"]["skipped_row_count"],
        },
        "metrics": {
            "observed_reject_proxy": round(observed_reject_proxy_raw, 2),
            "observed_reject_proxy_raw": observed_reject_proxy_raw,
            "row_count": overall["row_count"],
            "weighted_row_mass": overall["weighted_row_mass"],
        },
        "by_segment": by_segment,
        "outcome_override": {
            "release_id": "htops_2506_public_cost_pressure_proxy",
            "observation_window": "htops_2506_public_use_slice",
            "metrics": {
                "observed_reject_proxy": round(observed_reject_proxy_raw, 2),
                "complaint_rate": 0.0,
                "negative_sentiment_rate": round(
                    weighted_reaction["cash_cost_of_living_rebate"],
                    2,
                ),
                "conversion_delta": -round(weighted_reaction["food_subsidy_expansion"], 2),
            },
            "by_segment": by_segment,
            "source_refs": source_refs,
            "risk_flags": risk_flags,
            "data_quality_flags": data_quality_flags,
            "outcome_source_level": "public_proxy",
        },
        "data_quality_flags": data_quality_flags,
        "source_refs": source_refs,
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            ingestion["claim_boundary"],
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": risk_flags,
        "blocking_gaps": [
            "public_proxy_is_not_direct_release_outcome",
            "needs_second_public_or_real_outcome_case",
        ],
    }
    assert_strict_json(proxy)
    return proxy


def write_r6_public_outcome_proxy(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_public_outcome_proxy(**kwargs))


def _load_optional_json(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.exists():
        return {}
    return load_json_artifact(source)


def _segment_proxy(by_segment: dict[str, Any]) -> dict[str, dict[str, Any]]:
    segment_payload: dict[str, dict[str, Any]] = {}
    for segment_id, segment in by_segment.items():
        weighted = segment["weighted_mean_policy_reaction"]
        segment_payload[segment_id] = {
            "observed_reject_proxy": round(weighted["baseline_no_new_support"], 2),
            "observed_reject_proxy_raw": weighted["baseline_no_new_support"],
            "observed_behavior_change_proxy": round(
                weighted["cash_cost_of_living_rebate"] + weighted["food_subsidy_expansion"],
                2,
            ),
            "row_count": segment["row_count"],
            "weighted_row_mass": segment["weighted_row_mass"],
        }
    return segment_payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_public_outcome_proxy(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    proxy = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": proxy["artifact_id"],
                "output": str(output_path),
                "status": proxy["status"],
                "usable_row_count": proxy["public_source"]["usable_row_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
