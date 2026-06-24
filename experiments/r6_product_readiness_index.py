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
from experiments.r6_evidence_report import build_r6_evidence_report


R6_PRODUCT_READINESS_INDEX_SCHEMA_VERSION = "r6-product-readiness-index-v1"


def build_r6_product_readiness_index(
    *,
    artifact_id: str,
    run_id: str,
    evidence_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    if evidence_report is None:
        evidence_report = build_r6_evidence_report(
            artifact_id=f"{artifact_id}-evidence-report",
            run_id=run_id,
        )
    frontend_demo_ready = _frontend_demo_ready()
    evidence_artifact_id = evidence_report.get("artifact_id")
    report = {
        "schema_version": R6_PRODUCT_READINESS_INDEX_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "product_first_readiness_partial",
        "product_goal": {
            "primary": "usable_pre_release_risk_assessment_product",
            "research_role": "theory_and_evidence_boundary_support",
            "not_default_goal": "ccf_a_main_contribution",
        },
        "readiness_gates": {
            "scenario_intake_ready": True,
            "story_package_ready": True,
            "evidence_cards_ready": _evidence_cards_ready(evidence_report),
            "decision_report_ready": True,
            "outcome_review_ready": True,
            "product_api_manifest_ready": True,
            "trend_interval_risk_metrics_ready": True,
            "research_product_value_support_ready": True,
            "customer_value_report_ready": True,
            "customer_facing_ui_demo_ready": frontend_demo_ready,
            "static_narrative_fallback_allowed": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "contract_readiness": {
            "scenario_intake_contract_ready": True,
            "story_package_contract_ready": True,
            "decision_report_contract_ready": True,
            "customer_value_report_contract_ready": True,
            "outcome_review_contract_ready": True,
            "product_api_manifest_contract_ready": True,
            "customer_frontend_demo_contract_ready": frontend_demo_ready,
            "contract_ready_is_not_field_validation": True,
        },
        "blocking_gaps": _blocking_gaps(frontend_demo_ready),
        "allowed_claims": [
            "R6 can support bounded pre-release risk discussion.",
            "R6 evidence cards are available as customer-facing claim boundaries.",
            "Source-backed customer-facing demo can render guarded R6 artifacts.",
        ],
        "blocked_claims": [
            "field validation 已完成",
            "runtime default 可以开启",
            "R6 已达到 CCF-A 主贡献",
            "交互仿真稳定比静态先验更准",
            "精准预测系统",
        ],
        "source_refs": (
            [evidence_artifact_id]
            if isinstance(evidence_artifact_id, str) and evidence_artifact_id.strip()
            else []
        ),
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def _evidence_cards_ready(evidence_report: dict[str, Any]) -> bool:
    acceptance_gates = evidence_report.get("acceptance_gates")
    product_evidence_cards_summary = evidence_report.get(
        "product_evidence_cards_summary"
    )
    if not isinstance(acceptance_gates, dict) or not isinstance(
        product_evidence_cards_summary,
        dict,
    ):
        return False
    card_count = product_evidence_cards_summary.get("card_count")
    if isinstance(card_count, bool) or not isinstance(card_count, int):
        return False
    return (
        acceptance_gates.get("product_evidence_cards_present") is True
        and acceptance_gates.get("product_guard_preserved") is True
        and product_evidence_cards_summary.get("status")
        == "product_evidence_cards_ready"
        and card_count >= 8
        and product_evidence_cards_summary.get("static_narrative_fallback_allowed")
        is False
    )


def _frontend_demo_ready() -> bool:
    repo_root = Path(__file__).resolve().parents[1]
    required_files = [
        repo_root / "demo" / "index.html",
        repo_root / "demo" / "app.js",
        repo_root / "demo" / "styles.css",
    ]
    return all(path.is_file() for path in required_files)


def _blocking_gaps(frontend_demo_ready: bool) -> list[str]:
    gaps = [
        "needs_field_outcome_validation",
        "needs_runtime_default_holdout_review",
    ]
    if frontend_demo_ready:
        gaps.append("needs_customer_workflow_runtime_integration")
    else:
        gaps.insert(0, "needs_customer_facing_ui_integration")
    return gaps


def write_r6_product_readiness_index(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_readiness_index(**kwargs))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r6_product_readiness_index(
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
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
