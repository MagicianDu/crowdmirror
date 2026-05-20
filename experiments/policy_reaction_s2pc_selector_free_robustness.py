from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


S2PC_L1_SEARCH_POLICY_ABLATION_SCHEMA_VERSION = (
    "policy-reaction-s2pc-l1-search-policy-ablation-v1"
)
S2PC_RUNTIME_STABILITY_SCHEMA_VERSION = "policy-reaction-s2pc-runtime-stability-v1"
S2PC_SELECTOR_FREE_ROBUSTNESS_SCHEMA_VERSION = (
    "policy-reaction-s2pc-selector-free-robustness-v1"
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_s2pc_selector_free_robustness(
    *,
    search_policy_ablation: dict[str, Any],
    runtime_stability: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_search_policy_ablation(search_policy_ablation)
    _validate_runtime_stability(runtime_stability)
    deployable_policies = [
        policy
        for policy in search_policy_ablation["policies"]
        if not str(policy["policy_id"]).endswith("_oracle")
    ]
    if not deployable_policies:
        raise ValueError("selector-free robustness requires at least one deployable policy")
    selector = min(
        deployable_policies,
        key=lambda policy: (
            0 if policy.get("overall_status") == "improved" else 1,
            int(policy.get("selected_rank", 10**9)),
            str(policy["policy_id"]),
        ),
    )
    selected_candidate_id = str(selector["selected_candidate_id"])
    candidate_ids = [str(candidate_id) for candidate_id in runtime_stability["candidate_ids"]]
    if selected_candidate_id not in candidate_ids:
        raise ValueError("selector candidate is not covered by runtime_stability")
    artifact = {
        "schema_version": S2PC_SELECTOR_FREE_ROBUSTNESS_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": runtime_stability["overall_status"],
        "selector_policy_id": selector["policy_id"],
        "selected_candidate_id": selected_candidate_id,
        "selected_rank": int(selector["selected_rank"]),
        "selected_segment": str(selector["selected_segment"]),
        "selected_policy_id": str(selector["selected_policy_id"]),
        "stability_status": runtime_stability["overall_status"],
        "repeat_count": int(runtime_stability["effect_count"]),
        "improved_count": int(runtime_stability["improved_count"]),
        "regressed_count": int(runtime_stability["regressed_count"]),
        "no_change_count": int(runtime_stability["no_change_count"]),
        "relative_loss_reduction_mean": runtime_stability["loss_summary"].get(
            "relative_loss_reduction_mean"
        ),
        "claim_boundary": (
            "Selector-free robustness evaluates only deployable non-oracle selection logic "
            "against repeat stability evidence; it is not a cross-provider guarantee."
        ),
        "claim_boundaries": _unique_strings(
            [
                "Deployable selector means the rule can be applied without held-out lookahead.",
                *search_policy_ablation.get("claim_boundaries", []),
                *runtime_stability.get("claim_boundaries", []),
            ]
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_policy_reaction_s2pc_selector_free_robustness(
    path: str | Path,
    *,
    search_policy_ablation_path: str | Path,
    runtime_stability_path: str | Path,
    artifact_id: str,
) -> Path:
    artifact = build_policy_reaction_s2pc_selector_free_robustness(
        search_policy_ablation=load_json_artifact(search_policy_ablation_path),
        runtime_stability=load_json_artifact(runtime_stability_path),
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
    parser.add_argument("--search-policy-ablation", required=True)
    parser.add_argument("--runtime-stability", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-s2pc-selector-free-robustness-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-s2pc-selector-free-robustness-current-001.json"
        ),
    )
    args = parser.parse_args()
    output_path = write_policy_reaction_s2pc_selector_free_robustness(
        args.output,
        search_policy_ablation_path=args.search_policy_ablation,
        runtime_stability_path=args.runtime_stability,
        artifact_id=args.artifact_id,
    )
    artifact = load_json_artifact(output_path)
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["overall_status"],
                "selector_policy_id": artifact["selector_policy_id"],
                "selected_candidate_id": artifact["selected_candidate_id"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


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


def _validate_runtime_stability(runtime_stability: dict[str, Any]) -> None:
    if (
        runtime_stability.get("schema_version")
        != S2PC_RUNTIME_STABILITY_SCHEMA_VERSION
    ):
        raise ValueError("runtime_stability has unsupported schema_version")
    if not isinstance(runtime_stability.get("candidate_ids"), list) or not (
        runtime_stability["candidate_ids"]
    ):
        raise ValueError("runtime_stability missing candidate_ids")
    if not isinstance(runtime_stability.get("loss_summary"), dict):
        raise ValueError("runtime_stability missing loss_summary")


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
