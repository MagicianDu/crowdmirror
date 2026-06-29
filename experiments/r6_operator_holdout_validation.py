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
from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    finite_number,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_mechanism_ablation_report import (
    build_r6_mechanism_ablation_report,
)
from experiments.r6_mechanism_propagation_trace import (
    build_r6_mechanism_propagation_trace,
)


R6_OPERATOR_HOLDOUT_VALIDATION_SCHEMA_VERSION = (
    "r6-operator-holdout-validation-v1"
)
R6_BEHAVIORAL_UPDATE_OPERATOR_SCHEMA_VERSION = (
    "r6-behavioral-update-operator-v1"
)
R6_BEHAVIORAL_UPDATE_OPERATOR_STATUS = (
    "behavioral_update_candidate_blocked_pending_holdout"
)
R6_MECHANISM_ABLATION_REPORT_SCHEMA_VERSION = "r6-mechanism-ablation-report-v1"
R6_MECHANISM_ABLATION_REPORT_STATUS = "mechanism_ablation_diagnostic_only"
EXPECTED_OPERATOR_IDS = {
    "damp-rights-rule-over-amplification",
    "boost-service-access-memory-activation",
}
SAME_FAMILY_HOLDOUT_SOURCE_KEYS = [
    "anes_health_heldout",
    "anes_climate_heldout",
]
OUT_OF_FAMILY_NON_REGRESSION_SOURCE_KEY = "htops_cost_pressure"
EXPECTED_HOLDOUT_SOURCE_KEYS = {
    *SAME_FAMILY_HOLDOUT_SOURCE_KEYS,
    OUT_OF_FAMILY_NON_REGRESSION_SOURCE_KEY,
}


