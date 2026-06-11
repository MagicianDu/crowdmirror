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


R6_RISK_DISCOVERY_VALUE_REPORT_SCHEMA_VERSION = "r6-risk-discovery-value-report-v1"


def build_r6_risk_discovery_value_report(
    *,
    artifact_id: str,
    run_id: str,
    transfer_protocol: dict[str, Any] | None = None,
    holdout_ledger: dict[str, Any] | None = None,
    product_evidence_cards: dict[str, Any] | None = None,
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
    gates = {
        "static_prior_foundation_present": True,
        "interaction_delta_observable": _has_card(
            product_evidence_cards,
            "interaction-risk-shift",
        ),
        "failure_boundary_detected": _has_card(
            product_evidence_cards,
            "mechanism-cap-transfer",
        ),
        "product_evidence_cards_present": product_evidence_cards["card_count"] > 0,
        "in_condition_holdout_bound": holdout_ledger["summary"][
            "global_update_data_gate_passed"
        ],
        "decision_value_metric_present": False,
        "field_outcome_validated": False,
    }
    report = {
        "schema_version": R6_RISK_DISCOVERY_VALUE_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "risk_discovery_value_framework_ready_needs_holdout_validation",
        "objective_reframe": {
            "static_prior_role": "foundation_not_opponent",
            "interaction_role": "discover_auditable_risk_shifts_beyond_static_prior",
            "outcome_feedback_role": "learn_from_real_outcomes_under_runtime_guards",
        },
        "risk_discovery_gates": gates,
        "runtime_update_guard": {
            "beat_static_prior_required_for_default_update": True,
            "static_prior_gate_role": "runtime_update_guard_not_research_objective",
            "outcome_feedback_runtime_default_accepted": transfer_protocol[
                "acceptance_gates"
            ]["global_update_accepted"],
        },
        "decision": {
            "r6_overall_worth_continuing": True,
            "decision": "continue_as_prior_anchored_risk_discovery_framework",
            "runtime_update_default_ready": False,
            "ccf_a_risk_discovery_claim_ready": False,
            "reason": (
                "Static prior is the simulator base. R6 value is judged by whether "
                "the interaction layer surfaces auditable risk shifts, failure "
                "boundaries, and learnable update candidates, while runtime default "
                "updates remain blocked until they clear the static-prior guard."
            ),
        },
        "success_signals": [
            "static_prior_foundation_present",
            "interaction_risk_shift_card_present",
            "failure_boundary_card_present",
            "unvalidated_runtime_updates_blocked",
        ],
        "blocking_gaps": [
            "needs_risk_discovery_holdout_validation",
            "needs_decision_value_metric_topk_or_regret",
            "needs_field_outcome_validation",
            "needs_runtime_update_guard_before_default_enablement",
        ],
        "source_refs": [
            transfer_protocol["artifact_id"],
            holdout_ledger["artifact_id"],
            product_evidence_cards["artifact_id"],
        ],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            "Risk-discovery value is not a claim of aggregate accuracy superiority over the static prior.",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "static_prior_is_foundation_not_opponent",
            "risk_discovery_holdout_validation_missing",
            "decision_value_metric_missing",
            "field_validation_missing",
            "runtime_update_guard_not_passed",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_risk_discovery_value_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(
        output,
        build_r6_risk_discovery_value_report(**kwargs),
    )


def _has_card(report: dict[str, Any], card_id: str) -> bool:
    return any(card["card_id"] == card_id for card in report["cards"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_risk_discovery_value_report(
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
                "r6_overall_worth_continuing": report["decision"][
                    "r6_overall_worth_continuing"
                ],
                "status": report["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
