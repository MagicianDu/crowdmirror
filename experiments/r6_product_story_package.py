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
from experiments.r6_evidence_report import (
    R6_EVIDENCE_REPORT_SCHEMA_VERSION,
    build_r6_evidence_report,
)
from experiments.r6_cross_case_transfer_protocol import (
    build_r6_cross_case_transfer_protocol,
)
from experiments.r6_gap_closure_report import (
    R6_GAP_CLOSURE_REPORT_SCHEMA_VERSION,
    build_r6_gap_closure_report,
)
from experiments.r6_in_condition_holdout_ledger import (
    build_r6_in_condition_holdout_ledger,
)
from experiments.r6_mechanism_research_readiness_report import (
    build_r6_mechanism_research_readiness_report,
)
from experiments.r6_product_evidence_cards import (
    R6_PRODUCT_EVIDENCE_CARDS_SCHEMA_VERSION,
    build_r6_product_evidence_cards,
)
from experiments.r6_product_report import build_r6_product_report
from experiments.r6_product_scenario_intake import (
    R6_PRODUCT_SCENARIO_INTAKE_SCHEMA_VERSION,
    build_r6_product_scenario_intake,
)


R6_PRODUCT_STORY_PACKAGE_SCHEMA_VERSION = "r6-product-story-package-v1"
R6_PRODUCT_STORY_PACKAGE_SECTIONS = [
    "scenario",
    "static_prior_baseline",
    "interaction_risk_shift",
    "evidence_cards",
    "gap_closure",
    "blocked_claims",
    "next_measurement_plan",
]
R6_PRODUCT_STORY_DANGEROUS_CLAIM_STATUSES = {
    "accuracy_superiority_established",
    "field_validated",
    "runtime_default_ready",
    "ccf_a_ready",
}
R6_PRODUCT_STORY_CANONICAL_SOURCE_REGISTRY = [
    {
        "artifact_id": "r6-product-scenario-intake-current-001",
        "path": (
            "experiments/results/r6_product_scenario_intake/"
            "r6-product-scenario-intake-current-001.json"
        ),
    },
    {
        "artifact_id": "r6-product-report-current-003",
        "path": "experiments/results/r6_product_report/r6-product-report-current-003.json",
    },
    {
        "artifact_id": "r6-cross-case-transfer-protocol-current-002",
        "path": (
            "experiments/results/r6_cross_case_transfer_protocol/"
            "r6-cross-case-transfer-protocol-current-002.json"
        ),
    },
    {
        "artifact_id": "r6-in-condition-holdout-ledger-current-001",
        "path": (
            "experiments/results/r6_in_condition_holdout_ledger/"
            "r6-in-condition-holdout-ledger-current-001.json"
        ),
    },
    {
        "artifact_id": "r6-mechanism-research-readiness-report-current-001",
        "path": (
            "experiments/results/r6_mechanism_research_readiness_report/"
            "r6-mechanism-research-readiness-report-current-001.json"
        ),
    },
    {
        "artifact_id": "r6-gap-closure-report-current-001",
        "path": (
            "experiments/results/r6_gap_closure_report/"
            "r6-gap-closure-report-current-001.json"
        ),
    },
    {
        "artifact_id": "r6-evidence-report-current-014",
        "path": "experiments/results/r6_evidence_report/r6-evidence-report-current-014.json",
    },
    {
        "artifact_id": "r6-product-evidence-cards-current-003",
        "path": (
            "experiments/results/r6_product_evidence_cards/"
            "r6-product-evidence-cards-current-003.json"
        ),
    },
]


