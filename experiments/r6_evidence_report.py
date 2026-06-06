from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_ablation_report import build_r6_ablation_report
from experiments.r6_case_matrix import build_r6_case_matrix
from experiments.r6_contracts import R6_CLAIM_BOUNDARY, assert_strict_json, non_empty_string, write_json_artifact
from experiments.r6_mechanism_cap_ablation import build_r6_mechanism_cap_ablation
from experiments.r6_product_report import build_r6_product_report
from experiments.r6_public_outcome_proxy import build_r6_public_outcome_proxy


R6_EVIDENCE_REPORT_SCHEMA_VERSION = "r6-evidence-report-v1"


def build_r6_evidence_report(
    *,
    artifact_id: str,
    run_id: str,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    public_proxy = build_r6_public_outcome_proxy(
        artifact_id=f"{artifact_id}-public-outcome-proxy",
        run_id=run_id,
    )
    second_public_proxy = build_r6_public_outcome_proxy(
        artifact_id=f"{artifact_id}-public-outcome-proxy-anes-health",
        run_id=run_id,
        source_key="anes_health_heldout",
    )
    public_proxies = [public_proxy, second_public_proxy]
    case_matrix = build_r6_case_matrix(
        artifact_id=f"{artifact_id}-case-matrix",
        run_id=run_id,
        public_outcome_proxies=public_proxies,
    )
    mechanism_cap_ablation = build_r6_mechanism_cap_ablation(
        artifact_id=f"{artifact_id}-mechanism-cap-ablation",
        run_id=run_id,
    )
    product_report = build_r6_product_report(
        artifact_id=f"{artifact_id}-product-report",
        run_id=run_id,
        case_matrix=case_matrix,
        mechanism_cap_ablation=mechanism_cap_ablation,
    )
    ablation = build_r6_ablation_report(
        artifact_id=f"{artifact_id}-ablation",
        run_id=run_id,
        public_outcome_proxy=public_proxy,
    )
    second_ablation = build_r6_ablation_report(
        artifact_id=f"{artifact_id}-ablation-anes-health",
        run_id=run_id,
        public_outcome_proxy=second_public_proxy,
    )
    by_method = {result["method"]: result for result in ablation["baseline_results"]}
    prior_anchored_beats_no_interaction = (
        by_method["prior_anchored_interaction"]["mean_absolute_error"]
        < by_method["no_interaction_prior"]["mean_absolute_error"]
    )
    report = {
        "schema_version": R6_EVIDENCE_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "public_proxy_evidence_ready",
        "evidence_answer": {
            "current_decision": "continue_r6_with_constraints",
            "stoploss_triggered": False,
            "reason": (
                "Two public proxy cases are connected. One supports the prior-anchored "
                "interaction signal, one exposes a non-improvement boundary, and global "
                "updates remain blocked."
            ),
        },
        "public_outcome_proxies": [
            _public_proxy_summary(proxy) for proxy in public_proxies
        ],
        "public_outcome_proxy": {
            "artifact_id": public_proxy["artifact_id"],
            "target_case_id": public_proxy["target_case_id"],
            "usable_row_count": public_proxy["public_source"]["usable_row_count"],
            "source_url": public_proxy["public_source"]["source_url"],
            "observed_reject_proxy": public_proxy["metrics"]["observed_reject_proxy"],
        },
        "case_matrix_summary": {
            "artifact_id": case_matrix["artifact_id"],
            "case_count": case_matrix["case_count"],
            "public_outcome_proxy_case_count": case_matrix["public_outcome_proxy_case_count"],
        },
        "ablation_summary": {
            "artifact_id": ablation["artifact_id"],
            "prior_anchored_beats_no_interaction": prior_anchored_beats_no_interaction,
            "no_interaction_error": by_method["no_interaction_prior"]["mean_absolute_error"],
            "prior_anchored_error": by_method["prior_anchored_interaction"][
                "mean_absolute_error"
            ],
            "outcome_feedback_update_error": by_method["outcome_feedback_update"][
                "mean_absolute_error"
            ],
            "outcome_feedback_global_status": by_method["outcome_feedback_update"][
                "global_update_status"
            ],
            "current_best_non_feedback_method": ablation["current_best_non_feedback_method"],
        },
        "ablation_reports": [
            _ablation_case_summary(ablation),
            _ablation_case_summary(second_ablation),
        ],
        "multi_proxy_summary": _multi_proxy_summary([ablation, second_ablation]),
        "product_report_summary": {
            "artifact_id": product_report["artifact_id"],
            "status": product_report["status"],
            "market_claim_status": product_report["decision_support"]["market_claim_status"],
            "mechanism_cap_status": product_report["mechanism_cap_review"][
                "claim_status"
            ],
        },
        "acceptance_gates": {
            "public_outcome_proxy_connected": True,
            "second_public_outcome_proxy_connected": True,
            "ablation_baselines_present": _has_required_ablation_methods(ablation),
            "deterministic_replay_passed": (
                ablation["deterministic_replay"]["passed"]
                and second_ablation["deterministic_replay"]["passed"]
            ),
            "product_report_ingests_mechanism_cap": True,
            "global_update_accepted": False,
        },
        "remaining_gaps": [
            "needs_more_public_or_real_outcomes",
            "needs_holdout_case_for_feedback_update_acceptance",
            "needs_holdout_case_for_mechanism_cap_acceptance",
        ],
        "source_refs": [
            public_proxy["artifact_id"],
            second_public_proxy["artifact_id"],
            case_matrix["artifact_id"],
            product_report["artifact_id"],
            mechanism_cap_ablation["artifact_id"],
            ablation["artifact_id"],
            second_ablation["artifact_id"],
        ],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            "This is public proxy evidence only; it is not field validation.",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "public_proxy_not_field_validation",
            "same_case_feedback_not_global_acceptance",
            "not_cross_domain_accuracy_evidence",
            "mixed_public_proxy_evidence",
            "mechanism_cap_not_runtime_default",
        ],
        "blocking_gaps": [
            "global_update_acceptance_blocked",
            "cross_case_validation_missing",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_evidence_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_evidence_report(**kwargs))


def _public_proxy_summary(proxy: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": proxy["artifact_id"],
        "source_key": proxy["source_key"],
        "target_case_id": proxy["target_case_id"],
        "source_artifact_id": proxy["public_source"]["source_artifact_id"],
        "source_name": proxy["public_source"]["source_name"],
        "usable_row_count": proxy["public_source"]["usable_row_count"],
        "observed_reject_proxy": proxy["metrics"]["observed_reject_proxy"],
        "mapping_target_response_option": proxy["mapping_review"]["target_response_option"],
    }


def _ablation_case_summary(ablation: dict[str, Any]) -> dict[str, Any]:
    by_method = {result["method"]: result for result in ablation["baseline_results"]}
    prior_anchored_beats_no_interaction = (
        by_method["prior_anchored_interaction"]["mean_absolute_error"]
        < by_method["no_interaction_prior"]["mean_absolute_error"]
    )
    return {
        "artifact_id": ablation["artifact_id"],
        "target_case_id": ablation["target_case_id"],
        "public_proxy_observed_reject": ablation["public_proxy"]["observed_reject_proxy"],
        "no_interaction_error": by_method["no_interaction_prior"]["mean_absolute_error"],
        "prior_anchored_error": by_method["prior_anchored_interaction"][
            "mean_absolute_error"
        ],
        "prior_anchored_beats_no_interaction": prior_anchored_beats_no_interaction,
        "outcome_feedback_global_status": by_method["outcome_feedback_update"][
            "global_update_status"
        ],
    }


def _multi_proxy_summary(ablation_reports: list[dict[str, Any]]) -> dict[str, Any]:
    case_summaries = [_ablation_case_summary(ablation) for ablation in ablation_reports]
    positive_count = sum(
        1 for summary in case_summaries if summary["prior_anchored_beats_no_interaction"]
    )
    regression_count = len(case_summaries) - positive_count
    return {
        "public_proxy_count": len(case_summaries),
        "public_proxy_source_count": len(
            {summary["target_case_id"] for summary in case_summaries}
        ),
        "prior_anchored_positive_count": positive_count,
        "prior_anchored_regression_count": regression_count,
        "conclusion": (
            "mixed_public_proxy_evidence"
            if regression_count
            else "positive_public_proxy_evidence"
        ),
    }


def _has_required_ablation_methods(ablation: dict[str, Any]) -> bool:
    methods = {result["method"] for result in ablation["baseline_results"]}
    required = {
        "no_interaction_prior",
        "random_noise_baseline",
        "uncalibrated_interaction",
        "prior_anchored_interaction",
        "outcome_feedback_update",
    }
    return required <= methods


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_evidence_report(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "decision": report["evidence_answer"]["current_decision"],
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
