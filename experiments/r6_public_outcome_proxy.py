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
ANES_HEALTH_HELDOUT_PATH = (
    "experiments/results/policy_reaction_benchmark/"
    "policy-reaction-anes-health-001-heldout.json"
)
ANES_CLIMATE_HELDOUT_PATH = (
    "experiments/results/policy_reaction_benchmark/"
    "policy-reaction-anes-climate-001-heldout.json"
)
TARGET_CASE_ID = "generic-public-service-policy-change"


def build_r6_public_outcome_proxy(
    *,
    artifact_id: str,
    run_id: str,
    source_key: str = "htops_cost_pressure",
    public_ingestion_path: str | Path = DEFAULT_PUBLIC_INGESTION_PATH,
    source_intake_path: str | Path = DEFAULT_SOURCE_INTAKE_PATH,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    source_key = non_empty_string(source_key, field="source_key")
    if source_key == "anes_health_heldout":
        return _build_anes_health_proxy(
            artifact_id=artifact_id,
            run_id=run_id,
            public_ingestion_path=ANES_HEALTH_HELDOUT_PATH,
        )
    if source_key == "anes_climate_heldout":
        return _build_anes_climate_proxy(
            artifact_id=artifact_id,
            run_id=run_id,
            public_ingestion_path=ANES_CLIMATE_HELDOUT_PATH,
        )
    if source_key != "htops_cost_pressure":
        raise ValueError(f"unknown R6 public outcome proxy source_key: {source_key}")
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
        "source_key": source_key,
        "target_case_id": TARGET_CASE_ID,
        "target_case_type": "public_service_policy_change",
        "public_source": {
            "source_artifact_id": ingestion["artifact_id"],
            "source_name": "HTOPS/HPS public-use cost pressure",
            "source_schema_version": ingestion["schema_version"],
            "source_url": source_intake.get("source_url", "unknown_public_source_url"),
            "dataset_access_mode": source_intake.get("dataset_access_mode", "public_proxy_slice"),
            "puf_row_count": ingestion["data_profile"]["puf_row_count"],
            "usable_row_count": ingestion["data_profile"]["usable_row_count"],
            "skipped_row_count": ingestion["data_profile"]["skipped_row_count"],
            "split_role": "public_use_slice",
        },
        "metrics": {
            "observed_reject_proxy": round(observed_reject_proxy_raw, 2),
            "observed_reject_proxy_raw": observed_reject_proxy_raw,
            "row_count": overall["row_count"],
            "weighted_row_mass": overall["weighted_row_mass"],
        },
        "by_segment": by_segment,
        "mapping_review": {
            "proxy_family": "cost_pressure_reaction",
            "target_response_option": "baseline_no_new_support",
            "mapping_rationale": (
                "For a public service or policy support scenario, continued baseline "
                "without new support is treated as the observable reject proxy."
            ),
            "claim_boundary": "Proxy mapping only; not direct attitude truth.",
        },
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


def _build_anes_health_proxy(
    *,
    artifact_id: str,
    run_id: str,
    public_ingestion_path: str | Path,
) -> dict[str, Any]:
    ingestion = load_json_artifact(public_ingestion_path)
    observed = ingestion["observed_policy_reaction_summary"]
    by_segment = observed["by_segment"]
    target_option = "private_insurance_plan"
    weighted = _weighted_distribution(by_segment)
    observed_reject_proxy_raw = weighted[target_option]
    segment_payload = _segment_proxy_for_target(
        by_segment,
        target_option=target_option,
        behavior_options=["government_insurance_plan", "mixed_or_middle_position"],
    )
    usable_row_count = sum(segment["row_count"] for segment in segment_payload.values())
    weighted_row_mass = sum(segment["weighted_row_mass"] for segment in segment_payload.values())
    data_quality_flags = [
        "public_heldout_proxy_not_field_outcome",
        "proxy_metric_not_direct_attitude_truth",
        "heldout_split_not_customer_release",
    ]
    risk_flags = [
        "heldout_public_proxy_not_global_validation",
        "not_field_validation",
        "not_accuracy_superiority_evidence",
    ]
    source_refs = [
        ingestion["artifact_id"],
        str(public_ingestion_path),
    ]
    proxy = {
        "schema_version": R6_PUBLIC_OUTCOME_PROXY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "public_proxy_ready",
        "source_key": "anes_health_heldout",
        "target_case_id": "generic-rights-rule-change",
        "target_case_type": "rights_rule_change",
        "public_source": {
            "source_artifact_id": ingestion["artifact_id"],
            "source_name": "ANES 2024 public-use health heldout",
            "source_schema_version": ingestion["schema_version"],
            "source_url": ingestion.get("source", {}).get("source_url", "unknown_public_source_url"),
            "dataset_access_mode": "public_use_heldout_split",
            "puf_row_count": ingestion["row_count"],
            "usable_row_count": usable_row_count,
            "skipped_row_count": ingestion["row_count"] - usable_row_count,
            "split_role": ingestion["split_role"],
        },
        "metrics": {
            "observed_reject_proxy": round(observed_reject_proxy_raw, 2),
            "observed_reject_proxy_raw": observed_reject_proxy_raw,
            "row_count": usable_row_count,
            "weighted_row_mass": weighted_row_mass,
        },
        "by_segment": segment_payload,
        "mapping_review": {
            "proxy_family": "public_health_insurance_preference",
            "target_response_option": target_option,
            "mapping_rationale": (
                "For a rights/rule change case framed around public coverage, "
                "private-insurance preference is treated as a reject proxy."
            ),
            "claim_boundary": "Proxy mapping only; not field outcome or direct customer behavior.",
        },
        "outcome_override": {
            "release_id": "anes_2024_health_heldout_proxy",
            "observation_window": "anes_2024_public_use_heldout_split",
            "metrics": {
                "observed_reject_proxy": round(observed_reject_proxy_raw, 2),
                "complaint_rate": 0.0,
                "negative_sentiment_rate": round(weighted["mixed_or_middle_position"], 2),
                "conversion_delta": -round(weighted["government_insurance_plan"], 2),
            },
            "by_segment": segment_payload,
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
            "needs_cross_proxy_mapping_review",
        ],
    }
    assert_strict_json(proxy)
    return proxy


def _build_anes_climate_proxy(
    *,
    artifact_id: str,
    run_id: str,
    public_ingestion_path: str | Path,
) -> dict[str, Any]:
    ingestion = load_json_artifact(public_ingestion_path)
    observed = ingestion["observed_policy_reaction_summary"]
    by_segment = observed["by_segment"]
    target_option = "oppose_more_regulation_or_spending"
    weighted = _weighted_distribution(by_segment)
    observed_reject_proxy_raw = weighted[target_option]
    segment_payload = _segment_proxy_for_target(
        by_segment,
        target_option=target_option,
        behavior_options=[
            "support_more_regulation_or_spending",
            "mixed_or_status_quo",
        ],
    )
    usable_row_count = sum(segment["row_count"] for segment in segment_payload.values())
    weighted_row_mass = sum(segment["weighted_row_mass"] for segment in segment_payload.values())
    data_quality_flags = [
        "same_dataset_regulation_holdout_proxy_not_field_outcome",
        "proxy_metric_not_direct_attitude_truth",
        "heldout_split_not_customer_release",
    ]
    risk_flags = [
        "same_dataset_same_family_holdout_not_global_validation",
        "same_family_holdout_not_cap_condition_validation",
        "not_field_validation",
        "not_accuracy_superiority_evidence",
    ]
    source_refs = [
        ingestion["artifact_id"],
        str(public_ingestion_path),
    ]
    proxy = {
        "schema_version": R6_PUBLIC_OUTCOME_PROXY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "public_proxy_ready",
        "source_key": "anes_climate_heldout",
        "target_case_id": "generic-rights-rule-change",
        "target_case_type": "rights_rule_change",
        "public_source": {
            "source_artifact_id": ingestion["artifact_id"],
            "source_name": "ANES 2024 public-use climate-energy regulation heldout",
            "source_schema_version": ingestion["schema_version"],
            "source_url": ingestion.get("source", {}).get("source_url", "unknown_public_source_url"),
            "dataset_access_mode": "public_use_heldout_split",
            "puf_row_count": ingestion["row_count"],
            "usable_row_count": usable_row_count,
            "skipped_row_count": ingestion["row_count"] - usable_row_count,
            "split_role": ingestion["split_role"],
        },
        "metrics": {
            "observed_reject_proxy": round(observed_reject_proxy_raw, 2),
            "observed_reject_proxy_raw": observed_reject_proxy_raw,
            "row_count": usable_row_count,
            "weighted_row_mass": weighted_row_mass,
        },
        "by_segment": segment_payload,
        "mapping_review": {
            "proxy_family": "climate_energy_regulation_preference",
            "target_response_option": target_option,
            "mapping_rationale": (
                "For a rights/rule or regulation-change case, opposition to more "
                "regulation or spending is treated as a bounded reject proxy."
            ),
            "claim_boundary": "Same-dataset public proxy only; not field outcome or direct customer behavior.",
        },
        "outcome_override": {
            "release_id": "anes_2024_climate_heldout_proxy",
            "observation_window": "anes_2024_public_use_climate_heldout_split",
            "metrics": {
                "observed_reject_proxy": round(observed_reject_proxy_raw, 2),
                "complaint_rate": 0.0,
                "negative_sentiment_rate": round(weighted["mixed_or_status_quo"], 2),
                "conversion_delta": -round(weighted["support_more_regulation_or_spending"], 2),
            },
            "by_segment": segment_payload,
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
            "needs_in_condition_same_family_holdout",
        ],
    }
    assert_strict_json(proxy)
    return proxy


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


def _segment_proxy_for_target(
    by_segment: dict[str, Any],
    *,
    target_option: str,
    behavior_options: list[str],
) -> dict[str, dict[str, Any]]:
    segment_payload: dict[str, dict[str, Any]] = {}
    for segment_id, segment in by_segment.items():
        weighted = segment["weighted_mean_policy_reaction"]
        segment_payload[segment_id] = {
            "observed_reject_proxy": round(weighted[target_option], 2),
            "observed_reject_proxy_raw": weighted[target_option],
            "observed_behavior_change_proxy": round(
                sum(weighted[option] for option in behavior_options),
                2,
            ),
            "row_count": segment["row_count"],
            "weighted_row_mass": segment["weighted_row_mass"],
        }
    return segment_payload


def _weighted_distribution(by_segment: dict[str, Any]) -> dict[str, float]:
    total_mass = sum(segment["weighted_row_mass"] for segment in by_segment.values())
    if total_mass <= 0:
        raise ValueError("public proxy weighted row mass must be positive")
    totals: dict[str, float] = {}
    for segment in by_segment.values():
        weighted = segment["weighted_mean_policy_reaction"]
        for option, value in weighted.items():
            totals[option] = totals.get(option, 0.0) + value * segment["weighted_row_mass"]
    return {option: value / total_mass for option, value in totals.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source-key", default="htops_cost_pressure")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_public_outcome_proxy(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        source_key=args.source_key,
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
