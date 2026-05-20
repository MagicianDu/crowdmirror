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


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_s2pc_l1_search_policy_ablation(
    *,
    candidate_set: dict[str, Any],
    runtime_effect_matrix: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_candidate_set(candidate_set)
    _validate_runtime_effect_matrix(runtime_effect_matrix)
    joined = _join_candidates(candidate_set, runtime_effect_matrix)

    policies = [
        _direct_top1_policy(joined),
        _oracle_subset_policy(
            policy_id="beam_top3_oracle",
            family="beam_depth",
            rows=[row for row in joined if row["rank"] <= 3],
            description="Post-hoc best candidate within beam rank <= 3.",
        ),
        _oracle_subset_policy(
            policy_id="beam_top6_oracle",
            family="beam_depth",
            rows=joined,
            description="Post-hoc best candidate across the full evaluated beam.",
        ),
    ]
    for policy_name in sorted({row["policy_id"] for row in joined}):
        policies.append(
            _oracle_subset_policy(
                policy_id=f"policy_group_{policy_name}_oracle",
                family="policy_group",
                rows=[row for row in joined if row["policy_id"] == policy_name],
                description=f"Post-hoc best candidate within policy group {policy_name}.",
            )
        )
    for segment_name in sorted({row["segment"] for row in joined}):
        policies.append(
            _oracle_subset_policy(
                policy_id=f"segment_group_{segment_name}_oracle",
                family="segment_group",
                rows=[row for row in joined if row["segment"] == segment_name],
                description=f"Post-hoc best candidate within segment group {segment_name}.",
            )
        )

    ranked = sorted(
        policies,
        key=lambda policy: (
            0 if policy["overall_status"] == "improved" else 1,
            float(policy["selected_runtime_loss"]),
            policy["policy_id"],
        ),
    )
    best = ranked[0]
    artifact = {
        "schema_version": S2PC_L1_SEARCH_POLICY_ABLATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": (
            "improving_search_policies_available"
            if any(policy["overall_status"] == "improved" for policy in ranked)
            else "no_improving_search_policy"
        ),
        "candidate_set_id": candidate_set["candidate_set_id"],
        "runtime_effect_matrix_artifact_id": runtime_effect_matrix["artifact_id"],
        "policy_count": len(ranked),
        "best_policy_id": best["policy_id"],
        "best_candidate_id": best["selected_candidate_id"],
        "policies": ranked,
        "claim_boundary": (
            "S2PC L1 search-policy ablation is retrospective held-out analysis over "
            "evaluated candidates, not a deployable selector by itself."
        ),
        "claim_boundaries": _unique_strings(
            [
                "Direct top-1 policy is deployable because it follows beam rank only.",
                "Oracle group policies are retrospective analysis slices over already evaluated candidates.",
                *candidate_set.get("claim_boundaries", []),
                *runtime_effect_matrix.get("claim_boundaries", []),
            ]
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_policy_reaction_s2pc_l1_search_policy_ablation(
    path: str | Path,
    *,
    candidate_set_path: str | Path,
    runtime_effect_matrix_path: str | Path,
    artifact_id: str,
) -> Path:
    artifact = build_policy_reaction_s2pc_l1_search_policy_ablation(
        candidate_set=load_json_artifact(candidate_set_path),
        runtime_effect_matrix=load_json_artifact(runtime_effect_matrix_path),
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
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-s2pc-l1-search-policy-ablation-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-s2pc-l1-search-policy-ablation-current-001.json"
        ),
    )
    args = parser.parse_args()
    output_path = write_policy_reaction_s2pc_l1_search_policy_ablation(
        args.output,
        candidate_set_path=args.candidate_set,
        runtime_effect_matrix_path=args.runtime_effect_matrix,
        artifact_id=args.artifact_id,
    )
    artifact = load_json_artifact(output_path)
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["overall_status"],
                "best_policy_id": artifact["best_policy_id"],
                "best_candidate_id": artifact["best_candidate_id"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_candidate_set(candidate_set: dict[str, Any]) -> None:
    if candidate_set.get("schema_version") != S2PC_L1_CANDIDATE_SET_SCHEMA_VERSION:
        raise ValueError("candidate_set has unsupported schema_version")
    if not candidate_set.get("candidate_set_id"):
        raise ValueError("candidate_set missing candidate_set_id")
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


def _join_candidates(
    candidate_set: dict[str, Any],
    runtime_effect_matrix: dict[str, Any],
) -> list[dict[str, Any]]:
    effect_by_candidate = {
        result["s2pc_candidate_id"]: result
        for result in runtime_effect_matrix["candidate_results"]
    }
    rows = []
    for candidate in candidate_set["candidates"]:
        candidate_id = candidate["candidate_id"]
        effect = effect_by_candidate.get(candidate_id)
        if effect is None:
            continue
        rows.append(
            {
                "candidate_id": candidate_id,
                "rank": int(candidate["rank"]),
                "segment": str(candidate["segment"]),
                "policy_id": str(candidate["policy_id"]),
                "proxy_score": float(candidate["proxy_score"]),
                "overall_status": effect["overall_status"],
                "baseline_loss": float(effect["baseline_loss"]),
                "runtime_loss": float(effect["s2pc_runtime_loss"]),
                "absolute_loss_delta": float(effect["absolute_loss_delta"]),
                "relative_loss_reduction": float(effect["relative_loss_reduction"]),
            }
        )
    if not rows:
        raise ValueError("candidate_set and runtime_effect_matrix have no joined candidates")
    return rows


def _direct_top1_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected = min(rows, key=lambda row: row["rank"])
    return _policy_summary(
        policy_id="beam_top1_direct",
        family="beam_depth",
        description="Directly choose the rank-1 beam candidate without held-out lookahead.",
        rows=[selected],
        selected=selected,
    )


def _oracle_subset_policy(
    *,
    policy_id: str,
    family: str,
    rows: list[dict[str, Any]],
    description: str,
) -> dict[str, Any]:
    if not rows:
        raise ValueError(f"{policy_id} received no candidates")
    selected = min(rows, key=lambda row: (row["runtime_loss"], row["rank"], row["candidate_id"]))
    return _policy_summary(
        policy_id=policy_id,
        family=family,
        description=description,
        rows=rows,
        selected=selected,
    )


def _policy_summary(
    *,
    policy_id: str,
    family: str,
    description: str,
    rows: list[dict[str, Any]],
    selected: dict[str, Any],
) -> dict[str, Any]:
    return {
        "policy_id": policy_id,
        "family": family,
        "description": description,
        "candidate_count": len(rows),
        "selected_candidate_id": selected["candidate_id"],
        "selected_rank": selected["rank"],
        "selected_segment": selected["segment"],
        "selected_policy_id": selected["policy_id"],
        "overall_status": selected["overall_status"],
        "selected_runtime_loss": _round_float(selected["runtime_loss"]),
        "selected_relative_loss_reduction": _round_float(
            selected["relative_loss_reduction"]
        ),
    }


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
