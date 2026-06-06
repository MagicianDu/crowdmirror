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
from experiments.r6_in_condition_holdout_ledger import (
    build_r6_in_condition_holdout_ledger,
)
from experiments.r6_mechanism_cap_ablation import build_r6_mechanism_cap_ablation
from experiments.r6_product_report import build_r6_product_report


R6_PRODUCT_EVIDENCE_CARDS_SCHEMA_VERSION = "r6-product-evidence-cards-v1"


def build_r6_product_evidence_cards(
    *,
    artifact_id: str,
    run_id: str,
    product_report: dict[str, Any] | None = None,
    transfer_protocol: dict[str, Any] | None = None,
    holdout_ledger: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    if product_report is None:
        mechanism_cap = build_r6_mechanism_cap_ablation(
            artifact_id=f"{artifact_id}-mechanism-cap-ablation",
            run_id=run_id,
        )
        product_report = build_r6_product_report(
            artifact_id=f"{artifact_id}-product-report",
            run_id=run_id,
            mechanism_cap_ablation=mechanism_cap,
        )
    transfer_protocol = transfer_protocol or build_r6_cross_case_transfer_protocol(
        artifact_id=f"{artifact_id}-transfer-protocol",
        run_id=run_id,
    )
    holdout_ledger = holdout_ledger or build_r6_in_condition_holdout_ledger(
        artifact_id=f"{artifact_id}-holdout-ledger",
        run_id=run_id,
    )
    cards = _cards(
        product_report=product_report,
        transfer_protocol=transfer_protocol,
        holdout_ledger=holdout_ledger,
    )
    report = {
        "schema_version": R6_PRODUCT_EVIDENCE_CARDS_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "product_evidence_cards_ready",
        "card_count": len(cards),
        "cards": cards,
        "demo_api_contract": {
            "consume_only_artifact_fields": True,
            "static_narrative_fallback_allowed": False,
            "required_card_fields": [
                "card_id",
                "title",
                "claim_status",
                "allowed_claims",
                "blocked_claims",
                "source_artifact_ids",
            ],
            "rendering_rule": (
                "UI may summarize card fields, but must not introduce claims that are "
                "not present in allowed_claims."
            ),
        },
        "source_refs": [
            product_report["artifact_id"],
            transfer_protocol["artifact_id"],
            holdout_ledger["artifact_id"],
        ],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            "Product evidence cards are customer-facing claim boundaries, not accuracy proof.",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "product_claims_bounded_by_artifacts",
            "no_static_demo_narrative_fallback",
            "accuracy_claim_blocked",
        ],
        "blocking_gaps": [
            "needs_demo_or_api_to_consume_cards",
            "needs_field_outcome_before_accuracy_claim",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_product_evidence_cards(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_evidence_cards(**kwargs))


def _cards(
    *,
    product_report: dict[str, Any],
    transfer_protocol: dict[str, Any],
    holdout_ledger: dict[str, Any],
) -> list[dict[str, Any]]:
    mechanism_transfer = _candidate_by_type(transfer_protocol, "mechanism_cap")
    feedback_transfer = _candidate_by_type(
        transfer_protocol,
        "outcome_feedback_residual_transfer",
    )
    return [
        {
            "card_id": "static-prior-control",
            "title": "静态先验与 no-interaction control",
            "claim_status": "baseline_context_ready",
            "allowed_claims": [
                "系统能展示发布前静态先验分布",
                "静态先验是交互仿真的对照组",
            ],
            "blocked_claims": [
                "静态先验等于真实反应",
                "没有 outcome 也能证明预测准确",
            ],
            "source_artifact_ids": [product_report["artifact_id"]],
            "display_fields": [
                "pre_release.case_summaries[].static_prior",
                "decision_support.market_claim_status",
            ],
        },
        {
            "card_id": "interaction-risk-shift",
            "title": "交互风险偏移",
            "claim_status": "risk_hypothesis_ready",
            "allowed_claims": [
                "交互层可以展示相对静态先验的风险偏移",
                "偏移用于发布前风险复核",
            ],
            "blocked_claims": [
                "交互偏移已经被证明更准",
                "交互仿真可以替代真实 outcome",
            ],
            "source_artifact_ids": [product_report["artifact_id"]],
            "display_fields": [
                "pre_release.case_summaries[].interaction_shift",
                "pre_release.case_summaries[].top_risk_segment",
            ],
        },
        {
            "card_id": "mechanism-cap-transfer",
            "title": "机制 cap 迁移验收",
            "claim_status": "diagnostic_l3_partial_not_runtime_default",
            "allowed_claims": [
                "mechanism cap 可以修复 source case 的过度放大",
                "已有 cross-proxy non-regression 证据",
            ],
            "blocked_claims": [
                "mechanism cap 已可作为 runtime default",
                "mechanism cap 已通过 CCF-A 级 L4 迁移验证",
            ],
            "source_artifact_ids": [
                product_report["artifact_id"],
                transfer_protocol["artifact_id"],
            ],
            "display_fields": [
                "candidate_transfers[mechanism_cap].evidence_level",
                "candidate_transfers[mechanism_cap].acceptance_gates",
                "global_update_decision",
            ],
            "evidence_level": mechanism_transfer["evidence_level"],
        },
        {
            "card_id": "outcome-feedback-transfer",
            "title": "结果反馈迁移",
            "claim_status": "non_regression_only_not_global_update",
            "allowed_claims": [
                "结果反馈可以生成冻结 residual 更新规则",
                "当前 same-family transfer 只达到 non-regression 层级",
            ],
            "blocked_claims": [
                "outcome feedback 已经形成通用自动校准器",
                "same-case improvement 可以直接进入全局参数",
            ],
            "source_artifact_ids": [transfer_protocol["artifact_id"]],
            "display_fields": [
                "candidate_transfers[outcome_feedback].holdout_trials",
                "candidate_transfers[outcome_feedback].transfer_decision",
            ],
            "evidence_level": feedback_transfer["evidence_level"],
        },
        {
            "card_id": "holdout-data-gap",
            "title": "in-condition holdout 缺口",
            "claim_status": "data_gate_blocked",
            "allowed_claims": [
                "系统能说明当前公开数据为何不足以升级候选规则",
                "下一步数据采集条件已经明确",
            ],
            "blocked_claims": [
                "已有公开 proxy 足够证明全局可迁移",
                "继续增加任意 proxy 都能提升论文证据",
            ],
            "source_artifact_ids": [holdout_ledger["artifact_id"]],
            "display_fields": [
                "selection_criteria",
                "ledger_entries[].ledger_status",
                "next_search_profile",
            ],
            "in_condition_holdout_count": holdout_ledger["summary"][
                "in_condition_holdout_count"
            ],
        },
    ]


def _candidate_by_type(report: dict[str, Any], candidate_type: str) -> dict[str, Any]:
    for candidate in report["candidate_transfers"]:
        if candidate["candidate_type"] == candidate_type:
            return candidate
    raise ValueError(f"missing candidate transfer: {candidate_type}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_product_evidence_cards(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "card_count": report["card_count"],
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
