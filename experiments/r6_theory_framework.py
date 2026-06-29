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


R6_THEORY_FRAMEWORK_SCHEMA_VERSION = "r6-theory-framework-v1"


def build_r6_theory_framework(*, artifact_id: str, run_id: str) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    report = {
        "schema_version": R6_THEORY_FRAMEWORK_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "theory_framework_ready",
        "formal_problem": {
            "static_prior_role": "simulation_foundation",
            "interaction_role": "risk_discovery_layer",
            "operator_definition": (
                "Interaction operates as a guarded update operator over a "
                "static-prior simulation baseline, surfacing auditable cases "
                "where local propagation evidence may recover static-prior miss."
            ),
            "guarded_decision_rule": (
                "Accept interaction evidence only when it improves recoverable "
                "risk discovery after false-alarm, guard-violation, and overfit "
                "penalties; otherwise keep the static prior as the decision base."
            ),
        },
        "risk_discovery_value_function": {
            "formula": (
                "recovered_static_prior_miss - false_alarm_penalty "
                "- guard_violation_penalty - overfit_penalty"
            ),
            "optimization_target": "auditable_risk_discovery_not_raw_accuracy_superiority",
        },
        "error_attribution_components": [
            "static_prior_miss",
            "propagation_direction_error",
            "over_amplification",
            "under_diffusion",
            "topology_mismatch",
            "outcome_mapping_noise",
        ],
        "acceptance_gates": {
            "formal_problem_definition_present": True,
            "risk_discovery_value_defined": True,
            "error_attribution_defined": True,
            "runtime_default_allowed": False,
            "field_outcome_validated": False,
        },
        "blocked_claims": [
            "accuracy superiority is not established by this theory framework",
            "field validated evidence is not present",
            "runtime default enablement is blocked",
        ],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            (
                "This theory framework defines a research artifact for guarded "
                "risk discovery; it is not CCF-A readiness, field validation, "
                "or runtime default approval."
            ),
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "not_accuracy_superiority_evidence",
            "not_field_validated",
            "not_runtime_default",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_theory_framework(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_theory_framework(**kwargs))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_theory_framework(
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
