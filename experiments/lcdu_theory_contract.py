from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


THEORY_CONTRACT_SCHEMA_VERSION = "lcdu-theory-contract-v1"
LCDU_METHOD_SUMMARY_SCHEMA_VERSION = "policy-reaction-lcdu-l3-method-summary-v1"


FORMAL_OBJECTS = [
    {
        "object_id": "simulator_state_theta",
        "definition": "Accepted simulator state, including model, prompts, anchors, response contract, and calibration context.",
        "artifact_surface": "Product cohort manifest and LCDU candidate prompt components.",
        "required_artifact_fields": [
            "model",
            "scale",
            "candidate_prompt_components",
            "calibration_context",
        ],
    },
    {
        "object_id": "segment_space_s",
        "definition": "Public-data segment space used to aggregate simulated and target policy responses.",
        "artifact_surface": "Segment predictions and official segment benchmark metrics.",
        "required_artifact_fields": [
            "segment_predictions",
            "segment_metrics",
            "segment_schema",
        ],
    },
    {
        "object_id": "policy_option_space_p",
        "definition": "Finite policy option set over which the simulator returns strict JSON probabilities.",
        "artifact_surface": "Policy probability keys in Product predictions and target distributions.",
        "required_artifact_fields": [
            "policy_probabilities",
            "official_distribution",
            "predicted_distribution",
        ],
    },
    {
        "object_id": "target_distribution_p_star",
        "definition": "Public survey or public-use microdata target distribution for each segment.",
        "artifact_surface": "Official public-data benchmark artifacts.",
        "required_artifact_fields": [
            "source_ingestion_artifact_id",
            "official_distribution",
            "claim_boundary",
        ],
    },
    {
        "object_id": "simulator_distribution_q_theta",
        "definition": "LLM simulator output distribution after parsing and aggregation.",
        "artifact_surface": "Product segment prediction artifact and official benchmark prediction fields.",
        "required_artifact_fields": [
            "prediction_artifact_id",
            "predicted_distribution",
            "segment_predictions",
        ],
    },
    {
        "object_id": "residual_signature_r",
        "definition": "Difference between target and simulator distributions, summarized by segment and axis diagnostics.",
        "artifact_surface": "Axis weakness and residual weakness artifacts.",
        "required_artifact_fields": [
            "persistent_weakness",
            "weakness_summary",
            "aggregate_axis_summary",
        ],
    },
    {
        "object_id": "lcdu_update_candidate_u",
        "definition": "Structured update candidate composed of latent factors, constraint program, segment guard, and prompt-anchor realization.",
        "artifact_surface": "LCDU/S2PC-compatible candidate artifact.",
        "required_artifact_fields": [
            "candidate_id",
            "source_split_contract",
            "best_candidate",
            "candidate_prompt_components",
        ],
    },
    {
        "object_id": "split_gated_acceptance",
        "definition": "Calibration split generates candidates; held-out and test split decide acceptance and paper claims.",
        "artifact_surface": "Gate, runtime effect, stability, method summary, and paper gate artifacts.",
        "required_artifact_fields": [
            "source_split_contract",
            "initial_loss",
            "best_loss",
            "final_loss",
            "candidate_accepted_count",
            "candidate_rejected_count",
        ],
    },
]


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_lcdu_theory_contract(
    *,
    artifact_id: str,
    method_summary: dict[str, Any],
    theory_ref: str,
    algorithm_ref: str,
) -> dict[str, Any]:
    _validate_method_summary(method_summary)
    contract = {
        "schema_version": THEORY_CONTRACT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "formal_objects_mapped",
        "method_id": method_summary["method_id"],
        "method_summary_artifact_id": method_summary["artifact_id"],
        "theory_ref": theory_ref,
        "algorithm_ref": algorithm_ref,
        "formal_object_count": len(FORMAL_OBJECTS),
        "formal_objects": FORMAL_OBJECTS,
        "closed_gate_ids": ["complete_lcdu_theory_contract"],
        "remaining_theory_risks": [
            "semantic_factor_extractor_consistency_unproven",
            "constraint_builder_transferability_unproven",
            "cross_task_generalization_bound_missing",
        ],
        "claim_boundary": (
            "LCDU theory contract maps formal objects to current artifacts; it is "
            "not a proof of cross-task validity."
        ),
    }
    _assert_strict_json(contract)
    return contract


def write_lcdu_theory_contract(
    *,
    output: str | Path,
    artifact_id: str,
    method_summary_path: str | Path,
    theory_ref: str,
    algorithm_ref: str,
) -> dict[str, Any]:
    contract = build_lcdu_theory_contract(
        artifact_id=artifact_id,
        method_summary=load_json_artifact(method_summary_path),
        theory_ref=theory_ref,
        algorithm_ref=algorithm_ref,
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(contract, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return contract


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--method-summary",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-lcdu-l3-method-summary-current-001.json"
        ),
    )
    parser.add_argument(
        "--output",
        default="experiments/results/lcdu_theory/lcdu-theory-contract-current-001.json",
    )
    parser.add_argument("--artifact-id", default="lcdu-theory-contract-current-001")
    parser.add_argument("--theory-ref", default="paper/LCDU_THEORY.md")
    parser.add_argument("--algorithm-ref", default="paper/LCDU_ALGORITHM.md")
    args = parser.parse_args()
    contract = write_lcdu_theory_contract(
        output=args.output,
        artifact_id=args.artifact_id,
        method_summary_path=args.method_summary,
        theory_ref=args.theory_ref,
        algorithm_ref=args.algorithm_ref,
    )
    print(
        json.dumps(
            {
                "artifact_id": contract["artifact_id"],
                "formal_object_count": contract["formal_object_count"],
                "output": args.output,
                "overall_status": contract["overall_status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_method_summary(method_summary: dict[str, Any]) -> None:
    if method_summary.get("schema_version") != LCDU_METHOD_SUMMARY_SCHEMA_VERSION:
        raise ValueError("method_summary has unsupported schema_version")
    for field_name in (
        "artifact_id",
        "method_id",
        "accepted_candidate_ids",
        "evidence",
        "claim_boundaries",
    ):
        if field_name not in method_summary:
            raise ValueError(f"method_summary missing {field_name}")
    evidence = method_summary["evidence"]
    if not isinstance(evidence, dict):
        raise ValueError("method_summary evidence must be an object")
    for field_name in ("stability", "mechanism", "route_coverage", "residual_weakness"):
        if field_name not in evidence:
            raise ValueError(f"method_summary evidence missing {field_name}")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU theory contract must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
