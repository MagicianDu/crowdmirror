from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_behavioral_update_operator_v2 import (
    R6_BEHAVIORAL_UPDATE_OPERATOR_V2_SCHEMA_VERSION,
    R6_BEHAVIORAL_UPDATE_OPERATOR_V2_STATUS,
    R6_OPERATOR_V2_BLOCKING_GAPS,
    build_r6_behavioral_update_operator_v2,
)
from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_outcome_holdout_registry import (
    R6_OUTCOME_HOLDOUT_REGISTRY_SCHEMA_VERSION,
    build_r6_outcome_holdout_registry,
)
from experiments.r6_theory_framework import (
    R6_THEORY_FRAMEWORK_SCHEMA_VERSION,
    build_r6_theory_framework,
)


R6_GAP_CLOSURE_REPORT_SCHEMA_VERSION = "r6-gap-closure-report-v1"
R6_REGISTRY_REQUIRED_BLOCKING_GAPS = [
    "needs_independent_same_family_operator_holdout",
    "needs_independent_supported_signal_holdout",
    "needs_real_or_field_outcome_proxy",
]


def build_r6_gap_closure_report(
    *,
    artifact_id: str,
    run_id: str,
    theory_framework: dict[str, Any] | None = None,
    holdout_registry: dict[str, Any] | None = None,
    operator_v2: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    if theory_framework is None:
        theory_framework = build_r6_theory_framework(
            artifact_id=f"{artifact_id}-theory-framework",
            run_id=run_id,
        )
    if holdout_registry is None:
        holdout_registry = build_r6_outcome_holdout_registry(
            artifact_id=f"{artifact_id}-outcome-holdout-registry",
            run_id=run_id,
        )
    if operator_v2 is None:
        operator_v2 = build_r6_behavioral_update_operator_v2(
            artifact_id=f"{artifact_id}-behavioral-update-operator-v2",
            run_id=run_id,
            holdout_registry=holdout_registry,
            theory_framework=theory_framework,
        )
    theory_ref = _validate_theory_framework(theory_framework)
    registry_ref = _validate_holdout_registry(holdout_registry)
    operator_ref = _validate_operator_v2(operator_v2)

    report = {
        "schema_version": R6_GAP_CLOSURE_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "gap_closure_artifact_ready",
        "gap_statuses": {
            "theory_gap": "closed_by_artifact",
            "data_holdout_gap": "blocked_missing_data",
            "method_operator_gap": "partial_diagnostic",
            "product_gap": "closed_by_guarded_cards",
        },
        "acceptance_gates": {
            "formal_problem_definition_present": True,
            "risk_discovery_value_defined": True,
            "holdout_registry_present": True,
            "independent_holdout_missing_slots_visible": True,
            "operator_v2_structured": True,
            "operator_v2_runtime_default_allowed": False,
            "gap_closure_report_present": True,
            "product_gap_cards_required": True,
            "ccf_a_main_contribution_ready": False,
            "field_outcome_validated": False,
        },
        "remaining_gaps": _remaining_gaps(
            holdout_registry=holdout_registry,
            operator_v2=operator_v2,
        ),
        "source_refs": [
            theory_ref,
            registry_ref,
            operator_ref,
        ],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            (
                "This gap closure report closes only the artifact packaging "
                "gaps for theory framing, holdout registry visibility, "
                "operator-v2 structure, and guarded product cards; empirical "
                "validation gaps remain open."
            ),
            (
                "It does not establish CCF-A main contribution readiness, "
                "field outcome validation, Product runtime default enablement, "
                "or accuracy superiority."
            ),
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "blocked_claims": [
            "ccf_a_main_contribution_ready",
            "field_outcome_validated",
            "runtime_default_allowed",
            "accuracy_superiority_established",
        ],
        "risk_flags": [
            "empirical_gaps_open",
            "independent_holdout_missing",
            "field_outcome_missing",
            "operator_v2_diagnostic_only",
            "not_runtime_default",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_gap_closure_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_gap_closure_report(**kwargs))


def _remaining_gaps(
    *,
    holdout_registry: dict[str, Any],
    operator_v2: dict[str, Any],
) -> list[str]:
    gaps = []
    for field, artifact in (
        ("holdout_registry", holdout_registry),
        ("operator_v2", operator_v2),
    ):
        blocking_gaps = _blocking_gaps(artifact, field=f"{field}.blocking_gaps")
        for gap in blocking_gaps:
            gaps.append(non_empty_string(gap, field=f"{field}.blocking_gaps[]"))
    remaining_gaps = sorted(set(gaps))
    required = set(R6_REGISTRY_REQUIRED_BLOCKING_GAPS) | set(R6_OPERATOR_V2_BLOCKING_GAPS)
    missing = sorted(required - set(remaining_gaps))
    if missing:
        raise ValueError(f"remaining_gaps missing required blockers: {missing}")
    return remaining_gaps


def _validate_theory_framework(theory_framework: dict[str, Any]) -> str:
    _require_object(theory_framework, field="theory_framework")
    _require_exact(
        theory_framework,
        field="theory_framework.schema_version",
        expected=R6_THEORY_FRAMEWORK_SCHEMA_VERSION,
    )
    _require_exact(
        theory_framework,
        field="theory_framework.status",
        expected="theory_framework_ready",
    )
    artifact_id = non_empty_string(
        theory_framework.get("artifact_id"),
        field="theory_framework.artifact_id",
    )
    acceptance_gates = _require_object(
        theory_framework.get("acceptance_gates"),
        field="theory_framework.acceptance_gates",
    )
    _require_true(
        acceptance_gates,
        field="theory_framework.acceptance_gates.formal_problem_definition_present",
    )
    _require_true(
        acceptance_gates,
        field="theory_framework.acceptance_gates.risk_discovery_value_defined",
    )
    _require_false(
        acceptance_gates,
        field="theory_framework.acceptance_gates.runtime_default_allowed",
    )
    _require_false(
        acceptance_gates,
        field="theory_framework.acceptance_gates.field_outcome_validated",
    )
    return artifact_id


def _validate_holdout_registry(holdout_registry: dict[str, Any]) -> str:
    _require_object(holdout_registry, field="holdout_registry")
    _require_exact(
        holdout_registry,
        field="holdout_registry.schema_version",
        expected=R6_OUTCOME_HOLDOUT_REGISTRY_SCHEMA_VERSION,
    )
    _require_exact(
        holdout_registry,
        field="holdout_registry.status",
        expected="holdout_registry_ready_missing_required_slots",
    )
    artifact_id = non_empty_string(
        holdout_registry.get("artifact_id"),
        field="holdout_registry.artifact_id",
    )
    acceptance_gates = _require_object(
        holdout_registry.get("acceptance_gates"),
        field="holdout_registry.acceptance_gates",
    )
    _require_true(
        acceptance_gates,
        field="holdout_registry.acceptance_gates.holdout_registry_present",
    )
    _require_true(
        acceptance_gates,
        field=(
            "holdout_registry.acceptance_gates."
            "independent_holdout_missing_slots_visible"
        ),
    )
    _require_false(
        acceptance_gates,
        field="holdout_registry.acceptance_gates.runtime_default_allowed",
    )
    _require_false(
        acceptance_gates,
        field="holdout_registry.acceptance_gates.ccf_a_main_contribution_ready",
    )
    _require_false(
        acceptance_gates,
        field="holdout_registry.acceptance_gates.field_outcome_validated",
    )
    _require_blocking_gaps(
        holdout_registry,
        field="holdout_registry.blocking_gaps",
        required=R6_REGISTRY_REQUIRED_BLOCKING_GAPS,
    )
    return artifact_id


def _validate_operator_v2(operator_v2: dict[str, Any]) -> str:
    _require_object(operator_v2, field="operator_v2")
    _require_exact(
        operator_v2,
        field="operator_v2.schema_version",
        expected=R6_BEHAVIORAL_UPDATE_OPERATOR_V2_SCHEMA_VERSION,
    )
    _require_exact(
        operator_v2,
        field="operator_v2.status",
        expected=R6_BEHAVIORAL_UPDATE_OPERATOR_V2_STATUS,
    )
    artifact_id = non_empty_string(
        operator_v2.get("artifact_id"),
        field="operator_v2.artifact_id",
    )
    acceptance_gates = _require_object(
        operator_v2.get("acceptance_gates"),
        field="operator_v2.acceptance_gates",
    )
    _require_true(
        acceptance_gates,
        field="operator_v2.acceptance_gates.operator_v2_structured",
    )
    _require_false(
        acceptance_gates,
        field="operator_v2.acceptance_gates.operator_v2_runtime_default_allowed",
    )
    _require_false(
        acceptance_gates,
        field="operator_v2.acceptance_gates.independent_holdout_available",
    )
    _require_false(
        acceptance_gates,
        field="operator_v2.acceptance_gates.field_outcome_validated",
    )
    _require_false(
        acceptance_gates,
        field="operator_v2.acceptance_gates.ccf_a_main_contribution_ready",
    )
    _require_blocking_gaps(
        operator_v2,
        field="operator_v2.blocking_gaps",
        required=R6_OPERATOR_V2_BLOCKING_GAPS,
    )
    return artifact_id


def _require_object(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a JSON object")
    return value


def _require_exact(
    artifact: dict[str, Any],
    *,
    field: str,
    expected: str,
) -> None:
    key = field.rsplit(".", maxsplit=1)[-1]
    if artifact.get(key) != expected:
        raise ValueError(f"{field} must be {expected}")


def _require_true(artifact: dict[str, Any], *, field: str) -> None:
    key = field.rsplit(".", maxsplit=1)[-1]
    if artifact.get(key) is not True:
        raise ValueError(f"{field} must be True")


def _require_false(artifact: dict[str, Any], *, field: str) -> None:
    key = field.rsplit(".", maxsplit=1)[-1]
    if artifact.get(key) is not False:
        raise ValueError(f"{field} must be False")


def _require_blocking_gaps(
    artifact: dict[str, Any],
    *,
    field: str,
    required: list[str],
) -> None:
    blocking_gaps = set(_blocking_gaps(artifact, field=field))
    missing = sorted(set(required) - blocking_gaps)
    if missing:
        raise ValueError(f"{field} missing required blockers: {missing}")


def _blocking_gaps(artifact: dict[str, Any], *, field: str) -> list[str]:
    blocking_gaps = artifact.get("blocking_gaps")
    if not isinstance(blocking_gaps, list):
        raise ValueError(f"{field} must be a list")
    return [
        non_empty_string(gap, field=f"{field}[]")
        for gap in blocking_gaps
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_gap_closure_report(
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
