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


R6_FOLLOWUP_HOLDOUT_VALIDATION_SCHEMA_VERSION = "r6-followup-holdout-validation-v1"


def build_r6_followup_holdout_validation(
    *,
    artifact_id: str,
    run_id: str,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    mechanism_cap = build_r6_mechanism_cap_ablation(
        artifact_id=f"{artifact_id}-mechanism-cap-ablation",
        run_id=run_id,
    )
    ablations = [
        _build_ablation_for_source(
            artifact_id=artifact_id,
            run_id=run_id,
            source_key="htops_cost_pressure",
        ),
        _build_ablation_for_source(
            artifact_id=artifact_id,
            run_id=run_id,
            source_key="anes_health_heldout",
        ),
    ]
    mechanism_cap_validation = _mechanism_cap_validation(mechanism_cap)
    outcome_feedback_validation = _outcome_feedback_validation(ablations)
    report = {
        "schema_version": R6_FOLLOWUP_HOLDOUT_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "holdout_validation_partial",
        "validation_design": {
            "mechanism_cap_source_proxy_key": "anes_health_heldout",
            "cross_proxy_holdout_proxy_key": "htops_cost_pressure",
            "validation_scope": "cross_proxy_non_regression_not_global_acceptance",
        },
        "acceptance_gates": {
            "mechanism_cap_source_failure_fixed": mechanism_cap_validation[
                "source_case"
            ]["failure_fixed"],
            "mechanism_cap_cross_proxy_non_regression": mechanism_cap_validation[
                "cross_proxy_holdout"
            ]["non_regression_passed"],
            "mechanism_cap_same_family_holdout_available": False,
            "outcome_feedback_cross_case_transfer_available": outcome_feedback_validation[
                "cross_case_transfer_available"
            ],
            "global_update_accepted": False,
        },
        "mechanism_cap_validation": mechanism_cap_validation,
        "outcome_feedback_validation": outcome_feedback_validation,
        "recommended_next_data": [
            "same_family_rights_rule_holdout_proxy",
            "third_public_or_real_proxy",
            "outcome_feedback_cross_case_transfer_protocol",
        ],
        "source_refs": [
            mechanism_cap["artifact_id"],
        ]
        + [ablation["artifact_id"] for ablation in ablations],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            "Follow-up holdout validation is partial: cross-proxy non-regression is not global acceptance.",
            "Outcome feedback remains same-case only until a cross-case transfer protocol is validated.",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "partial_holdout_not_runtime_acceptance",
            "same_family_holdout_missing",
            "outcome_feedback_same_case_only",
            "public_proxy_not_field_validation",
        ],
        "blocking_gaps": [
            "needs_same_family_rights_rule_holdout",
            "needs_outcome_feedback_cross_case_transfer_validation",
            "needs_third_public_or_real_proxy",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_followup_holdout_validation(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_followup_holdout_validation(**kwargs))


def _build_ablation_for_source(
    *,
    artifact_id: str,
    run_id: str,
    source_key: str,
) -> dict[str, Any]:
    proxy = build_r6_public_outcome_proxy(
        artifact_id=f"{artifact_id}-{source_key}-proxy",
        run_id=run_id,
        source_key=source_key,
    )
    return build_r6_ablation_report(
        artifact_id=f"{artifact_id}-{source_key}-ablation",
        run_id=run_id,
        public_outcome_proxy=proxy,
    )


def _mechanism_cap_validation(mechanism_cap: dict[str, Any]) -> dict[str, Any]:
    by_source = {
        case["source_proxy_key"]: case for case in mechanism_cap["case_results"]
    }
    source_case = by_source["anes_health_heldout"]
    holdout_case = by_source["htops_cost_pressure"]
    return {
        "upgrade_status": "partial_pass_needs_same_family_holdout",
        "accepted_for_runtime": False,
        "source_case": {
            "target_case_id": source_case["target_case_id"],
            "source_proxy_key": source_case["source_proxy_key"],
            "original_prior_anchored_error": source_case[
                "original_prior_anchored_error"
            ],
            "capped_prior_anchored_error": source_case[
                "capped_prior_anchored_error"
            ],
            "failure_fixed": source_case["failure_fixed"],
        },
        "cross_proxy_holdout": {
            "target_case_id": holdout_case["target_case_id"],
            "source_proxy_key": holdout_case["source_proxy_key"],
            "cap_applied": holdout_case["cap_applied"],
            "original_prior_anchored_error": holdout_case[
                "original_prior_anchored_error"
            ],
            "capped_prior_anchored_error": holdout_case[
                "capped_prior_anchored_error"
            ],
            "non_regression_passed": holdout_case["capped_prior_anchored_error"]
            <= holdout_case["original_prior_anchored_error"],
        },
        "missing_holdout": "same_family_rights_rule_public_or_real_proxy",
    }


def _outcome_feedback_validation(
    ablations: list[dict[str, Any]],
) -> dict[str, Any]:
    case_results = [_outcome_feedback_case_result(ablation) for ablation in ablations]
    return {
        "upgrade_status": "blocked_same_case_only",
        "accepted_for_global_update": False,
        "same_case_feedback_improved_count": sum(
            1 for case in case_results if case["same_case_feedback_improved"]
        ),
        "cross_case_transfer_available": False,
        "case_results": case_results,
    }


def _outcome_feedback_case_result(ablation: dict[str, Any]) -> dict[str, Any]:
    by_method = {result["method"]: result for result in ablation["baseline_results"]}
    prior = by_method["prior_anchored_interaction"]
    feedback = by_method["outcome_feedback_update"]
    return {
        "target_case_id": ablation["target_case_id"],
        "source_proxy_key": _source_proxy_key(ablation),
        "prior_anchored_error": prior["mean_absolute_error"],
        "outcome_feedback_error": feedback["mean_absolute_error"],
        "same_case_feedback_improved": feedback["mean_absolute_error"]
        < prior["mean_absolute_error"],
        "global_update_status": feedback["global_update_status"],
    }


def _source_proxy_key(ablation: dict[str, Any]) -> str:
    artifact_id = ablation["source_public_outcome_proxy_id"]
    if "anes_health_heldout" in artifact_id:
        return "anes_health_heldout"
    return "htops_cost_pressure"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_followup_holdout_validation(
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
