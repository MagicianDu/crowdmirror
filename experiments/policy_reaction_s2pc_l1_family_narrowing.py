from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


S2PC_L1_CANDIDATE_SET_SCHEMA_VERSION = "policy-reaction-s2pc-l1-candidate-set-v1"
S2PC_RUNTIME_EFFECT_MATRIX_SCHEMA_VERSION = (
    "policy-reaction-s2pc-runtime-effect-matrix-v1"
)
S2PC_L1_SEARCH_POLICY_ABLATION_SCHEMA_VERSION = (
    "policy-reaction-s2pc-l1-search-policy-ablation-v1"
)
S2PC_L1_FAMILY_NARROWING_SCHEMA_VERSION = (
    "policy-reaction-s2pc-l1-family-narrowing-v1"
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_s2pc_l1_family_narrowing(
    *,
    candidate_set: dict[str, Any],
    runtime_effect_matrix: dict[str, Any],
    search_policy_ablation: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_candidate_set(candidate_set)
    _validate_runtime_effect_matrix(runtime_effect_matrix)
    _validate_search_policy_ablation(search_policy_ablation)
    candidate_by_id = {
        str(candidate["candidate_id"]): candidate for candidate in candidate_set["candidates"]
    }
    improving_policies = [
        policy
        for policy in search_policy_ablation["policies"]
        if policy.get("overall_status") == "improved"
    ]
    if not improving_policies:
        raise ValueError("family narrowing requires at least one improving policy")

    selected_candidates = [
        candidate_by_id[str(policy["selected_candidate_id"])]
        for policy in improving_policies
        if str(policy["selected_candidate_id"]) in candidate_by_id
    ]
    if not selected_candidates:
        raise ValueError("family narrowing could not resolve selected candidates")

    segment_allowlist = _common_string_values(selected_candidates, "segment")
    policy_allowlist = _common_string_values(selected_candidates, "policy_id")
    max_rank = min(int(candidate["rank"]) for candidate in selected_candidates)
    retained = [
        candidate
        for candidate in candidate_set["candidates"]
        if (
            str(candidate["segment"]) in segment_allowlist
            and str(candidate["policy_id"]) in policy_allowlist
            and int(candidate["rank"]) <= max_rank
        )
    ]
    runtime_losses = {
        str(result["s2pc_candidate_id"]): float(result["s2pc_runtime_loss"])
        for result in runtime_effect_matrix["candidate_results"]
    }
    artifact = {
        "schema_version": S2PC_L1_FAMILY_NARROWING_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "narrowed_family_available",
        "candidate_set_id": candidate_set["candidate_set_id"],
        "runtime_effect_matrix_artifact_id": runtime_effect_matrix["artifact_id"],
        "search_policy_ablation_artifact_id": search_policy_ablation["artifact_id"],
        "narrowing_rules": {
            "segment_allowlist": segment_allowlist,
            "policy_allowlist": policy_allowlist,
            "max_rank": max_rank,
        },
        "retained_candidate_count": len(retained),
        "excluded_candidate_count": len(candidate_set["candidates"]) - len(retained),
        "retained_candidate_ids": [str(candidate["candidate_id"]) for candidate in retained],
        "retained_candidates": [
            {
                "candidate_id": str(candidate["candidate_id"]),
                "rank": int(candidate["rank"]),
                "segment": str(candidate["segment"]),
                "policy_id": str(candidate["policy_id"]),
                "proxy_score": float(candidate["proxy_score"]),
                "runtime_loss": _round_float(
                    runtime_losses[str(candidate["candidate_id"])]
                ),
            }
            for candidate in retained
        ],
        "claim_boundary": (
            "S2PC L1 family narrowing is a retrospective reduction of the current "
            "candidate space based on evaluated evidence; it is not yet a general selector."
        ),
        "claim_boundaries": _unique_strings(
            [
                "Family narrowing preserves only the intersection shared by improving policy slices.",
                *candidate_set.get("claim_boundaries", []),
                *runtime_effect_matrix.get("claim_boundaries", []),
                *search_policy_ablation.get("claim_boundaries", []),
            ]
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_policy_reaction_s2pc_l1_family_narrowing(
    path: str | Path,
    *,
    candidate_set_path: str | Path,
    runtime_effect_matrix_path: str | Path,
    search_policy_ablation_path: str | Path,
    artifact_id: str,
) -> Path:
    artifact = build_policy_reaction_s2pc_l1_family_narrowing(
        candidate_set=load_json_artifact(candidate_set_path),
        runtime_effect_matrix=load_json_artifact(runtime_effect_matrix_path),
        search_policy_ablation=load_json_artifact(search_policy_ablation_path),
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
    parser.add_argument("--candidate-set", required=True)
    parser.add_argument("--runtime-effect-matrix", required=True)
    parser.add_argument("--search-policy-ablation", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-s2pc-l1-family-narrowing-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-s2pc-l1-family-narrowing-current-001.json"
        ),
    )
    args = parser.parse_args()
    output_path = write_policy_reaction_s2pc_l1_family_narrowing(
        args.output,
        candidate_set_path=args.candidate_set,
        runtime_effect_matrix_path=args.runtime_effect_matrix,
        search_policy_ablation_path=args.search_policy_ablation,
        artifact_id=args.artifact_id,
    )
    artifact = load_json_artifact(output_path)
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["overall_status"],
                "retained_candidate_count": artifact["retained_candidate_count"],
                "retained_candidate_ids": artifact["retained_candidate_ids"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_candidate_set(candidate_set: dict[str, Any]) -> None:
    if candidate_set.get("schema_version") != S2PC_L1_CANDIDATE_SET_SCHEMA_VERSION:
        raise ValueError("candidate_set has unsupported schema_version")
    if not isinstance(candidate_set.get("candidates"), list) or not candidate_set["candidates"]:
        raise ValueError("candidate_set missing candidates")


def _validate_runtime_effect_matrix(runtime_effect_matrix: dict[str, Any]) -> None:
    if (
        runtime_effect_matrix.get("schema_version")
        != S2PC_RUNTIME_EFFECT_MATRIX_SCHEMA_VERSION
    ):
        raise ValueError("runtime_effect_matrix has unsupported schema_version")
    if not isinstance(runtime_effect_matrix.get("candidate_results"), list) or not (
        runtime_effect_matrix["candidate_results"]
    ):
        raise ValueError("runtime_effect_matrix missing candidate_results")


def _validate_search_policy_ablation(search_policy_ablation: dict[str, Any]) -> None:
    if (
        search_policy_ablation.get("schema_version")
        != S2PC_L1_SEARCH_POLICY_ABLATION_SCHEMA_VERSION
    ):
        raise ValueError("search_policy_ablation has unsupported schema_version")
    if not isinstance(search_policy_ablation.get("policies"), list) or not (
        search_policy_ablation["policies"]
    ):
        raise ValueError("search_policy_ablation missing policies")


def _common_string_values(
    selected_candidates: list[dict[str, Any]],
    field_name: str,
) -> list[str]:
    values = {str(candidate[field_name]) for candidate in selected_candidates}
    return sorted(values)


def _round_float(value: float) -> float:
    return round(float(value), 12)


def _unique_strings(values: list[str]) -> list[str]:
    unique = []
    for value in values:
        if value and value not in unique:
            unique.append(value)
    return unique


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
