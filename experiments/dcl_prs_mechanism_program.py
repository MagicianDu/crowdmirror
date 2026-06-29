from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


MECHANISM_PROGRAM_SCHEMA_VERSION = "dcl-prs-mechanism-program-v1"
MECHANISM_PROGRAM_INDEX_SCHEMA_VERSION = "dcl-prs-mechanism-program-index-v1"


PROGRAM_DEFINITIONS: list[dict[str, Any]] = [
    {
        "program_id": "mechanism-public-health-lower-income-conservative-v1",
        "policy_id": "public_health_medical_insurance_attitude_v1",
        "cohort_selector": {
            "party_or_ideology": "conservative",
            "income": "lower",
        },
        "mechanisms": [
            {
                "name": "direct_benefit_expectation",
                "direction": "increase_support",
                "strength": 0.55,
                "evidence_source": "cohort_material_interest",
            },
            {
                "name": "fiscal_burden_concern",
                "direction": "decrease_support",
                "strength": 0.62,
                "evidence_source": "policy_semantics_and_cohort_prior",
            },
            {
                "name": "public_private_preference",
                "direction": "conditional_support",
                "strength": 0.48,
                "evidence_source": "ideology_prior",
            },
        ],
        "uncertainty": 0.34,
        "mapping_actions": [
            {
                "action_type": "adjust_support_prior",
                "target_response": "government_insurance_plan",
                "signed_delta": -0.07,
                "mechanism_refs": [
                    "fiscal_burden_concern",
                    "public_private_preference",
                ],
            },
            {
                "action_type": "increase_segment_uncertainty",
                "target_segment": "party_or_ideology=conservative|income=lower",
                "signed_delta": 0.04,
                "mechanism_refs": ["direct_benefit_expectation"],
            },
        ],
    },
    {
        "program_id": "mechanism-climate-energy-moderate-middle-income-v1",
        "policy_id": "climate_energy_regulation_attitude_v1",
        "cohort_selector": {
            "party_or_ideology": "moderate",
            "income": "middle",
        },
        "mechanisms": [
            {
                "name": "environmental_risk_salience",
                "direction": "increase_support",
                "strength": 0.58,
                "evidence_source": "policy_semantics_and_public_risk_frame",
            },
            {
                "name": "energy_cost_exposure",
                "direction": "decrease_support",
                "strength": 0.51,
                "evidence_source": "cohort_material_interest",
            },
            {
                "name": "government_regulation_trust",
                "direction": "increase_uncertainty",
                "strength": 0.42,
                "evidence_source": "institutional_trust_prior",
            },
        ],
        "uncertainty": 0.29,
        "mapping_actions": [
            {
                "action_type": "adjust_support_prior",
                "target_response": "support_more_regulation_or_spending",
                "signed_delta": 0.05,
                "mechanism_refs": ["environmental_risk_salience"],
            },
            {
                "action_type": "hold_anchor_for_segment",
                "target_segment": "party_or_ideology=moderate|income=middle",
                "signed_delta": 0.0,
                "mechanism_refs": [
                    "energy_cost_exposure",
                    "government_regulation_trust",
                ],
            },
        ],
    },
]


def build_mechanism_program_index(*, artifact_id: str) -> dict[str, Any]:
    programs = [_build_program(definition) for definition in PROGRAM_DEFINITIONS]
    index = {
        "schema_version": MECHANISM_PROGRAM_INDEX_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "mechanism_programs_ready_for_l0_gate",
        "program_count": len(programs),
        "program_ids": [program["program_id"] for program in programs],
        "policy_ids": [program["policy_id"] for program in programs],
        "mechanism_count": sum(len(program["mechanisms"]) for program in programs),
        "programs": programs,
        "next_gate": "run_mechanism_ablation_matrix",
        "risk_flags": [
            "deterministic_l0_programs_only",
            "mechanism_ablation_not_run",
            "not_prediction_quality_evidence",
            "not_llm_generated_runtime_evidence",
        ],
        "claim_boundary": {
            "ccf_a_claim_status": "not_claimable",
            "product_claim_status": "not_runtime_ready",
            "summary": (
                "Mechanism programs are structured intermediate hypotheses. "
                "They require ablation, repeat validation, and product runtime "
                "evidence before any stronger claim."
            ),
        },
    }
    _assert_strict_json(index)
    return index


def write_mechanism_program_index(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-mechanism-program-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    index = build_mechanism_program_index(artifact_id=artifact_id)
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(index, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "index": index}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_mechanism_program",
    )
    parser.add_argument("--artifact-id", default="dcl-prs-mechanism-program-current-001")
    args = parser.parse_args()

    written = write_mechanism_program_index(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "program_count": written["index"]["program_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _build_program(definition: dict[str, Any]) -> dict[str, Any]:
    program = {
        "schema_version": MECHANISM_PROGRAM_SCHEMA_VERSION,
        "program_id": definition["program_id"],
        "policy_id": definition["policy_id"],
        "cohort_selector": definition["cohort_selector"],
        "mechanisms": definition["mechanisms"],
        "uncertainty": definition["uncertainty"],
        "mapping_actions": definition["mapping_actions"],
        "risk_flags": [
            "deterministic_l0_program",
            "mechanism_strength_not_learned",
            "requires_ablation_validation",
        ],
        "claim_boundary": {
            "prediction_quality_status": "not_validated",
            "uses_test_split_for_current_claim": False,
            "summary": (
                "This mechanism program is a structured hypothesis and not a "
                "validated prediction or product report."
            ),
        },
    }
    _validate_program(program)
    return program


def _validate_program(program: dict[str, Any]) -> None:
    if not program["mechanisms"]:
        raise ValueError("mechanisms must not be empty")
    for mechanism in program["mechanisms"]:
        direction = mechanism["direction"]
        if direction not in {
            "increase_support",
            "decrease_support",
            "conditional_support",
            "increase_uncertainty",
        }:
            raise ValueError("unsupported mechanism direction")
        strength = mechanism["strength"]
        if not 0.0 <= strength <= 1.0:
            raise ValueError("mechanism strength must be within [0, 1]")
    for action in program["mapping_actions"]:
        if action["action_type"] not in {
            "adjust_support_prior",
            "increase_segment_uncertainty",
            "hold_anchor_for_segment",
        }:
            raise ValueError("unsupported mapping action")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
