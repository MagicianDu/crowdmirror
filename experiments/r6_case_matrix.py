from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_case_templates import R6_CASE_TEMPLATES
from experiments.r6_contracts import R6_CLAIM_BOUNDARY, assert_strict_json, non_empty_string, write_json_artifact
from experiments.r6_foundation_pipeline import build_r6_foundation_pipeline


R6_CASE_MATRIX_SCHEMA_VERSION = "r6-case-matrix-v1"


def build_r6_case_matrix(
    *,
    artifact_id: str,
    run_id: str,
    case_templates: list[dict[str, Any]] | None = None,
    public_outcome_proxy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    templates = _templates_with_public_proxy(
        case_templates if case_templates is not None else R6_CASE_TEMPLATES,
        public_outcome_proxy=public_outcome_proxy,
    )
    packages = [
        build_r6_foundation_pipeline(
            artifact_id=f"{artifact_id}-{template['case_id']}",
            run_id=run_id,
            case_template=template,
        )
        for template in templates
    ]
    cases = [_case_summary(package) for package in packages]
    public_outcome_case_count = sum(
        1 for case in cases if case["outcome_source_level"] == "public_proxy"
    )
    matrix = {
        "schema_version": R6_CASE_MATRIX_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "diagnostic_ready",
        "case_count": len(cases),
        "public_outcome_proxy_case_count": public_outcome_case_count,
        "case_types_covered": [case["case_type"] for case in cases],
        "industry_binding": "generic_multi_case_templates",
        "cases": cases,
        "acceptance_gates": {
            "minimum_case_templates_met": len(cases) >= 3,
            "all_cases_have_no_interaction_control": all(
                case["no_interaction_control_enabled"] for case in cases
            ),
            "all_cases_have_outcome_feedback": all(
                case["outcome_feedback_available"] for case in cases
            ),
            "all_updates_blocked_until_validated": all(
                not case["default_runtime_enabled"] for case in cases
            ),
        },
        "source_refs": [package["artifact_id"] for package in packages],
        "claim_boundaries": [R6_CLAIM_BOUNDARY],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "no_cross_domain_accuracy_claim",
            "case_templates_are_fixture_level_evidence",
            "unvalidated_update_not_enabled",
        ]
        + (["one_case_has_public_outcome_proxy"] if public_outcome_case_count else []),
        "blocking_gaps": [
            "needs_real_or_public_outcome_proxy_cases",
            "needs_holdout_validation_before_global_update_acceptance",
        ],
    }
    assert_strict_json(matrix)
    return matrix


def write_r6_case_matrix(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_case_matrix(**kwargs))


def _case_summary(package: dict[str, Any]) -> dict[str, Any]:
    prior = package["prior_manifest"]
    scenario = package["scenario_manifest"]
    risk = package["risk_shift_report"]
    outcome = package["outcome_manifest"]
    learning = package["learning_report"]
    registry = package["update_registry"]
    top_risk_segment = risk["top_risk_segments"][0]
    update = registry["updates"][0]
    return {
        "artifact_id": package["artifact_id"],
        "case_id": package["case_id"],
        "case_type": package["case_type"],
        "industry_binding": package["industry_binding"],
        "status": package["status"],
        "scenario": {
            "scenario_id": scenario["scenario_id"],
            "change_type": scenario["change_type"],
            "impact_dimensions": scenario["impact_dimensions"],
        },
        "static_prior": {
            "reject_rate": risk["overall_static_reject_rate"],
            "distribution": prior["aggregate_static_response_prior"],
        },
        "risk_shift": {
            "interaction_reject_rate": risk["overall_interaction_reject_rate"],
            "delta": risk["delta"],
            "recommended_observations": risk["recommended_observations"],
        },
        "top_risk_segment": top_risk_segment,
        "learning": {
            "observed_reject_proxy": outcome["metrics"]["observed_reject_proxy"],
            "absolute_error": learning["prediction_vs_outcome"]["absolute_error"],
            "error_attribution_types": [
                attribution["type"] for attribution in learning["error_attribution"]
            ],
        },
        "outcome_source_level": outcome.get("outcome_source_level", "fixture_proxy"),
        "data_quality_flags": outcome.get("data_quality_flags", []),
        "update_status": registry["overall_status"],
        "default_runtime_enabled": update["default_runtime_enabled"],
        "no_interaction_control_enabled": prior["no_interaction_control"]["enabled"],
        "outcome_feedback_available": bool(learning["error_attribution"]),
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }


def _templates_with_public_proxy(
    templates: list[dict[str, Any]],
    *,
    public_outcome_proxy: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    copied = [copy.deepcopy(template) for template in templates]
    if public_outcome_proxy is None:
        return copied
    target_case_id = public_outcome_proxy["target_case_id"]
    for template in copied:
        if template["case_id"] == target_case_id:
            template["outcome"] = {
                **template.get("outcome", {}),
                **public_outcome_proxy["outcome_override"],
            }
            template["public_outcome_proxy_artifact_id"] = public_outcome_proxy["artifact_id"]
            return copied
    raise ValueError(f"public outcome proxy target case not found: {target_case_id}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_case_matrix(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    matrix = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": matrix["artifact_id"],
                "case_count": matrix["case_count"],
                "output": str(output_path),
                "status": matrix["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
