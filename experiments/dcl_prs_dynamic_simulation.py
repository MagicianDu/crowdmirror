from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.dcl_prs_mechanism_program import (  # noqa: E402
    build_mechanism_program_index,
)


DYNAMIC_SIMULATION_SCHEMA_VERSION = "dcl-prs-dynamic-simulation-trace-v1"


def build_dynamic_simulation_trace(
    *,
    artifact_id: str,
    mechanism_program_index: dict[str, Any],
) -> dict[str, Any]:
    _validate_mechanism_program_index(mechanism_program_index)
    time_steps = _build_time_steps(mechanism_program_index["programs"])
    trace = {
        "schema_version": DYNAMIC_SIMULATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "dynamic_trace_ready_for_l0_gate",
        "mechanism_program_refs": mechanism_program_index["program_ids"],
        "population": {
            "agent_count": 1000,
            "cohort_schema": [
                "party_or_ideology",
                "income",
                "age_group",
                "education",
            ],
            "population_status": "cohort_level_synthetic_l0",
        },
        "interaction_model": {
            "network_type": "cohort_mixing",
            "influence_sources": [
                "policy_institution_frame",
                "media_frame",
                "peer_discussion",
            ],
            "llm_agent_calls": 0,
            "update_rule": "deterministic_mechanism_weighted_shift",
        },
        "time_step_count": len(time_steps),
        "time_steps": time_steps,
        "next_gate": "run_product_cohort_report_evidence",
        "risk_flags": [
            "deterministic_l0_trace_only",
            "not_field_validated",
            "no_real_social_network_loaded",
            "not_population_scale_proof",
        ],
        "claim_boundary": {
            "simulation_status": "exploratory_not_field_validated",
            "ccf_a_claim_status": "not_claimable",
            "product_claim_status": "cohort_report_pending",
            "summary": (
                "Dynamic simulation trace is bounded and reproducible, but it "
                "is not calibrated against temporal field data."
            ),
        },
    }
    _assert_strict_json(trace)
    return trace


def write_dynamic_simulation_trace(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-dynamic-simulation-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    mechanism_program_index = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-current-001"
    )
    trace = build_dynamic_simulation_trace(
        artifact_id=artifact_id,
        mechanism_program_index=mechanism_program_index,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(trace, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "trace": trace}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_dynamic_simulation",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-dynamic-simulation-current-001",
    )
    args = parser.parse_args()

    written = write_dynamic_simulation_trace(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "time_step_count": written["trace"]["time_step_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _build_time_steps(programs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    net_shift = _net_support_shift(programs)
    uncertainty = sum(program["uncertainty"] for program in programs) / len(programs)
    base_support = 0.5
    base_polarization = 0.16
    steps = []
    for t in range(4):
        support = _clamp(base_support + net_shift * (t / 3.0))
        polarization = _clamp(base_polarization + uncertainty * 0.18 * (t / 3.0))
        volatility = _clamp(abs(net_shift) * 0.6 + uncertainty * 0.12 * (t / 3.0))
        steps.append(
            {
                "t": t,
                "aggregate_support": round(support, 12),
                "polarization_index": round(polarization, 12),
                "volatility_index": round(volatility, 12),
                "state_status": "bounded_deterministic_l0",
            }
        )
    return steps


def _net_support_shift(programs: list[dict[str, Any]]) -> float:
    shift = 0.0
    mechanism_count = 0
    for program in programs:
        for mechanism in program["mechanisms"]:
            mechanism_count += 1
            direction = mechanism["direction"]
            strength = mechanism["strength"]
            if direction == "increase_support":
                shift += strength
            elif direction == "decrease_support":
                shift -= strength
            elif direction == "conditional_support":
                shift += strength * 0.15
            elif direction == "increase_uncertainty":
                shift -= strength * 0.05
    return shift / max(mechanism_count, 1) * 0.18


def _validate_mechanism_program_index(index: dict[str, Any]) -> None:
    if index.get("schema_version") != "dcl-prs-mechanism-program-index-v1":
        raise ValueError("mechanism_program_index has unsupported schema_version")
    if not index.get("programs"):
        raise ValueError("mechanism_program_index must contain programs")


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
