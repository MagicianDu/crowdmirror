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
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_cross_case_transfer_protocol import (
    build_r6_cross_case_transfer_protocol,
)
from experiments.r6_false_alarm_control_report import build_r6_false_alarm_control_report
from experiments.r6_learning_counterfactual_holdout_validation import (
    build_r6_learning_counterfactual_holdout_validation,
)
from experiments.r6_learning_counterfactual_simulator import (
    build_r6_learning_counterfactual_simulator,
)
from experiments.r6_mechanism_ablation_report import build_r6_mechanism_ablation_report
from experiments.r6_segment_risk_reports import (
    build_r6_abnormal_segment_validation_report,
    build_r6_segment_risk_ranking_report,
)
from experiments.r6_trend_interval_calibration_report import (
    build_r6_trend_interval_calibration_report,
)


R6_PRODUCT_CLAIM_EVIDENCE_REGISTRY_SCHEMA_VERSION = (
    "r6-product-claim-evidence-registry-v1"
)
R6_RESEARCH_PRODUCT_VALUE_SUPPORT_V2_SCHEMA_VERSION = (
    "r6-research-product-value-support-v2"
)


def build_r6_product_claim_evidence_registry(
    *,
    artifact_id: str,
    run_id: str,
    trend_interval_calibration_report: dict[str, Any] | None = None,
    segment_risk_ranking_report: dict[str, Any] | None = None,
    abnormal_segment_validation_report: dict[str, Any] | None = None,
    false_alarm_control_report: dict[str, Any] | None = None,
    mechanism_ablation_report: dict[str, Any] | None = None,
    outcome_feedback_source: dict[str, Any] | None = None,
    learning_counterfactual_simulator: dict[str, Any] | None = None,
    learning_counterfactual_holdout_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    trend = trend_interval_calibration_report or build_r6_trend_interval_calibration_report(
        artifact_id=f"{artifact_id}-trend-interval-calibration",
        run_id=run_id,
    )
    ranking = segment_risk_ranking_report or build_r6_segment_risk_ranking_report(
        artifact_id=f"{artifact_id}-segment-risk-ranking",
        run_id=run_id,
    )
    abnormal = (
        abnormal_segment_validation_report
        or build_r6_abnormal_segment_validation_report(
            artifact_id=f"{artifact_id}-abnormal-segment-validation",
            run_id=run_id,
            segment_risk_ranking_report=ranking,
        )
    )
    false_alarm = false_alarm_control_report or build_r6_false_alarm_control_report(
        artifact_id=f"{artifact_id}-false-alarm-control",
        run_id=run_id,
    )
    mechanism = mechanism_ablation_report or build_r6_mechanism_ablation_report(
        artifact_id=f"{artifact_id}-mechanism-ablation",
        run_id=run_id,
    )
    feedback = outcome_feedback_source or build_r6_cross_case_transfer_protocol(
        artifact_id=f"{artifact_id}-cross-case-transfer",
        run_id=run_id,
    )
    counterfactual = (
        learning_counterfactual_simulator
        or build_r6_learning_counterfactual_simulator(
            artifact_id=f"{artifact_id}-learning-counterfactual-simulator",
            run_id=run_id,
        )
    )
    counterfactual_holdout = (
        learning_counterfactual_holdout_validation
        or build_r6_learning_counterfactual_holdout_validation(
            artifact_id=f"{artifact_id}-learning-counterfactual-holdout",
            run_id=run_id,
            learning_counterfactual_simulator=counterfactual,
        )
    )
    claims = [
        _claim(
            product_section="trend_direction",
            claim_status=trend["claim_status"],
            source_artifact_ids=[trend["artifact_id"]],
            support_status="partial_current_proxy",
            blocked_reason="trend_direction_accuracy_below_validation_threshold",
        ),
        _claim(
            product_section="risk_interval",
            claim_status=_risk_interval_claim_status(trend),
            source_artifact_ids=[trend["artifact_id"]],
            support_status=_risk_interval_support_status(trend),
            blocked_reason=(
                ""
                if _risk_interval_claim_status(trend) == "guarded"
                else "interval_coverage_below_validation_threshold"
            ),
        ),
        _claim(
            product_section="risk_distribution",
            claim_status=ranking["claim_status"],
            source_artifact_ids=[
                ranking["artifact_id"],
                false_alarm["artifact_id"],
            ],
            support_status="supported_current_proxy_guarded",
            blocked_reason="field_holdout_missing",
        ),
        _claim(
            product_section="abnormal_segments",
            claim_status=abnormal["claim_status"],
            source_artifact_ids=[abnormal["artifact_id"], ranking["artifact_id"]],
            support_status="guarded_proxy_supported",
            blocked_reason="field_segment_labels_missing",
        ),
        _claim(
            product_section="mechanism_explanation",
            claim_status="diagnostic",
            source_artifact_ids=[mechanism["artifact_id"]],
            support_status="diagnostic_only",
            blocked_reason="operator_holdout_not_runtime_default",
        ),
        _claim(
            product_section="false_alarm_control",
            claim_status=false_alarm["claim_status"],
            source_artifact_ids=[false_alarm["artifact_id"]],
            support_status="supported_current_proxy_guarded",
            blocked_reason="holdout_validation_missing",
        ),
        _claim(
            product_section="counterfactual_policy_comparison",
            claim_status="diagnostic",
            source_artifact_ids=[
                counterfactual["artifact_id"],
                counterfactual_holdout["artifact_id"],
            ],
            support_status="guarded_current_proxy_positive_signal",
            blocked_reason="independent_holdout_not_passed",
        ),
        _claim(
            product_section="outcome_feedback",
            claim_status="blocked",
            source_artifact_ids=[feedback["artifact_id"]],
            support_status="blocked_until_feedback_protocol",
            blocked_reason="bounded_feedback_protocol_not_yet_available",
        ),
        _claim(
            product_section="bounded_update_candidate",
            claim_status="blocked",
            source_artifact_ids=[feedback["artifact_id"]],
            support_status="blocked_until_feedback_protocol",
            blocked_reason="accepted_rejected_candidate_contract_missing",
        ),
    ]
    summary = _summary(claims)
    report = {
        "schema_version": R6_PRODUCT_CLAIM_EVIDENCE_REGISTRY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "product_claim_evidence_registry_ready_guarded",
        "claim_results": claims,
        "summary": summary,
        "acceptance_gates": {
            "claim_evidence_registry_present": True,
            "all_product_visible_claims_source_backed": all(
                bool(claim["source_artifact_ids"]) for claim in claims
            ),
            "no_source_claim_rejected": all(
                bool(claim["source_artifact_ids"])
                or claim["claim_status"] == "blocked"
                for claim in claims
            ),
            "supported_value_count_gt_zero": summary["supported_value_count"] > 0,
            "counterfactual_policy_comparison_source_backed": all(
                claim["source_artifact_ids"]
                for claim in claims
                if claim["product_section"] == "counterfactual_policy_comparison"
            ),
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": _unique_strings(
            source_ref
            for claim in claims
            for source_ref in claim["source_artifact_ids"]
        ),
        "allowed_claims": [
            "Risk interval can be presented as a guarded supported interval when coverage and width gates pass.",
            "Risk distribution and false-alarm control can be presented as guarded current-proxy supported claims.",
            "Abnormal segments can be presented as guarded proxy/audit supported claims.",
            "Counterfactual policy comparison can be presented as diagnostic current-proxy decision support.",
        ],
        "blocked_claims": [
            "Research 已完整支撑 Product 全部核心价值",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "候选更新已可自动上线",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def build_r6_research_product_value_support_v2(
    *,
    artifact_id: str,
    run_id: str,
    claim_evidence_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    registry = claim_evidence_registry or build_r6_product_claim_evidence_registry(
        artifact_id=f"{artifact_id}-claim-evidence-registry",
        run_id=run_id,
    )
    support_matrix = [
        {
            "product_value": claim["product_section"],
            "claim_status": claim["claim_status"],
            "support_status": claim["support_status"],
            "source_artifact_ids": claim["source_artifact_ids"],
            "blocked_reason": claim["blocked_reason"],
        }
        for claim in registry["claim_results"]
    ]
    coverage = _support_coverage(support_matrix)
    overall_supported = (
        coverage["validated_value_count"] > 0
        and coverage["blocked_value_count"] == 0
    )
    report = {
        "schema_version": R6_RESEARCH_PRODUCT_VALUE_SUPPORT_V2_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "product_value_support_v2_ready"
        if overall_supported
        else "product_value_support_v2_partial_supported",
        "overall_product_core_value_supported": overall_supported,
        "support_matrix": support_matrix,
        "support_coverage": coverage,
        "acceptance_gates": {
            "all_product_values_mapped": {
                item["product_value"] for item in support_matrix
            }
            == {
                "trend_direction",
                "risk_interval",
                "risk_distribution",
                "abnormal_segments",
                "mechanism_explanation",
                "false_alarm_control",
                "counterfactual_policy_comparison",
                "outcome_feedback",
                "bounded_update_candidate",
            },
            "all_product_visible_claims_source_backed": registry["acceptance_gates"][
                "all_product_visible_claims_source_backed"
            ],
            "supported_value_count_gt_zero": coverage["supported_value_count"] > 0,
            "validated_value_count_gt_zero": coverage["validated_value_count"] > 0,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
            "overall_product_core_value_supported": overall_supported,
        },
        "source_refs": [registry["artifact_id"], *registry["source_refs"]],
        "allowed_claims": registry["allowed_claims"],
        "blocked_claims": [
            *registry["blocked_claims"],
            "精准预测系统",
            "系统可以精确预测单点结果",
        ],
        "blocking_gaps": [
            "needs_trend_interval_holdout_improvement",
            "needs_mechanism_operator_holdout_validation",
            "needs_bounded_feedback_protocol",
            "needs_field_outcome_validation",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_product_claim_evidence_registry(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_claim_evidence_registry(**kwargs))


def _claim(
    *,
    product_section: str,
    claim_status: str,
    source_artifact_ids: list[str],
    support_status: str,
    blocked_reason: str,
) -> dict[str, Any]:
    return {
        "product_section": product_section,
        "claim_status": claim_status,
        "support_status": support_status,
        "source_artifact_ids": source_artifact_ids,
        "blocked_reason": blocked_reason,
    }


def _risk_interval_claim_status(trend: dict[str, Any]) -> str:
    gates = trend["acceptance_gates"]
    if (
        gates["interval_coverage_passed"]
        and gates["interval_width_passed"]
    ):
        return "guarded"
    return "diagnostic"


def _risk_interval_support_status(trend: dict[str, Any]) -> str:
    if _risk_interval_claim_status(trend) == "guarded":
        return "guarded_interval_supported"
    return "partial_current_proxy"


def _summary(claims: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "claim_count": len(claims),
        "validated_claim_count": sum(
            1 for claim in claims if claim["claim_status"] == "validated"
        ),
        "guarded_claim_count": sum(
            1 for claim in claims if claim["claim_status"] == "guarded"
        ),
        "diagnostic_claim_count": sum(
            1 for claim in claims if claim["claim_status"] == "diagnostic"
        ),
        "blocked_claim_count": sum(
            1 for claim in claims if claim["claim_status"] == "blocked"
        ),
        "supported_value_count": sum(
            1
            for claim in claims
            if claim["support_status"]
            in {
                "supported_current_proxy_guarded",
                "guarded_proxy_supported",
                "guarded_interval_supported",
                "guarded_current_proxy_positive_signal",
            }
        ),
    }


def _support_coverage(support_matrix: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "product_value_count": len(support_matrix),
        "validated_value_count": sum(
            1 for item in support_matrix if item["claim_status"] == "validated"
        ),
        "supported_value_count": sum(
            1
            for item in support_matrix
            if item["support_status"]
            in {
                "supported_current_proxy_guarded",
                "guarded_proxy_supported",
                "guarded_interval_supported",
                "guarded_current_proxy_positive_signal",
            }
        ),
        "guarded_value_count": sum(
            1 for item in support_matrix if item["claim_status"] == "guarded"
        ),
        "diagnostic_value_count": sum(
            1 for item in support_matrix if item["claim_status"] == "diagnostic"
        ),
        "blocked_value_count": sum(
            1 for item in support_matrix if item["claim_status"] == "blocked"
        ),
    }


def _unique_strings(values: Any) -> list[str]:
    return list(dict.fromkeys(values))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_product_claim_evidence_registry(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "output": str(output_path),
                "status": report["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
