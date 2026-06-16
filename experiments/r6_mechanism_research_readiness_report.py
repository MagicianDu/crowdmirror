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
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_mechanism_ablation_report import (
    build_r6_mechanism_ablation_report,
)
from experiments.r6_mechanism_propagation_trace import (
    build_r6_mechanism_propagation_trace,
)
from experiments.r6_operator_holdout_validation import (
    build_r6_operator_holdout_validation,
)


R6_MECHANISM_RESEARCH_READINESS_REPORT_SCHEMA_VERSION = (
    "r6-mechanism-research-readiness-report-v1"
)
R6_MECHANISM_PROPAGATION_TRACE_SCHEMA_VERSION = (
    "r6-mechanism-propagation-trace-v1"
)
R6_BEHAVIORAL_UPDATE_OPERATOR_SCHEMA_VERSION = (
    "r6-behavioral-update-operator-v1"
)
R6_MECHANISM_ABLATION_REPORT_SCHEMA_VERSION = "r6-mechanism-ablation-report-v1"
R6_OPERATOR_HOLDOUT_VALIDATION_SCHEMA_VERSION = (
    "r6-operator-holdout-validation-v1"
)


def build_r6_mechanism_research_readiness_report(
    artifact_id: str,
    run_id: str,
    propagation_trace: dict[str, Any] | None = None,
    behavioral_update_operator: dict[str, Any] | None = None,
    mechanism_ablation_report: dict[str, Any] | None = None,
    operator_holdout_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    if propagation_trace is None:
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
    if operator_holdout_validation is None:
        operator_holdout_validation = build_r6_operator_holdout_validation(
            artifact_id=f"{artifact_id}-operator-holdout-validation",
            run_id=run_id,
            behavioral_update_operator=behavioral_update_operator,
            mechanism_ablation_report=mechanism_ablation_report,
        )

    for field, artifact in [
        ("propagation_trace", propagation_trace),
        ("behavioral_update_operator", behavioral_update_operator),
        ("mechanism_ablation_report", mechanism_ablation_report),
        ("operator_holdout_validation", operator_holdout_validation),
    ]:
        if not isinstance(artifact, dict):
            raise ValueError(f"{field} must be a JSON object")

    readiness_gates = _readiness_gates(
        propagation_trace=propagation_trace,
        behavioral_update_operator=behavioral_update_operator,
        mechanism_ablation_report=mechanism_ablation_report,
        operator_holdout_validation=operator_holdout_validation,
    )
    report = {
        "schema_version": R6_MECHANISM_RESEARCH_READINESS_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "mechanism_research_diagnostic_only",
        "decision": {
            "mechanism_mvp_result": "diagnostic_only",
            "continue_research_with_constraints": True,
            "ccf_a_main_contribution_ready": False,
            "runtime_default_allowed": False,
        },
        "readiness_gates": readiness_gates,
        "readiness_summary": {
            "mechanism_trace_present": readiness_gates["mechanism_trace_present"],
            "operator_candidate_count": behavioral_update_operator[
                "operator_summary"
            ]["candidate_update_count"],
            "mechanism_positive_case_count": mechanism_ablation_report[
                "method_summary"
            ]["mechanism_positive_case_count"],
            "mechanism_regression_case_count": mechanism_ablation_report[
                "method_summary"
            ]["mechanism_regression_case_count"],
            "operator_holdout_trial_count": operator_holdout_validation[
                "validation_summary"
            ]["holdout_trial_count"],
            "operator_holdout_passed_trial_count": operator_holdout_validation[
                "validation_summary"
            ]["passed_trial_count"],
            "runtime_default_allowed": False,
            "field_outcome_validated": False,
        },
        "research_boundary": {
            "allowed_claim": (
                "R6 mechanism MVP is a diagnostic research artifact with "
                "auditable dynamic-path traces, blocked structured operator "
                "candidates, visible ablation regressions, and explicit Product "
                "guards."
            ),
            "blocked_claim": (
                "R6 mechanism MVP is not CCF-A main-contribution ready, not "
                "field outcome validated, and not allowed as Product runtime "
                "default behavior."
            ),
        },
        "recommended_next_research_steps": [
            "add_independent_same_family_operator_holdout",
            "validate_operator_against_field_or_real_release_outcome",
            "separate_generalizable_operator_evidence_from_public_proxy_diagnostics",
            "keep_product_runtime_guard_fail_closed_until_holdout_passes",
        ],
        "source_refs": _source_refs(
            propagation_trace,
            behavioral_update_operator,
            mechanism_ablation_report,
            operator_holdout_validation,
        ),
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            (
                "Readiness is diagnostic-only because a mechanism trace exists "
                "but operator holdout validation fails on current public proxies."
            ),
            (
                "Research can continue under constraints; CCF-A main contribution "
                "and Product runtime defaults remain blocked."
            ),
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": _risk_flags(
            mechanism_ablation_report=mechanism_ablation_report,
            operator_holdout_validation=operator_holdout_validation,
        ),
        "blocking_gaps": _blocking_gaps(
            mechanism_ablation_report=mechanism_ablation_report,
            operator_holdout_validation=operator_holdout_validation,
        ),
    }
    assert_strict_json(report)
    return report


def write_r6_mechanism_research_readiness_report(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r6_mechanism_research_readiness_report(**kwargs),
    )