def build_r6_product_story_package(
    *,
    artifact_id: str,
    run_id: str,
    scenario_intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    if scenario_intake is None:
        scenario_intake = build_r6_product_scenario_intake(
            artifact_id="r6-product-scenario-intake-current-001",
            run_id=run_id,
        )
    scenario_intake_artifact_id = _validate_scenario_intake(scenario_intake)

    gap_closure_report = build_r6_gap_closure_report(
        artifact_id="r6-gap-closure-report-current-001",
        run_id=run_id,
    )
    gap_closure_artifact_id = _validate_gap_closure_report(gap_closure_report)
    product_report = build_r6_product_report(
        artifact_id="r6-product-report-current-003",
        run_id=run_id,
    )
    transfer_protocol = build_r6_cross_case_transfer_protocol(
        artifact_id="r6-cross-case-transfer-protocol-current-002",
        run_id=run_id,
    )
    holdout_ledger = build_r6_in_condition_holdout_ledger(
        artifact_id="r6-in-condition-holdout-ledger-current-001",
        run_id=run_id,
    )
    mechanism_research_readiness_report = build_r6_mechanism_research_readiness_report(
        artifact_id="r6-mechanism-research-readiness-report-current-001",
        run_id=run_id,
    )
    evidence_cards = build_r6_product_evidence_cards(
        artifact_id="r6-product-evidence-cards-current-003",
        run_id=run_id,
        product_report=product_report,
        transfer_protocol=transfer_protocol,
        holdout_ledger=holdout_ledger,
        mechanism_research_readiness_report=mechanism_research_readiness_report,
        gap_closure_report=gap_closure_report,
    )
    evidence_cards_artifact_id = _validate_product_evidence_cards(evidence_cards)
    evidence_report = build_r6_evidence_report(
        artifact_id="r6-evidence-report-current-014",
        run_id=run_id,
    )
    evidence_report_artifact_id = _validate_evidence_report(evidence_report)

    cards = evidence_cards["cards"]
    evidence_card_ids = [card["card_id"] for card in cards]
    display_field_paths = _card_display_field_paths(cards)
    section_contracts = _section_contracts(
        scenario_intake_artifact_id=scenario_intake_artifact_id,
        evidence_cards_artifact_id=evidence_cards_artifact_id,
        evidence_report_artifact_id=evidence_report_artifact_id,
        gap_closure_artifact_id=gap_closure_artifact_id,
        cards=cards,
    )
    report = {
        "schema_version": R6_PRODUCT_STORY_PACKAGE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "product_story_package_ready_guarded",
        "sections": R6_PRODUCT_STORY_PACKAGE_SECTIONS,
        "artifact_refs": {
            "scenario_intake": scenario_intake_artifact_id,
            "product_evidence_cards": evidence_cards_artifact_id,
            "evidence_report": evidence_report_artifact_id,
            "gap_closure_report": gap_closure_artifact_id,
        },
        "section_contracts": section_contracts,
        "evidence_card_ids": evidence_card_ids,
        "customer_visible_claim_cards": _customer_visible_claim_cards(cards),
        "display_field_paths": display_field_paths,
        "source_registry": _source_registry(scenario_intake_artifact_id),
        "ui_contract": {
            "consume_only_artifact_fields": True,
            "static_narrative_fallback_allowed": False,
            "all_customer_visible_claims_require_source_artifact": True,
            "section_ids": R6_PRODUCT_STORY_PACKAGE_SECTIONS,
            "required_display_fields": [
                "artifact_refs",
                "section_contracts[].source_artifact_ids",
                "section_contracts[].card_ids",
                "customer_visible_claim_cards[].source_artifact_ids",
                "customer_visible_claim_cards[].display_fields",
            ],
        },
        "claim_boundaries": _unique_strings(
            [
                R6_CLAIM_BOUNDARY,
                *evidence_cards.get("claim_boundaries", []),
                *gap_closure_report.get("claim_boundaries", []),
            ]
        ),
        "blocked_claims": _blocked_claims(
            cards=cards,
            gap_closure_report=gap_closure_report,
        ),
        "next_measurement_plan": {
            "source_artifact_ids": [
                evidence_report_artifact_id,
                gap_closure_artifact_id,
            ],
            "required_gate_paths": [
                "acceptance_gates.field_outcome_validated",
                "acceptance_gates.ccf_a_main_contribution_ready",
                "acceptance_gates.global_update_accepted",
                "remaining_gaps",
            ],
            "current_gate_values": {
                "field_outcome_validated": evidence_report["acceptance_gates"][
                    "field_outcome_validated"
                ],
                "ccf_a_main_contribution_ready": evidence_report[
                    "acceptance_gates"
                ]["ccf_a_main_contribution_ready"],
                "global_update_accepted": evidence_report["acceptance_gates"][
                    "global_update_accepted"
                ],
            },
        },
        "source_refs": _source_refs(
            scenario_intake,
            evidence_cards,
            evidence_report,
            gap_closure_report,
            required_refs=[
                scenario_intake_artifact_id,
                evidence_cards_artifact_id,
                evidence_report_artifact_id,
                gap_closure_artifact_id,
            ],
        ),
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_product_story_package(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_story_package(**kwargs))


def _validate_scenario_intake(report: dict[str, Any]) -> str:
    if not isinstance(report, dict):
        raise ValueError("scenario_intake must be an object")
    _require_exact(
        report,
        field="scenario_intake.schema_version",
        expected=R6_PRODUCT_SCENARIO_INTAKE_SCHEMA_VERSION,
    )
    _require_exact(
        report,
        field="scenario_intake.status",
        expected="scenario_intake_ready",
    )
    artifact_id = non_empty_string(
        report.get("artifact_id"),
        field="scenario_intake.artifact_id",
    )
    scenario = _require_object(
        report.get("scenario"),
        field="scenario_intake.scenario",
    )
    for field in (
        "scenario_id",
        "change_type",
        "target_population",
        "communication_plan",
        "decision_question",
        "domain_binding",
        "method_family",
    ):
        non_empty_string(
            scenario.get(field),
            field=f"scenario_intake.scenario.{field}",
        )
    _require_non_empty_string_list(
        scenario.get("impact_dimensions"),
        field="scenario_intake.scenario.impact_dimensions",
    )
    _require_non_empty_string_list(
        scenario.get("alternative_scenarios"),
        field="scenario_intake.scenario.alternative_scenarios",
    )
    _require_non_empty_string_list(
        scenario.get("assumptions"),
        field="scenario_intake.scenario.assumptions",
    )
    return artifact_id


def _validate_gap_closure_report(report: dict[str, Any]) -> str:
    _require_exact(
        report,
        field="gap_closure_report.schema_version",
        expected=R6_GAP_CLOSURE_REPORT_SCHEMA_VERSION,
    )
    _require_exact(
        report,
        field="gap_closure_report.status",
        expected="gap_closure_artifact_ready",
    )
    return non_empty_string(
        report.get("artifact_id"),
        field="gap_closure_report.artifact_id",
    )


def _validate_product_evidence_cards(report: dict[str, Any]) -> str:
    _require_exact(
        report,
        field="product_evidence_cards.schema_version",
        expected=R6_PRODUCT_EVIDENCE_CARDS_SCHEMA_VERSION,
    )
    _require_exact(
        report,
        field="product_evidence_cards.status",
        expected="product_evidence_cards_ready",
    )
    artifact_id = non_empty_string(
        report.get("artifact_id"),
        field="product_evidence_cards.artifact_id",
    )
    cards = report.get("cards")
    if not isinstance(cards, list) or not cards:
        raise ValueError("product_evidence_cards.cards must be a non-empty list")
    card_ids = []
    for index, card in enumerate(cards):
        if not isinstance(card, dict):
            raise ValueError(f"product_evidence_cards.cards[{index}] must be an object")
        card_ids.append(
            non_empty_string(
                card.get("card_id"),
                field=f"product_evidence_cards.cards[{index}].card_id",
            )
        )
        _validate_card_claim_status(
            card.get("claim_status"),
            field=f"product_evidence_cards.cards[{index}].claim_status",
        )
        _require_non_empty_string_list(
            card.get("allowed_claims"),
            field=f"product_evidence_cards.cards[{index}].allowed_claims",
        )
        _require_non_empty_string_list(
            card.get("blocked_claims"),
            field=f"product_evidence_cards.cards[{index}].blocked_claims",
        )
        _require_non_empty_string_list(
            card.get("source_artifact_ids"),
            field=f"product_evidence_cards.cards[{index}].source_artifact_ids",
        )
        _require_non_empty_string_list(
            card.get("display_fields"),
            field=f"product_evidence_cards.cards[{index}].display_fields",
        )
    if "r6-gap-closure-status" not in card_ids:
        raise ValueError("product_evidence_cards.cards must include r6-gap-closure-status")
    contract = _require_object(
        report.get("demo_api_contract"),
        field="product_evidence_cards.demo_api_contract",
    )
    if contract.get("static_narrative_fallback_allowed") is not False:
        raise ValueError(
            "product_evidence_cards.demo_api_contract."
            "static_narrative_fallback_allowed must be False"
        )
    return artifact_id


def _validate_evidence_report(report: dict[str, Any]) -> str:
    _require_exact(
        report,
        field="evidence_report.schema_version",
        expected=R6_EVIDENCE_REPORT_SCHEMA_VERSION,
    )
    artifact_id = non_empty_string(
        report.get("artifact_id"),
        field="evidence_report.artifact_id",
    )
    _require_object(
        report.get("acceptance_gates"),
        field="evidence_report.acceptance_gates",
    )
    return artifact_id


def _section_contracts(
    *,
    scenario_intake_artifact_id: str,
    evidence_cards_artifact_id: str,
    evidence_report_artifact_id: str,
    gap_closure_artifact_id: str,
    cards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    card_by_id = {card["card_id"]: card for card in cards}
    return [
        {
            "section_id": "scenario",
            "source_artifact_ids": [scenario_intake_artifact_id],
            "card_ids": [],
            "display_fields": [
                "scenario.scenario_id",
                "scenario.change_type",
                "scenario.target_population",
                "scenario.impact_dimensions",
                "scenario.decision_question",
            ],
        },
        _card_section(
            section_id="static_prior_baseline",
            card=card_by_id["static-prior-control"],
        ),
        _card_section(
            section_id="interaction_risk_shift",
            card=card_by_id["interaction-risk-shift"],
        ),
        {
            "section_id": "evidence_cards",
            "source_artifact_ids": [evidence_cards_artifact_id],
            "card_ids": [card["card_id"] for card in cards],
            "display_fields": [
                "cards[].card_id",
                "cards[].claim_status",
                "cards[].allowed_claims",
                "cards[].blocked_claims",
                "cards[].source_artifact_ids",
                "cards[].display_fields",
            ],
        },
        _card_section(
            section_id="gap_closure",
            card=card_by_id["r6-gap-closure-status"],
        ),
        {
            "section_id": "blocked_claims",
            "source_artifact_ids": [
                evidence_cards_artifact_id,
                gap_closure_artifact_id,
            ],
            "card_ids": [card["card_id"] for card in cards],
            "display_fields": [
                "cards[].blocked_claims",
                "blocked_claims",
                "claim_boundaries",
            ],
        },
        {
            "section_id": "next_measurement_plan",
            "source_artifact_ids": [
                evidence_report_artifact_id,
                gap_closure_artifact_id,
            ],
            "card_ids": ["r6-gap-closure-status"],
            "display_fields": [
                "acceptance_gates.field_outcome_validated",
                "acceptance_gates.ccf_a_main_contribution_ready",
                "acceptance_gates.global_update_accepted",
                "remaining_gaps",
            ],
        },
    ]


def _card_section(*, section_id: str, card: dict[str, Any]) -> dict[str, Any]:
    return {
        "section_id": section_id,
        "source_artifact_ids": card["source_artifact_ids"],
        "card_ids": [card["card_id"]],
        "display_fields": card["display_fields"],
    }


def _customer_visible_claim_cards(
    cards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    claim_cards = []
    for index, card in enumerate(cards):
        claim_cards.append(
            {
                "card_id": card["card_id"],
                "claim_status": _validate_card_claim_status(
                    card["claim_status"],
                    field=f"product_evidence_cards.cards[{index}].claim_status",
                ),
                "allowed_claims": _require_non_empty_string_list(
                    card["allowed_claims"],
                    field=f"product_evidence_cards.cards[{index}].allowed_claims",
                ),
                "blocked_claims": _require_non_empty_string_list(
                    card["blocked_claims"],
                    field=f"product_evidence_cards.cards[{index}].blocked_claims",
                ),
                "source_artifact_ids": card["source_artifact_ids"],
                "display_fields": card["display_fields"],
            }
        )
    return claim_cards


def _card_display_field_paths(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "card_id": card["card_id"],
            "source_artifact_ids": card["source_artifact_ids"],
            "display_fields": card["display_fields"],
        }
        for card in cards
    ]


def _blocked_claims(
    *,
    cards: list[dict[str, Any]],
    gap_closure_report: dict[str, Any],
) -> list[str]:
    claims = []
    for index, card in enumerate(cards):
        claims.extend(
            _require_non_empty_string_list(
                card.get("blocked_claims"),
                field=f"product_evidence_cards.cards[{index}].blocked_claims",
            )
        )
    claims.extend(
        _require_non_empty_string_list(
            gap_closure_report.get("blocked_claims"),
            field="gap_closure_report.blocked_claims",
        )
    )
    return _unique_strings(claims)


def _source_refs(
    *artifacts: dict[str, Any],
    required_refs: list[str],
) -> list[str]:
    refs = [*required_refs]
    for artifact in artifacts:
        artifact_id = artifact.get("artifact_id")
        if isinstance(artifact_id, str):
            refs.append(artifact_id)
    return _unique_strings(refs)


def _source_registry(scenario_intake_artifact_id: str) -> list[dict[str, str]]:
    registry = [dict(entry) for entry in R6_PRODUCT_STORY_CANONICAL_SOURCE_REGISTRY]
    registry_ids = {entry["artifact_id"] for entry in registry}
    if scenario_intake_artifact_id not in registry_ids:
        registry.append(
            {
                "artifact_id": scenario_intake_artifact_id,
                "path": "direct_input:scenario_intake",
            }
        )
    return registry


def _unique_strings(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        normalized = non_empty_string(value, field="source_ref")
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _validate_card_claim_status(value: Any, *, field: str) -> str:
    status = non_empty_string(value, field=field)
    if status in R6_PRODUCT_STORY_DANGEROUS_CLAIM_STATUSES:
        raise ValueError(f"{field} contains dangerous ready claim: {status}")
    return status


def _require_exact(report: dict[str, Any], *, field: str, expected: str) -> None:
    key = field.rsplit(".", 1)[-1]
    if report.get(key) != expected:
        raise ValueError(f"{field} must be {expected!r}")


def _require_object(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _require_non_empty_string_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a non-empty list")
    items = [
        non_empty_string(item, field=f"{field}[{index}]")
        for index, item in enumerate(value)
    ]
    if not items:
        raise ValueError(f"{field} must be a non-empty list")
    return items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r6_product_story_package(
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