def build_r6_operator_holdout_validation(
    artifact_id: str,
    run_id: str,
    behavioral_update_operator: dict[str, Any] | None = None,
    mechanism_ablation_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    if behavioral_update_operator is None or mechanism_ablation_report is None:
        propagation_trace = build_r6_mechanism_propagation_trace(
            artifact_id=f"{artifact_id}-mechanism-propagation-trace",
            run_id=run_id,
        )
        if behavioral_update_operator is None:
            behavioral_update_operator = build_r6_behavioral_update_operator(
                artifact_id=f"{artifact_id}-behavioral-update-operator",
                run_id=run_id,
                propagation_trace=propagation_trace,
            )
        if mechanism_ablation_report is None:
            mechanism_ablation_report = build_r6_mechanism_ablation_report(
                artifact_id=f"{artifact_id}-mechanism-ablation-report",
                run_id=run_id,
                propagation_trace=propagation_trace,
                behavioral_update_operator=behavioral_update_operator,
            )
    if not isinstance(behavioral_update_operator, dict):
        raise ValueError("behavioral_update_operator must be a JSON object")
    if not isinstance(mechanism_ablation_report, dict):
        raise ValueError("mechanism_ablation_report must be a JSON object")
    _validate_behavioral_update_operator(behavioral_update_operator)
    _validate_mechanism_ablation_report(mechanism_ablation_report)

    candidate_updates = behavioral_update_operator["candidate_updates"]
    ablation_results = _ablation_results_by_source(mechanism_ablation_report)
    holdout_trials = [
        trial
        for candidate_update in candidate_updates
        for trial in _candidate_holdout_trials(
            candidate_update=candidate_update,
            ablation_results=ablation_results,
        )
    ]
    validation_summary = _validation_summary(
        candidate_updates=candidate_updates,
        holdout_trials=holdout_trials,
    )
    report = {
        "schema_version": R6_OPERATOR_HOLDOUT_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "operator_holdout_validation_failed_current_public_proxies",
        "validation_protocol": {
            "candidate_source_rule": (
                "Freeze each structured behavioral update candidate before "
                "looking at current public proxy holdout outcomes."
            ),
            "same_family_holdout_source_keys": SAME_FAMILY_HOLDOUT_SOURCE_KEYS,
            "out_of_family_non_regression_source_key": (
                OUT_OF_FAMILY_NON_REGRESSION_SOURCE_KEY
            ),
            "holdout_label_used_for_candidate_derivation": False,
            "field_outcome_validated": False,
            "runtime_default_requires_all_holdout_trials_to_pass": True,
        },
        "validation_summary": validation_summary,
        "acceptance_gates": {
            "operator_update_structured": bool(candidate_updates),
            "operator_holdout_non_regression": False,
            "runtime_default_allowed": False,
            "field_outcome_validated": False,
            "product_guard_required": True,
        },
        "holdout_trials": holdout_trials,
        "decision": {
            "operator_holdout_passed": False,
            "decision": "keep_operator_update_blocked",
            "recommended_next_step": (
                "add_independent_same_family_operator_holdout_or_field_outcome"
            ),
            "runtime_default_allowed": False,
        },
        "source_refs": _source_refs(
            behavioral_update_operator,
            mechanism_ablation_report,
        ),
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            (
                "Operator holdout validation failed on current public proxies: "
                "ANES health/climate same-family holdouts contradict the "
                "candidate updates, while HTOPS only provides out-of-family "
                "non-regression evidence."
            ),
            (
                "Structured behavioral update candidates remain diagnostic only; "
                "they are not field validation and cannot be Product runtime "
                "defaults."
            ),
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "operator_update_blocked",
            "operator_holdout_failed_current_public_proxies",
            "out_of_family_non_regression_not_generalization",
            "field_outcome_validation_missing",
            "runtime_default_blocked",
        ],
        "blocking_gaps": [
            "needs_operator_holdout_validation",
            "needs_independent_same_family_operator_holdout",
            "needs_field_outcome_validation",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_operator_holdout_validation(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r6_operator_holdout_validation(**kwargs),
    )


def _candidate_holdout_trials(
    *,
    candidate_update: dict[str, Any],
    ablation_results: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _same_family_trial(
            candidate_update=candidate_update,
            ablation_results=ablation_results,
        ),
        _out_of_family_non_regression_trial(
            candidate_update=candidate_update,
            ablation_results=ablation_results,
        ),
    ]


def _same_family_trial(
    *,
    candidate_update: dict[str, Any],
    ablation_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    holdout_results = [
        _holdout_result(source_key=source_key, ablation_results=ablation_results)
        for source_key in SAME_FAMILY_HOLDOUT_SOURCE_KEYS
    ]
    failed_source_keys = [
        result["source_key"]
        for result in holdout_results
        if result["beats_static_prior"] is False
    ]
    return {
        "trial_id": f"operator-holdout:{candidate_update['operator_id']}:anes",
        "candidate_update_id": candidate_update["operator_id"],
        "trial_type": "same_family_current_public_proxy_holdout",
        "holdout_source_keys": SAME_FAMILY_HOLDOUT_SOURCE_KEYS,
        "validation_status": "failed_same_family_holdout_regression",
        "passed": False,
        "non_regression_only": False,
        "runtime_default_allowed": False,
        "field_outcome_validated": False,
        "holdout_results": holdout_results,
        "failed_source_keys": failed_source_keys,
        "failure_reason": (
            "Current ANES health/climate public proxy holdouts do not preserve "
            "mechanism performance over the static prior, so the structured "
            "operator update cannot generalize."
        ),
        "claim_boundary": (
            "Same-family public proxy contradiction blocks runtime default; "
            "this is not field outcome validation."
        ),
    }


def _out_of_family_non_regression_trial(
    *,
    candidate_update: dict[str, Any],
    ablation_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    holdout_result = _holdout_result(
        source_key=OUT_OF_FAMILY_NON_REGRESSION_SOURCE_KEY,
        ablation_results=ablation_results,
    )
    return {
        "trial_id": (
            "operator-holdout:"
            f"{candidate_update['operator_id']}:htops-non-regression"
        ),
        "candidate_update_id": candidate_update["operator_id"],
        "trial_type": "out_of_family_non_regression",
        "holdout_source_keys": [OUT_OF_FAMILY_NON_REGRESSION_SOURCE_KEY],
        "validation_status": "non_regression_out_of_family_only",
        "passed": False,
        "non_regression_only": True,
        "runtime_default_allowed": False,
        "field_outcome_validated": False,
        "holdout_results": [holdout_result],
        "failure_reason": (
            "HTOPS is retained as an out-of-family non-regression check only; "
            "it cannot validate the candidate update as a same-family or field "
            "outcome operator."
        ),
        "claim_boundary": (
            "Out-of-family non-regression evidence does not authorize Product "
            "runtime defaults."
        ),
    }


def _holdout_result(
    *,
    source_key: str,
    ablation_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if source_key not in ablation_results:
        raise ValueError(f"mechanism_ablation_report missing source_key: {source_key}")
    result = ablation_results[source_key]
    return {
        "source_key": source_key,
        "case_id": result["case_id"],
        "case_type": result["case_type"],
        "target_case_type": result["target_case_type"],
        "method": result["method"],
        "beats_static_prior": result["beats_static_prior"],
        "mechanism_mean_absolute_error": result["mean_absolute_error"],
        "static_prior_error": result["static_prior_error"],
        "evaluation_status": result["evaluation_status"],
        "runtime_default_allowed": result["runtime_default_allowed"],
        "evidence_boundary": result["evidence_boundary"],
    }


def _validation_summary(
    *,
    candidate_updates: list[dict[str, Any]],
    holdout_trials: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "candidate_update_count": len(candidate_updates),
        "holdout_trial_count": len(holdout_trials),
        "passed_trial_count": sum(1 for trial in holdout_trials if trial["passed"]),
        "non_regression_trial_count": sum(
            1 for trial in holdout_trials if trial["non_regression_only"]
        ),
        "failed_trial_count": sum(
            1
            for trial in holdout_trials
            if trial["validation_status"].startswith("failed_")
        ),
        "runtime_default_allowed": False,
    }


def _ablation_results_by_source(
    mechanism_ablation_report: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for result in mechanism_ablation_report["case_method_results"]:
        if result.get("method") != "mechanism_propagation":
            continue
        source_key = result.get("source_key")
        if not isinstance(source_key, str):
            raise ValueError(
                "mechanism_ablation_report.case_method_results source_key "
                "must be a string"
            )
        results[source_key] = result
    return results


def _validate_behavioral_update_operator(
    behavioral_update_operator: dict[str, Any],
) -> None:
    if (
        behavioral_update_operator.get("schema_version")
        != R6_BEHAVIORAL_UPDATE_OPERATOR_SCHEMA_VERSION
    ):
        raise ValueError(
            "behavioral_update_operator.schema_version must be "
            f"{R6_BEHAVIORAL_UPDATE_OPERATOR_SCHEMA_VERSION}"
        )
    if behavioral_update_operator.get("status") != R6_BEHAVIORAL_UPDATE_OPERATOR_STATUS:
        raise ValueError(
            "behavioral_update_operator.status must be "
            f"{R6_BEHAVIORAL_UPDATE_OPERATOR_STATUS}"
        )
    if behavioral_update_operator.get("runtime_default_allowed") is not False:
        raise ValueError(
            "behavioral_update_operator.runtime_default_allowed must be False"
        )
    acceptance_gates = behavioral_update_operator.get("acceptance_gates")
    if not isinstance(acceptance_gates, dict):
        raise ValueError(
            "behavioral_update_operator.acceptance_gates must be a JSON object"
        )
    if acceptance_gates.get("operator_update_structured") is not True:
        raise ValueError(
            "behavioral_update_operator.acceptance_gates."
            "operator_update_structured must be True"
        )
    if acceptance_gates.get("runtime_default_allowed") is not False:
        raise ValueError(
            "behavioral_update_operator.acceptance_gates."
            "runtime_default_allowed must be False"
        )
    operator_summary = behavioral_update_operator.get("operator_summary")
    if not isinstance(operator_summary, dict):
        raise ValueError(
            "behavioral_update_operator.operator_summary must be a JSON object"
        )
    if operator_summary.get("candidate_update_count") != 2:
        raise ValueError(
            "behavioral_update_operator.operator_summary."
            "candidate_update_count must be 2"
        )
    if operator_summary.get("runtime_default_allowed_count") != 0:
        raise ValueError(
            "behavioral_update_operator.operator_summary."
            "runtime_default_allowed_count must be 0"
        )
    candidate_updates = behavioral_update_operator.get("candidate_updates")
    if not isinstance(candidate_updates, list) or not candidate_updates:
        raise ValueError(
            "behavioral_update_operator.candidate_updates must be a non-empty list"
        )
    candidate_ids = [
        candidate_update.get("operator_id")
        for candidate_update in candidate_updates
        if isinstance(candidate_update, dict)
    ]
    if set(candidate_ids) != EXPECTED_OPERATOR_IDS or len(candidate_ids) != 2:
        raise ValueError(
            "behavioral_update_operator.candidate_updates operator_id set "
            "must exactly match current MVP"
        )
    for update_index, candidate_update in enumerate(candidate_updates):
        if not isinstance(candidate_update, dict):
            raise ValueError(
                "behavioral_update_operator.candidate_updates"
                f"[{update_index}] must be a JSON object"
            )
        if not candidate_update.get("operator_id"):
            raise ValueError(
                "behavioral_update_operator.candidate_updates"
                f"[{update_index}].operator_id must be present"
            )
        if candidate_update.get("runtime_default_allowed") is not False:
            raise ValueError(
                "behavioral_update_operator.candidate_updates"
                f"[{update_index}].runtime_default_allowed must be False"
            )
        if (
            candidate_update.get("runtime_decision")
            != "blocked_pending_operator_holdout"
        ):
            raise ValueError(
                "behavioral_update_operator.candidate_updates"
                f"[{update_index}].runtime_decision must be "
                "blocked_pending_operator_holdout"
            )
        if candidate_update.get("prompt_patch_text") != "":
            raise ValueError(
                "behavioral_update_operator.candidate_updates"
                f"[{update_index}].prompt_patch_text must be empty"
            )


def _validate_mechanism_ablation_report(
    mechanism_ablation_report: dict[str, Any],
) -> None:
    if (
        mechanism_ablation_report.get("schema_version")
        != R6_MECHANISM_ABLATION_REPORT_SCHEMA_VERSION
    ):
        raise ValueError(
            "mechanism_ablation_report.schema_version must be "
            f"{R6_MECHANISM_ABLATION_REPORT_SCHEMA_VERSION}"
        )
    if mechanism_ablation_report.get("status") != R6_MECHANISM_ABLATION_REPORT_STATUS:
        raise ValueError(
            "mechanism_ablation_report.status must be "
            f"{R6_MECHANISM_ABLATION_REPORT_STATUS}"
        )
    method_summary = mechanism_ablation_report.get("method_summary")
    if not isinstance(method_summary, dict):
        raise ValueError("mechanism_ablation_report.method_summary must be a JSON object")
    if method_summary.get("runtime_default_allowed") is not False:
        raise ValueError(
            "mechanism_ablation_report.method_summary.runtime_default_allowed "
            "must be False"
        )
    acceptance_gates = mechanism_ablation_report.get("acceptance_gates")
    if not isinstance(acceptance_gates, dict):
        raise ValueError(
            "mechanism_ablation_report.acceptance_gates must be a JSON object"
        )
    if acceptance_gates.get("product_guard_preserved") is not True:
        raise ValueError(
            "mechanism_ablation_report.acceptance_gates."
            "product_guard_preserved must be True"
        )
    case_method_results = mechanism_ablation_report.get("case_method_results")
    if not isinstance(case_method_results, list) or not case_method_results:
        raise ValueError(
            "mechanism_ablation_report.case_method_results must be a non-empty list"
        )
    _validate_mechanism_ablation_selected_rows(case_method_results)


def _validate_mechanism_ablation_selected_rows(
    case_method_results: list[Any],
) -> None:
    selected_source_keys = []
    for row_index, result in enumerate(case_method_results):
        if not isinstance(result, dict):
            raise ValueError(
                "mechanism_ablation_report.case_method_results"
                f"[{row_index}] must be a JSON object"
            )
        if result.get("method") != "mechanism_propagation":
            continue
        source_key = result.get("source_key")
        if not isinstance(source_key, str) or not source_key:
            raise ValueError(
                "mechanism_ablation_report.case_method_results"
                f"[{row_index}].source_key must be a non-empty string"
            )
        selected_source_keys.append(source_key)
        if result.get("runtime_default_allowed") is not False:
            raise ValueError(
                "mechanism_ablation_report.case_method_results"
                f"[{row_index}].runtime_default_allowed must be False"
            )
        mean_absolute_error = finite_number(
            result.get("mean_absolute_error"),
            field=(
                "mechanism_ablation_report.case_method_results"
                f"[{row_index}].mean_absolute_error"
            ),
        )
        static_prior_error = finite_number(
            result.get("static_prior_error"),
            field=(
                "mechanism_ablation_report.case_method_results"
                f"[{row_index}].static_prior_error"
            ),
        )
        expected_beats_static_prior = mean_absolute_error < static_prior_error
        if result.get("beats_static_prior") is not expected_beats_static_prior:
            raise ValueError(
                "mechanism_ablation_report.case_method_results"
                f"[{row_index}].beats_static_prior must equal "
                "mean_absolute_error < static_prior_error"
            )

    if (
        set(selected_source_keys) != EXPECTED_HOLDOUT_SOURCE_KEYS
        or len(selected_source_keys) != len(EXPECTED_HOLDOUT_SOURCE_KEYS)
    ):
        raise ValueError(
            "mechanism_ablation_report selected mechanism_propagation source "
            "keys must exactly include "
            f"{sorted(EXPECTED_HOLDOUT_SOURCE_KEYS)}"
        )
    _validate_current_mvp_holdout_shape(case_method_results)


def _validate_current_mvp_holdout_shape(case_method_results: list[Any]) -> None:
    selected_rows = [
        result
        for result in case_method_results
        if isinstance(result, dict) and result.get("method") == "mechanism_propagation"
    ]
    anes_rows = [
        result
        for result in selected_rows
        if result.get("source_key") in SAME_FAMILY_HOLDOUT_SOURCE_KEYS
    ]
    if any(result.get("beats_static_prior") is not False for result in anes_rows):
        raise ValueError(
            "mechanism_ablation_report selected ANES rows must have "
            "beats_static_prior False"
        )
    htops_rows = [
        result
        for result in selected_rows
        if result.get("source_key") == OUT_OF_FAMILY_NON_REGRESSION_SOURCE_KEY
    ]
    if any(result.get("beats_static_prior") is not True for result in htops_rows):
        raise ValueError(
            "mechanism_ablation_report selected HTOPS row must have "
            "beats_static_prior True"
        )


def _source_refs(*artifacts: dict[str, Any]) -> list[str]:
    refs = []
    for artifact in artifacts:
        artifact_id = artifact.get("artifact_id")
        if artifact_id:
            refs.append(str(artifact_id))
        refs.extend(str(ref) for ref in artifact.get("source_refs", []))
    return list(dict.fromkeys(refs))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_operator_holdout_validation(
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