def _readiness_gates(
    *,
    propagation_trace: dict[str, Any],
    behavioral_update_operator: dict[str, Any],
    mechanism_ablation_report: dict[str, Any],
    operator_holdout_validation: dict[str, Any],
) -> dict[str, bool]:
    _validate_propagation_trace(propagation_trace)
    _validate_behavioral_update_operator(behavioral_update_operator)
    _validate_mechanism_ablation_report(mechanism_ablation_report)
    _validate_operator_holdout_validation(operator_holdout_validation)
    return {
        "mechanism_trace_present": (
            propagation_trace["acceptance_gates"]["mechanism_trace_present"]
        ),
        "dynamic_path_distinct_from_static_prior": propagation_trace[
            "acceptance_gates"
        ]["dynamic_path_distinct_from_static_prior"],
        "behavioral_update_operator_structured": behavioral_update_operator[
            "acceptance_gates"
        ]["operator_update_structured"],
        "mechanism_ablation_positive": mechanism_ablation_report[
            "acceptance_gates"
        ]["mechanism_ablation_positive"],
        "false_alarm_not_hidden": mechanism_ablation_report["acceptance_gates"][
            "false_alarm_not_hidden"
        ],
        "operator_holdout_non_regression": operator_holdout_validation[
            "acceptance_gates"
        ]["operator_holdout_non_regression"],
        "product_guard_preserved": (
            mechanism_ablation_report["acceptance_gates"][
                "product_guard_preserved"
            ]
            and operator_holdout_validation["acceptance_gates"][
                "product_guard_required"
            ]
        ),
        "runtime_default_allowed": False,
        "field_outcome_validated": False,
    }


def _validate_propagation_trace(propagation_trace: dict[str, Any]) -> None:
    if (
        propagation_trace.get("schema_version")
        != R6_MECHANISM_PROPAGATION_TRACE_SCHEMA_VERSION
    ):
        raise ValueError(
            "propagation_trace.schema_version must be "
            f"{R6_MECHANISM_PROPAGATION_TRACE_SCHEMA_VERSION}"
        )
    if propagation_trace.get("status") != "mechanism_propagation_trace_ready":
        raise ValueError(
            "propagation_trace.status must be mechanism_propagation_trace_ready"
        )
    acceptance_gates = propagation_trace.get("acceptance_gates")
    if not isinstance(acceptance_gates, dict):
        raise ValueError("propagation_trace.acceptance_gates must be a JSON object")
    if acceptance_gates.get("mechanism_trace_present") is not True:
        raise ValueError(
            "propagation_trace.acceptance_gates.mechanism_trace_present "
            "must be True"
        )
    if acceptance_gates.get("dynamic_path_distinct_from_static_prior") is not True:
        raise ValueError(
            "propagation_trace.acceptance_gates."
            "dynamic_path_distinct_from_static_prior must be True"
        )


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
    if (
        behavioral_update_operator.get("status")
        != "behavioral_update_candidate_blocked_pending_holdout"
    ):
        raise ValueError(
            "behavioral_update_operator.status must be "
            "behavioral_update_candidate_blocked_pending_holdout"
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
    if mechanism_ablation_report.get("status") != "mechanism_ablation_diagnostic_only":
        raise ValueError(
            "mechanism_ablation_report.status must be "
            "mechanism_ablation_diagnostic_only"
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


def _validate_operator_holdout_validation(
    operator_holdout_validation: dict[str, Any],
) -> None:
    if (
        operator_holdout_validation.get("schema_version")
        != R6_OPERATOR_HOLDOUT_VALIDATION_SCHEMA_VERSION
    ):
        raise ValueError(
            "operator_holdout_validation.schema_version must be "
            f"{R6_OPERATOR_HOLDOUT_VALIDATION_SCHEMA_VERSION}"
        )
    if (
        operator_holdout_validation.get("status")
        != "operator_holdout_validation_failed_current_public_proxies"
    ):
        raise ValueError(
            "operator_holdout_validation.status must be "
            "operator_holdout_validation_failed_current_public_proxies"
        )
    acceptance_gates = operator_holdout_validation.get("acceptance_gates")
    if not isinstance(acceptance_gates, dict):
        raise ValueError(
            "operator_holdout_validation.acceptance_gates must be a JSON object"
        )
    if acceptance_gates.get("runtime_default_allowed") is not False:
        raise ValueError(
            "operator_holdout_validation.acceptance_gates."
            "runtime_default_allowed must be False"
        )
    if acceptance_gates.get("field_outcome_validated") is not False:
        raise ValueError(
            "operator_holdout_validation.acceptance_gates."
            "field_outcome_validated must be False"
        )


def _risk_flags(
    *,
    mechanism_ablation_report: dict[str, Any],
    operator_holdout_validation: dict[str, Any],
) -> list[str]:
    return _merge_lists(
        mechanism_ablation_report.get("risk_flags", []),
        operator_holdout_validation.get("risk_flags", []),
        [
            "mechanism_research_diagnostic_only",
            "not_ccf_a_ready",
            "runtime_default_blocked",
        ],
    )


def _blocking_gaps(
    *,
    mechanism_ablation_report: dict[str, Any],
    operator_holdout_validation: dict[str, Any],
) -> list[str]:
    return _merge_lists(
        mechanism_ablation_report.get("blocking_gaps", []),
        operator_holdout_validation.get("blocking_gaps", []),
    )


def _source_refs(*artifacts: dict[str, Any]) -> list[str]:
    refs = []
    for artifact in artifacts:
        artifact_id = artifact.get("artifact_id")
        if artifact_id:
            refs.append(str(artifact_id))
        refs.extend(str(ref) for ref in artifact.get("source_refs", []))
    return list(dict.fromkeys(refs))


def _merge_lists(*values: list[Any]) -> list[str]:
    merged = []
    for value in values:
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, str) or not item:
                continue
            if item not in merged:
                merged.append(item)
    return merged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_mechanism_research_readiness_report(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "mechanism_mvp_result": report["decision"][
                    "mechanism_mvp_result"
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
