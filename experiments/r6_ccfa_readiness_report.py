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
from experiments.r6_product_evidence_cards import build_r6_product_evidence_cards
from experiments.r6_risk_discovery_value_report import (
    build_r6_risk_discovery_value_report,
)


R6_CCFA_READINESS_REPORT_SCHEMA_VERSION = "r6-ccfa-readiness-report-v1"


def build_r6_ccfa_readiness_report(
    *,
    artifact_id: str,
    run_id: str,
    transfer_protocol: dict[str, Any] | None = None,
    holdout_ledger: dict[str, Any] | None = None,
    product_evidence_cards: dict[str, Any] | None = None,
    risk_discovery_value_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    transfer_protocol = transfer_protocol or build_r6_cross_case_transfer_protocol(
        artifact_id=f"{artifact_id}-transfer-protocol",
        run_id=run_id,
    )
    holdout_ledger = holdout_ledger or build_r6_in_condition_holdout_ledger(
        artifact_id=f"{artifact_id}-holdout-ledger",
        run_id=run_id,
    )
    product_evidence_cards = (
        product_evidence_cards
        or build_r6_product_evidence_cards(
            artifact_id=f"{artifact_id}-product-evidence-cards",
            run_id=run_id,
            transfer_protocol=transfer_protocol,
            holdout_ledger=holdout_ledger,
        )
    )
    risk_discovery_value_report = (
        risk_discovery_value_report
        or build_r6_risk_discovery_value_report(
            artifact_id=f"{artifact_id}-risk-discovery-value-report",
            run_id=run_id,
            transfer_protocol=transfer_protocol,
            holdout_ledger=holdout_ledger,
            product_evidence_cards=product_evidence_cards,
        )
    )
    checklist = _readiness_checklist(
        transfer_protocol=transfer_protocol,
        holdout_ledger=holdout_ledger,
        product_evidence_cards=product_evidence_cards,
        risk_discovery_value_report=risk_discovery_value_report,
    )
    failed_required = [
        item for item in checklist if item["required_for_ccf_a"] and item["status"] != "passed"
    ]
    report = {
        "schema_version": R6_CCFA_READINESS_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "ccf_a_readiness_evaluated",
        "verdict": {
            "ccf_a_main_contribution_ready": False,
            "readiness_level": "L3_risk_discovery_framework_needs_validation",
            "decision": "not_ready_for_ccf_a_submission_as_main_algorithm",
            "short_answer": (
                "R6 should be evaluated as a static-prior anchored risk-discovery "
                "framework. The static prior is the simulation base, while interaction "
                "adds auditable risk hypotheses. The framework is not CCF-A-ready until "
                "risk-discovery holdout validation, decision-value metrics, and field "
                "outcome validation are present."
            ),
        },
        "readiness_checklist": checklist,
        "failed_required_gate_count": len(failed_required),
        "failed_required_gates": [
            {
                "gate_id": item["gate_id"],
                "status": item["status"],
                "blocking_gap": item["blocking_gap"],
            }
            for item in failed_required
        ],
        "positive_assets": [
            "prior_anchored_interaction_problem_reframed",
            "static_prior_reframed_as_simulation_foundation",
            "risk_discovery_value_report_added",
            "no_interaction_control_and_public_proxy_baselines_available",
            "failure_boundary_and_candidate_repair_are_auditable",
            "unvalidated_updates_are_blocked_by_registry_and_gates",
            "product_evidence_cards_make_claim_boundary_customer_visible",
        ],
        "paper_claim_boundary": {
            "allowed_claim": (
                "R6 is a static-prior anchored risk-discovery framework with "
                "diagnostic evidence, explicit blocked-update gates, and Product-visible "
                "claim boundaries."
            ),
            "blocked_claim": (
                "R6 already guarantees aggregate predictive accuracy, field validity, "
                "or default runtime updates beyond the static-prior foundation."
            ),
        },
        "recommended_next_research_steps": [
            "define_risk_discovery_decision_value_metric",
            "bind_in_condition_holdout_to_risk_discovery_validation",
            "add_field_or_real_release_outcome_validation",
            "formalize_interaction_operator_and_gated_update_theory",
            "compare_risk_discovery_value_against_static_prior_only_and_random_interaction",
        ],
        "source_refs": [
            transfer_protocol["artifact_id"],
            holdout_ledger["artifact_id"],
            product_evidence_cards["artifact_id"],
            risk_discovery_value_report["artifact_id"],
        ],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            "CCF-A readiness report is a gate evaluation; failed gates must not be softened into positive claims.",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "not_ccf_a_ready",
            "risk_discovery_holdout_validation_missing",
            "decision_value_metric_missing",
            "field_validation_missing",
            "runtime_update_guard_not_passed",
        ],
        "blocking_gaps": sorted(
            {
                item["blocking_gap"]
                for item in failed_required
                if item["blocking_gap"]
            }
        ),
    }
    assert_strict_json(report)
    return report


