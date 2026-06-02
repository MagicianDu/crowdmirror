from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FAILURE_ATTRIBUTION_INDEX_SCHEMA_VERSION = "dcl-prs-failure-attribution-index-v1"

ERROR_TYPES = [
    "persona_mispecified",
    "policy_semantics_misread",
    "mechanism_missing",
    "mechanism_direction_wrong",
    "cohort_weight_wrong",
    "interaction_path_missing",
    "over_shrinkage",
    "under_shrinkage",
    "anchor_should_hold",
]

ATTRIBUTION_DEFINITIONS: list[dict[str, Any]] = [
    {
        "task_id": "climate_energy_regulation_attitude_v1",
        "segment_key": "party_or_ideology=moderate|income=middle",
        "observed_failure": {
            "failure_family": "segment_gate_not_better_than_fixed_party_prior",
            "loss_direction": "candidate_worse_than_strong_baseline",
            "worst_segment_regression": True,
        },
        "error_attribution": [
            {
                "type": "mechanism_direction_wrong",
                "confidence": 0.62,
                "reason": (
                    "Environmental risk salience and energy cost exposure were "
                    "not balanced at segment level."
                ),
            },
            {
                "type": "anchor_should_hold",
                "confidence": 0.54,
                "reason": "Historical SG diagnostics suggest this segment is harmed by shrinkage.",
            },
        ],
        "repair_candidates": [
            {
                "repair_id": "repair-climate-moderate-mechanism-rebalance-v1",
                "action": "rebalance_mechanism_strength",
                "target": "environmental_risk_salience",
                "signed_delta": 0.12,
                "acceptance_gate": "heldout_repeat_gate",
            },
            {
                "repair_id": "repair-climate-moderate-anchor-fallback-v1",
                "action": "fallback_anchor",
                "target": "party_or_ideology=moderate|income=middle",
                "signed_delta": 0.0,
                "acceptance_gate": "heldout_repeat_gate",
            },
        ],
    },
    {
        "task_id": "public_health_medical_insurance_attitude_v1",
        "segment_key": "party_or_ideology=conservative|income=lower",
        "observed_failure": {
            "failure_family": "test_worst_segment_guard_failed",
            "loss_direction": "local_worst_segment_worse_than_anchor",
            "worst_segment_regression": True,
        },
        "error_attribution": [
            {
                "type": "mechanism_missing",
                "confidence": 0.59,
                "reason": (
                    "Direct benefit expectation was present but uncertainty from "
                    "policy implementation trust was not represented."
                ),
            },
            {
                "type": "over_shrinkage",
                "confidence": 0.57,
                "reason": "The SG route accepted shrinkage while local segment evidence was weak.",
            },
        ],
        "repair_candidates": [
            {
                "repair_id": "repair-health-conservative-uncertainty-v1",
                "action": "increase_uncertainty",
                "target": "implementation_trust_uncertainty",
                "signed_delta": 0.08,
                "acceptance_gate": "heldout_repeat_gate",
            },
            {
                "repair_id": "repair-health-conservative-switch-family-v1",
                "action": "switch_candidate_family",
                "target": "income_prior_k_10",
                "signed_delta": 0.0,
                "acceptance_gate": "heldout_repeat_gate",
            },
        ],
    },
]


def build_failure_attribution_index(*, artifact_id: str) -> dict[str, Any]:
    attributions = [_build_attribution(definition) for definition in ATTRIBUTION_DEFINITIONS]
    repair_candidate_count = sum(
        len(attribution["repair_candidates"]) for attribution in attributions
    )
    index = {
        "schema_version": FAILURE_ATTRIBUTION_INDEX_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "failure_attribution_ready_for_l0_gate",
        "error_taxonomy": ERROR_TYPES,
        "attribution_count": len(attributions),
        "repair_candidate_count": repair_candidate_count,
        "attributions": attributions,
        "next_gate": "run_repair_repeat_acceptance_matrix",
        "risk_flags": [
            "deterministic_l0_attribution_only",
            "repair_candidates_not_accepted_yet",
            "no_test_split_closed_loop",
            "not_prediction_quality_evidence",
        ],
        "claim_boundary": {
            "ccf_a_claim_status": "not_claimable",
            "product_claim_status": "not_runtime_ready",
            "uses_test_split_for_current_claim": False,
            "summary": (
                "Failure attribution records candidate error causes and repair "
                "actions. Repairs must pass heldout/repeat gates before use."
            ),
        },
    }
    _assert_strict_json(index)
    return index


def write_failure_attribution_index(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-failure-attribution-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    index = build_failure_attribution_index(artifact_id=artifact_id)
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(index, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "index": index}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_failure_attribution",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-failure-attribution-current-001",
    )
    args = parser.parse_args()

    written = write_failure_attribution_index(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "attribution_count": written["index"]["attribution_count"],
                "index": written["index_path"],
                "repair_candidate_count": written["index"]["repair_candidate_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _build_attribution(definition: dict[str, Any]) -> dict[str, Any]:
    attribution = {
        "task_id": definition["task_id"],
        "segment_key": definition["segment_key"],
        "observed_failure": definition["observed_failure"],
        "error_attribution": definition["error_attribution"],
        "repair_candidates": definition["repair_candidates"],
        "claim_boundary": {
            "uses_test_split_for_current_claim": False,
            "acceptance_required_before_use": True,
        },
    }
    _validate_attribution(attribution)
    return attribution


def _validate_attribution(attribution: dict[str, Any]) -> None:
    for error in attribution["error_attribution"]:
        if error["type"] not in ERROR_TYPES:
            raise ValueError("unsupported error attribution type")
        if not 0.0 <= error["confidence"] <= 1.0:
            raise ValueError("error confidence must be within [0, 1]")
    for repair in attribution["repair_candidates"]:
        if repair["acceptance_gate"] != "heldout_repeat_gate":
            raise ValueError("repair candidates must use heldout_repeat_gate")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
