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
from experiments.r6_decision_value_metrics import build_r6_decision_value_metrics
from experiments.r6_false_alarm_discriminator import build_r6_false_alarm_discriminator
from experiments.r6_trend_interval_calibration_report import (
    build_r6_trend_interval_calibration_report,
)


R6_FALSE_ALARM_CONTROL_REPORT_SCHEMA_VERSION = "r6-false-alarm-control-report-v1"
R6_CLAIM_ESCALATION_GATE_REPORT_SCHEMA_VERSION = (
    "r6-claim-escalation-gate-report-v1"
)


def build_r6_false_alarm_control_report(
    *,
    artifact_id: str,
    run_id: str,
    decision_value_metrics: dict[str, Any] | None = None,
    false_alarm_discriminator: dict[str, Any] | None = None,
    trend_interval_calibration_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    decision = decision_value_metrics or build_r6_decision_value_metrics(
        artifact_id=f"{artifact_id}-decision-value",
        run_id=run_id,
    )
    discriminator = false_alarm_discriminator or build_r6_false_alarm_discriminator(
        artifact_id=f"{artifact_id}-false-alarm-discriminator",
        run_id=run_id,
        decision_value_metrics=decision,
    )
    calibration = (
        trend_interval_calibration_report
        or build_r6_trend_interval_calibration_report(
            artifact_id=f"{artifact_id}-trend-interval-calibration",
            run_id=run_id,
        )
    )
    selected_candidate = _select_control_candidate(discriminator)
    controlled_cases = _controlled_cases(
        decision["case_results"],
        selected_candidate["selected_source_keys"],
    )
    summary = _control_summary(
        baseline_summary=decision["summary"],
        case_results=decision["case_results"],
        controlled_cases=controlled_cases,
    )
    current_proxy_control_passed = (
        summary["controlled_false_alarm_rate"] <= 0.30
        and summary["missed_risk_rate"] <= 0.30
        and summary["risk_escalation_precision"] >= 0.60
        and summary["risk_escalation_recall"] >= 0.75
    )
    holdout_validated = False
    report = {
        "schema_version": R6_FALSE_ALARM_CONTROL_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "false_alarm_control_validated"
            if current_proxy_control_passed and holdout_validated
            else "false_alarm_control_guarded_proxy_passed"
            if current_proxy_control_passed
            else "false_alarm_control_diagnostic_only"
        ),
        "claim_status": "validated"
        if current_proxy_control_passed and holdout_validated
        else "guarded"
        if current_proxy_control_passed
        else "diagnostic",
        "selected_control_policy": {
            "candidate_id": selected_candidate["candidate_id"],
            "rule": selected_candidate["rule"],
            "feature_scope": selected_candidate["feature_scope"],
            "pre_outcome_safe": selected_candidate["pre_outcome_safe"],
            "holdout_validated": holdout_validated,
            "selected_source_keys": selected_candidate["selected_source_keys"],
            "rejected_false_alarm_source_keys": selected_candidate[
                "rejected_false_alarm_source_keys"
            ],
        },
        "summary": summary,
        "case_results": _case_results(
            decision["case_results"],
            controlled_cases,
            selected_candidate["rejected_false_alarm_source_keys"],
        ),
        "acceptance_gates": {
            "false_alarm_control_present": True,
            "current_proxy_control_passed": current_proxy_control_passed,
            "controlled_false_alarm_rate_passed": summary[
                "controlled_false_alarm_rate"
            ]
            <= 0.30,
            "missed_risk_rate_passed": summary["missed_risk_rate"] <= 0.30,
            "holdout_validated": holdout_validated,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [
            decision["artifact_id"],
            discriminator["artifact_id"],
            calibration["artifact_id"],
        ],
        "allowed_claims": [
            "Current public proxy evidence supports guarded false-alarm control reporting.",
        ],
        "blocked_claims": [
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "交互仿真稳定比静态先验更准",
        ],
        "blocking_gaps": [
            "needs_false_alarm_control_holdout_validation",
            "needs_field_outcome_validation",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def build_r6_claim_escalation_gate_report(
    *,
    artifact_id: str,
    run_id: str,
    false_alarm_control_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    control = false_alarm_control_report or build_r6_false_alarm_control_report(
        artifact_id=f"{artifact_id}-false-alarm-control",
        run_id=run_id,
    )
    claims = _claim_results(control)
    escalation_summary = {
        "claim_count": len(claims),
        "validated_claim_count": sum(
            1 for claim in claims if claim["claim_status"] == "validated"
        ),
        "guarded_claim_count": sum(
            1 for claim in claims if claim["claim_status"] == "guarded"
        ),
        "blocked_or_diagnostic_claim_count": sum(
            1
            for claim in claims
            if claim["claim_status"] in {"blocked", "diagnostic"}
        ),
    }
    report = {
        "schema_version": R6_CLAIM_ESCALATION_GATE_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "claim_escalation_gate_fail_closed_guarded",
        "claim_results": claims,
        "escalation_summary": escalation_summary,
        "acceptance_gates": {
            "claim_escalation_gate_present": True,
            "no_source_claim_rejected": all(
                claim["claim_status"] == "blocked"
                for claim in claims
                if not claim["source_artifact_ids"]
            ),
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [control["artifact_id"]],
        "blocked_claims": [
            "Research 已完整支撑 Product 全部核心价值",
            "runtime_default_allowed=true",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_false_alarm_control_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_false_alarm_control_report(**kwargs))


def _select_control_candidate(discriminator: dict[str, Any]) -> dict[str, Any]:
    candidates = discriminator["candidate_discriminators"]
    for candidate in candidates:
        if candidate["candidate_id"] == "target_case_family_gate":
            return candidate
    raise ValueError("target_case_family_gate missing from discriminator")


def _controlled_cases(
    case_results: list[dict[str, Any]],
    selected_source_keys: list[str],
) -> list[dict[str, Any]]:
    selected = set(selected_source_keys)
    return [case for case in case_results if case["source_key"] in selected]


def _control_summary(
    *,
    baseline_summary: dict[str, Any],
    case_results: list[dict[str, Any]],
    controlled_cases: list[dict[str, Any]],
) -> dict[str, Any]:
    true_positive_count = sum(1 for case in case_results if case["recovered_static_prior_miss"])
    true_positive_kept = sum(
        1 for case in controlled_cases if case["recovered_static_prior_miss"]
    )
    false_alarm_kept = sum(
        1 for case in controlled_cases if case["interaction_false_alarm"]
    )
    controlled_count = len(controlled_cases)
    blocked_count = len(case_results) - controlled_count
    return {
        "case_count": len(case_results),
        "baseline_false_alarm_rate": baseline_summary["false_alarm_rate"],
        "controlled_false_alarm_rate": _rate(false_alarm_kept, controlled_count),
        "missed_risk_rate": _rate(
            true_positive_count - true_positive_kept,
            true_positive_count,
        ),
        "risk_escalation_precision": _rate(true_positive_kept, controlled_count),
        "risk_escalation_recall": _rate(true_positive_kept, true_positive_count),
        "blocked_risk_count": blocked_count,
        "controlled_static_prior_miss_recovery_rate": _rate(
            true_positive_kept,
            true_positive_count,
        ),
    }


def _case_results(
    all_cases: list[dict[str, Any]],
    controlled_cases: list[dict[str, Any]],
    rejected_false_alarm_source_keys: list[str],
) -> list[dict[str, Any]]:
    selected = {case["source_key"] for case in controlled_cases}
    rejected = set(rejected_false_alarm_source_keys)
    results = []
    for case in all_cases:
        escalated = case["source_key"] in selected
        results.append(
            {
                "source_key": case["source_key"],
                "target_case_id": case["target_case_id"],
                "escalated_to_product_claim": escalated,
                "blocked_as_false_alarm_candidate": case["source_key"] in rejected,
                "recovered_static_prior_miss": case["recovered_static_prior_miss"],
                "interaction_false_alarm": case["interaction_false_alarm"],
                "blocked_reason": ""
                if escalated
                else "blocked_by_current_proxy_false_alarm_control",
            }
        )
    return results


def _claim_results(control: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "product_section": "risk_distribution",
            "claim_status": control["claim_status"],
            "claim_text": "Risk distribution can be shown as guarded current-proxy evidence.",
            "source_artifact_ids": [control["artifact_id"]],
            "blocked_reason": "",
        },
        {
            "product_section": "false_alarm_diagnosis",
            "claim_status": "diagnostic",
            "claim_text": "Blocked and diagnostic risks remain visible in Product reporting.",
            "source_artifact_ids": [control["artifact_id"]],
            "blocked_reason": "holdout_validation_missing",
        },
        {
            "product_section": "unsupported_runtime_default",
            "claim_status": "blocked",
            "claim_text": "Runtime default cannot be enabled without holdout validation.",
            "source_artifact_ids": [],
            "blocked_reason": "missing_source_and_runtime_guard_failed",
        },
    ]


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

    output_path = write_r6_false_alarm_control_report(
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