def write_r6_ccfa_readiness_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_ccfa_readiness_report(**kwargs))


def _readiness_checklist(
    *,
    transfer_protocol: dict[str, Any],
    holdout_ledger: dict[str, Any],
    product_evidence_cards: dict[str, Any],
    risk_discovery_value_report: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "formal_problem_defined",
            "required_for_ccf_a": True,
            "status": "partial",
            "evidence": (
                "active R6 specs define the prior-anchored risk-discovery problem, "
                "but no manuscript-level formal objective is complete."
            ),
            "blocking_gap": "needs_formal_problem_and_theory_section",
        },
        {
            "gate_id": "static_prior_foundation",
            "required_for_ccf_a": True,
            "status": "passed",
            "evidence": (
                "risk_discovery_report.static_prior_role="
                f"{risk_discovery_value_report['objective_reframe']['static_prior_role']}"
            ),
            "blocking_gap": "",
        },
        {
            "gate_id": "risk_discovery_objective_defined",
            "required_for_ccf_a": True,
            "status": "passed",
            "evidence": (
                "interaction_role="
                f"{risk_discovery_value_report['objective_reframe']['interaction_role']}"
            ),
            "blocking_gap": "",
        },
        {
            "gate_id": "interaction_risk_signal_present",
            "required_for_ccf_a": True,
            "status": "passed",
            "evidence": (
                "interaction_delta_observable="
                f"{risk_discovery_value_report['risk_discovery_gates']['interaction_delta_observable']}; "
                "failure_boundary_detected="
                f"{risk_discovery_value_report['risk_discovery_gates']['failure_boundary_detected']}"
            ),
            "blocking_gap": "",
        },
        {
            "gate_id": "risk_discovery_holdout_validation",
            "required_for_ccf_a": True,
            "status": "failed",
            "evidence": (
                "in_condition_holdout_count="
                f"{holdout_ledger['summary']['in_condition_holdout_count']}; "
                "mechanism_cap_l4_in_condition_transfer_passed="
                f"{transfer_protocol['acceptance_gates']['mechanism_cap_l4_in_condition_transfer_passed']}"
            ),
            "blocking_gap": "needs_risk_discovery_holdout_validation",
        },
        {
            "gate_id": "failure_boundary_systematically_explained",
            "required_for_ccf_a": True,
            "status": "passed",
            "evidence": (
                "ANES health over-amplification is diagnosed, converted into a "
                "candidate cap, and exposed through Product evidence cards; predictive "
                "holdout validation is tracked by the risk-discovery holdout gate."
            ),
            "blocking_gap": "",
        },
        {
            "gate_id": "decision_value_metric",
            "required_for_ccf_a": True,
            "status": "failed",
            "evidence": (
                "decision_value_metric_present="
                f"{risk_discovery_value_report['risk_discovery_gates']['decision_value_metric_present']}"
            ),
            "blocking_gap": "needs_decision_value_metric_topk_or_regret",
        },
        {
            "gate_id": "runtime_update_guard",
            "required_for_ccf_a": False,
            "status": "failed",
            "evidence": transfer_protocol["global_update_decision"]["reason"],
            "blocking_gap": "needs_runtime_update_guard_before_default_enablement",
        },
        {
            "gate_id": "field_or_real_outcome_validation",
            "required_for_ccf_a": True,
            "status": "failed",
            "evidence": "Current evidence is bounded public proxy evidence, not field outcome validation.",
            "blocking_gap": "needs_field_outcome_validation",
        },
        {
            "gate_id": "product_claim_boundary",
            "required_for_ccf_a": False,
            "status": "passed",
            "evidence": (
                "product_evidence_card_count="
                f"{product_evidence_cards['card_count']}; "
                "static_narrative_fallback_allowed="
                f"{product_evidence_cards['demo_api_contract']['static_narrative_fallback_allowed']}"
            ),
            "blocking_gap": "",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_ccfa_readiness_report(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "ccf_a_main_contribution_ready": report["verdict"][
                    "ccf_a_main_contribution_ready"
                ],
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
