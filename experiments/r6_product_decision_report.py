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
from experiments.r6_product_story_package import build_r6_product_story_package


R6_PRODUCT_DECISION_REPORT_SCHEMA_VERSION = "r6-product-decision-report-v1"
R6_PRODUCT_DECISION_REPORT_CUSTOMER_SECTIONS = [
    "what_changed",
    "who_is_at_risk",
    "why_risk_moved",
    "what_is_supported_by_evidence",
    "what_is_blocked",
    "what_to_measure_next",
]


def build_r6_product_decision_report(
    *,
    artifact_id: str,
    run_id: str,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    story_package = build_r6_product_story_package(
        artifact_id=f"{artifact_id}-story-package",
        run_id=run_id,
    )
    report = {
        "schema_version": R6_PRODUCT_DECISION_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "decision_report_ready_guarded",
        "customer_sections": R6_PRODUCT_DECISION_REPORT_CUSTOMER_SECTIONS,
        "report_contract": {
            "source_backed_only": True,
            "static_narrative_fallback_allowed": False,
            "customer_visible_claims_require_source_artifact": True,
        },
        "display_sources": {
            "scenario": "story_package.section_contracts[scenario]",
            "evidence_cards": "story_package.evidence_card_ids",
            "blocked_claims": "story_package.blocked_claims",
            "next_measurement_plan": "story_package.next_measurement_plan",
        },
        "blocked_claims": story_package["blocked_claims"],
        "next_measurement_plan": story_package["next_measurement_plan"],
        "source_refs": [story_package["artifact_id"]],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_product_decision_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_decision_report(**kwargs))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r6_product_decision_report(
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
