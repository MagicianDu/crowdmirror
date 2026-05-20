from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_s2pc_selector_redesign(
    *,
    family_narrowing: dict[str, Any],
    selector_free_robustness: dict[str, Any],
    sparse_subset_matrix: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_schema(
        family_narrowing,
        "policy-reaction-s2pc-l1-family-narrowing-v1",
        "family_narrowing",
    )
    _validate_schema(
        selector_free_robustness,
        "policy-reaction-s2pc-selector-free-robustness-v1",
        "selector_free_robustness",
    )
    _validate_schema(
        sparse_subset_matrix,
        "policy-reaction-s2pc-runtime-effect-matrix-v1",
        "sparse_subset_matrix",
    )
    direct_mixed = selector_free_robustness.get("overall_status") != "stable_improvement"
    sparse_failed = sparse_subset_matrix.get("improved_count", 0) == 0
    best_sparse_candidate_id = sparse_subset_matrix.get("best_candidate_id")
    if direct_mixed and sparse_failed:
        overall_status = "abstain"
        recommended_selector_policy_id = None
        recommended_candidate_id = None
        abstain_reason = (
            "current_direct_selector_not_robust_and_sparse_subsets_all_regressed"
        )
        selector_transition = "keep_abstain"
    elif direct_mixed:
        overall_status = "proceed_with_sparse_selector"
        recommended_selector_policy_id = "sparse_subset_best_runtime_effect"
        recommended_candidate_id = best_sparse_candidate_id
        abstain_reason = None
        selector_transition = "redirect_from_direct_to_sparse_subset"
    else:
        overall_status = "proceed"
        recommended_selector_policy_id = selector_free_robustness.get("selector_policy_id")
        recommended_candidate_id = selector_free_robustness.get("selected_candidate_id")
        abstain_reason = None
        selector_transition = "keep_direct_selector"
    artifact = {
        "schema_version": "policy-reaction-s2pc-selector-redesign-v1",
        "artifact_id": artifact_id,
        "overall_status": overall_status,
        "recommended_selector_policy_id": recommended_selector_policy_id,
        "recommended_candidate_id": recommended_candidate_id,
        "abstain_reason": abstain_reason,
        "family_narrowing_artifact_id": family_narrowing.get("artifact_id"),
        "selector_free_robustness_artifact_id": selector_free_robustness.get(
            "artifact_id"
        ),
        "sparse_subset_matrix_artifact_id": sparse_subset_matrix.get("artifact_id"),
        "selector_transition": selector_transition,
        "sparse_subset_improved_count": sparse_subset_matrix.get("improved_count"),
        "sparse_subset_regressed_count": sparse_subset_matrix.get("regressed_count"),
        "sparse_subset_best_candidate_id": best_sparse_candidate_id,
        "claim_boundaries": [
            "Selector redesign is a decision artifact over current held-out evidence, not a proof of model validity.",
            "If direct selector robustness is mixed but sparse subset search yields a held-out improvement, prefer the best sparse subset candidate.",
            "If sparse subset search has no held-out improvement, abstain rather than deploy a weak direct selector.",
        ],
        "claim_boundary": (
            "Selector redesign is a decision artifact over current evidence, not a proof of model validity."
        ),
    }
    json.dumps(artifact, allow_nan=False)
    return artifact


def write_policy_reaction_s2pc_selector_redesign(
    path: str | Path,
    *,
    family_narrowing_path: str | Path,
    selector_free_robustness_path: str | Path,
    sparse_subset_matrix_path: str | Path,
    artifact_id: str,
) -> Path:
    artifact = build_policy_reaction_s2pc_selector_redesign(
        family_narrowing=load_json_artifact(family_narrowing_path),
        selector_free_robustness=load_json_artifact(selector_free_robustness_path),
        sparse_subset_matrix=load_json_artifact(sparse_subset_matrix_path),
        artifact_id=artifact_id,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family-narrowing", required=True)
    parser.add_argument("--selector-free-robustness", required=True)
    parser.add_argument("--sparse-subset-matrix", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-s2pc-selector-redesign-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-s2pc-selector-redesign-current-001.json"
        ),
    )
    args = parser.parse_args()
    output_path = write_policy_reaction_s2pc_selector_redesign(
        args.output,
        family_narrowing_path=args.family_narrowing,
        selector_free_robustness_path=args.selector_free_robustness,
        sparse_subset_matrix_path=args.sparse_subset_matrix,
        artifact_id=args.artifact_id,
    )
    artifact = load_json_artifact(output_path)
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["overall_status"],
                "recommended_selector_policy_id": artifact[
                    "recommended_selector_policy_id"
                ],
                "recommended_candidate_id": artifact["recommended_candidate_id"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_schema(payload: dict[str, Any], expected: str, label: str) -> None:
    if payload.get("schema_version") != expected:
        raise ValueError(f"{label} has unsupported schema_version")


if __name__ == "__main__":
    raise SystemExit(main())
