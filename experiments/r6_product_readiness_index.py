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


def build_r6_product_readiness_index(*, artifact_id: str, run_id: str) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    evidence_report = build_r6_evidence_report(
        artifact_id=f"{artifact_id}-evidence-report",
        run_id=run_id,
    )
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
            "scenario_intake_ready": False,
            "evidence_cards_ready": evidence_report["acceptance_gates"][
                "product_evidence_cards_present"
            ],
            "decision_report_ready": False,
            "outcome_review_ready": False,
            "static_narrative_fallback_allowed": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "blocking_gaps": [
            "needs_product_scenario_intake",
            "needs_customer_decision_report",
            "needs_outcome_review_contract",
            "needs_product_ui_or_api_contract",
        ],
        "allowed_claims": [
            "R6 can support bounded pre-release risk discussion.",
            "R6 evidence cards are available as customer-facing claim boundaries.",
        ],
        "blocked_claims": [
            "field validation 已完成",
            "runtime default 可以开启",
            "R6 已达到 CCF-A 主贡献",
            "交互仿真稳定比静态先验更准",
        ],
        "source_refs": [evidence_report["artifact_id"]],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


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
