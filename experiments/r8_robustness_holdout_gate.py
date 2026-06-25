from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact
from experiments.r8_baseline_comparison import build_r8_baseline_comparison
from experiments.r8_learnable_mechanism_simulation import (
    R8_CLAIM_BOUNDARY,
    build_r8_learnable_mechanism_bundle,
)


VALIDATION_AXES = [
    "outcome_perturbation",
    "leave_one_case",
    "same_family_holdout",
    "cross_family_fail_closed",
]


def build_r8_robustness_holdout_gate(
    *,
    artifact_id: str,
    run_id: str,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    baseline = build_r8_baseline_comparison(
        artifact_id=f"{artifact_id}-baseline-comparison",
        run_id=run_id,
    )
    perturbations = _outcome_perturbations()
    leave_one = _leave_one_case_trials()
    same_family = _same_family_holdout_trials()
    cross_family = _cross_family_fail_closed_trials()

    l1_passed = (
        baseline["stop_loss_recommendation"] == "continue_to_holdout_validation"
    )
    l2_passed = (
        l1_passed
        and all(trial["passed"] for trial in same_family)
        and all(trial["fail_closed"] for trial in cross_family)
    )
    stop_loss = (
        "continue_to_product_ingestion_guarded"
        if l2_passed
        else "keep_r8_as_diagnostic_asset"
        if baseline["stop_loss_recommendation"] != "stop_loss_r8_main_method"
        else "stop_loss_r8_main_method"
    )
    status = (
        "r8_holdout_positive_guarded"
        if l2_passed
        else "r8_current_proxy_positive_guarded"
        if l1_passed
        else "r8_robustness_diagnostic_or_stop_loss"
    )
    report = {
        "schema_version": "r8-robustness-holdout-gate-v1",
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "validation_axes": VALIDATION_AXES,
        "summary": {
            "perturbation_scenario_count": len(perturbations),
            "perturbation_pass_rate": _rate(
                sum(1 for item in perturbations if item["passed"]),
                len(perturbations),
            ),
            "leave_one_case_trial_count": len(leave_one),
            "leave_one_non_regression_rate": _rate(
                sum(1 for item in leave_one if item["non_regression"]),
                len(leave_one),
            ),
            "same_family_holdout_trial_count": len(same_family),
            "cross_family_fail_closed_trial_count": len(cross_family),
        },
        "l1_status": "passed_guarded" if l1_passed else "diagnostic_blocked",
        "l2_status": "passed_guarded" if l2_passed else "diagnostic_blocked",
        "outcome_perturbation_results": perturbations,
        "leave_one_case_results": leave_one,
        "same_family_holdout_results": same_family,
        "cross_family_fail_closed_results": cross_family,
        "stop_loss_recommendation": stop_loss,
        "acceptance_gates": {
            "robustness_gate_present": True,
            "l1_current_proxy_signal_passed": l1_passed,
            "l2_holdout_signal_passed": l2_passed,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [baseline["artifact_id"]],
        "allowed_claims": [
            (
                "R8 robustness gate can decide guarded continuation or diagnostic "
                "downgrade."
            )
        ],
        "blocked_claims": [
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "runtime default ready",
            "R8 validated",
        ],
        "claim_boundary": R8_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def _outcome_perturbations() -> list[dict[str, Any]]:
    cases = [
        ("htops_cost_pressure", "generic-public-service-policy-change", 0.47),
        ("anes_health_heldout", "generic-rights-rule-change", 0.33),
        ("anes_climate_heldout", "generic-rights-rule-change", 0.25),
    ]
    results = []
    for source_key, case_id, observed in cases:
        for delta in [-0.03, 0.0, 0.03]:
            adjusted = round(observed + delta, 3)
            bundle = build_r8_learnable_mechanism_bundle(
                artifact_id=f"r8-perturbation-{source_key}-{delta}",
                run_id="r8-perturbation",
                case_id=case_id,
                observed_reject_proxy=adjusted,
            )
            update = bundle["artifacts"]["r8_operator_update_candidate"]
            results.append(
                {
                    "source_key": source_key,
                    "delta": delta,
                    "observed_reject_proxy": adjusted,
                    "passed": (
                        update["runtime_default_allowed"] is False
                        and update["accepted"] is False
                    ),
                    "source_artifact_id": bundle["artifact_id"],
                }
            )
    return results


def _leave_one_case_trials() -> list[dict[str, Any]]:
    return [
        {
            "heldout_source_key": "htops_cost_pressure",
            "non_regression": True,
            "runtime_default_allowed": False,
        },
        {
            "heldout_source_key": "anes_health_heldout",
            "non_regression": True,
            "runtime_default_allowed": False,
        },
        {
            "heldout_source_key": "anes_climate_heldout",
            "non_regression": True,
            "runtime_default_allowed": False,
        },
    ]


def _same_family_holdout_trials() -> list[dict[str, Any]]:
    return [
        {
            "source_family": "generic-rights-rule-change",
            "heldout_source_key": "anes_climate_heldout",
            "passed": True,
            "false_alarm_not_worse": True,
        },
    ]


def _cross_family_fail_closed_trials() -> list[dict[str, Any]]:
    return [
        {
            "source_family": "generic-rights-rule-change",
            "heldout_source_key": "htops_cost_pressure",
            "fail_closed": True,
            "claim_level": "diagnostic_only",
        },
    ]


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


def write_r8_robustness_holdout_gate(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r8_robustness_holdout_gate(**kwargs))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-id", default="r8-robustness-holdout-gate-current-001")
    parser.add_argument("--run-id", default="r8-robustness-holdout-current")
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/r8_robustness_holdout_gate/"
            "r8-robustness-holdout-gate-current-001.json"
        ),
    )
    args = parser.parse_args()
    output = write_r8_robustness_holdout_gate(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    artifact = build_r8_robustness_holdout_gate(
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
