from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_behavioral_update_operator import (
    build_r6_behavioral_update_operator,
)
from experiments.r6_case_templates import get_r6_case_template
from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_mechanism_propagation_trace import (
    build_r6_mechanism_propagation_trace,
)


R6_MECHANISM_ABLATION_REPORT_SCHEMA_VERSION = (
    "r6-mechanism-ablation-report-v1"
)
METHODS = [
    "static_prior",
    "no_propagation_interaction",
    "random_propagation",
    "mechanism_propagation",
    "behavioral_update_candidate",
]
RANDOM_PROPAGATION_OFFSETS = {
    "htops_cost_pressure": -0.01,
    "anes_health_heldout": 0.04,
    "anes_climate_heldout": -0.02,
}


def build_r6_mechanism_ablation_report(
    artifact_id: str,
    run_id: str,
    propagation_trace: dict[str, Any] | None = None,
    behavioral_update_operator: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    if propagation_trace is None:
        propagation_trace = build_r6_mechanism_propagation_trace(
            artifact_id=f"{artifact_id}-mechanism-propagation-trace",
            run_id=run_id,
        )
    if not isinstance(propagation_trace, dict):
        raise ValueError("propagation_trace must be a JSON object")
    if behavioral_update_operator is None:
        behavioral_update_operator = build_r6_behavioral_update_operator(
            artifact_id=f"{artifact_id}-behavioral-update-operator",
            run_id=run_id,
            propagation_trace=propagation_trace,
        )
    if not isinstance(behavioral_update_operator, dict):
        raise ValueError("behavioral_update_operator must be a JSON object")

    case_traces = propagation_trace.get("case_traces", [])
    if not isinstance(case_traces, list):
        raise ValueError("propagation_trace.case_traces must be a list")

    case_method_results = [
        method_result
        for case_trace in case_traces
        for method_result in _build_case_method_results(
            case_trace=case_trace,
            behavioral_update_operator=behavioral_update_operator,
        )
    ]
    mechanism_results = [
        result
        for result in case_method_results
        if result["method"] == "mechanism_propagation"
    ]
    mechanism_positive_case_count = sum(
        1 for result in mechanism_results if result["beats_static_prior"]
    )
    mechanism_regression_case_count = len(mechanism_results) - (
        mechanism_positive_case_count
    )
    report = {
        "schema_version": R6_MECHANISM_ABLATION_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "mechanism_ablation_diagnostic_only",
        "method_summary": {
            "case_count": len(case_traces),
            "method_count": len(METHODS),
            "mechanism_positive_case_count": mechanism_positive_case_count,
            "mechanism_regression_case_count": mechanism_regression_case_count,
            "runtime_default_allowed": False,
        },
        "acceptance_gates": {
            "mechanism_trace_present": bool(case_traces),
            "dynamic_path_distinct_from_static_prior": (
                _dynamic_path_distinct_from_static_prior(propagation_trace)
            ),
            "mechanism_ablation_positive": False,
            "false_alarm_not_hidden": mechanism_regression_case_count > 0,
            "product_guard_preserved": not behavioral_update_operator.get(
                "runtime_default_allowed",
                False,
            ),
        },
        "case_method_results": case_method_results,
        "source_refs": _source_refs(propagation_trace, behavioral_update_operator),
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            (
                "Mechanism ablation is diagnostic only: one public proxy "
                "improves over the static prior while two heldout public "
                "proxies regress, so it is not CCF-A readiness evidence."
            ),
            (
                "Behavioral update candidates remain blocked pending operator "
                "holdout validation and cannot be enabled as Product runtime "
                "defaults."
            ),
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "mechanism_ablation_not_ccf_a_ready",
            "false_alarm_visible",
            "runtime_default_blocked",
        ],
        "blocking_gaps": [
            "needs_mechanism_holdout_validation",
            "needs_operator_holdout_validation",
            "needs_field_outcome_validation",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_mechanism_ablation_report(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r6_mechanism_ablation_report(**kwargs),
    )


def _build_case_method_results(
    *,
    case_trace: dict[str, Any],
    behavioral_update_operator: dict[str, Any],
) -> list[dict[str, Any]]:
    source_key = non_empty_string(case_trace.get("source_key"), field="source_key")
    case_id = non_empty_string(case_trace.get("case_id"), field="case_id")
    template = get_r6_case_template(case_id)
    observed = case_trace["proxy_summary"]["observed_reject_proxy"]
    static_prediction = _weighted_static_reject_prior(template)
    static_error = _absolute_error(static_prediction, observed)
    dynamic_path_count = len(case_trace.get("dynamic_paths", []))
    return [
        _prediction_result(
            case_trace=case_trace,
            method="static_prior",
            prediction=static_prediction,
            observed=observed,
            static_prediction=static_prediction,
            static_error=static_error,
            evaluation_status="not_update_candidate",
            evidence_boundary="segment_weighted_static_prior_only",
        ),
        _prediction_result(
            case_trace=case_trace,
            method="no_propagation_interaction",
            prediction=_no_propagation_interaction_prediction(
                template=template,
                static_prediction=static_prediction,
            ),
            observed=observed,
            static_prediction=static_prediction,
            static_error=static_error,
            evaluation_status="diagnostic_baseline",
            evidence_boundary="direct_official_exposure_without_dynamic_paths",
        ),
        _prediction_result(
            case_trace=case_trace,
            method="random_propagation",
            prediction=_random_propagation_prediction(
                source_key=source_key,
                static_prediction=static_prediction,
            ),
            observed=observed,
            static_prediction=static_prediction,
            static_error=static_error,
            evaluation_status="diagnostic_baseline",
            evidence_boundary="deterministic_random_path_baseline",
            random_seed="source_key_fixed_offset_v1",
        ),
        _prediction_result(
            case_trace=case_trace,
            method="mechanism_propagation",
            prediction=_mechanism_propagation_prediction(
                template=template,
                static_prediction=static_prediction,
            ),
            observed=observed,
            static_prediction=static_prediction,
            static_error=static_error,
            evaluation_status="diagnostic_candidate",
            evidence_boundary="uses_mechanism_trace_dynamic_paths",
            source_dynamic_path_count=dynamic_path_count,
        ),
        _blocked_behavioral_update_result(
            case_trace=case_trace,
            observed=observed,
            static_prediction=static_prediction,
            static_error=static_error,
            behavioral_update_operator=behavioral_update_operator,
        ),
    ]


def _prediction_result(
    *,
    case_trace: dict[str, Any],
    method: str,
    prediction: float,
    observed: float,
    static_prediction: float,
    static_error: float,
    evaluation_status: str,
    evidence_boundary: str,
    random_seed: str | None = None,
    source_dynamic_path_count: int | None = None,
) -> dict[str, Any]:
    mean_absolute_error = _absolute_error(prediction, observed)
    result = {
        "source_key": case_trace["source_key"],
        "case_id": case_trace["case_id"],
        "case_type": case_trace["case_type"],
        "target_case_type": case_trace["target_case_type"],
        "method": method,
        "prediction": prediction,
        "observed_reject_proxy": observed,
        "mean_absolute_error": mean_absolute_error,
        "static_prior_prediction": static_prediction,
        "static_prior_error": static_error,
        "beats_static_prior": (
            method != "static_prior" and mean_absolute_error < static_error
        ),
        "evaluation_status": evaluation_status,
        "runtime_default_allowed": False,
        "evidence_boundary": evidence_boundary,
    }
    if random_seed is not None:
        result["random_seed"] = random_seed
    if source_dynamic_path_count is not None:
        result["source_dynamic_path_count"] = source_dynamic_path_count
    return result


def _blocked_behavioral_update_result(
    *,
    case_trace: dict[str, Any],
    observed: float,
    static_prediction: float,
    static_error: float,
    behavioral_update_operator: dict[str, Any],
) -> dict[str, Any]:
    candidate_update_ids = _candidate_update_ids_for_case(
        behavioral_update_operator=behavioral_update_operator,
        source_key=case_trace["source_key"],
        case_id=case_trace["case_id"],
    )
    return {
        "source_key": case_trace["source_key"],
        "case_id": case_trace["case_id"],
        "case_type": case_trace["case_type"],
        "target_case_type": case_trace["target_case_type"],
        "method": "behavioral_update_candidate",
        "prediction": None,
        "observed_reject_proxy": observed,
        "mean_absolute_error": None,
        "static_prior_prediction": static_prediction,
        "static_prior_error": static_error,
        "beats_static_prior": False,
        "evaluation_status": "blocked_pending_operator_holdout",
        "runtime_decision": "blocked_pending_operator_holdout",
        "runtime_default_allowed": False,
        "candidate_update_ids": candidate_update_ids,
        "evidence_boundary": "structured_candidate_only_not_runtime_default",
    }


def _weighted_static_reject_prior(template: dict[str, Any]) -> float:
    reject_rate = sum(
        segment["weight"] * segment["static_response_prior"]["reject"]
        for segment in template["prior_segments"]
    )
    return round(_bounded_probability(reject_rate), 2)


def _no_propagation_interaction_prediction(
    *,
    template: dict[str, Any],
    static_prediction: float,
) -> float:
    segment_shifts = {
        shift["segment_id"]: shift
        for shift in template["interaction_profile"]["segment_shifts"]
    }
    direct_delta = 0.0
    for segment in template["prior_segments"]:
        shift = segment_shifts.get(segment["segment_id"])
        if shift is None or "official_trust_buffer" not in shift["mechanisms"]:
            continue
        direct_delta += (
            segment["weight"] * shift["delta_distribution"]["reject"]
        )
    return round(_bounded_probability(static_prediction + direct_delta), 2)


def _random_propagation_prediction(
    *,
    source_key: str,
    static_prediction: float,
) -> float:
    offset = RANDOM_PROPAGATION_OFFSETS.get(source_key, 0.0)
    return round(_bounded_probability(static_prediction + offset), 2)


def _mechanism_propagation_prediction(
    *,
    template: dict[str, Any],
    static_prediction: float,
) -> float:
    reject_delta = template["interaction_profile"]["delta_distribution"]["reject"]
    return round(_bounded_probability(static_prediction + reject_delta), 2)


def _candidate_update_ids_for_case(
    *,
    behavioral_update_operator: dict[str, Any],
    source_key: str,
    case_id: str,
) -> list[str]:
    candidate_update_ids = []
    for update in behavioral_update_operator.get("candidate_updates", []):
        if any(
            path.get("source_key") == source_key and path.get("case_id") == case_id
            for path in update.get("source_dynamic_paths", [])
        ):
            candidate_update_ids.append(update["operator_id"])
    return candidate_update_ids


def _dynamic_path_distinct_from_static_prior(
    propagation_trace: dict[str, Any],
) -> bool:
    case_traces = propagation_trace.get("case_traces", [])
    return bool(case_traces) and all(
        not dynamic_path.get("static_prior_can_express_path", True)
        for case_trace in case_traces
        for dynamic_path in case_trace.get("dynamic_paths", [])
    )


def _source_refs(
    propagation_trace: dict[str, Any],
    behavioral_update_operator: dict[str, Any],
) -> list[str]:
    refs = []
    for artifact in [propagation_trace, behavioral_update_operator]:
        artifact_id = artifact.get("artifact_id")
        if artifact_id:
            refs.append(str(artifact_id))
        refs.extend(str(ref) for ref in artifact.get("source_refs", []))
    return list(dict.fromkeys(refs))


def _absolute_error(prediction: float, observed: float) -> float:
    return round(abs(prediction - observed), 3)


def _bounded_probability(value: float) -> float:
    return max(0.0, min(1.0, value))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_mechanism_ablation_report(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "mechanism_positive_case_count": report["method_summary"][
                    "mechanism_positive_case_count"
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
