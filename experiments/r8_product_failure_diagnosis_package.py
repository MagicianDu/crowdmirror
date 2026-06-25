from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact
from experiments.r8_learnable_mechanism_simulation import R8_CLAIM_BOUNDARY
from experiments.r8_stop_loss_diagnosis import build_r8_stop_loss_diagnosis


R8_PRODUCT_FAILURE_DIAGNOSIS_PACKAGE_SCHEMA_VERSION = (
    "r8-product-failure-diagnosis-package-v1"
)


_FAILURE_CARD_TEMPLATES = {
    "not_beating_fixed_rule_baseline": {
        "title": "R8 尚未超过固定规则 baseline",
        "customer_question": "为什么当前不能把 R8 当成默认人群模拟方法？",
        "product_response": (
            "系统展示 R8 的失败归因和对照结果，但不把它作为默认预测或策略建议方法。"
        ),
    },
    "insufficient_metric_dominance": {
        "title": "R8 没有形成多指标优势",
        "customer_question": "哪些指标还不足以支撑产品核心价值？",
        "product_response": (
            "报告继续展示趋势、区间、风险排序和异常群体，但把支撑等级标为诊断态。"
        ),
    },
    "l1_l2_gate_blocked": {
        "title": "鲁棒性与 holdout gate 被阻断",
        "customer_question": "为什么不能直接上线自动更新？",
        "product_response": (
            "系统保留 replay 与 guard 输出，真实启用前必须重新通过鲁棒性和 holdout gate。"
        ),
    },
    "field_customer_outcome_missing": {
        "title": "缺少真实 field/customer outcome",
        "customer_question": "需要客户提供什么结果数据才能进入方法验证？",
        "product_response": (
            "系统要求对齐场景、群体、观测窗口和结果指标后，才能做 outcome replay 与更新候选。"
        ),
    },
    "runtime_default_guard_blocked": {
        "title": "runtime default guard 未通过",
        "customer_question": "为什么结果只能展示为诊断，而不是自动决策？",
        "product_response": (
            "Product 可以呈现风险边界和证据请求，但不会默认启用 R8 更新算子。"
        ),
    },
}


def build_r8_product_failure_diagnosis_package(
    *,
    artifact_id: str,
    run_id: str,
    stop_loss_diagnosis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    diagnosis = stop_loss_diagnosis or build_r8_stop_loss_diagnosis(
        artifact_id=f"{artifact_id}-stop-loss-diagnosis",
        run_id=run_id,
    )
    package = {
        "schema_version": R8_PRODUCT_FAILURE_DIAGNOSIS_PACKAGE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r8_product_failure_diagnosis_package_ready_guarded",
        "product_positioning": "人群反应趋势与风险区间模拟器",
        "package_contract": {
            "source_backed_only": True,
            "customer_visible": True,
            "diagnostic_only": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "executive_summary": {
            "research_decision": diagnosis["research_decision"],
            "display_level": "diagnostic_only",
            "primary_message": (
                "R8 当前不能支撑 Product 核心方法声明，但可作为失败诊断、"
                "证据请求和 outcome replay 工作流资产。"
            ),
        },
        "failure_cards": _failure_cards(diagnosis),
        "outcome_replay_workflow": _outcome_replay_workflow(diagnosis),
        "evidence_requests": [
            {
                "request_id": "field_or_customer_outcome",
                "why_needed": "R8 cannot move beyond diagnostic-only without real outcome validation.",
                "minimum_required_fields": [
                    "scenario_id",
                    "release_date",
                    "segment_id",
                    "observed_response_metric",
                    "measurement_window",
                ],
            },
            {
                "request_id": "segment_outcome_labels",
                "why_needed": "Risk ranking and abnormal segment claims require segment-level outcome support.",
                "minimum_required_fields": [
                    "segment_id",
                    "risk_label",
                    "label_source",
                    "label_confidence",
                ],
            },
        ],
        "acceptance_gates": {
            "failure_diagnosis_package_present": True,
            "customer_visible_diagnostic_allowed": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [diagnosis["artifact_id"]],
        "allowed_claims": [
            "R8 can be shown as a diagnostic failure-analysis and replay asset.",
            "Product can request outcome evidence before method promotion.",
        ],
        "blocked_claims": [
            "R8 validated",
            "R8 supports Product core method by default",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "accuracy superiority",
        ],
        "claim_boundary": R8_CLAIM_BOUNDARY,
    }
    assert_strict_json(package)
    return package


def write_r8_product_failure_diagnosis_package(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r8_product_failure_diagnosis_package(**kwargs))


def _failure_cards(diagnosis: dict[str, Any]) -> list[dict[str, Any]]:
    evidence_by_cause = {
        item["cause_id"]: item["evidence"] for item in diagnosis.get("diagnosis", [])
    }
    cards = []
    for cause_id in diagnosis["root_causes"]:
        template = _FAILURE_CARD_TEMPLATES.get(
            cause_id,
            {
                "title": cause_id,
                "customer_question": "这个阻断原因对产品展示有什么影响？",
                "product_response": "系统只展示 source-backed diagnostic 内容，不升级产品声明。",
            },
        )
        cards.append(
            {
                "card_id": cause_id,
                "title": template["title"],
                "customer_question": template["customer_question"],
                "evidence": evidence_by_cause.get(
                    cause_id,
                    f"Root cause reported by stop-loss diagnosis: {cause_id}.",
                ),
                "product_response": template["product_response"],
                "source_artifact_ids": [diagnosis["artifact_id"]],
                "display_level": "diagnostic_only",
            }
        )
    return cards


def _outcome_replay_workflow(diagnosis: dict[str, Any]) -> dict[str, Any]:
    return {
        "workflow_id": "r8_failure_diagnosis_outcome_replay",
        "status": "ready_guarded",
        "source_artifact_ids": [diagnosis["artifact_id"]],
        "steps": [
            {
                "step_id": "replay_current_blocked_result",
                "goal": "重放当前 R8 被阻断的 method support 与 root cause。",
            },
            {
                "step_id": "compare_against_baselines",
                "goal": "同口径比较 static prior、R6/R7 baseline 与 R8 输出。",
            },
            {
                "step_id": "collect_customer_or_field_outcome",
                "goal": "接入真实场景结果、群体标签和观测窗口。",
            },
            {
                "step_id": "rerun_r8_gate",
                "goal": "重新运行 robustness、holdout、field outcome 与 runtime default gate。",
            },
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-id",
        default="r8-product-failure-diagnosis-package-current-001",
    )
    parser.add_argument(
        "--run-id",
        default="r8-product-failure-diagnosis-package-current",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/r8_product_failure_diagnosis_package/"
            "r8-product-failure-diagnosis-package-current-001.json"
        ),
    )
    args = parser.parse_args()
    output = write_r8_product_failure_diagnosis_package(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    artifact = build_r8_product_failure_diagnosis_package(
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "output": str(output),
                "status": artifact["status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
