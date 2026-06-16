from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_behavioral_update_operator_v2 import (
    build_r6_behavioral_update_operator_v2,
)
from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_outcome_holdout_registry import (
    build_r6_outcome_holdout_registry,
)
from experiments.r6_theory_framework import build_r6_theory_framework


R6_GAP_CLOSURE_REPORT_SCHEMA_VERSION = "r6-gap-closure-report-v1"


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
    for field, artifact in (
        ("theory_framework", theory_framework),
        ("holdout_registry", holdout_registry),
        ("operator_v2", operator_v2),
    ):
        if not isinstance(artifact, dict):
            raise ValueError(f"{field} must be a JSON object")
        non_empty_string(artifact.get("artifact_id"), field=f"{field}.artifact_id")

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
            theory_framework["artifact_id"],
            holdout_registry["artifact_id"],
            operator_v2["artifact_id"],
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
    for artifact in (holdout_registry, operator_v2):
        blocking_gaps = artifact.get("blocking_gaps", [])
        if not isinstance(blocking_gaps, list):
            raise ValueError("blocking_gaps must be a list")
        for gap in blocking_gaps:
            gaps.append(non_empty_string(gap, field="blocking_gaps[]"))
    return sorted(set(gaps))


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
