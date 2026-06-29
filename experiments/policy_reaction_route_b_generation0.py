from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
ROUTE_B_CANDIDATE_SET_SCHEMA_VERSION = "policy-reaction-route-b-candidate-set-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_route_b_generation0_candidate_set(
    *,
    base_candidate: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_base_candidate(base_candidate)
    base_best = copy.deepcopy(base_candidate["best_candidate"])
    variants = [
        _variant(
            base_best,
            candidate_id=f"{artifact_id}-g01",
            tag="anchor_down_multiplier_down",
            adjustments={
                "prior_anchor_strength": ("toward_min", 0.20),
                "trust_multiplier": ("toward_min", 0.15),
            },
            segment_suffix=(
                "Use a lighter trust anchor and avoid overstating confidence when "
                "generalization may be fragile."
            ),
        ),
        _variant(
            base_best,
            candidate_id=f"{artifact_id}-g02",
            tag="anchor_down_multiplier_hold",
            adjustments={
                "prior_anchor_strength": ("toward_min", 0.20),
            },
            segment_suffix=(
                "Rely less on the prior anchor while preserving the current trust weighting."
            ),
        ),
        _variant(
            base_best,
            candidate_id=f"{artifact_id}-g03",
            tag="anchor_hold_multiplier_down",
            adjustments={
                "trust_multiplier": ("toward_min", 0.20),
            },
            segment_suffix=(
                "Keep the anchor stable but soften the trust multiplier to reduce worst-case swings."
            ),
        ),
        _variant(
            base_best,
            candidate_id=f"{artifact_id}-g04",
            tag="anchor_mid_multiplier_mid",
            adjustments={
                "prior_anchor_strength": ("toward_mid", 0.50),
                "trust_multiplier": ("toward_mid", 0.50),
            },
            segment_suffix=(
                "Use a centered trust profile that balances calibration fit and repeat robustness."
            ),
        ),
    ]
    artifact = {
        "schema_version": ROUTE_B_CANDIDATE_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "route_b_generation0_small_population_search",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "candidate_count": len(variants),
        "candidates": variants,
        "claim_boundary": (
            "Route B generation-0 candidate set is a bounded structured search population only."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_route_b_candidate(
    candidate_set: dict[str, Any],
    *,
    candidate_id: str,
) -> dict[str, Any]:
    _validate_candidate_set(candidate_set)
    selected = None
    for candidate in candidate_set["candidates"]:
        if candidate["candidate_id"] == candidate_id:
            selected = candidate
            break
    if selected is None:
        raise ValueError("candidate_id not found in candidate_set")
    artifact = {
        "schema_version": S2PC_CANDIDATE_SCHEMA_VERSION,
        "candidate_id": selected["candidate_id"],
        "generator": candidate_set["generator"],
        "source_split_contract": copy.deepcopy(candidate_set["source_split_contract"]),
        "best_candidate": {
            "candidate_index": selected["candidate_index"],
            "segment": selected["segment"],
            "policy_id": selected["policy_id"],
            "proxy_score": selected["proxy_score"],
            "parameter_patches": copy.deepcopy(selected["parameter_patches"]),
        },
        "candidate_prompt_components": copy.deepcopy(selected["candidate_prompt_components"]),
        "claim_boundary": "Route B candidate is a runtime probe candidate only.",
    }
    _assert_strict_json(artifact)
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-candidate", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-route-b-generation0-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-route-b-generation0-current-001.json"
        ),
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()
    candidate_set = build_policy_reaction_route_b_generation0_candidate_set(
        base_candidate=load_json_artifact(args.base_candidate),
        artifact_id=args.artifact_id,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(candidate_set, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    summary = {
        "artifact_id": candidate_set["artifact_id"],
        "output": str(output_path),
        "status": "generated",
        "candidate_count": candidate_set["candidate_count"],
    }
    if args.extract_candidate_id and args.extract_output:
        extracted = extract_policy_reaction_route_b_candidate(
            candidate_set,
            candidate_id=args.extract_candidate_id,
        )
        extracted_path = Path(args.extract_output)
        extracted_path.parent.mkdir(parents=True, exist_ok=True)
        extracted_path.write_text(
            json.dumps(extracted, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
        summary["extracted_candidate_id"] = args.extract_candidate_id
        summary["extracted_output"] = str(extracted_path)
    print(json.dumps(summary, sort_keys=True, allow_nan=False))
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


def _validate_candidate_set(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != ROUTE_B_CANDIDATE_SET_SCHEMA_VERSION:
        raise ValueError("candidate_set has unsupported schema_version")
    if not isinstance(artifact.get("candidates"), list) or not artifact["candidates"]:
        raise ValueError("candidate_set missing candidates")


def _variant(
    base_best: dict[str, Any],
    *,
    candidate_id: str,
    tag: str,
    adjustments: dict[str, tuple[str, float]],
    segment_suffix: str,
) -> dict[str, Any]:
    best = copy.deepcopy(base_best)
    for patch in best["parameter_patches"]:
        parameter_name = patch["parameter_name"]
        if parameter_name not in adjustments:
            continue
        direction, ratio = adjustments[parameter_name]
        patch["parameter_value"] = _adjust_value(
            float(patch["parameter_value"]),
            bounds=patch["parameter_bounds"],
            direction=direction,
            ratio=ratio,
        )
        provenance = patch.setdefault("provenance", {})
        provenance["route_b_generation_tag"] = tag
        provenance["route_b_adjustment"] = {
            "direction": direction,
            "ratio": ratio,
        }
    prompt_components = _render_candidate_prompt_components(best)
    segment = best["segment"]
    prompt_components["segment_prompt"][segment] = (
        prompt_components["segment_prompt"][segment] + " " + segment_suffix
    )
    return {
        "candidate_id": candidate_id,
        "candidate_index": 1,
        "segment": best["segment"],
        "policy_id": best["policy_id"],
        "proxy_score": round(float(best["proxy_score"]), 12),
        "variant_tag": tag,
        "parameter_patches": best["parameter_patches"],
        "candidate_prompt_components": prompt_components,
    }


def _adjust_value(
    value: float,
    *,
    bounds: dict[str, Any],
    direction: str,
    ratio: float,
) -> float:
    lower = float(bounds["min"])
    upper = float(bounds["max"])
    midpoint = (lower + upper) / 2.0
    if direction == "toward_max":
        adjusted = value + (upper - value) * ratio
    elif direction == "toward_min":
        adjusted = value - (value - lower) * ratio
    elif direction == "toward_mid":
        adjusted = value + (midpoint - value) * ratio
    else:
        raise ValueError("unsupported direction")
    return round(min(upper, max(lower, adjusted)), 12)


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
                f"Route-B factors={','.join(factor_ids)}; "
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
