from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
S2PC_PARAMETER_SUBSET_SET_SCHEMA_VERSION = (
    "policy-reaction-s2pc-parameter-subset-set-v1"
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_s2pc_s02_parameter_subset_set(
    *,
    base_candidate: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_base_candidate(base_candidate)
    base_best = copy.deepcopy(base_candidate["best_candidate"])
    base_patches = base_best["parameter_patches"]
    candidates = [
        _subset_candidate(
            base_best,
            candidate_id=f"{artifact_id}-p01",
            tag="prior_anchor_only",
            selected=[
                patch
                for patch in base_patches
                if patch["parameter_name"] == "prior_anchor_strength"
            ],
        ),
        _subset_candidate(
            base_best,
            candidate_id=f"{artifact_id}-p02",
            tag="trust_multiplier_only",
            selected=[
                patch
                for patch in base_patches
                if patch["parameter_name"] == "trust_multiplier"
            ],
        ),
    ]
    artifact = {
        "schema_version": S2PC_PARAMETER_SUBSET_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "s2pc_s02_parameter_subset_search",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "claim_boundary": (
            "S2PC trust-only parameter subset search is a local candidate-exploration artifact only."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_s2pc_s02_parameter_subset_candidate(
    subset_set: dict[str, Any],
    *,
    candidate_id: str,
) -> dict[str, Any]:
    _validate_subset_set(subset_set)
    selected = None
    for candidate in subset_set["candidates"]:
        if candidate["candidate_id"] == candidate_id:
            selected = candidate
            break
    if selected is None:
        raise ValueError("candidate_id not found in subset_set")
    artifact = {
        "schema_version": S2PC_CANDIDATE_SCHEMA_VERSION,
        "candidate_id": selected["candidate_id"],
        "generator": subset_set["generator"],
        "source_split_contract": copy.deepcopy(subset_set["source_split_contract"]),
        "best_candidate": {
            "candidate_index": selected["candidate_index"],
            "segment": selected["segment"],
            "policy_id": selected["policy_id"],
            "proxy_score": selected["proxy_score"],
            "parameter_patches": copy.deepcopy(selected["parameter_patches"]),
        },
        "candidate_prompt_components": copy.deepcopy(selected["candidate_prompt_components"]),
    }
    _assert_strict_json(artifact)
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-candidate", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-s2pc-s02-parameter-subset-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-s2pc-s02-parameter-subset-current-001.json"
        ),
    )
    args = parser.parse_args()
    artifact = build_policy_reaction_s2pc_s02_parameter_subset_set(
        base_candidate=load_json_artifact(args.base_candidate),
        artifact_id=args.artifact_id,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": "generated",
                "candidate_count": artifact["candidate_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_base_candidate(candidate: dict[str, Any]) -> None:
    if candidate.get("schema_version") != S2PC_CANDIDATE_SCHEMA_VERSION:
        raise ValueError("base_candidate has unsupported schema_version")
    best_candidate = candidate.get("best_candidate")
    if not isinstance(best_candidate, dict):
        raise ValueError("base_candidate missing best_candidate")
    patches = best_candidate.get("parameter_patches")
    if not isinstance(patches, list) or not patches:
        raise ValueError("base_candidate missing parameter_patches")
    factor_ids = {patch.get("factor_id") for patch in patches}
    if factor_ids != {"institutional_trust"}:
        raise ValueError("base_candidate must be trust-only")


def _validate_subset_set(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != S2PC_PARAMETER_SUBSET_SET_SCHEMA_VERSION:
        raise ValueError("subset_set has unsupported schema_version")
    if not isinstance(artifact.get("candidates"), list) or not artifact["candidates"]:
        raise ValueError("subset_set missing candidates")


def _subset_candidate(
    base_best: dict[str, Any],
    *,
    candidate_id: str,
    tag: str,
    selected: list[dict[str, Any]],
) -> dict[str, Any]:
    if not selected:
        raise ValueError(f"{tag} received empty subset")
    candidate = copy.deepcopy(base_best)
    candidate["parameter_patches"] = copy.deepcopy(selected)
    return {
        "candidate_id": candidate_id,
        "candidate_index": 1,
        "segment": candidate["segment"],
        "policy_id": candidate["policy_id"],
        "proxy_score": round(float(candidate["proxy_score"]), 12),
        "variant_tag": tag,
        "parameter_patches": candidate["parameter_patches"],
        "candidate_prompt_components": _render_candidate_prompt_components(candidate),
    }


def _render_candidate_prompt_components(candidate: dict[str, Any]) -> dict[str, Any]:
    segment = candidate["segment"]
    policy_id = candidate["policy_id"]
    factor_ids = sorted({patch["factor_id"] for patch in candidate["parameter_patches"]})
    parameter_lines = [
        f"{patch['parameter_name']}={patch['parameter_value']}"
        for patch in candidate["parameter_patches"]
    ]
    return {
        "segment_prompt": {
            segment: (
                "Use the persona's calibrated policy-reaction parameters when "
                "estimating support probabilities for this segment."
            )
        },
        "calibration_anchor": {
            segment: (
                f"S2PC factors={','.join(factor_ids)}; "
                f"primary_policy={policy_id}; "
                f"parameters={';'.join(parameter_lines)}"
            )
        },
        "response_contract": (
            "Return strict JSON probabilities over the available policy alternatives."
        ),
    }


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
