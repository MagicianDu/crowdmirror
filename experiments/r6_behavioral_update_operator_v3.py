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
from experiments.r6_false_alarm_control_report import build_r6_false_alarm_control_report
from experiments.r6_trend_interval_risk_metrics import build_r6_trend_interval_risk_metrics


R6_BEHAVIORAL_UPDATE_OPERATOR_V3_SCHEMA_VERSION = "r6-behavioral-update-operator-v3"
R6_MECHANISM_OPERATOR_ABLATION_REPORT_SCHEMA_VERSION = (
    "r6-mechanism-operator-ablation-report-v1"
)
R6_OPERATOR_HOLDOUT_NON_REGRESSION_REPORT_SCHEMA_VERSION = (
    "r6-operator-holdout-non-regression-report-v1"
)


def build_r6_behavioral_update_operator_v3(
    *,
    artifact_id: str,
    run_id: str,
    trend_interval_risk_metrics: dict[str, Any] | None = None,
    false_alarm_control_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    metrics = trend_interval_risk_metrics or build_r6_trend_interval_risk_metrics(
        artifact_id=f"{artifact_id}-trend-interval-risk",
        run_id=run_id,
    )
    control = false_alarm_control_report or build_r6_false_alarm_control_report(
        artifact_id=f"{artifact_id}-false-alarm-control",
        run_id=run_id,
    )
    case_results = [
        _operator_case(case, control)
        for case in metrics["case_results"]
    ]
    summary = _operator_summary(case_results)
    report = {
        "schema_version": R6_BEHAVIORAL_UPDATE_OPERATOR_V3_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "operator_v3_guarded_static_fallback_ready",
        "runtime_default_allowed": False,
        "operator_definition": {
            "operator_type": "guarded_mechanism_update_with_static_prior_fallback",
            "decision_rule": (
                "Apply interaction delta only when false-alarm control escalates "
                "the case; otherwise fall back to static prior."
            ),
            "field_outcome_required_for_runtime_default": True,
        },
        "mechanisms": _mechanisms(),
        "summary": summary,
        "case_results": case_results,
        "acceptance_gates": {
            "operator_v3_structured": True,
            "operator_non_regression_rate_passed": summary[
                "operator_non_regression_rate"
            ]
            >= 0.80,
            "static_prior_guard_passed": summary["static_prior_guard_passed"],
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [metrics["artifact_id"], control["artifact_id"]],
        "allowed_claims": [
            "Operator v3 can be evaluated as a guarded proxy non-regression operator.",
        ],
        "blocked_claims": [
            "runtime_default_allowed=true",
            "field_outcome_validated=true",
            "候选更新已可自动上线",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def build_r6_mechanism_operator_ablation_report(
    *,
    artifact_id: str,
    run_id: str,
    behavioral_update_operator_v3: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    operator = behavioral_update_operator_v3 or build_r6_behavioral_update_operator_v3(
        artifact_id=f"{artifact_id}-operator-v3",
        run_id=run_id,
    )
    summary = {
        "case_count": operator["summary"]["case_count"],
        "mechanism_ablation_delta": operator["summary"]["mean_error_reduction_vs_static"],
        "guarded_interaction_case_count": operator["summary"][
            "guarded_interaction_case_count"
        ],
        "static_fallback_case_count": operator["summary"][
            "static_fallback_case_count"
        ],
    }
    report = {
        "schema_version": R6_MECHANISM_OPERATOR_ABLATION_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "mechanism_operator_ablation_guarded_proxy",
        "summary": summary,
        "case_results": [
            {
                "source_key": case["source_key"],
                "target_case_id": case["target_case_id"],
                "guard_decision": case["guard_decision"],
                "mechanism_ablation_delta": case["static_prior_error"]
                - case["operator_error"],
                "structured_risk_delta": case["structured_risk_delta"],
            }
            for case in operator["case_results"]
        ],
        "acceptance_gates": {
            "mechanism_operator_ablation_present": True,
            "mechanism_ablation_explains_risk_change": summary[
                "mechanism_ablation_delta"
            ]
            > 0,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [operator["artifact_id"]],
        "blocked_claims": [
            "runtime_default_allowed=true",
            "field_outcome_validated=true",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def build_r6_operator_holdout_non_regression_report(
    *,
    artifact_id: str,
    run_id: str,
    behavioral_update_operator_v3: dict[str, Any] | None = None,
    mechanism_operator_ablation_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    operator = behavioral_update_operator_v3 or build_r6_behavioral_update_operator_v3(
        artifact_id=f"{artifact_id}-operator-v3",
        run_id=run_id,
    )
    ablation = (
        mechanism_operator_ablation_report
        or build_r6_mechanism_operator_ablation_report(
            artifact_id=f"{artifact_id}-mechanism-ablation",
            run_id=run_id,
            behavioral_update_operator_v3=operator,
        )
    )
    summary = {
        "case_count": operator["summary"]["case_count"],
        "operator_holdout_pass_rate": operator["summary"]["operator_holdout_pass_rate"],
        "operator_non_regression_rate": operator["summary"][
            "operator_non_regression_rate"
        ],
        "static_prior_guard_passed": operator["summary"]["static_prior_guard_passed"],
        "runtime_default_allowed": False,
    }
    report = {
        "schema_version": R6_OPERATOR_HOLDOUT_NON_REGRESSION_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "operator_holdout_non_regression_proxy_passed_runtime_blocked",
        "summary": summary,
        "holdout_trials": [
            {
                "source_key": case["source_key"],
                "passed_non_regression": case["operator_error"]
                <= case["static_prior_error"],
                "static_prior_error": case["static_prior_error"],
                "operator_error": case["operator_error"],
                "runtime_default_allowed": False,
            }
            for case in operator["case_results"]
        ],
        "acceptance_gates": {
            "operator_holdout_non_regression_present": True,
            "operator_non_regression_rate_passed": summary[
                "operator_non_regression_rate"
            ]
            >= 0.80,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [operator["artifact_id"], ablation["artifact_id"]],
        "blocked_claims": [
            "runtime_default_allowed=true",
            "field_outcome_validated=true",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_behavioral_update_operator_v3(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_behavioral_update_operator_v3(**kwargs))


def _operator_case(
    case: dict[str, Any],
    control: dict[str, Any],
) -> dict[str, Any]:
    control_case = {
        item["source_key"]: item for item in control["case_results"]
    }[case["source_key"]]
    apply_interaction = control_case["escalated_to_product_claim"]
    operator_prediction = (
        case["interaction_prediction"] if apply_interaction else case["static_prior_prediction"]
    )
    static_error = round(
        abs(case["static_prior_prediction"] - case["observed_reject_proxy"]),
        3,
    )
    interaction_error = round(
        abs(case["interaction_prediction"] - case["observed_reject_proxy"]),
        3,
    )
    operator_error = round(abs(operator_prediction - case["observed_reject_proxy"]), 3)
    return {
        "source_key": case["source_key"],
        "target_case_id": case["target_case_id"],
        "guard_decision": "apply_guarded_interaction"
        if apply_interaction
        else "fallback_to_static_prior",
        "static_prior_prediction": case["static_prior_prediction"],
        "interaction_prediction": case["interaction_prediction"],
        "operator_prediction": operator_prediction,
        "observed_reject_proxy": case["observed_reject_proxy"],
        "static_prior_error": static_error,
        "interaction_error": interaction_error,
        "operator_error": operator_error,
        "structured_risk_delta": {
            "reject_delta": round(
                operator_prediction - case["static_prior_prediction"],
                3,
            ),
            "applied_mechanisms": _applied_mechanisms(case, apply_interaction),
            "static_prior_fallback_used": not apply_interaction,
        },
    }


def _operator_summary(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    case_count = len(case_results)
    pass_count = sum(
        1 for case in case_results if case["operator_error"] <= case["static_prior_error"]
    )
    return {
        "case_count": case_count,
        "operator_holdout_pass_rate": _rate(pass_count, case_count),
        "operator_non_regression_rate": _rate(pass_count, case_count),
        "mean_error_reduction_vs_static": round(
            sum(case["static_prior_error"] - case["operator_error"] for case in case_results)
            / case_count,
            3,
        ),
        "guarded_interaction_case_count": sum(
            1 for case in case_results if case["guard_decision"] == "apply_guarded_interaction"
        ),
        "static_fallback_case_count": sum(
            1 for case in case_results if case["guard_decision"] == "fallback_to_static_prior"
        ),
        "static_prior_guard_passed": pass_count == case_count,
        "runtime_default_allowed": False,
    }


def _mechanisms() -> list[dict[str, str]]:
    return [
        {
            "mechanism_id": "interest_loss_propagation",
            "description": "利益受损传播",
        },
        {
            "mechanism_id": "trust_decline_propagation",
            "description": "信任下降传播",
        },
        {
            "mechanism_id": "service_dependency_propagation",
            "description": "服务依赖传播",
        },
        {
            "mechanism_id": "rule_sensitivity_propagation",
            "description": "规则敏感传播",
        },
        {
            "mechanism_id": "peer_influence_propagation",
            "description": "同伴影响传播",
        },
        {
            "mechanism_id": "reverse_resistance_response",
            "description": "反向抵抗或逆反应",
        },
    ]


def _applied_mechanisms(case: dict[str, Any], apply_interaction: bool) -> list[str]:
    if not apply_interaction:
        return ["static_prior_fallback"]
    mechanisms = []
    for segment in case["top_abnormal_segments"]:
        mechanisms.extend(segment["mechanisms"])
    return list(dict.fromkeys(mechanisms))


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

    output_path = write_r6_behavioral_update_operator_v3(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
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
