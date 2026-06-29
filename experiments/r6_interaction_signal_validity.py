from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_case_templates import get_r6_case_template
from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_decision_value_metrics import (
    DEFAULT_SOURCE_KEYS,
    build_r6_decision_value_metrics,
)
from experiments.r6_foundation_pipeline import build_r6_foundation_pipeline
from experiments.r6_public_outcome_proxy import build_r6_public_outcome_proxy


R6_INTERACTION_SIGNAL_VALIDITY_SCHEMA_VERSION = (
    "r6-interaction-signal-validity-v1"
)
FORBIDDEN_SCORING_FEATURES = [
    "source_key",
    "target_case_id",
    "target_case_type",
]
SCORING_FEATURE_NAMES = [
    "segment_delta_span",
    "segment_delta_concentration",
    "mechanism_impact_overlap",
    "counterfactual_alternative_count",
    "interaction_delta_magnitude",
    "top_risk_segment_prior_uncertainty",
    "holdout_outcome_support",
]
SCORE_WEIGHTS = {
    "segment_pattern_score": 0.20,
    "mechanism_alignment_score": 0.20,
    "counterfactual_sensitivity_score": 0.15,
    "prior_uncertainty_score": 0.20,
    "holdout_consistency_score": 0.25,
}


def build_r6_interaction_signal_validity(
    *,
    artifact_id: str,
    run_id: str,
    decision_value_metrics: dict[str, Any] | None = None,
    case_evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    decision_value_metrics = decision_value_metrics or build_r6_decision_value_metrics(
        artifact_id=f"{artifact_id}-decision-value-metrics",
        run_id=run_id,
    )
    evidence = case_evidence or _default_case_evidence(
        artifact_id=artifact_id,
        run_id=run_id,
        decision_value_metrics=decision_value_metrics,
    )
    case_scores = [_score_case(case) for case in evidence]
    summary = _summary(case_scores)
    generalized = summary["generalized_accept_count"] > 0
    report = {
        "schema_version": R6_INTERACTION_SIGNAL_VALIDITY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "interaction_signal_validity_generalized"
            if generalized
            else "interaction_signal_validity_diagnostic_only"
        ),
        "scoring_policy": {
            "purpose": (
                "Score whether an interaction risk signal has validity beyond the "
                "static prior without using source or policy-family labels as the "
                "core rule."
            ),
            "dimension_weights": SCORE_WEIGHTS,
            "scoring_feature_names": SCORING_FEATURE_NAMES,
            "forbidden_scoring_features": FORBIDDEN_SCORING_FEATURES,
            "audit_fields_excluded_from_scoring": FORBIDDEN_SCORING_FEATURES
            + ["public_proxy_artifact_id"],
        },
        "summary": summary,
        "case_validity_scores": case_scores,
        "acceptance_gates": {
            "interaction_signal_validity_present": True,
            "forbidden_label_features_excluded": summary[
                "forbidden_label_feature_count"
            ]
            == 0,
            "case_level_validity_scores_present": bool(case_scores),
            "current_proxy_supported_signal_observed": summary[
                "current_proxy_supported_signal_count"
            ]
            > 0,
            "likely_false_alarm_cases_identified": summary[
                "rejected_false_alarm_count"
            ]
            > 0,
            "interaction_signal_validity_generalized": generalized,
            "field_outcome_validated": False,
        },
        "decision": {
            "decision": (
                "accept_interaction_signal_validity"
                if generalized
                else "continue_with_diagnostic_signal_validity"
            ),
            "interaction_signal_validity_generalized": generalized,
            "recommended_next_step": (
                "validate_signal_validity_on_field_or_external_holdout"
                if generalized
                else "add_holdout_or_field_outcome_for_signal_validity_generalization"
            ),
        },
        "source_refs": _source_refs(evidence, decision_value_metrics),
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            (
                "Interaction Signal Validity Score is a diagnostic validity score; "
                "without holdout or field validation it must not be treated as a "
                "generalized risk acceptance rule."
            ),
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": _risk_flags(summary, generalized=generalized),
        "blocking_gaps": [] if generalized else [
            "needs_interaction_signal_validity_generalization",
            "needs_signal_validity_holdout_validation",
            "needs_field_outcome_validation",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_interaction_signal_validity(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r6_interaction_signal_validity(**kwargs),
    )


def _default_case_evidence(
    *,
    artifact_id: str,
    run_id: str,
    decision_value_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    cases_by_source = {
        case["source_key"]: case
        for case in decision_value_metrics["case_results"]
    }
    evidence = []
    for source_key in DEFAULT_SOURCE_KEYS:
        proxy = build_r6_public_outcome_proxy(
            artifact_id=f"{artifact_id}-{source_key}-proxy",
            run_id=run_id,
            source_key=source_key,
        )
        template = get_r6_case_template(proxy["target_case_id"])
        template["outcome"] = {
            **template["outcome"],
            **proxy["outcome_override"],
        }
        template["public_outcome_proxy_artifact_id"] = proxy["artifact_id"]
        package = build_r6_foundation_pipeline(
            artifact_id=f"{artifact_id}-{source_key}-foundation",
            run_id=run_id,
            case_template=template,
        )
        evidence.append(
            {
                "audit": {
                    "source_key": source_key,
                    "target_case_id": proxy["target_case_id"],
                    "target_case_type": proxy.get(
                        "target_case_type",
                        template["case_type"],
                    ),
                    "public_proxy_artifact_id": proxy["artifact_id"],
                },
                "case_result": cases_by_source[source_key],
                "prior_manifest": package["prior_manifest"],
                "scenario_manifest": package["scenario_manifest"],
                "interaction_trace": package["interaction_trace"],
                "risk_shift_report": package["risk_shift_report"],
                "public_proxy_summary": {
                    "observed_reject_proxy": proxy["metrics"]["observed_reject_proxy"],
                    "usable_row_count": proxy["public_source"]["usable_row_count"],
                    "source_artifact_id": proxy["public_source"][
                        "source_artifact_id"
                    ],
                },
            }
        )
    return evidence


def _score_case(case: dict[str, Any]) -> dict[str, Any]:
    scoring_inputs = _scoring_inputs(case)
    component_scores = {
        "segment_pattern_score": _segment_pattern_score(scoring_inputs),
        "mechanism_alignment_score": _mechanism_alignment_score(scoring_inputs),
        "counterfactual_sensitivity_score": _counterfactual_sensitivity_score(
            scoring_inputs
        ),
        "prior_uncertainty_score": _prior_uncertainty_score(scoring_inputs),
        "holdout_consistency_score": _holdout_consistency_score(scoring_inputs),
    }
    validity_score = _weighted_score(component_scores)
    classification, reason = _classification(
        validity_score=validity_score,
        component_scores=component_scores,
        case_result=case["case_result"],
    )
    return {
        "audit": dict(case["audit"]),
        "scoring_inputs": scoring_inputs,
        "scoring_fingerprint": _fingerprint(scoring_inputs),
        "component_scores": component_scores,
        "validity_score": validity_score,
        "classification": classification,
        "classification_reason": reason,
        "explanation": _explanation(
            validity_score=validity_score,
            component_scores=component_scores,
            classification=classification,
        ),
    }


def _scoring_inputs(case: dict[str, Any]) -> dict[str, Any]:
    interaction_trace = case["interaction_trace"]
    scenario = case["scenario_manifest"]
    prior = case["prior_manifest"]
    case_result = case["case_result"]
    segment_shifts = interaction_trace["segment_shifts"]
    reject_deltas = [
        float(segment["delta_distribution"]["reject"])
        for segment in segment_shifts
    ]
    top_segment = max(
        segment_shifts,
        key=lambda segment: float(segment["delta_distribution"]["reject"]),
    )
    top_segment_id = top_segment["segment_id"]
    top_prior_segment = _prior_segment(prior, top_segment_id)
    impact_terms = _terms(scenario["impact_dimensions"])
    mechanism_terms = _terms(
        mechanism
        for segment in segment_shifts
        for mechanism in segment.get("mechanisms", [])
    )
    overlap_terms = sorted(impact_terms & mechanism_terms)
    return {
        "segment_delta_span": round(max(reject_deltas) - min(reject_deltas), 3),
        "segment_delta_concentration": round(
            max(reject_deltas) / sum(reject_deltas),
            3,
        ),
        "mechanism_impact_overlap": overlap_terms,
        "counterfactual_alternative_count": len(
            scenario.get("alternative_scenarios", [])
        ),
        "interaction_delta_magnitude": round(
            abs(float(interaction_trace["delta_distribution"]["reject"])),
            3,
        ),
        "top_risk_segment_prior_uncertainty": round(
            float(top_prior_segment.get("uncertainty", 0.0)),
            3,
        ),
        "holdout_outcome_support": _holdout_support(case_result),
        "interaction_flags_new_risk": bool(
            case_result.get("interaction_flags_new_risk")
        ),
        "observed_high_risk": bool(case_result.get("observed_high_risk")),
        "public_proxy_available": "observed_reject_proxy" in case["public_proxy_summary"],
    }


def _prior_segment(prior: dict[str, Any], segment_id: str) -> dict[str, Any]:
    for segment in prior["segments"]:
        if segment["segment_id"] == segment_id:
            return segment
    return {}


def _segment_pattern_score(scoring_inputs: dict[str, Any]) -> float:
    span = scoring_inputs["segment_delta_span"]
    concentration = scoring_inputs["segment_delta_concentration"]
    if span >= 0.08 and 0.35 <= concentration <= 0.70:
        return 1.0
    if span >= 0.04:
        return 0.7
    return 0.2


def _mechanism_alignment_score(scoring_inputs: dict[str, Any]) -> float:
    overlap_count = len(scoring_inputs["mechanism_impact_overlap"])
    if overlap_count >= 2:
        return 1.0
    if overlap_count == 1:
        return 0.7
    return 0.3


def _counterfactual_sensitivity_score(scoring_inputs: dict[str, Any]) -> float:
    if (
        scoring_inputs["counterfactual_alternative_count"] >= 2
        and scoring_inputs["interaction_delta_magnitude"] >= 0.05
        and scoring_inputs["segment_delta_span"] >= 0.08
    ):
        return 0.8
    if scoring_inputs["interaction_delta_magnitude"] > 0:
        return 0.5
    return 0.2


def _prior_uncertainty_score(scoring_inputs: dict[str, Any]) -> float:
    uncertainty = scoring_inputs["top_risk_segment_prior_uncertainty"]
    if uncertainty >= 0.18:
        return 0.8
    if uncertainty >= 0.14:
        return 0.6
    return 0.3


def _holdout_consistency_score(scoring_inputs: dict[str, Any]) -> float | None:
    support = scoring_inputs["holdout_outcome_support"]
    if support == "supported":
        return 1.0
    if support == "contradicted":
        return 0.0
    if support == "available_unclear":
        return 0.5
    return None


def _holdout_support(case_result: dict[str, Any]) -> str:
    if "observed_high_risk" not in case_result:
        return "missing"
    if case_result.get("interaction_false_alarm"):
        return "contradicted"
    if case_result.get("recovered_static_prior_miss"):
        return "supported"
    return "available_unclear"


def _weighted_score(component_scores: dict[str, float | None]) -> float:
    numerator = 0.0
    denominator = 0.0
    for name, weight in SCORE_WEIGHTS.items():
        score = component_scores[name]
        if score is None:
            continue
        numerator += float(score) * weight
        denominator += weight
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


def _classification(
    *,
    validity_score: float,
    component_scores: dict[str, float | None],
    case_result: dict[str, Any],
) -> tuple[str, str]:
    if component_scores["holdout_consistency_score"] is None:
        return "needs_more_outcome", "no_outcome_or_holdout_available"
    if case_result.get("interaction_false_alarm"):
        return "reject_as_likely_false_alarm", "current_proxy_contradicts_signal"
    if validity_score >= 0.85 and case_result.get("field_validated"):
        return "accept_as_risk_signal", "field_validated_signal"
    if case_result.get("recovered_static_prior_miss") and validity_score >= 0.75:
        return (
            "diagnostic_only",
            "current_proxy_supports_signal_but_generalization_missing",
        )
    return "diagnostic_only", "signal_not_generalized"


def _explanation(
    *,
    validity_score: float,
    component_scores: dict[str, float | None],
    classification: str,
) -> list[str]:
    explanation = [
        f"validity_score={validity_score}",
        f"segment_pattern_score={component_scores['segment_pattern_score']}",
        f"mechanism_alignment_score={component_scores['mechanism_alignment_score']}",
        f"holdout_consistency_score={component_scores['holdout_consistency_score']}",
        f"classification={classification}",
    ]
    return explanation


def _summary(case_scores: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [
        case for case in case_scores if case["classification"] == "accept_as_risk_signal"
    ]
    diagnostic = [
        case for case in case_scores if case["classification"] == "diagnostic_only"
    ]
    rejected = [
        case
        for case in case_scores
        if case["classification"] == "reject_as_likely_false_alarm"
    ]
    needs_more = [
        case for case in case_scores if case["classification"] == "needs_more_outcome"
    ]
    supported = [
        case
        for case in case_scores
        if case["scoring_inputs"]["holdout_outcome_support"] == "supported"
    ]
    return {
        "case_count": len(case_scores),
        "accepted_count": len(accepted),
        "diagnostic_only_count": len(diagnostic),
        "rejected_false_alarm_count": len(rejected),
        "needs_more_outcome_count": len(needs_more),
        "current_proxy_supported_signal_count": len(supported),
        "generalized_accept_count": len(accepted),
        "forbidden_label_feature_count": _forbidden_label_feature_count(case_scores),
        "mean_validity_score": _mean_score(case_scores),
    }


def _forbidden_label_feature_count(case_scores: list[dict[str, Any]]) -> int:
    count = 0
    for case in case_scores:
        count += len(set(case["scoring_inputs"]) & set(FORBIDDEN_SCORING_FEATURES))
    return count


def _mean_score(case_scores: list[dict[str, Any]]) -> float:
    if not case_scores:
        return 0.0
    return round(
        sum(float(case["validity_score"]) for case in case_scores) / len(case_scores),
        3,
    )


def _source_refs(
    evidence: list[dict[str, Any]],
    decision_value_metrics: dict[str, Any],
) -> list[str]:
    refs = [decision_value_metrics["artifact_id"]]
    for case in evidence:
        refs.append(case["audit"].get("public_proxy_artifact_id", ""))
        refs.append(case.get("risk_shift_report", {}).get("artifact_id", ""))
    return [ref for ref in dict.fromkeys(refs) if ref]


def _risk_flags(summary: dict[str, Any], *, generalized: bool) -> list[str]:
    flags = ["case_source_family_gate_not_used_for_scoring"]
    if summary["current_proxy_supported_signal_count"] > 0:
        flags.append("current_proxy_supported_signal_observed")
    if summary["rejected_false_alarm_count"] > 0:
        flags.append("current_proxy_false_alarms_identified")
    if not generalized:
        flags.append("interaction_signal_validity_not_generalized")
    return flags


def _terms(values: Any) -> set[str]:
    terms: set[str] = set()
    for value in values:
        for token in re.split(r"[^a-zA-Z0-9]+", str(value).lower()):
            if token and token not in {"and", "or", "the"}:
                terms.add(token)
    return terms


def _fingerprint(scoring_inputs: dict[str, Any]) -> str:
    payload = json.dumps(scoring_inputs, sort_keys=True, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_interaction_signal_validity(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "interaction_signal_validity_generalized": report[
                    "acceptance_gates"
                ]["interaction_signal_validity_generalized"],
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
