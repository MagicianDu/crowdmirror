from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
S2PC_NEIGHBORHOOD_SET_SCHEMA_VERSION = "policy-reaction-s2pc-neighborhood-set-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_s2pc_c01_neighborhood_set(
    *,
    base_candidate: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_base_candidate(base_candidate)
    base_best = copy.deepcopy(base_candidate["best_candidate"])
    variants = [
        _variant(
            base_best,
            candidate_id=f"{artifact_id}-n01",
            tag="anchor_up_temp_down",
            adjustments={
                "response_temperature": ("toward_min", 0.18),
                "prior_anchor_strength": ("toward_max", 0.20),
                "trust_multiplier": ("toward_max", 0.15),
            },
            segment_suffix="Lean slightly more on the calibrated anchor when institutional trust and budget rigidity are jointly elevated.",
        ),
        _variant(
            base_best,
            candidate_id=f"{artifact_id}-n02",
            tag="budget_up_temp_down",
            adjustments={
                "household_budget_rigidity": ("toward_max", 0.20),
                "response_temperature": ("toward_min", 0.10),
                "prior_anchor_strength": ("toward_max", 0.08),
            },
            segment_suffix="Be slightly more decisive when fixed-income households show persistent budget rigidity under inflation pressure.",
        ),
        _variant(
            base_best,
            candidate_id=f"{artifact_id}-n03",
            tag="anchor_down_temp_up",
            adjustments={
                "response_temperature": ("toward_max", 0.12),
                "prior_anchor_strength": ("toward_min", 0.15),
                "trust_multiplier": ("toward_min", 0.10),
            },
            segment_suffix="Use a softer anchor and preserve more uncertainty when the calibrated signal may be overstated.",
        ),
    ]
    artifact = {
        "schema_version": S2PC_NEIGHBORHOOD_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "s2pc_c01_local_neighborhood_search",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "candidate_count": len(variants),
        "candidates": variants,
        "claim_boundary": (
            "S2PC c01 neighborhood search is a local candidate-exploration artifact, "
            "not accepted runtime evidence."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_s2pc_c01_neighborhood_candidate(
    neighborhood_set: dict[str, Any],
    *,
    candidate_id: str,
) -> dict[str, Any]:
    _validate_neighborhood_set(neighborhood_set)
    selected = None
    for candidate in neighborhood_set["candidates"]:
        if candidate["candidate_id"] == candidate_id:
            selected = candidate
            break
    if selected is None:
        raise ValueError("candidate_id not found in neighborhood_set")
    artifact = {
        "schema_version": S2PC_CANDIDATE_SCHEMA_VERSION,
        "candidate_id": selected["candidate_id"],
        "generator": neighborhood_set["generator"],
        "source_split_contract": copy.deepcopy(
            neighborhood_set["source_split_contract"]
        ),
        "best_candidate": {
            "candidate_index": selected["candidate_index"],
            "segment": selected["segment"],
            "policy_id": selected["policy_id"],
            "proxy_score": selected["proxy_score"],
            "parameter_patches": copy.deepcopy(selected["parameter_patches"]),
        },
        "candidate_prompt_components": copy.deepcopy(
            selected["candidate_prompt_components"]
        ),
        "claim_boundary": (
            "S2PC neighborhood candidate is a local runtime probe candidate only."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_policy_reaction_s2pc_c01_neighborhood_candidate(
    path: str | Path,
    *,
    neighborhood_set_path: str | Path,
    candidate_id: str,
) -> Path:
    artifact = extract_policy_reaction_s2pc_c01_neighborhood_candidate(
        load_json_artifact(neighborhood_set_path),
        candidate_id=candidate_id,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-candidate", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-s2pc-c01-neighborhood-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-s2pc-c01-neighborhood-current-001.json"
        ),
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()
    base_candidate = load_json_artifact(args.base_candidate)
    neighborhood = build_policy_reaction_s2pc_c01_neighborhood_set(
        base_candidate=base_candidate,
        artifact_id=args.artifact_id,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(neighborhood, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    summary = {
        "artifact_id": args.artifact_id,
        "output": str(output_path),
        "status": "generated",
        "candidate_count": neighborhood["candidate_count"],
    }
    if args.extract_candidate_id and args.extract_output:
        extracted = write_policy_reaction_s2pc_c01_neighborhood_candidate(
            args.extract_output,
            neighborhood_set_path=output_path,
            candidate_id=args.extract_candidate_id,
        )
        summary["extracted_candidate_id"] = args.extract_candidate_id
        summary["extracted_output"] = str(extracted)
    print(json.dumps(summary, sort_keys=True, allow_nan=False))
    return 0


def _validate_base_candidate(candidate: dict[str, Any]) -> None:
    if candidate.get("schema_version") != S2PC_CANDIDATE_SCHEMA_VERSION:
        raise ValueError("base_candidate has unsupported schema_version")
    best_candidate = candidate.get("best_candidate")
    if not isinstance(best_candidate, dict):
        raise ValueError("base_candidate missing best_candidate")
    if best_candidate.get("segment") != "fixed_income_inflation_stressed":
        raise ValueError("base_candidate must be fixed_income_inflation_stressed")
    if best_candidate.get("policy_id") != "food_subsidy_expansion":
        raise ValueError("base_candidate must target food_subsidy_expansion")
    if not isinstance(best_candidate.get("parameter_patches"), list) or not best_candidate[
        "parameter_patches"
    ]:
        raise ValueError("base_candidate missing parameter_patches")


def _validate_neighborhood_set(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != S2PC_NEIGHBORHOOD_SET_SCHEMA_VERSION:
        raise ValueError("neighborhood_set has unsupported schema_version")
    if not isinstance(artifact.get("candidates"), list) or not artifact["candidates"]:
        raise ValueError("neighborhood_set missing candidates")


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
        provenance["neighborhood_tag"] = tag
        provenance["neighborhood_adjustment"] = {
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
    if direction == "toward_max":
        adjusted = value + (upper - value) * ratio
    elif direction == "toward_min":
        adjusted = value - (value - lower) * ratio
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
