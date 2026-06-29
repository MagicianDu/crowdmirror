from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import median
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    assert_strict_json,
    load_json_artifact,
    non_empty_string,
    write_json_artifact,
)


R10_HPS_PRECEDENT_RETRIEVAL_SCHEMA_VERSION = "r10-hps-precedent-retrieval-v1"
R10_HPS_PRECEDENT_RETRIEVAL_CLAIM_BOUNDARY = (
    "R10 HPS precedent retrieval artifact. It turns a real public-use HPS "
    "ingestion artifact into guarded route-B precedent and risk-ranking inputs; "
    "it is not field validation, not method superiority, and not runtime "
    "default authorization."
)
R10_HPS_DEFAULT_RANKING_SEGMENTS = ["REGION", "METRO_STATUS"]


def build_r10_hps_precedent_retrieval(
    *,
    artifact_id: str,
    run_id: str,
    hps_ingestion: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_hps_ingestion(hps_ingestion)
    top_segments = _top_price_concern_segments(hps_ingestion)
    risk_shares = [segment["risk_proxy_share"] for segment in top_segments]
    artifact = {
        "schema_version": R10_HPS_PRECEDENT_RETRIEVAL_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r10_hps_precedent_retrieval_ready_guarded",
        "route_id": "route_b_semantic_precedent_retrieval",
        "claim_boundary": R10_HPS_PRECEDENT_RETRIEVAL_CLAIM_BOUNDARY,
        "retrieval_contract": {
            "source_backed_only": True,
            "uses_real_public_data_ingestion": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
            "customer_visible": False,
        },
        "source_refs": [hps_ingestion["artifact_id"]],
        "scenario_query": {
            "scenario_family": "policy_reaction_survey",
            "query_terms": [
                "price pressure",
                "household stress",
                "policy reaction",
                "risk segment",
            ],
            "outcome_focus": ["PRICECHANGE", "PRICESTRESS", "PRICECONCERN"],
        },
        "precedent_cases": [_precedent_case(hps_ingestion)],
        "risk_ranking": {
            "ranking_basis": "PRICECONCERN.segment_outcome_profiles",
            "default_ranking_segments": R10_HPS_DEFAULT_RANKING_SEGMENTS,
            "top_segments": top_segments,
            "ranking_guard": (
                "Risk ranking is a survey proxy from public-use data; it must be "
                "validated against holdout or field/customer outcome before Product escalation."
            ),
        },
        "metric_candidates": {
            "trend_signal": _trend_signal(hps_ingestion),
            "risk_interval_proxy": _risk_interval_proxy(risk_shares),
            "risk_ranking_quality": "computable_after_holdout_or_outcome_mapping",
            "decision_value_score": "not_computed_until_policy_action_set",
        },
        "route_a_input_candidate": {
            "mechanism_priors": [
                "economic_stress",
                "price_sensitivity",
                "policy_salience",
            ],
            "outcome_signal_columns": ["PRICECHANGE", "PRICESTRESS", "PRICECONCERN"],
            "segment_risk_profile_source": hps_ingestion["artifact_id"],
        },
        "route_c_input_candidate": {
            "affected_segments": [
                segment["segment_column"] for segment in top_segments[:5]
            ],
            "risk_observation_window": hps_ingestion["source_dataset"][
                "release_window"
            ],
        },
        "acceptance_gates": {
            "source_ingestion_available": True,
            "precedent_case_constructed": True,
            "risk_ranking_constructed": bool(top_segments),
            "metric_candidates_constructed": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "allowed_claims": [
            "R10 L2 route B can consume real HPS public-use ingestion as a guarded precedent input.",
            "HPS price-concern segment profiles can produce a source-backed risk ranking proxy.",
        ],
        "blocked_claims": [
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "runtime default ready",
            "R10 validated",
            "R10 supports Product core method by default",
            "HPS risk ranking is a validated Product decision rule",
            "accuracy superiority",
            "精准预测系统",
        ],
    }
    assert_strict_json(artifact)
    return artifact


def write_r10_hps_precedent_retrieval(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r10_hps_precedent_retrieval(**kwargs),
    )


def _validate_hps_ingestion(hps_ingestion: dict[str, Any]) -> None:
    if hps_ingestion.get("schema_version") != "r10-hps-policy-reaction-ingestion-v1":
        raise ValueError("hps_ingestion.schema_version must be r10-hps-policy-reaction-ingestion-v1")
    contract = hps_ingestion.get("ingestion_contract")
    if not isinstance(contract, dict):
        raise ValueError("hps_ingestion.ingestion_contract must be an object")
    if contract.get("actual_public_data_ingested") is not True:
        raise ValueError("hps_ingestion must have actual_public_data_ingested=true")
    if contract.get("field_outcome_validated") is not False:
        raise ValueError("hps_ingestion.field_outcome_validated must be False")
    if contract.get("runtime_default_allowed") is not False:
        raise ValueError("hps_ingestion.runtime_default_allowed must be False")


def _precedent_case(hps_ingestion: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": "hps_price_pressure_public_use_precedent",
        "source_artifact_id": hps_ingestion["artifact_id"],
        "source_owner": hps_ingestion["source_dataset"]["source_owner"],
        "source_url": hps_ingestion["source_dataset"]["source_url"],
        "scenario_family": "policy_reaction_survey",
        "row_count": hps_ingestion["data_profile"]["row_count"],
        "outcome_columns": hps_ingestion["outcome_label_contract"][
            "outcome_columns"
        ],
        "segment_columns": hps_ingestion["data_profile"]["segment_columns_present"],
        "evidence_strength": "official_public_use_microdata_ingested",
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }


def _top_price_concern_segments(hps_ingestion: dict[str, Any]) -> list[dict[str, Any]]:
    profiles = hps_ingestion["segment_outcome_profiles"]["PRICECONCERN"]
    rows = []
    for segment_column, segment_rows in profiles.items():
        if segment_column not in R10_HPS_DEFAULT_RANKING_SEGMENTS:
            continue
        for row in segment_rows:
            rows.append(
                {
                    "segment_column": segment_column,
                    "segment_value": row["segment_value"],
                    "risk_proxy_share": row["risk_proxy_share"],
                    "weighted_valid_total": row["weighted_valid_total"],
                }
            )
    return sorted(
        rows,
        key=lambda item: (
            -item["risk_proxy_share"],
            -item["weighted_valid_total"],
            item["segment_column"],
            item["segment_value"],
        ),
    )[:10]


def _trend_signal(hps_ingestion: dict[str, Any]) -> str:
    concern_summary = hps_ingestion["outcome_summary"]["PRICECONCERN"]
    distribution = concern_summary["response_distribution"]
    if not distribution:
        return "price_pressure_signal_missing"
    numeric_values = []
    for value, share in distribution.items():
        try:
            numeric_values.append((float(value), share))
        except ValueError:
            continue
    if not numeric_values:
        return "price_pressure_signal_missing"
    numeric_values.sort()
    threshold = numeric_values[len(numeric_values) // 2][0]
    risk_share = sum(share for value, share in numeric_values if value >= threshold)
    if risk_share >= 0.5:
        return "price_pressure_risk_present"
    return "price_pressure_risk_watch"


def _risk_interval_proxy(risk_shares: list[float]) -> dict[str, float]:
    if not risk_shares:
        return {"lower": 0.0, "median": 0.0, "upper": 0.0}
    ordered = sorted(risk_shares)
    return {
        "lower": round(ordered[0], 6),
        "median": round(float(median(ordered)), 6),
        "upper": round(ordered[-1], 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--hps-ingestion-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r10_hps_precedent_retrieval(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        hps_ingestion=load_json_artifact(args.hps_ingestion_path),
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
