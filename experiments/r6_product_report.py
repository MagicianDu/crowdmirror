from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_case_matrix import build_r6_case_matrix
from experiments.r6_contracts import R6_CLAIM_BOUNDARY, assert_strict_json, non_empty_string, write_json_artifact
from experiments.r6_mechanism_cap_ablation import build_r6_mechanism_cap_ablation


R6_PRODUCT_REPORT_SCHEMA_VERSION = "r6-product-report-v1"


def build_r6_product_report(
    *,
    artifact_id: str,
    run_id: str,
    case_matrix: dict[str, Any] | None = None,
    mechanism_cap_ablation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    matrix = case_matrix or build_r6_case_matrix(
        artifact_id=f"{artifact_id}-case-matrix",
        run_id=run_id,
    )
    next_actions = [
        "collect_real_or_proxy_outcomes_for_each_release",
        "review_error_attribution_before_enabling_updates",
        "add_holdout_or_follow_up_cases_before_accepting_global_updates",
    ]
    source_refs = [matrix["artifact_id"]]
    claim_boundaries = [R6_CLAIM_BOUNDARY]
    risk_flags = [
        "report_does_not_claim_prediction_accuracy",
        "risk_hypothesis_requires_outcome_validation",
        "unvalidated_update_not_enabled",
    ]
    report = {
        "schema_version": R6_PRODUCT_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "report_ready",
        "source_case_matrix": {
            "artifact_id": matrix["artifact_id"],
            "case_count": matrix["case_count"],
            "case_types_covered": matrix["case_types_covered"],
        },
        "decision_support": {
            "primary_use": "pre_release_risk_review_and_post_release_learning",
            "market_claim_status": "diagnostic_workflow_ready_not_accuracy_claim",
            "recommended_use": (
                "Use risk shifts as release-review hypotheses, then collect outcome "
                "signals before accepting any global method update."
            ),
        },
        "pre_release": {
            "case_summaries": [_pre_release_case(case) for case in matrix["cases"]],
        },
        "post_release_review": {
            "case_reviews": [_post_release_case(case) for case in matrix["cases"]],
        },
        "outcome_collection_checklist": _outcome_collection_checklist(matrix["cases"]),
        "next_actions": next_actions,
        "source_refs": source_refs,
        "claim_boundaries": claim_boundaries,
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": risk_flags,
        "blocking_gaps": matrix["blocking_gaps"],
    }
    if mechanism_cap_ablation is not None:
        report["mechanism_cap_review"] = _mechanism_cap_review(mechanism_cap_ablation)
        report["product_evidence_chain"] = _product_evidence_chain(
            mechanism_cap_ablation
        )
        next_actions.append("validate_mechanism_cap_on_follow_up_or_holdout_case")
        source_refs.append(mechanism_cap_ablation["artifact_id"])
        claim_boundaries.extend(mechanism_cap_ablation["claim_boundaries"][1:])
        risk_flags.append("mechanism_cap_not_runtime_default")
        report["blocking_gaps"] = sorted(
            set(report["blocking_gaps"] + mechanism_cap_ablation["blocking_gaps"])
        )
    assert_strict_json(report)
    return report


def write_r6_product_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_report(**kwargs))


def _pre_release_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "case_type": case["case_type"],
        "change_type": case["scenario"]["change_type"],
        "static_prior": {
            "reject_rate": case["static_prior"]["reject_rate"],
            "distribution": case["static_prior"]["distribution"],
        },
        "interaction_shift": {
            "interaction_reject_rate": case["risk_shift"]["interaction_reject_rate"],
            "delta": case["risk_shift"]["delta"],
            "claim_status": "risk_hypothesis",
        },
        "top_risk_segment": case["top_risk_segment"],
        "claim_boundary": case["claim_boundary"],
    }


def _post_release_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "observed_reject_proxy": case["learning"]["observed_reject_proxy"],
        "absolute_error": case["learning"]["absolute_error"],
        "error_attribution_types": case["learning"]["error_attribution_types"],
        "update_status": case["update_status"],
        "default_runtime_enabled": case["default_runtime_enabled"],
        "claim_boundary": case["claim_boundary"],
    }


def _outcome_collection_checklist(cases: list[dict[str, Any]]) -> list[str]:
    checklist: list[str] = []
    for case in cases:
        checklist.extend(case["risk_shift"]["recommended_observations"])
    checklist.append("observed_reject_proxy_by_segment")
    return sorted(set(checklist))


def _mechanism_cap_review(mechanism_cap_ablation: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_artifact_id": mechanism_cap_ablation["artifact_id"],
        "claim_status": "diagnostic_candidate_not_runtime_default",
        "global_update_status": mechanism_cap_ablation["summary"]["global_update_status"],
        "default_runtime_enabled": mechanism_cap_ablation["recommended_update"][
            "default_runtime_enabled"
        ],
        "cap_rule": mechanism_cap_ablation["cap_rule"],
        "summary": {
            "public_proxy_count": mechanism_cap_ablation["summary"][
                "public_proxy_count"
            ],
            "cap_applied_count": mechanism_cap_ablation["summary"][
                "cap_applied_count"
            ],
            "failure_fixed_count": mechanism_cap_ablation["summary"][
                "failure_fixed_count"
            ],
            "positive_signal_preserved_count": mechanism_cap_ablation["summary"][
                "positive_signal_preserved_count"
            ],
        },
        "case_reviews": [
            _mechanism_cap_case_review(case)
            for case in mechanism_cap_ablation["case_results"]
        ],
    }


def _mechanism_cap_case_review(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_case_id": case["target_case_id"],
        "source_proxy_key": case["source_proxy_key"],
        "cap_applied": case["cap_applied"],
        "original_prior_anchored_error": case["original_prior_anchored_error"],
        "capped_prior_anchored_error": case["capped_prior_anchored_error"],
        "failure_fixed": case["failure_fixed"],
        "positive_signal_preserved": case["positive_signal_preserved"],
    }


def _product_evidence_chain(
    mechanism_cap_ablation: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "stage": "pre_release_risk_shift",
            "status": "risk_hypothesis_ready",
            "claim_status": "not_accuracy_claim",
        },
        {
            "stage": "public_proxy_failure_boundary",
            "status": "mixed_evidence_diagnosed",
            "claim_status": "public_proxy_not_field_validation",
        },
        {
            "stage": "mechanism_cap_candidate",
            "status": mechanism_cap_ablation["summary"]["global_update_status"],
            "claim_status": "diagnostic_candidate_not_runtime_default",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--include-mechanism-cap-ablation", action="store_true")
    args = parser.parse_args()

    mechanism_cap_ablation = None
    if args.include_mechanism_cap_ablation:
        mechanism_cap_ablation = build_r6_mechanism_cap_ablation(
            artifact_id=f"{args.artifact_id}-mechanism-cap-ablation",
            run_id=args.run_id,
        )
    output_path = write_r6_product_report(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        mechanism_cap_ablation=mechanism_cap_ablation,
    )
    report = json.loads(Path(output_path).read_text())
    summary = {
        "artifact_id": report["artifact_id"],
        "case_count": report["source_case_matrix"]["case_count"],
        "output": str(output_path),
        "status": report["status"],
    }
    if "mechanism_cap_review" in report:
        summary["mechanism_cap_status"] = report["mechanism_cap_review"][
            "claim_status"
        ]
    print(json.dumps(summary, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
