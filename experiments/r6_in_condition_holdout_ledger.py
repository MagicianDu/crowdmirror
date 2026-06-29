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


R6_IN_CONDITION_HOLDOUT_LEDGER_SCHEMA_VERSION = "r6-in-condition-holdout-ledger-v1"


def build_r6_in_condition_holdout_ledger(
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
    cap_rule = mechanism_cap["cap_rule"]
    entries = [
        _ledger_entry(
            artifact_id=artifact_id,
            run_id=run_id,
            source_key="anes_health_heldout",
            role="source_case",
            cap_rule=cap_rule,
        ),
        _ledger_entry(
            artifact_id=artifact_id,
            run_id=run_id,
            source_key="anes_climate_heldout",
            role="same_family_holdout",
            cap_rule=cap_rule,
        ),
        _ledger_entry(
            artifact_id=artifact_id,
            run_id=run_id,
            source_key="htops_cost_pressure",
            role="cross_proxy_holdout",
            cap_rule=cap_rule,
        ),
    ]
    in_condition_entries = [
        entry for entry in entries if entry["ledger_status"] == "in_condition_holdout"
    ]
    report = {
        "schema_version": R6_IN_CONDITION_HOLDOUT_LEDGER_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "ledger_ready_no_in_condition_holdout_found",
        "selection_target": {
            "candidate_update": "rights_rule_reject_delta_cap_v1",
            "purpose": "find an independent holdout that exercises the cap trigger condition",
            "cap_rule": cap_rule,
        },
        "selection_criteria": [
            {
                "criterion": "same_family_rights_rule_case",
                "required": True,
                "reason": "mechanism cap is scoped to rights/rule rejection amplification",
            },
            {
                "criterion": "independent_holdout_not_source_case",
                "required": True,
                "reason": "source-case repair cannot validate transfer",
            },
            {
                "criterion": "static_prior_error_lte_threshold",
                "required": True,
                "threshold": cap_rule["condition_static_prior_abs_error_lte"],
                "reason": "cap only applies when the static prior is already close",
            },
            {
                "criterion": "original_reject_delta_gt_cap",
                "required": True,
                "threshold": cap_rule["max_aggregate_reject_delta"],
                "reason": "holdout must actually exercise the capped amplification",
            },
            {
                "criterion": "public_or_field_outcome_mapping_auditable",
                "required": True,
                "reason": "proxy mapping must be inspectable before it can support a gate",
            },
        ],
        "ledger_entries": entries,
        "summary": {
            "candidate_count": len(entries),
            "in_condition_holdout_count": len(in_condition_entries),
            "same_family_out_of_condition_count": sum(
                1
                for entry in entries
                if entry["ledger_status"] == "out_of_condition_holdout"
            ),
            "source_case_not_holdout_count": sum(
                1
                for entry in entries
                if entry["ledger_status"] == "source_case_not_holdout"
            ),
            "out_of_family_holdout_count": sum(
                1 for entry in entries if entry["ledger_status"] == "out_of_family_holdout"
            ),
            "global_update_data_gate_passed": bool(in_condition_entries),
        },
        "next_search_profile": {
            "case_type": "rights_rule_change",
            "impact_dimension": "rights_reduction_or_rule_constraint",
            "measurement_level": "public_proxy_or_field_outcome",
            "required_static_prior_error_lte": cap_rule[
                "condition_static_prior_abs_error_lte"
            ],
            "required_original_reject_delta_gt": cap_rule[
                "max_aggregate_reject_delta"
            ],
            "examples_of_useful_sources": [
                "independent public survey split with rights/rule reject response",
                "field rollout outcome with segment-level reject proxy",
                "customer policy-change cohort with no-interaction prior reconstruction",
            ],
        },
        "source_refs": [mechanism_cap["artifact_id"]]
        + [entry["source_artifact_id"] for entry in entries],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            "Holdout ledger is a data-selection gate, not evidence that the method is accurate.",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "no_in_condition_holdout_found",
            "public_proxy_not_field_validation",
            "global_update_blocked_by_data_gate",
        ],
        "blocking_gaps": [
            "needs_in_condition_same_family_rights_rule_holdout",
            "needs_independent_field_or_public_proxy_with_cap_condition",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_in_condition_holdout_ledger(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_in_condition_holdout_ledger(**kwargs))


def _ledger_entry(
    *,
    artifact_id: str,
    run_id: str,
    source_key: str,
    role: str,
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
    static = by_method["no_interaction_prior"]
    prior = by_method["prior_anchored_interaction"]
    original_reject_delta = round(
        prior["mean_prediction"] - static["mean_prediction"],
        3,
    )
    checks = {
        "same_family_rights_rule_case": proxy["target_case_id"]
        == "generic-rights-rule-change",
        "independent_holdout_not_source_case": role != "source_case",
        "static_prior_error_lte_threshold": static["mean_absolute_error"]
        <= cap_rule["condition_static_prior_abs_error_lte"],
        "original_reject_delta_gt_cap": original_reject_delta
        > cap_rule["max_aggregate_reject_delta"],
        "public_or_field_outcome_mapping_auditable": bool(proxy["mapping_review"]),
    }
    ledger_status = _ledger_status(role=role, checks=checks)
    return {
        "candidate_id": f"{source_key}:{role}",
        "source_key": source_key,
        "role": role,
        "ledger_status": ledger_status,
        "source_artifact_id": proxy["artifact_id"],
        "public_source": {
            "source_name": proxy["public_source"]["source_name"],
            "usable_row_count": proxy["public_source"]["usable_row_count"],
            "split_role": proxy["public_source"]["split_role"],
        },
        "case_family_axes": {
            "case_type": proxy["target_case_type"],
            "target_case_id": proxy["target_case_id"],
            "proxy_family": proxy["mapping_review"]["proxy_family"],
            "measurement_level": "public_proxy",
            "population_axis": "public_use_segment_schema",
        },
        "metrics": {
            "observed_reject_proxy": proxy["metrics"]["observed_reject_proxy"],
            "static_prior_error": static["mean_absolute_error"],
            "prior_anchored_error": prior["mean_absolute_error"],
            "original_reject_delta": original_reject_delta,
        },
        "condition_checks": checks,
        "why_not_sufficient": _why_not_sufficient(ledger_status),
    }


def _ledger_status(*, role: str, checks: dict[str, bool]) -> str:
    if role == "source_case":
        return "source_case_not_holdout"
    if not checks["same_family_rights_rule_case"]:
        return "out_of_family_holdout"
    if not (
        checks["static_prior_error_lte_threshold"]
        and checks["original_reject_delta_gt_cap"]
    ):
        return "out_of_condition_holdout"
    if not checks["public_or_field_outcome_mapping_auditable"]:
        return "invalid_proxy"
    return "in_condition_holdout"


def _why_not_sufficient(ledger_status: str) -> list[str]:
    reasons = {
        "source_case_not_holdout": [
            "used_to_derive_candidate_update",
            "cannot_validate_transfer",
        ],
        "out_of_family_holdout": [
            "case_family_does_not_match_cap_scope",
            "usable_only_for_cross_proxy_non_regression",
        ],
        "out_of_condition_holdout": [
            "same_family_available_but_cap_trigger_not_exercised",
            "usable_only_as_condition_not_covered_evidence",
        ],
        "invalid_proxy": [
            "proxy_mapping_not_auditable",
        ],
        "in_condition_holdout": [],
    }
    return reasons[ledger_status]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_in_condition_holdout_ledger(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "in_condition_holdout_count": report["summary"][
                    "in_condition_holdout_count"
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
