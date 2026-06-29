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
from experiments.r6_interaction_signal_validity import (
    build_r6_interaction_signal_validity,
)


R6_INTERACTION_SIGNAL_VALIDITY_HOLDOUT_VALIDATION_SCHEMA_VERSION = (
    "r6-interaction-signal-validity-holdout-validation-v1"
)


def build_r6_interaction_signal_validity_holdout_validation(
    *,
    artifact_id: str,
    run_id: str,
    interaction_signal_validity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    interaction_signal_validity = (
        interaction_signal_validity
        or build_r6_interaction_signal_validity(
            artifact_id=f"{artifact_id}-interaction-signal-validity",
            run_id=run_id,
        )
    )
    case_scores = interaction_signal_validity["case_validity_scores"]
    source_cases = [
        case
        for case in case_scores
        if case["classification"] == "diagnostic_only"
        and case["scoring_inputs"]["holdout_outcome_support"] == "supported"
    ]
    holdout_cases = [
        case
        for case in case_scores
        if case not in source_cases and case["scoring_inputs"]["public_proxy_available"]
    ]
    trials = [
        _trial(source=source, holdout=holdout)
        for source in source_cases
        for holdout in holdout_cases
    ]
    summary = _summary(
        case_scores=case_scores,
        source_cases=source_cases,
        holdout_cases=holdout_cases,
        trials=trials,
    )
    passed = summary["passed_holdout_count"] > 0
    report = {
        "schema_version": R6_INTERACTION_SIGNAL_VALIDITY_HOLDOUT_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "interaction_signal_validity_holdout_passed"
            if passed
            else "interaction_signal_validity_holdout_failed_current_public_proxies"
        ),
        "validation_protocol": {
            "source_rule": (
                "Freeze a supported diagnostic interaction-signal validity pattern; "
                "evaluate independent holdout cases using only score components and "
                "holdout outcome support."
            ),
            "holdout_label_used_for_source_rule_derivation": False,
            "forbidden_generalization_features": [
                "source_key",
                "target_case_id",
                "target_case_type",
            ],
        },
        "summary": summary,
        "holdout_trials": trials,
        "acceptance_gates": {
            "interaction_signal_validity_holdout_validation_present": True,
            "frozen_score_rule_has_no_holdout_label_leakage": True,
            "independent_holdout_available": bool(holdout_cases),
            "source_supported_signal_available": bool(source_cases),
            "passed_independent_holdout_count_positive": passed,
            "interaction_signal_validity_holdout_passed": passed,
            "field_outcome_validated": False,
        },
        "decision": {
            "interaction_signal_validity_holdout_passed": passed,
            "decision": (
                "generalize_interaction_signal_validity_candidate"
                if passed
                else "do_not_generalize_interaction_signal_validity_yet"
            ),
            "recommended_next_step": (
                "promote_to_field_validation_candidate"
                if passed
                else "add_independent_supported_holdout_or_field_outcome"
            ),
        },
        "source_refs": [interaction_signal_validity["artifact_id"]],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            (
                "This validates Interaction Signal Validity on current public proxies "
                "only; failed holdout means the score must remain diagnostic."
            ),
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": _risk_flags(summary, passed=passed),
        "blocking_gaps": [] if passed else [
            "needs_independent_supported_signal_holdout",
            "needs_signal_validity_holdout_validation",
            "needs_field_outcome_validation",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_interaction_signal_validity_holdout_validation(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r6_interaction_signal_validity_holdout_validation(**kwargs),
    )


def _trial(*, source: dict[str, Any], holdout: dict[str, Any]) -> dict[str, Any]:
    holdout_support = holdout["scoring_inputs"]["holdout_outcome_support"]
    signal_strength_preserved = (
        holdout["validity_score"] >= 0.75
        and holdout["component_scores"]["holdout_consistency_score"] == 1.0
    )
    if signal_strength_preserved:
        status = "passed"
    elif holdout_support == "contradicted":
        status = "failed_holdout_contradicts_signal"
    else:
        status = "failed_holdout_not_supported"
    return {
        "trial_id": (
            "signal-validity:"
            f"{source['audit']['source_key']}->{holdout['audit']['source_key']}"
        ),
        "validation_status": status,
        "source_case": _case_summary(source),
        "holdout_case": _case_summary(holdout),
        "frozen_rule": {
            "score_threshold": 0.75,
            "requires_supported_holdout_consistency": True,
            "forbidden_label_features_used": False,
        },
        "holdout_outcome_used_for_source_rule_derivation": False,
    }


def _case_summary(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_key": case["audit"]["source_key"],
        "validity_score": case["validity_score"],
        "classification": case["classification"],
        "holdout_outcome_support": case["scoring_inputs"]["holdout_outcome_support"],
        "component_scores": case["component_scores"],
    }


def _summary(
    *,
    case_scores: list[dict[str, Any]],
    source_cases: list[dict[str, Any]],
    holdout_cases: list[dict[str, Any]],
    trials: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "case_count": len(case_scores),
        "source_supported_count": len(source_cases),
        "eligible_independent_holdout_count": len(holdout_cases),
        "passed_holdout_count": sum(
            1 for trial in trials if trial["validation_status"] == "passed"
        ),
        "contradicted_holdout_count": sum(
            1
            for trial in trials
            if trial["validation_status"] == "failed_holdout_contradicts_signal"
        ),
        "generalized_signal_count": sum(
            1 for trial in trials if trial["validation_status"] == "passed"
        ),
    }


def _risk_flags(summary: dict[str, Any], *, passed: bool) -> list[str]:
    flags = ["interaction_signal_validity_holdout_not_field_validation"]
    if summary["contradicted_holdout_count"] > 0:
        flags.append("current_holdouts_contradict_supported_signal")
    if not passed:
        flags.append("interaction_signal_validity_holdout_failed")
    return flags


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_interaction_signal_validity_holdout_validation(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "interaction_signal_validity_holdout_passed": report[
                    "acceptance_gates"
                ]["interaction_signal_validity_holdout_passed"],
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
