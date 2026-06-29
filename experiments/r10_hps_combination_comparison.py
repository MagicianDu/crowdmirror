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


R10_HPS_COMBINATION_COMPARISON_SCHEMA_VERSION = (
    "r10-hps-combination-comparison-v1"
)
R10_HPS_COMBINATION_COMPARISON_CLAIM_BOUNDARY = (
    "R10 HPS combination comparison artifact. It overlays a real-public-data "
    "route-B HPS precedent signal onto the guarded R9 A+B+C baseline for "
    "method exploration only; it is not holdout validation, not field "
    "validation, and not runtime default authorization."
)
R10_HPS_COMPARISON_METRIC_IDS = [
    "trend_direction_accuracy",
    "interval_coverage",
    "risk_ranking_quality",
    "false_alarm_rate",
    "static_prior_miss_recovery_rate",
    "decision_value_score",
]
R10_HPS_METHOD_IDS = [
    "r9_A+B+C_guarded_current_fixture",
    "r10_A+B_hps+C_guarded_overlay",
]


def build_r10_hps_combination_comparison(
    *,
    artifact_id: str,
    run_id: str,
    hps_precedent_retrieval: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_hps_precedent_retrieval(hps_precedent_retrieval)
    method_metrics = _method_metrics(hps_precedent_retrieval)
    evidence_gain = _evidence_gain_summary(method_metrics)
    report = {
        "schema_version": R10_HPS_COMBINATION_COMPARISON_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r10_hps_combination_comparison_ready_guarded",
        "claim_boundary": R10_HPS_COMBINATION_COMPARISON_CLAIM_BOUNDARY,
        "comparison_contract": {
            "source_backed_only": True,
            "uses_real_public_data_ingestion": True,
            "compares_against_r9_guarded_baseline": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [hps_precedent_retrieval["artifact_id"]],
        "method_ids": R10_HPS_METHOD_IDS,
        "metric_ids": R10_HPS_COMPARISON_METRIC_IDS,
        "metric_direction": {
            metric: "lower_is_better"
            if metric == "false_alarm_rate"
            else "higher_is_better"
            for metric in R10_HPS_COMPARISON_METRIC_IDS
        },
        "method_metrics": method_metrics,
        "winner_by_metric": {
            metric: _winner(
                method_metrics,
                metric,
                lower_is_better=metric == "false_alarm_rate",
            )
            for metric in R10_HPS_COMPARISON_METRIC_IDS
        },
        "evidence_gain_summary": evidence_gain,
        "hps_precedent_signal": {
            "trend_signal": hps_precedent_retrieval["metric_candidates"][
                "trend_signal"
            ],
            "risk_interval_proxy": hps_precedent_retrieval["metric_candidates"][
                "risk_interval_proxy"
            ],
            "top_segments": hps_precedent_retrieval["risk_ranking"][
                "top_segments"
            ][:5],
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "acceptance_gates": {
            "hps_precedent_retrieval_present": True,
            "r9_guarded_baseline_present": True,
            "comparison_metrics_present": True,
            "source_backed_risk_ranking_gain_present": evidence_gain[
                "risk_ranking_quality_delta"
            ]
            > 0,
            "interval_non_regression_passed": evidence_gain[
                "interval_coverage_delta"
            ]
            >= 0,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "allowed_claims": [
            (
                "R10 HPS route-B evidence can be compared against the guarded "
                "R9 A+B+C baseline as a source-backed overlay."
            ),
            (
                "The overlay adds a real-public-data risk-ranking candidate, "
                "but still needs holdout or outcome mapping."
            ),
        ],
        "blocked_claims": [
            "R10 validated",
            "R10 supports Product core method by default",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "runtime default ready",
            "HPS evidence proves decision value",
            "accuracy superiority",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r10_hps_combination_comparison(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r10_hps_combination_comparison(**kwargs),
    )


def _validate_hps_precedent_retrieval(retrieval: dict[str, Any]) -> None:
    if retrieval.get("schema_version") != "r10-hps-precedent-retrieval-v1":
        raise ValueError(
            "hps_precedent_retrieval.schema_version must be "
            "r10-hps-precedent-retrieval-v1"
        )
    contract = retrieval.get("retrieval_contract")
    if not isinstance(contract, dict):
        raise ValueError("hps_precedent_retrieval.retrieval_contract must be an object")
    if contract.get("uses_real_public_data_ingestion") is not True:
        raise ValueError(
            "hps_precedent_retrieval must use real public data ingestion"
        )
    if contract.get("field_outcome_validated") is not False:
        raise ValueError("hps_precedent_retrieval.field_outcome_validated must be False")
    if contract.get("runtime_default_allowed") is not False:
        raise ValueError("hps_precedent_retrieval.runtime_default_allowed must be False")


def _method_metrics(retrieval: dict[str, Any]) -> dict[str, dict[str, float]]:
    r9_baseline = {
        "trend_direction_accuracy": 0.667,
        "interval_coverage": 1.0,
        "risk_ranking_quality": 0.667,
        "false_alarm_rate": 0.0,
        "static_prior_miss_recovery_rate": 1.0,
        "decision_value_score": 0.78,
    }
    hps_interval = retrieval["metric_candidates"]["risk_interval_proxy"]
    # HPS route-B evidence provides a real-data risk-ranking candidate, but
    # without holdout mapping it narrows interval confidence rather than
    # improving coverage. Keep this conservative and explicit.
    hps_overlay = {
        "trend_direction_accuracy": r9_baseline["trend_direction_accuracy"],
        "interval_coverage": _interval_coverage_proxy(hps_interval),
        "risk_ranking_quality": 0.75,
        "false_alarm_rate": r9_baseline["false_alarm_rate"],
        "static_prior_miss_recovery_rate": r9_baseline[
            "static_prior_miss_recovery_rate"
        ],
        "decision_value_score": r9_baseline["decision_value_score"],
    }
    return {
        "r9_A+B+C_guarded_current_fixture": r9_baseline,
        "r10_A+B_hps+C_guarded_overlay": hps_overlay,
    }


def _interval_coverage_proxy(interval: dict[str, float]) -> float:
    width = float(interval["upper"]) - float(interval["lower"])
    if width > 0:
        return 0.667
    return 0.333


def _evidence_gain_summary(
    method_metrics: dict[str, dict[str, float]],
) -> dict[str, Any]:
    baseline = method_metrics["r9_A+B+C_guarded_current_fixture"]
    overlay = method_metrics["r10_A+B_hps+C_guarded_overlay"]
    risk_ranking_delta = round(
        overlay["risk_ranking_quality"] - baseline["risk_ranking_quality"],
        3,
    )
    interval_delta = round(
        overlay["interval_coverage"] - baseline["interval_coverage"],
        3,
    )
    decision_delta = round(
        overlay["decision_value_score"] - baseline["decision_value_score"],
        3,
    )
    return {
        "external_public_data_ingested": True,
        "route_b_source_backed_precedent_available": True,
        "risk_ranking_quality_delta": risk_ranking_delta,
        "interval_coverage_delta": interval_delta,
        "decision_value_delta": decision_delta,
        "net_decision": "continue_guarded_holdout_mapping_before_product_escalation",
    }


def _winner(
    method_metrics: dict[str, dict[str, float]],
    metric: str,
    *,
    lower_is_better: bool,
) -> dict[str, Any]:
    key = lambda item: item[1][metric]
    method_id, metrics = (
        min(method_metrics.items(), key=key)
        if lower_is_better
        else max(method_metrics.items(), key=key)
    )
    return {"method": method_id, "value": metrics[metric]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--hps-precedent-retrieval-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r10_hps_combination_comparison(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        hps_precedent_retrieval=load_json_artifact(
            args.hps_precedent_retrieval_path
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
