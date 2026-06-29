from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_ablation_report import build_r6_ablation_report
from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_mechanism_cap_ablation import build_r6_mechanism_cap_ablation
from experiments.r6_public_outcome_proxy import build_r6_public_outcome_proxy


R6_CROSS_CASE_TRANSFER_PROTOCOL_SCHEMA_VERSION = "r6-cross-case-transfer-protocol-v1"
TRANSFER_STATUSES = {
    "passed",
    "non_regression_only",
    "condition_not_covered",
    "regressed",
    "invalid_proxy",
}


def build_r6_cross_case_transfer_protocol(
    *,
    artifact_id: str,
    run_id: str,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    ablations = _build_public_proxy_ablations(artifact_id=artifact_id, run_id=run_id)
    mechanism_cap = build_r6_mechanism_cap_ablation(
        artifact_id=f"{artifact_id}-mechanism-cap-ablation",
        run_id=run_id,
    )
    mechanism_cap_transfer = _mechanism_cap_transfer(
        artifact_id=artifact_id,
        mechanism_cap=mechanism_cap,
        ablations=ablations,
    )
    outcome_feedback_transfer = _outcome_feedback_transfer(
        artifact_id=artifact_id,
        ablations=ablations,
    )
    report = {
        "schema_version": R6_CROSS_CASE_TRANSFER_PROTOCOL_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "transfer_protocol_ready_global_update_blocked",
        "protocol_definition": {
            "purpose": "test frozen update rules across cases without peeking at holdout outcomes",
            "allowed_transfer_statuses": sorted(TRANSFER_STATUSES),
            "case_family_axes": [
                "case_type",
                "impact_dimension",
                "proxy_family",
                "population_axis",
                "measurement_level",
                "cap_condition",
            ],
        },
        "static_prior_role": {
            "role": "foundation_not_opponent",
            "runtime_update_guard": "candidate_updates_must_not_hurt_static_prior_before_default_enablement",
            "research_value_gate": "interaction_layer_must_discover_auditable_risk_not_visible_in_static_prior",
        },
        "candidate_transfers": [
            mechanism_cap_transfer,
            outcome_feedback_transfer,
        ],
        "acceptance_gates": {
            "cross_case_transfer_protocol_present": True,
            "mechanism_cap_source_fix_passed": mechanism_cap_transfer[
                "acceptance_gates"
            ]["source_fix_passed"],
            "mechanism_cap_l4_in_condition_transfer_passed": mechanism_cap_transfer[
                "acceptance_gates"
            ]["l4_in_condition_transfer_passed"],
            "outcome_feedback_transfer_available": True,
            "outcome_feedback_transfer_beats_prior_interaction": outcome_feedback_transfer[
                "acceptance_gates"
            ]["beats_prior_interaction_on_holdout"],
            "outcome_feedback_transfer_beats_static_prior": outcome_feedback_transfer[
                "acceptance_gates"
            ]["beats_static_prior_on_holdout"],
            "runtime_update_guard_passed": outcome_feedback_transfer[
                "acceptance_gates"
            ]["runtime_update_guard_passed"],
            "risk_discovery_value_path_open": True,
            "global_update_accepted": False,
        },
        "global_update_decision": {
            "accepted": False,
            "decision": "blocked",
            "reason": (
                "Mechanism cap lacks an in-condition same-family holdout. Outcome "
                "feedback transfers improve prior-interaction error, but default runtime "
                "updates remain blocked because they do not clear the static-prior guard. "
                "This blocks automatic update enablement, not the risk-discovery research "
                "path."
            ),
        },
        "source_refs": [
            mechanism_cap["artifact_id"],
        ]
        + [ablation["artifact_id"] for ablation in ablations.values()],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            "Cross-case transfer protocol is method-governance evidence, not field validation.",
            "The static prior is the simulator foundation; beating it is a runtime-update guard, not the whole R6 objective.",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "global_update_blocked",
            "mechanism_cap_l4_transfer_missing",
            "outcome_feedback_runtime_update_guard_failed",
            "public_proxy_not_field_validation",
        ],
        "blocking_gaps": [
            "needs_in_condition_same_family_rights_rule_holdout",
            "needs_runtime_update_guard_before_default_enablement",
            "needs_field_outcome_validation",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_cross_case_transfer_protocol(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_cross_case_transfer_protocol(**kwargs))


def _build_public_proxy_ablations(
    *,
    artifact_id: str,
    run_id: str,
) -> dict[str, dict[str, Any]]:
    ablations = {}
    for source_key in [
        "htops_cost_pressure",
        "anes_health_heldout",
        "anes_climate_heldout",
    ]:
        proxy = build_r6_public_outcome_proxy(
            artifact_id=f"{artifact_id}-{source_key}-proxy",
            run_id=run_id,
            source_key=source_key,
        )
        ablations[source_key] = build_r6_ablation_report(
            artifact_id=f"{artifact_id}-{source_key}-ablation",
            run_id=run_id,
            public_outcome_proxy=proxy,
        )
    return ablations


def _mechanism_cap_transfer(
    *,
    artifact_id: str,
    mechanism_cap: dict[str, Any],
    ablations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    cap_rule = mechanism_cap["cap_rule"]
    source_case = _case_from_ablation(
        ablations["anes_health_heldout"],
        source_key="anes_health_heldout",
        role="source",
    )
    holdout_trials = [
        _mechanism_cap_holdout_trial(
            ablations["htops_cost_pressure"],
            source_key="htops_cost_pressure",
            source_case=source_case,
            cap_rule=cap_rule,
        ),
        _mechanism_cap_holdout_trial(
            ablations["anes_climate_heldout"],
            source_key="anes_climate_heldout",
            source_case=source_case,
            cap_rule=cap_rule,
        ),
    ]
    l4_passed = any(trial["transfer_status"] == "passed" for trial in holdout_trials)
    return {
        "candidate_id": f"{artifact_id}-candidate-mechanism-cap",
        "candidate_type": "mechanism_cap",
        "evidence_level": "L3_partial",
        "source_case": source_case,
        "candidate_update": {
            "update_rule_id": "rights_rule_reject_delta_cap_v1",
            "update_type": "frozen_mechanism_cap",
            "frozen_rule": cap_rule,
            "derived_from_source_case": source_case["source_key"],
            "default_runtime_enabled": False,
        },
        "holdout_trials": holdout_trials,
        "acceptance_gates": {
            "source_fix_passed": True,
            "cross_proxy_non_regression_passed": any(
                trial["non_regression_vs_prior_interaction"]
                and not trial["same_family"]
                for trial in holdout_trials
            ),
            "same_family_holdout_available": any(
                trial["same_family"] for trial in holdout_trials
            ),
            "same_family_cap_condition_covered": any(
                trial["same_family"] and trial["cap_condition_met"]
                for trial in holdout_trials
            ),
            "l4_in_condition_transfer_passed": l4_passed,
            "global_update_accepted": False,
        },
        "transfer_decision": {
            "accepted": False,
            "decision": "blocked_until_in_condition_transfer",
            "reason": "ANES climate is same-family but does not cover the cap trigger condition.",
        },
    }


def _outcome_feedback_transfer(
    *,
    artifact_id: str,
    ablations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    trials = [
        _outcome_feedback_holdout_trial(
            source_ablation=ablations["anes_health_heldout"],
            source_key="anes_health_heldout",
            holdout_ablation=ablations["anes_climate_heldout"],
            holdout_key="anes_climate_heldout",
        ),
        _outcome_feedback_holdout_trial(
            source_ablation=ablations["anes_climate_heldout"],
            source_key="anes_climate_heldout",
            holdout_ablation=ablations["anes_health_heldout"],
            holdout_key="anes_health_heldout",
        ),
    ]
    return {
        "candidate_id": f"{artifact_id}-candidate-outcome-feedback",
        "candidate_type": "outcome_feedback_residual_transfer",
        "evidence_level": "L2_same_case_to_non_regression_transfer",
        "candidate_update": {
            "update_rule_id": "source_residual_shrinkage_transfer_v1",
            "update_type": "frozen_residual_delta",
            "feedback_alpha": 0.60,
            "direct_observed_value_copy": False,
            "holdout_outcome_used_for_rule_derivation": False,
            "default_runtime_enabled": False,
        },
        "holdout_trials": trials,
        "acceptance_gates": {
            "cross_case_transfer_available": True,
            "beats_prior_interaction_on_holdout": all(
                trial["updated_error"] < trial["prior_anchored_error"]
                for trial in trials
            ),
            "beats_static_prior_on_holdout": all(
                trial["updated_error"] <= trial["static_prior_error"]
                for trial in trials
            ),
            "runtime_update_guard_passed": all(
                trial["updated_error"] <= trial["static_prior_error"]
                for trial in trials
            ),
            "l4_in_condition_transfer_passed": all(
                trial["transfer_status"] == "passed" for trial in trials
            ),
            "global_update_accepted": False,
        },
        "transfer_decision": {
            "accepted": False,
            "decision": "runtime_update_blocked_but_risk_discovery_continues",
            "reason": (
                "Frozen residual transfer improves prior-interaction error on same-family "
                "holdouts, but remains worse than the static prior baseline. This blocks "
                "default runtime enablement while preserving the risk-discovery signal."
            ),
        },
    }


def _mechanism_cap_holdout_trial(
    ablation: dict[str, Any],
    *,
    source_key: str,
    source_case: dict[str, Any],
    cap_rule: dict[str, Any],
) -> dict[str, Any]:
    case = _case_from_ablation(ablation, source_key=source_key, role="holdout")
    no_interaction, prior = _baseline_pair(ablation)
    static_prediction = no_interaction["mean_prediction"]
    prior_prediction = prior["mean_prediction"]
    original_delta = round(prior_prediction - static_prediction, 3)
    cap_condition_met = _cap_condition_met(
        target_case_id=ablation["target_case_id"],
        static_error=no_interaction["mean_absolute_error"],
        original_reject_delta=original_delta,
        cap_rule=cap_rule,
    )
    if cap_condition_met:
        updated_prediction = round(
            static_prediction + cap_rule["max_aggregate_reject_delta"],
            2,
        )
    else:
        updated_prediction = prior_prediction
    observed = ablation["public_proxy"]["observed_reject_proxy"]
    updated_error = round(abs(updated_prediction - observed), 3)
    same_family = case["target_case_id"] == source_case["target_case_id"]
    status = _mechanism_transfer_status(
        same_family=same_family,
        cap_condition_met=cap_condition_met,
        prior_error=prior["mean_absolute_error"],
        static_error=no_interaction["mean_absolute_error"],
        updated_error=updated_error,
    )
    return {
        "trial_id": f"mechanism-cap:{source_case['source_key']}->{source_key}",
        "transfer_status": status,
        "source_case_key": source_case["source_key"],
        "holdout_case": case,
        "same_family": same_family,
        "cap_condition_met": cap_condition_met,
        "holdout_outcome_used_for_rule_derivation": False,
        "static_prior_prediction": static_prediction,
        "prior_anchored_prediction": prior_prediction,
        "updated_prediction": updated_prediction,
        "static_prior_error": no_interaction["mean_absolute_error"],
        "prior_anchored_error": prior["mean_absolute_error"],
        "updated_error": updated_error,
        "non_regression_vs_prior_interaction": updated_error
        <= prior["mean_absolute_error"],
        "strong_prior_gate_passed": updated_error
        <= no_interaction["mean_absolute_error"],
    }


def _outcome_feedback_holdout_trial(
    *,
    source_ablation: dict[str, Any],
    source_key: str,
    holdout_ablation: dict[str, Any],
    holdout_key: str,
) -> dict[str, Any]:
    source_no_interaction, source_prior = _baseline_pair(source_ablation)
    holdout_no_interaction, holdout_prior = _baseline_pair(holdout_ablation)
    source_observed = source_ablation["public_proxy"]["observed_reject_proxy"]
    residual_delta = round(
        0.60 * (source_observed - source_prior["mean_prediction"]),
        3,
    )
    updated_prediction = round(
        max(0.0, min(1.0, holdout_prior["mean_prediction"] + residual_delta)),
        2,
    )
    holdout_observed = holdout_ablation["public_proxy"]["observed_reject_proxy"]
    updated_error = round(abs(updated_prediction - holdout_observed), 3)
    same_family = (
        source_ablation["target_case_id"] == holdout_ablation["target_case_id"]
    )
    status = _outcome_transfer_status(
        same_family=same_family,
        prior_error=holdout_prior["mean_absolute_error"],
        static_error=holdout_no_interaction["mean_absolute_error"],
        updated_error=updated_error,
    )
    return {
        "trial_id": f"outcome-feedback:{source_key}->{holdout_key}",
        "transfer_status": status,
        "source_case": _case_from_ablation(
            source_ablation,
            source_key=source_key,
            role="source",
        ),
        "holdout_case": _case_from_ablation(
            holdout_ablation,
            source_key=holdout_key,
            role="holdout",
        ),
        "same_family": same_family,
        "frozen_rule": {
            "feedback_alpha": 0.60,
            "source_residual_delta": residual_delta,
            "application": "add_source_residual_delta_to_holdout_prior_interaction",
        },
        "holdout_outcome_used_for_rule_derivation": False,
        "static_prior_prediction": holdout_no_interaction["mean_prediction"],
        "prior_anchored_prediction": holdout_prior["mean_prediction"],
        "updated_prediction": updated_prediction,
        "static_prior_error": holdout_no_interaction["mean_absolute_error"],
        "prior_anchored_error": holdout_prior["mean_absolute_error"],
        "updated_error": updated_error,
        "non_regression_vs_prior_interaction": updated_error
        <= holdout_prior["mean_absolute_error"],
        "strong_prior_gate_passed": updated_error
        <= holdout_no_interaction["mean_absolute_error"],
        "source_static_prior_error": source_no_interaction["mean_absolute_error"],
        "source_prior_anchored_error": source_prior["mean_absolute_error"],
    }


def _case_from_ablation(
    ablation: dict[str, Any],
    *,
    source_key: str,
    role: str,
) -> dict[str, Any]:
    return {
        "role": role,
        "source_key": source_key,
        "target_case_id": ablation["target_case_id"],
        "case_type": _case_type(ablation["target_case_id"]),
        "proxy_family": _proxy_family(source_key),
        "measurement_level": "public_proxy",
        "population_axis": "public_use_segment_schema",
        "source_public_outcome_proxy_id": ablation["source_public_outcome_proxy_id"],
    }


def _baseline_pair(ablation: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    by_method = {result["method"]: result for result in ablation["baseline_results"]}
    return by_method["no_interaction_prior"], by_method["prior_anchored_interaction"]


def _cap_condition_met(
    *,
    target_case_id: str,
    static_error: float,
    original_reject_delta: float,
    cap_rule: dict[str, Any],
) -> bool:
    return (
        target_case_id == "generic-rights-rule-change"
        and static_error <= cap_rule["condition_static_prior_abs_error_lte"]
        and original_reject_delta > cap_rule["max_aggregate_reject_delta"]
    )


def _mechanism_transfer_status(
    *,
    same_family: bool,
    cap_condition_met: bool,
    prior_error: float,
    static_error: float,
    updated_error: float,
) -> str:
    if updated_error > prior_error:
        return "regressed"
    if same_family and not cap_condition_met:
        return "condition_not_covered"
    if updated_error < prior_error and updated_error <= static_error:
        return "passed"
    return "non_regression_only"


def _outcome_transfer_status(
    *,
    same_family: bool,
    prior_error: float,
    static_error: float,
    updated_error: float,
) -> str:
    if not same_family:
        return "invalid_proxy"
    if updated_error > prior_error:
        return "regressed"
    if updated_error < prior_error and updated_error <= static_error:
        return "passed"
    return "non_regression_only"


def _case_type(target_case_id: str) -> str:
    if target_case_id == "generic-rights-rule-change":
        return "rights_rule_change"
    if target_case_id == "generic-public-service-policy-change":
        return "public_service_policy_change"
    return "unknown"


def _proxy_family(source_key: str) -> str:
    return {
        "htops_cost_pressure": "cost_pressure_reaction",
        "anes_health_heldout": "public_health_insurance_preference",
        "anes_climate_heldout": "climate_energy_regulation_preference",
    }.get(source_key, "unknown")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_cross_case_transfer_protocol(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "global_update_accepted": report["acceptance_gates"][
                    "global_update_accepted"
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
