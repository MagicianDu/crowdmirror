from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_decision_value_metrics import build_r6_decision_value_metrics


R6_FALSE_ALARM_DISCRIMINATOR_SCHEMA_VERSION = "r6-false-alarm-discriminator-v1"


def build_r6_false_alarm_discriminator(
    *,
    artifact_id: str,
    run_id: str,
    decision_value_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    decision_value_metrics = decision_value_metrics or build_r6_decision_value_metrics(
        artifact_id=f"{artifact_id}-decision-value-metrics",
        run_id=run_id,
    )
    case_results = decision_value_metrics["case_results"]
    true_positives = [case for case in case_results if case["recovered_static_prior_miss"]]
    false_alarms = [case for case in case_results if case["interaction_false_alarm"]]
    in_family_positive_signal_available = bool(
        {case["target_case_id"] for case in true_positives}
        & {case["target_case_id"] for case in false_alarms}
    )
    candidates = _candidate_discriminators(
        case_results=case_results,
        true_positive_count=len(true_positives),
        false_alarm_count=len(false_alarms),
        in_family_positive_signal_available=in_family_positive_signal_available,
    )
    summary = _summary(
        case_results=case_results,
        true_positive_count=len(true_positives),
        false_alarm_count=len(false_alarms),
        candidates=candidates,
    )
    current_proxy_separation_found = summary["current_proxy_separating_candidate_count"] > 0
    pre_outcome_safe_candidate_found = summary["pre_outcome_safe_candidate_count"] > 0
    generalizable_discriminator_found = summary["accepted_candidate_count"] > 0
    ready = (
        current_proxy_separation_found
        and pre_outcome_safe_candidate_found
        and in_family_positive_signal_available
        and generalizable_discriminator_found
    )
    report = {
        "schema_version": R6_FALSE_ALARM_DISCRIMINATOR_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "false_alarm_discriminator_ready"
            if ready
            else "false_alarm_discriminator_diagnostic_only"
        ),
        "diagnostic_definition": {
            "purpose": (
                "Test whether case-level or source-level features can distinguish "
                "interaction true positives from interaction false alarms after "
                "threshold tuning fails."
            ),
            "pre_outcome_safe_rule": (
                "A runtime discriminator may use only release-time case metadata "
                "and pre-outcome simulation signals."
            ),
            "acceptance_rule": (
                "A discriminator must separate current proxies and survive "
                "in-family or external holdout validation before runtime use."
            ),
        },
        "summary": summary,
        "candidate_discriminators": candidates,
        "acceptance_gates": {
            "false_alarm_discriminator_present": True,
            "current_proxy_separation_found": current_proxy_separation_found,
            "pre_outcome_safe_candidate_found": pre_outcome_safe_candidate_found,
            "in_family_positive_signal_available": in_family_positive_signal_available,
            "generalizable_discriminator_found": generalizable_discriminator_found,
            "false_alarm_discriminator_ready": ready,
        },
        "decision": {
            "decision": (
                "accept_false_alarm_discriminator"
                if ready
                else "continue_but_do_not_accept_discriminator"
            ),
            "false_alarm_discriminator_ready": ready,
            "recommended_next_step": (
                "validate_discriminator_on_in_family_holdout"
                if ready
                else "add_in_family_positive_signal_or_external_holdout_before_runtime_gate"
            ),
        },
        "source_refs": [decision_value_metrics["artifact_id"]],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            (
                "False-alarm discriminator diagnostics can identify overfit case "
                "memory; they are not field validation or runtime acceptance."
            ),
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": _risk_flags(
            current_proxy_separation_found=current_proxy_separation_found,
            in_family_positive_signal_available=in_family_positive_signal_available,
            ready=ready,
        ),
        "blocking_gaps": [] if ready else [
            "needs_generalizable_false_alarm_discriminator",
            "needs_discriminator_holdout_validation",
            "needs_in_family_positive_signal",
            "needs_field_outcome_validation",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_false_alarm_discriminator(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(
        output,
        build_r6_false_alarm_discriminator(**kwargs),
    )


def _candidate_discriminators(
    *,
    case_results: list[dict[str, Any]],
    true_positive_count: int,
    false_alarm_count: int,
    in_family_positive_signal_available: bool,
) -> list[dict[str, Any]]:
    return [
        _candidate(
            candidate_id="target_case_family_gate",
            description=(
                "Keep interaction risk only for target case families that already "
                "have a current true-positive proxy."
            ),
            feature_scope="pre_outcome_case_metadata",
            rule="target_case_id in current_true_positive_target_case_ids",
            uses_observed_outcome=False,
            case_results=case_results,
            keep=lambda case: case["target_case_id"]
            in {
                source["target_case_id"]
                for source in case_results
                if source["recovered_static_prior_miss"]
            },
            true_positive_count=true_positive_count,
            false_alarm_count=false_alarm_count,
            generalizable_without_holdout=False,
            accepted=False,
            rejection_reason=(
                ""
                if in_family_positive_signal_available
                else "case_family_memory_without_in_family_positive_holdout"
            ),
        ),
        _candidate(
            candidate_id="source_family_gate",
            description=(
                "Keep interaction risk only for public source families that already "
                "have a current true-positive proxy."
            ),
            feature_scope="pre_outcome_source_metadata",
            rule="source_family in current_true_positive_source_families",
            uses_observed_outcome=False,
            case_results=case_results,
            keep=lambda case: _source_family(case["source_key"])
            in {
                _source_family(source["source_key"])
                for source in case_results
                if source["recovered_static_prior_miss"]
            },
            true_positive_count=true_positive_count,
            false_alarm_count=false_alarm_count,
            generalizable_without_holdout=False,
            accepted=False,
            rejection_reason="source_family_memory_without_external_holdout",
        ),
        _candidate(
            candidate_id="post_outcome_static_error_gate",
            description=(
                "Post-outcome diagnostic: keep cases where the static prior miss is "
                "large after observing the public proxy."
            ),
            feature_scope="post_outcome_diagnostic",
            rule="static_absolute_error > max_false_alarm_static_absolute_error",
            uses_observed_outcome=True,
            case_results=case_results,
            keep=lambda case: case["static_absolute_error"]
            > max(source["static_absolute_error"] for source in case_results if source["interaction_false_alarm"]),
            true_positive_count=true_positive_count,
            false_alarm_count=false_alarm_count,
            generalizable_without_holdout=False,
            accepted=False,
            rejection_reason="uses_observed_outcome_not_available_pre_release",
        ),
    ]


def _candidate(
    *,
    candidate_id: str,
    description: str,
    feature_scope: str,
    rule: str,
    uses_observed_outcome: bool,
    case_results: list[dict[str, Any]],
    keep: Callable[[dict[str, Any]], bool],
    true_positive_count: int,
    false_alarm_count: int,
    generalizable_without_holdout: bool,
    accepted: bool,
    rejection_reason: str,
) -> dict[str, Any]:
    kept_cases = [
        case
        for case in case_results
        if case["interaction_flags_new_risk"] and keep(case)
    ]
    true_positive_kept = [
        case for case in kept_cases if case["recovered_static_prior_miss"]
    ]
    false_alarm_kept = [case for case in kept_cases if case["interaction_false_alarm"]]
    false_alarm_rejected = [
        case
        for case in case_results
        if case["interaction_false_alarm"] and case not in false_alarm_kept
    ]
    summary = {
        "predicted_risk_count": len(kept_cases),
        "true_positive_kept_count": len(true_positive_kept),
        "false_alarm_kept_count": len(false_alarm_kept),
        "false_alarm_rejected_count": len(false_alarm_rejected),
        "static_prior_miss_recovery_rate": _rate(
            len(true_positive_kept),
            true_positive_count,
        ),
        "false_alarm_rate": _rate(len(false_alarm_kept), len(kept_cases)),
    }
    current_proxy_separates = (
        true_positive_count > 0
        and false_alarm_count > 0
        and summary["true_positive_kept_count"] == true_positive_count
        and summary["false_alarm_kept_count"] == 0
    )
    return {
        "candidate_id": candidate_id,
        "description": description,
        "feature_scope": feature_scope,
        "rule": rule,
        "uses_observed_outcome": uses_observed_outcome,
        "pre_outcome_safe": not uses_observed_outcome,
        "selected_source_keys": [case["source_key"] for case in kept_cases],
        "rejected_false_alarm_source_keys": [
            case["source_key"] for case in false_alarm_rejected
        ],
        "summary": summary,
        "current_proxy_separates": current_proxy_separates,
        "generalizable_without_holdout": generalizable_without_holdout,
        "accepted": accepted,
        "rejection_reason": rejection_reason,
    }


def _summary(
    *,
    case_results: list[dict[str, Any]],
    true_positive_count: int,
    false_alarm_count: int,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "case_count": len(case_results),
        "true_positive_count": true_positive_count,
        "false_alarm_count": false_alarm_count,
        "candidate_count": len(candidates),
        "current_proxy_separating_candidate_count": sum(
            1 for candidate in candidates if candidate["current_proxy_separates"]
        ),
        "pre_outcome_safe_candidate_count": sum(
            1 for candidate in candidates if candidate["pre_outcome_safe"]
        ),
        "post_outcome_diagnostic_candidate_count": sum(
            1 for candidate in candidates if candidate["uses_observed_outcome"]
        ),
        "generalizable_candidate_count": sum(
            1 for candidate in candidates if candidate["generalizable_without_holdout"]
        ),
        "accepted_candidate_count": sum(1 for candidate in candidates if candidate["accepted"]),
    }


def _source_family(source_key: str) -> str:
    if source_key.startswith("anes_"):
        return "anes_public_opinion"
    if source_key.startswith("htops_"):
        return "htops_household_pulse"
    return source_key.split("_", maxsplit=1)[0]


def _risk_flags(
    *,
    current_proxy_separation_found: bool,
    in_family_positive_signal_available: bool,
    ready: bool,
) -> list[str]:
    flags = ["false_alarm_discriminator_not_field_validation"]
    if current_proxy_separation_found:
        flags.append("case_family_gate_overfit_risk")
    if not in_family_positive_signal_available:
        flags.append("no_in_family_positive_signal")
    if not ready:
        flags.append("false_alarm_discriminator_not_runtime_ready")
    return flags


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_false_alarm_discriminator(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "false_alarm_discriminator_ready": report["acceptance_gates"][
                    "false_alarm_discriminator_ready"
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
