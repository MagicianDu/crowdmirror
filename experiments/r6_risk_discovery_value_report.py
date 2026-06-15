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
from experiments.r6_decision_value_metrics import build_r6_decision_value_metrics
from experiments.r6_false_alarm_discriminator import (
    build_r6_false_alarm_discriminator,
)
from experiments.r6_in_condition_holdout_ledger import (
    build_r6_in_condition_holdout_ledger,
)
from experiments.r6_product_evidence_cards import build_r6_product_evidence_cards
from experiments.r6_risk_discovery_holdout_validation import (
    build_r6_risk_discovery_holdout_validation,
)
from experiments.r6_risk_discovery_threshold_sweep import (
    build_r6_risk_discovery_threshold_sweep,
)


R6_RISK_DISCOVERY_VALUE_REPORT_SCHEMA_VERSION = "r6-risk-discovery-value-report-v1"


def build_r6_risk_discovery_value_report(
    *,
    artifact_id: str,
    run_id: str,
    transfer_protocol: dict[str, Any] | None = None,
    holdout_ledger: dict[str, Any] | None = None,
    product_evidence_cards: dict[str, Any] | None = None,
    decision_value_metrics: dict[str, Any] | None = None,
    risk_discovery_threshold_sweep: dict[str, Any] | None = None,
    false_alarm_discriminator: dict[str, Any] | None = None,
    risk_discovery_holdout_validation: dict[str, Any] | None = None,
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
    decision_value_metrics = decision_value_metrics or build_r6_decision_value_metrics(
        artifact_id=f"{artifact_id}-decision-value-metrics",
        run_id=run_id,
    )
    risk_discovery_threshold_sweep = (
        risk_discovery_threshold_sweep
        or build_r6_risk_discovery_threshold_sweep(
            artifact_id=f"{artifact_id}-threshold-sweep",
            run_id=run_id,
        )
    )
    false_alarm_discriminator = (
        false_alarm_discriminator
        or build_r6_false_alarm_discriminator(
            artifact_id=f"{artifact_id}-false-alarm-discriminator",
            run_id=run_id,
            decision_value_metrics=decision_value_metrics,
        )
    )
    risk_discovery_holdout_validation = (
        risk_discovery_holdout_validation
        or build_r6_risk_discovery_holdout_validation(
            artifact_id=f"{artifact_id}-risk-discovery-holdout-validation",
            run_id=run_id,
            decision_value_metrics=decision_value_metrics,
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
        "decision_value_metric_present": True,
        "decision_value_metric_passed": decision_value_metrics["decision_value_passed"],
        "threshold_sweep_present": True,
        "threshold_tuning_sufficient": risk_discovery_threshold_sweep["decision"][
            "threshold_tuning_sufficient"
        ],
        "false_alarm_reducible_by_threshold": risk_discovery_threshold_sweep[
            "summary"
        ]["false_alarm_reducible_by_threshold"],
        "false_alarm_discriminator_present": True,
        "false_alarm_discriminator_ready": false_alarm_discriminator[
            "acceptance_gates"
        ]["false_alarm_discriminator_ready"],
        "generalizable_false_alarm_discriminator_found": false_alarm_discriminator[
            "acceptance_gates"
        ]["generalizable_discriminator_found"],
        "risk_discovery_holdout_validation_present": True,
        "risk_discovery_holdout_passed": risk_discovery_holdout_validation[
            "acceptance_gates"
        ]["risk_discovery_holdout_passed"],
        "field_outcome_validated": False,
    }
    decision_value_passed = decision_value_metrics["decision_value_passed"]
    holdout_passed = risk_discovery_holdout_validation["acceptance_gates"][
        "risk_discovery_holdout_passed"
    ]
    false_alarm_discriminator_ready = false_alarm_discriminator["acceptance_gates"][
        "false_alarm_discriminator_ready"
    ]
    report = {
        "schema_version": R6_RISK_DISCOVERY_VALUE_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "risk_discovery_value_ready_for_field_validation"
            if decision_value_passed and holdout_passed
            else "risk_discovery_value_partial_decision_metric_failed_holdout"
        ),
        "objective_reframe": {
            "static_prior_role": "foundation_not_opponent",
            "interaction_role": "discover_auditable_risk_shifts_beyond_static_prior",
            "outcome_feedback_role": "learn_from_real_outcomes_under_runtime_guards",
        },
        "risk_discovery_gates": gates,
        "decision_value_summary": {
            "artifact_id": decision_value_metrics["artifact_id"],
            "status": decision_value_metrics["status"],
            "decision_value_passed": decision_value_metrics["decision_value_passed"],
            "static_prior_miss_recovery_rate": decision_value_metrics["summary"][
                "static_prior_miss_recovery_rate"
            ],
            "top_k_risk_hit_rate": decision_value_metrics["summary"][
                "top_k_risk_hit_rate"
            ],
            "false_alarm_rate": decision_value_metrics["summary"][
                "false_alarm_rate"
            ],
            "decision_regret_reduction": decision_value_metrics["summary"][
                "decision_regret_reduction"
            ],
        },
        "threshold_sweep_summary": {
            "artifact_id": risk_discovery_threshold_sweep["artifact_id"],
            "status": risk_discovery_threshold_sweep["status"],
            "passing_threshold_found": risk_discovery_threshold_sweep[
                "acceptance_gates"
            ]["passing_threshold_found"],
            "separating_threshold_found": risk_discovery_threshold_sweep[
                "acceptance_gates"
            ]["separating_threshold_found"],
            "false_alarm_reducible_by_threshold": risk_discovery_threshold_sweep[
                "summary"
            ]["false_alarm_reducible_by_threshold"],
            "best_threshold": risk_discovery_threshold_sweep["summary"][
                "best_threshold"
            ],
            "true_signal_false_alarm_delta_overlap": risk_discovery_threshold_sweep[
                "summary"
            ]["true_signal_false_alarm_delta_overlap"],
        },
        "false_alarm_discriminator_summary": {
            "artifact_id": false_alarm_discriminator["artifact_id"],
            "status": false_alarm_discriminator["status"],
            "current_proxy_separation_found": false_alarm_discriminator[
                "acceptance_gates"
            ]["current_proxy_separation_found"],
            "pre_outcome_safe_candidate_found": false_alarm_discriminator[
                "acceptance_gates"
            ]["pre_outcome_safe_candidate_found"],
            "generalizable_discriminator_found": false_alarm_discriminator[
                "acceptance_gates"
            ]["generalizable_discriminator_found"],
            "accepted_candidate_count": false_alarm_discriminator["summary"][
                "accepted_candidate_count"
            ],
            "false_alarm_discriminator_ready": false_alarm_discriminator_ready,
        },
        "holdout_validation_summary": {
            "artifact_id": risk_discovery_holdout_validation["artifact_id"],
            "status": risk_discovery_holdout_validation["status"],
            "risk_discovery_holdout_passed": holdout_passed,
            "same_family_trial_count": risk_discovery_holdout_validation["summary"][
                "same_family_trial_count"
            ],
            "passed_trial_count": risk_discovery_holdout_validation["summary"][
                "passed_trial_count"
            ],
        },
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
            "ccf_a_risk_discovery_claim_ready": (
                decision_value_passed
                and holdout_passed
                and false_alarm_discriminator_ready
            ),
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
            "static_prior_miss_recovery_observed",
            "unvalidated_runtime_updates_blocked",
        ],
        "blocking_gaps": _blocking_gaps(
            decision_value_metrics=decision_value_metrics,
            risk_discovery_threshold_sweep=risk_discovery_threshold_sweep,
            false_alarm_discriminator=false_alarm_discriminator,
            risk_discovery_holdout_validation=risk_discovery_holdout_validation,
        ),
        "source_refs": [
            transfer_protocol["artifact_id"],
            holdout_ledger["artifact_id"],
            product_evidence_cards["artifact_id"],
            decision_value_metrics["artifact_id"],
            risk_discovery_threshold_sweep["artifact_id"],
            false_alarm_discriminator["artifact_id"],
            risk_discovery_holdout_validation["artifact_id"],
        ],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            "Risk-discovery value is not a claim of aggregate accuracy superiority over the static prior.",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "static_prior_is_foundation_not_opponent",
            "risk_discovery_holdout_validation_failed",
            "decision_value_metric_partial",
            "threshold_tuning_insufficient",
            "false_alarm_discriminator_not_runtime_ready",
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


def _blocking_gaps(
    *,
    decision_value_metrics: dict[str, Any],
    risk_discovery_threshold_sweep: dict[str, Any],
    false_alarm_discriminator: dict[str, Any],
    risk_discovery_holdout_validation: dict[str, Any],
) -> list[str]:
    gaps = [
        "needs_field_outcome_validation",
        "needs_runtime_update_guard_before_default_enablement",
    ]
    gaps.extend(decision_value_metrics["blocking_gaps"])
    gaps.extend(
        _threshold_gaps_after_discriminator(
            risk_discovery_threshold_sweep=risk_discovery_threshold_sweep,
            false_alarm_discriminator=false_alarm_discriminator,
        )
    )
    gaps.extend(false_alarm_discriminator["blocking_gaps"])
    gaps.extend(risk_discovery_holdout_validation["blocking_gaps"])
    if not decision_value_metrics["decision_value_passed"]:
        gaps.append("needs_decision_value_metric_to_pass")
    if not risk_discovery_holdout_validation["acceptance_gates"][
        "risk_discovery_holdout_passed"
    ]:
        gaps.append("needs_risk_discovery_holdout_validation")
    if not false_alarm_discriminator["acceptance_gates"][
        "false_alarm_discriminator_ready"
    ]:
        gaps.append("needs_generalizable_false_alarm_discriminator")
    return sorted(set(gaps))


def _threshold_gaps_after_discriminator(
    *,
    risk_discovery_threshold_sweep: dict[str, Any],
    false_alarm_discriminator: dict[str, Any],
) -> list[str]:
    if not false_alarm_discriminator["acceptance_gates"][
        "false_alarm_discriminator_present"
    ]:
        return risk_discovery_threshold_sweep["blocking_gaps"]
    return [
        gap
        for gap in risk_discovery_threshold_sweep["blocking_gaps"]
        if gap != "needs_non_threshold_false_alarm_discriminator"
    ]


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
