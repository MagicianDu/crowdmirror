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


R6_OUTCOME_HOLDOUT_REGISTRY_SCHEMA_VERSION = "r6-outcome-holdout-registry-v1"


def build_r6_outcome_holdout_registry(*, artifact_id: str, run_id: str) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    outcome_entries = [
        {
            "source_key": "htops_cost_pressure",
            "outcome_type": "public_proxy",
            "independence_level": "out_of_family_non_regression_proxy",
            "case_family": "htops_cost_pressure",
            "in_condition_holdout": False,
            "field_outcome_validated": False,
            "accepted_for_generalization": False,
        },
        {
            "source_key": "anes_health_heldout",
            "outcome_type": "public_proxy",
            "independence_level": "source_case_proxy",
            "case_family": "anes_health",
            "in_condition_holdout": False,
            "field_outcome_validated": False,
            "accepted_for_generalization": False,
        },
        {
            "source_key": "anes_climate_heldout",
            "outcome_type": "public_proxy",
            "independence_level": "same_source_out_of_condition_proxy",
            "case_family": "anes_climate",
            "in_condition_holdout": False,
            "field_outcome_validated": False,
            "accepted_for_generalization": False,
        },
    ]
    missing_required_slots = [
        {
            "slot_id": "independent_same_family_in_condition_holdout",
            "status": "missing",
        },
        {
            "slot_id": "independent_supported_signal_holdout",
            "status": "missing",
        },
        {
            "slot_id": "real_field_outcome",
            "status": "missing",
        },
    ]
    registry = {
        "schema_version": R6_OUTCOME_HOLDOUT_REGISTRY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "holdout_registry_ready_missing_required_slots",
        "outcome_entries": outcome_entries,
        "registry_summary": {
            "registered_outcome_count": len(outcome_entries),
            "independent_public_proxy_count": 0,
            "field_outcome_count": 0,
            "missing_required_slot_count": len(missing_required_slots),
            "in_condition_independent_holdout_available": False,
        },
        "missing_required_slots": missing_required_slots,
        "acceptance_gates": {
            "holdout_registry_present": True,
            "independent_holdout_missing_slots_visible": True,
            "field_outcome_validated": False,
        },
        "blocking_gaps": [
            "needs_independent_same_family_operator_holdout",
            "needs_independent_supported_signal_holdout",
            "needs_real_or_field_outcome_proxy",
        ],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            (
                "Current HTOPS and ANES proxies are registered for gap tracking "
                "only; they are not independent field validation and do not "
                "permit runtime default enablement."
            ),
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "independent_holdout_missing",
            "field_outcome_missing",
            "not_runtime_default",
        ],
    }
    assert_strict_json(registry)
    return registry


def write_r6_outcome_holdout_registry(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_outcome_holdout_registry(**kwargs))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_outcome_holdout_registry(
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
