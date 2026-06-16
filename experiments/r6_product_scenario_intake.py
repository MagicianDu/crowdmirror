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


R6_PRODUCT_SCENARIO_INTAKE_SCHEMA_VERSION = "r6-product-scenario-intake-v1"


def build_r6_product_scenario_intake(
    *,
    artifact_id: str,
    run_id: str,
    scenario: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    scenario_payload = scenario or _default_scenario()
    normalized = {
        "scenario_id": non_empty_string(
            scenario_payload.get("scenario_id"), field="scenario.scenario_id"
        ),
        "change_type": non_empty_string(
            scenario_payload.get("change_type"), field="scenario.change_type"
        ),
        "target_population": non_empty_string(
            scenario_payload.get("target_population"),
            field="scenario.target_population",
        ),
        "impact_dimensions": _string_list(
            scenario_payload.get("impact_dimensions"),
            field="scenario.impact_dimensions",
        ),
        "communication_plan": non_empty_string(
            scenario_payload.get("communication_plan"),
            field="scenario.communication_plan",
        ),
        "alternative_scenarios": _string_list(
            scenario_payload.get("alternative_scenarios"),
            field="scenario.alternative_scenarios",
        ),
        "decision_question": non_empty_string(
            scenario_payload.get("decision_question"),
            field="scenario.decision_question",
        ),
        "assumptions": _string_list(
            scenario_payload.get("assumptions"),
            field="scenario.assumptions",
        ),
        "domain_binding": "case_input_not_method_definition",
        "method_family": _method_family(scenario_payload.get("change_type")),
    }
    report = {
        "schema_version": R6_PRODUCT_SCENARIO_INTAKE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "scenario_intake_ready",
        "scenario": normalized,
        "product_contract": {
            "can_drive_product_story_package": True,
            "vertical_overfit_allowed": False,
            "requires_static_prior_baseline": True,
            "requires_evidence_cards": True,
        },
        "risk_flags": [
            "case_specific_input_not_research_method",
            "scenario_assumptions_require_customer_review",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_product_scenario_intake(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_scenario_intake(**kwargs))


def _default_scenario() -> dict[str, Any]:
    return {
        "scenario_id": "generic-price-or-rule-change-001",
        "change_type": "price",
        "target_population": "affected_customers_or_public",
        "impact_dimensions": ["price_sensitivity", "fairness_concern", "churn_risk"],
        "communication_plan": "announce_change_with_reason",
        "alternative_scenarios": ["no_change", "phased_release", "support_credit"],
        "decision_question": "Which population segments need risk review before release?",
        "assumptions": ["static prior is available", "interaction risk is diagnostic"],
    }


def _string_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    items = [
        non_empty_string(item, field=f"{field}[{index}]")
        for index, item in enumerate(value)
    ]
    if not items:
        raise ValueError(f"{field} must contain at least one item")
    return items


def _method_family(change_type: Any) -> str:
    normalized = non_empty_string(change_type, field="scenario.change_type")
    if normalized in {"price", "fee", "fare", "charge"}:
        return "price_or_rule_change_reaction"
    if normalized in {"rule", "policy", "rights", "service"}:
        return "price_or_rule_change_reaction"
    return "general_change_reaction"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r6_product_scenario_intake(
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
