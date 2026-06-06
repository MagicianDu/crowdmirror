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
from experiments.r6_public_outcome_proxy import build_r6_public_outcome_proxy


R6_MECHANISM_CAP_ABLATION_SCHEMA_VERSION = "r6-mechanism-cap-ablation-v1"
STATIC_PRIOR_ERROR_CAP_THRESHOLD = 0.03
MAX_RIGHTS_RULE_REJECT_DELTA = 0.02


def build_r6_mechanism_cap_ablation(*, artifact_id: str, run_id: str) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    cap_rule = {
        "condition_static_prior_abs_error_lte": STATIC_PRIOR_ERROR_CAP_THRESHOLD,
        "max_aggregate_reject_delta": MAX_RIGHTS_RULE_REJECT_DELTA,
        "scope": "rights_or_rule_change_rejection_amplification",
    }
    case_results = [
        _build_case_result(
            artifact_id=artifact_id,
            run_id=run_id,
            source_key="htops_cost_pressure",
            cap_rule=cap_rule,
        ),
        _build_case_result(
            artifact_id=artifact_id,
            run_id=run_id,
            source_key="anes_health_heldout",
            cap_rule=cap_rule,
        ),
    ]
    report = {
        "schema_version": R6_MECHANISM_CAP_ABLATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "diagnostic_cap_candidate_ready",
        "cap_rule": cap_rule,
        "summary": {
            "public_proxy_count": len(case_results),
            "cap_applied_count": sum(1 for case in case_results if case["cap_applied"]),
            "failure_fixed_count": sum(1 for case in case_results if case["failure_fixed"]),
            "positive_signal_preserved_count": sum(
                1 for case in case_results if case["positive_signal_preserved"]
            ),
            "global_update_status": "blocked_until_follow_up_holdout",
        },
        "case_results": case_results,
        "recommended_update": {
            "status": "diagnostic_only",
            "default_runtime_enabled": False,
            "target_change": (
                "cap rights/rule rejection amplification only when static prior is already close"
            ),
            "acceptance_requirement": (
                "requires follow-up or cross-proxy holdout without HTOPS regression"
            ),
        },
        "source_refs": [case["source_public_outcome_proxy_id"] for case in case_results]
        + [case["source_ablation_report_id"] for case in case_results],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            "Mechanism cap ablation is diagnostic only and not a global runtime update.",
            "The cap is derived from public proxy behavior and requires holdout validation.",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "same_case_cap_not_global_update",
            "public_proxy_not_field_validation",
            "needs_follow_up_holdout",
        ],
        "blocking_gaps": [
            "needs_follow_up_case_for_update_acceptance",
            "needs_third_public_or_real_proxy",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_mechanism_cap_ablation(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_mechanism_cap_ablation(**kwargs))


def _build_case_result(
    *,
    artifact_id: str,
    run_id: str,
    source_key: str,
    cap_rule: dict[str, Any],
) -> dict[str, Any]:
    proxy = build_r6_public_outcome_proxy(
        artifact_id=f"{artifact_id}-{source_key}-proxy",
        run_id=run_id,
        source_key=source_key,
    )
    ablation = build_r6_ablation_report(
        artifact_id=f"{artifact_id}-{source_key}-ablation",
        run_id=run_id,
        public_outcome_proxy=proxy,
    )
    by_method = {result["method"]: result for result in ablation["baseline_results"]}
    no_interaction = by_method["no_interaction_prior"]
    prior_anchored = by_method["prior_anchored_interaction"]
    observed = ablation["public_proxy"]["observed_reject_proxy"]
    static_prediction = no_interaction["mean_prediction"]
    prior_prediction = prior_anchored["mean_prediction"]
    static_error = no_interaction["mean_absolute_error"]
    prior_error = prior_anchored["mean_absolute_error"]
    original_delta = round(prior_prediction - static_prediction, 3)
    cap_applied = _should_apply_cap(
        target_case_id=proxy["target_case_id"],
        static_error=static_error,
        original_reject_delta=original_delta,
        cap_rule=cap_rule,
    )
    if cap_applied:
        capped_delta = cap_rule["max_aggregate_reject_delta"]
        capped_prediction = round(static_prediction + capped_delta, 2)
    else:
        capped_delta = original_delta
        capped_prediction = prior_prediction
    capped_error = round(abs(capped_prediction - observed), 3)
    failure_fixed = cap_applied and prior_error > static_error and capped_error <= static_error
    positive_signal_preserved = (
        not cap_applied
        and prior_error < static_error
        and capped_error == prior_error
    )
    return {
        "source_proxy_key": source_key,
        "target_case_id": proxy["target_case_id"],
        "target_case_type": proxy["target_case_type"],
        "source_public_outcome_proxy_id": proxy["artifact_id"],
        "source_ablation_report_id": ablation["artifact_id"],
        "observed_reject_proxy": observed,
        "static_prior_prediction": static_prediction,
        "static_prior_error": static_error,
        "original_prior_anchored_prediction": prior_prediction,
        "original_prior_anchored_error": prior_error,
        "original_reject_delta": original_delta,
        "cap_applied": cap_applied,
        "capped_prediction": capped_prediction,
        "capped_reject_delta": round(capped_delta, 3),
        "capped_prior_anchored_error": capped_error,
        "failure_fixed": failure_fixed,
        "positive_signal_preserved": positive_signal_preserved,
    }


def _should_apply_cap(
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_mechanism_cap_ablation(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "failure_fixed_count": report["summary"]["failure_fixed_count"],
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
