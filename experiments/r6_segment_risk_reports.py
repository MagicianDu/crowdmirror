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


R6_SEGMENT_RISK_RANKING_REPORT_SCHEMA_VERSION = "r6-segment-risk-ranking-report-v1"
R6_ABNORMAL_SEGMENT_VALIDATION_REPORT_SCHEMA_VERSION = (
    "r6-abnormal-segment-validation-report-v1"
)


def build_r6_segment_risk_ranking_report(
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
    case_results = [_case_segment_ranking(case, control) for case in metrics["case_results"]]
    label_summary = _segment_label_summary(case_results)
    summary = {
        "case_count": len(case_results),
        "risk_ranking_quality": control["summary"]["risk_escalation_precision"],
        "top_k_segment_precision": label_summary["segment_precision"],
        "segment_recall": label_summary["segment_recall"],
        "segment_precision": label_summary["segment_precision"],
        "static_prior_miss_recovery_rate": control["summary"][
            "controlled_static_prior_miss_recovery_rate"
        ],
        "interaction_only_risk_discovery_count": sum(
            1
            for case in control["case_results"]
            if case["escalated_to_product_claim"]
            and case["recovered_static_prior_miss"]
        ),
    }
    report = {
        "schema_version": R6_SEGMENT_RISK_RANKING_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "segment_risk_ranking_supported_guarded_proxy",
        "claim_status": "guarded",
        "summary": summary,
        "case_results": case_results,
        "acceptance_gates": {
            "segment_risk_ranking_present": True,
            "risk_ranking_quality_passed": summary["risk_ranking_quality"] >= 0.60,
            "top_k_segment_precision_passed": summary["top_k_segment_precision"] >= 0.60,
            "segment_recall_passed": summary["segment_recall"] >= 0.75,
            "all_segments_source_backed": all(
                segment["source_artifact_ids"]
                for case in case_results
                for segment in case["segments"]
            ),
            "field_segment_labels_available": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [metrics["artifact_id"], control["artifact_id"]],
        "allowed_claims": [
            "Product can show guarded segment risk ranking after current-proxy false-alarm control.",
        ],
        "blocked_claims": [
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "异常群体已经完成 field validation",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def build_r6_abnormal_segment_validation_report(
    *,
    artifact_id: str,
    run_id: str,
    segment_risk_ranking_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    ranking = segment_risk_ranking_report or build_r6_segment_risk_ranking_report(
        artifact_id=f"{artifact_id}-segment-risk-ranking",
        run_id=run_id,
    )
    case_results = []
    total_predicted = 0
    total_labeled = 0
    total_true_positive = 0
    for case in ranking["case_results"]:
        predicted = [segment["segment_id"] for segment in case["segments"]]
        labels = [
            segment["segment_id"]
            for segment in case["segments"]
            if segment["proxy_audit_label_positive"]
        ]
        true_positive = sorted(set(predicted) & set(labels))
        total_predicted += len(predicted)
        total_labeled += len(labels)
        total_true_positive += len(true_positive)
        case_results.append(
            {
                "source_key": case["source_key"],
                "predicted_segment_ids": predicted,
                "audit_label_segment_ids": labels,
                "true_positive_segment_ids": true_positive,
            }
        )
    summary = {
        "case_count": len(case_results),
        "segment_precision": _rate(total_true_positive, total_predicted),
        "segment_recall": _rate(total_true_positive, total_labeled),
        "labeled_case_count": len(case_results),
    }
    report = {
        "schema_version": R6_ABNORMAL_SEGMENT_VALIDATION_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "abnormal_segment_validation_guarded_proxy",
        "claim_status": "guarded",
        "label_source_type": "proxy_aligned_audit_fixture_not_field_outcome",
        "summary": summary,
        "case_results": case_results,
        "acceptance_gates": {
            "abnormal_segment_validation_present": True,
            "segment_metrics_computable": total_predicted > 0 and total_labeled > 0,
            "segment_precision_passed": summary["segment_precision"] >= 0.60,
            "segment_recall_passed": summary["segment_recall"] >= 0.75,
            "field_segment_labels_available": False,
            "product_claim_upgrade_allowed": False,
        },
        "source_refs": [ranking["artifact_id"]],
        "allowed_claims": [
            "Product can show abnormal segment findings as guarded proxy/audit evidence.",
        ],
        "blocked_claims": [
            "field_outcome_validated=true",
            "异常群体 field labels 已完成",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_segment_risk_ranking_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_segment_risk_ranking_report(**kwargs))


def _case_segment_ranking(
    case: dict[str, Any],
    control: dict[str, Any],
) -> dict[str, Any]:
    control_by_source = {
        item["source_key"]: item for item in control["case_results"]
    }
    control_case = control_by_source[case["source_key"]]
    segments = []
    for index, segment in enumerate(case["top_abnormal_segments"]):
        segments.append(
            {
                "segment_id": segment["segment_id"],
                "segment_type": _segment_type(
                    index=index,
                    escalated=control_case["escalated_to_product_claim"],
                    recovered_static_prior_miss=control_case[
                        "recovered_static_prior_miss"
                    ],
                    false_alarm=control_case["interaction_false_alarm"],
                ),
                "delta_reject": segment["delta_reject"],
                "risk_reason": _risk_reason(segment["mechanisms"]),
                "mechanisms": segment["mechanisms"],
                "uncertainty_level": "medium"
                if control_case["escalated_to_product_claim"]
                else "diagnostic_only",
                "proxy_audit_label_positive": segment["delta_reject"] >= 0.06,
                "source_artifact_ids": [case["source_ablation_artifact_id"]],
            }
        )
    return {
        "source_key": case["source_key"],
        "target_case_id": case["target_case_id"],
        "escalated_to_product_claim": control_case["escalated_to_product_claim"],
        "blocked_reason": control_case["blocked_reason"],
        "segments": segments,
    }


def _segment_type(
    *,
    index: int,
    escalated: bool,
    recovered_static_prior_miss: bool,
    false_alarm: bool,
) -> str:
    if false_alarm and not escalated:
        return "false_alarm_candidate"
    if recovered_static_prior_miss and index == 0:
        return "static_prior_missed_risk"
    if escalated:
        return "interaction_amplified_risk"
    return "reverse_response_segment"


def _risk_reason(mechanisms: list[str]) -> str:
    return " + ".join(mechanisms) if mechanisms else "interaction_delta_positive"


def _segment_label_summary(case_results: list[dict[str, Any]]) -> dict[str, float]:
    total_predicted = 0
    total_labeled = 0
    total_true_positive = 0
    for case in case_results:
        predicted = {segment["segment_id"] for segment in case["segments"]}
        labels = {
            segment["segment_id"]
            for segment in case["segments"]
            if segment["proxy_audit_label_positive"]
        }
        total_predicted += len(predicted)
        total_labeled += len(labels)
        total_true_positive += len(predicted & labels)
    return {
        "segment_precision": _rate(total_true_positive, total_predicted),
        "segment_recall": _rate(total_true_positive, total_labeled),
    }


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

    output_path = write_r6_segment_risk_ranking_report(
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
