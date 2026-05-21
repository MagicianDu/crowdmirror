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


def build_policy_reaction_route_b_generation1_candidate_set(
    *,
    base_candidate: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_base_candidate(base_candidate)
    base_best = copy.deepcopy(base_candidate["best_candidate"])
    variants = [
        _variant(
            base_best,
            candidate_id=f"{artifact_id}-h01",
            mechanism_profile={
                "anchor_regime": "balanced",
                "trust_mode": "capped",
                "uncertainty_mode": "retain",
                "focus_mode": "distributional_balance",
            },
        ),
        _variant(
            base_best,
            candidate_id=f"{artifact_id}-h02",
            mechanism_profile={
                "anchor_regime": "conservative",
                "trust_mode": "gated",
                "uncertainty_mode": "retain",
                "focus_mode": "paired_policy_balance",
            },
        ),
        _variant(
            base_best,
            candidate_id=f"{artifact_id}-h03",
            mechanism_profile={
                "anchor_regime": "balanced",
                "trust_mode": "gated",
                "uncertainty_mode": "moderate",
                "focus_mode": "distributional_balance",
            },
        ),
        _variant(
            base_best,
            candidate_id=f"{artifact_id}-h04",
            mechanism_profile={
                "anchor_regime": "assertive",
                "trust_mode": "capped",
                "uncertainty_mode": "moderate",
                "focus_mode": "single_policy_focus",
            },
        ),
    ]
    artifact = {
        "schema_version": ROUTE_B_CANDIDATE_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "route_b_generation1_mechanism_search",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "candidate_count": len(variants),
        "candidates": variants,
        "claim_boundary": (
            "Route B generation-1 candidate set is a bounded mechanism-level search "
            "population only."
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
        default="policy-reaction-route-b-generation1-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-route-b-generation1-current-001.json"
        ),
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()
    candidate_set = build_policy_reaction_route_b_generation1_candidate_set(
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
    mechanism_profile: dict[str, str],
) -> dict[str, Any]:
    best = copy.deepcopy(base_best)
    for patch in best["parameter_patches"]:
        patch["parameter_value"] = _compiled_parameter_value(
            patch=patch,
            mechanism_profile=mechanism_profile,
        )
        provenance = patch.setdefault("provenance", {})
        provenance["route_b_generation_tag"] = "generation1_mechanism_profile"
        provenance["route_b_mechanism_profile"] = copy.deepcopy(mechanism_profile)
    prompt_components = _render_candidate_prompt_components(
        best,
        mechanism_profile=mechanism_profile,
    )
    profile_tag = "-".join(
        mechanism_profile[key]
        for key in (
            "anchor_regime",
            "trust_mode",
            "uncertainty_mode",
            "focus_mode",
        )
    )
    return {
        "candidate_id": candidate_id,
        "candidate_index": 1,
        "segment": best["segment"],
        "policy_id": best["policy_id"],
        "proxy_score": round(float(best["proxy_score"]), 12),
        "variant_tag": profile_tag,
        "mechanism_profile": copy.deepcopy(mechanism_profile),
        "parameter_patches": best["parameter_patches"],
        "candidate_prompt_components": prompt_components,
    }


def _compiled_parameter_value(
    *,
    patch: dict[str, Any],
    mechanism_profile: dict[str, str],
) -> float:
    bounds = patch["parameter_bounds"]
    lower = float(bounds["min"])
    upper = float(bounds["max"])
    midpoint = (lower + upper) / 2.0
    span = upper - lower
    name = patch["parameter_name"]
    if name == "prior_anchor_strength":
        regime_ratio = {
            "conservative": 0.35,
            "balanced": 0.5,
            "assertive": 0.72,
        }[mechanism_profile["anchor_regime"]]
        value = lower + span * regime_ratio
    elif name == "trust_multiplier":
        base_ratio = {
            "direct": 0.58,
            "capped": 0.48,
            "gated": 0.43,
        }[mechanism_profile["trust_mode"]]
        uncertainty_offset = {
            "retain": -0.03,
            "moderate": 0.0,
            "collapse": 0.04,
        }[mechanism_profile["uncertainty_mode"]]
        focus_offset = {
            "single_policy_focus": 0.04,
            "paired_policy_balance": -0.01,
            "distributional_balance": -0.03,
        }[mechanism_profile["focus_mode"]]
        value = lower + span * (base_ratio + uncertainty_offset + focus_offset)
    else:
        value = midpoint
    return round(min(upper, max(lower, value)), 12)


def _render_candidate_prompt_components(
    candidate: dict[str, Any],
    *,
    mechanism_profile: dict[str, str],
) -> dict[str, Any]:
    segment = candidate["segment"]
    policy_id = candidate["policy_id"]
    factor_ids = sorted({patch["factor_id"] for patch in candidate["parameter_patches"]})
    parameter_lines = [
        f"{patch['parameter_name']}={patch['parameter_value']}"
        for patch in candidate["parameter_patches"]
    ]
    anchor_text = {
        "conservative": "Use a conservative prior anchor and avoid over-committing to the segment prior.",
        "balanced": "Use a balanced prior anchor that preserves segment signal without overfitting.",
        "assertive": "Use a stronger segment prior anchor when the observed pattern is consistent.",
    }[mechanism_profile["anchor_regime"]]
    trust_text = {
        "direct": "Apply trust effects directly when mapping support probabilities.",
        "capped": "Apply trust effects with a cap so that they cannot dominate the full distribution.",
        "gated": "Only apply trust reinforcement when the primary policy remains competitive under the prior anchor.",
    }[mechanism_profile["trust_mode"]]
    uncertainty_text = {
        "retain": "Retain visible uncertainty and avoid turning the response into a sharp single-policy peak.",
        "moderate": "Allow moderate concentration when the evidence favors one response pattern.",
        "collapse": "Collapse uncertainty toward the leading policy when the segment prior is strong.",
    }[mechanism_profile["uncertainty_mode"]]
    focus_text = {
        "single_policy_focus": (
            f"Primary focus stays on {policy_id}; secondary policies only need coarse consistency."
        ),
        "paired_policy_balance": (
            f"Balance {policy_id} against the nearest alternative instead of optimizing a single policy alone."
        ),
        "distributional_balance": (
            f"Preserve the full three-policy distribution while keeping {policy_id} competitive."
        ),
    }[mechanism_profile["focus_mode"]]
    return {
        "segment_prompt": {
            segment: " ".join(
                [
                    "Use the persona's calibrated policy-reaction parameters for this segment.",
                    anchor_text,
                    trust_text,
                    uncertainty_text,
                    focus_text,
                ]
            )
        },
        "calibration_anchor": {
            segment: (
                f"Route-B generation1 factors={','.join(factor_ids)}; "
                f"primary_policy={policy_id}; "
                f"anchor_regime={mechanism_profile['anchor_regime']}; "
                f"trust_mode={mechanism_profile['trust_mode']}; "
                f"uncertainty_mode={mechanism_profile['uncertainty_mode']}; "
                f"focus_mode={mechanism_profile['focus_mode']}; "
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
