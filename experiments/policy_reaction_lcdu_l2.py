from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
LCDU_SEGMENT_GUARD_SET_SCHEMA_VERSION = "policy-reaction-lcdu-segment-guard-set-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_lcdu_l2_segment_guard_set(
    *,
    base_candidate: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_base_candidate(base_candidate)
    base_best = copy.deepcopy(base_candidate["best_candidate"])
    candidates = [
        _candidate(
            base_best,
            candidate_id=f"{artifact_id}-g01",
            tag="working_family_baseline_guard",
            latent_state_updates={
                "institutional_trust": -0.12,
                "household_cost_pressure": 0.06,
                "policy_relief_urgency": 0.0,
            },
            constraint_program=[
                {"constraint_type": "distribution_smoothness", "max_top1_probability": 0.50},
                {"constraint_type": "segment_rank_guard", "guard": "retain_current_ordering_bias"},
            ],
            segment_overrides={
                "working_family_price_stressed": {
                    "guard_policy": "baseline_profile_preservation",
                    "max_food_subsidy_probability": 0.235,
                    "min_cash_rebate_probability": 0.41,
                }
            },
        ),
        _candidate(
            base_best,
            candidate_id=f"{artifact_id}-g02",
            tag="working_family_cash_rebate_guard",
            latent_state_updates={
                "institutional_trust": -0.10,
                "household_cost_pressure": 0.05,
                "policy_relief_urgency": 0.01,
            },
            constraint_program=[
                {"constraint_type": "distribution_smoothness", "max_top1_probability": 0.51},
                {"constraint_type": "segment_rank_guard", "guard": "retain_current_ordering_bias"},
            ],
            segment_overrides={
                "working_family_price_stressed": {
                    "guard_policy": "cash_rebate_competitiveness",
                    "max_food_subsidy_probability": 0.23,
                    "min_cash_rebate_probability": 0.42,
                }
            },
        ),
        _candidate(
            base_best,
            candidate_id=f"{artifact_id}-g03",
            tag="working_family_soft_guard",
            latent_state_updates={
                "institutional_trust": -0.11,
                "household_cost_pressure": 0.04,
                "policy_relief_urgency": 0.0,
            },
            constraint_program=[
                {"constraint_type": "distribution_smoothness", "max_top1_probability": 0.50},
                {"constraint_type": "segment_rank_guard", "guard": "retain_current_ordering_bias"},
            ],
            segment_overrides={
                "working_family_price_stressed": {
                    "guard_policy": "soft_distribution_guard",
                    "max_food_subsidy_probability": 0.24,
                    "min_cash_rebate_probability": 0.40,
                }
            },
        ),
        _candidate(
            base_best,
            candidate_id=f"{artifact_id}-g04",
            tag="dual_segment_guard",
            latent_state_updates={
                "institutional_trust": -0.12,
                "household_cost_pressure": 0.06,
                "policy_relief_urgency": 0.0,
            },
            constraint_program=[
                {"constraint_type": "distribution_smoothness", "max_top1_probability": 0.50},
                {"constraint_type": "segment_rank_guard", "guard": "retain_current_ordering_bias"},
            ],
            segment_overrides={
                "working_family_price_stressed": {
                    "guard_policy": "baseline_profile_preservation",
                    "max_food_subsidy_probability": 0.235,
                    "min_cash_rebate_probability": 0.41,
                },
                "general_population_cost_pressure": {
                    "guard_policy": "baseline_profile_preservation",
                    "max_food_subsidy_probability": 0.195,
                    "min_cash_rebate_probability": 0.26,
                },
            },
        ),
    ]
    artifact = {
        "schema_version": LCDU_SEGMENT_GUARD_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "lcdu_l2_segment_guard_family",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "claim_boundary": (
            "LCDU L2 segment guard set is a local candidate family for unstable segments only."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_lcdu_l2_candidate(
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
        "claim_boundary": "LCDU candidate is a runtime probe candidate only.",
    }
    _assert_strict_json(artifact)
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-candidate", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-lcdu-l2-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-lcdu-l2-current-001.json"
        ),
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()
    candidate_set = build_policy_reaction_lcdu_l2_segment_guard_set(
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
        extracted = extract_policy_reaction_lcdu_l2_candidate(
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
    if artifact.get("schema_version") != LCDU_SEGMENT_GUARD_SET_SCHEMA_VERSION:
        raise ValueError("candidate_set has unsupported schema_version")
    if not isinstance(artifact.get("candidates"), list) or not artifact["candidates"]:
        raise ValueError("candidate_set missing candidates")


def _candidate(
    base_best: dict[str, Any],
    *,
    candidate_id: str,
    tag: str,
    latent_state_updates: dict[str, float],
    constraint_program: list[dict[str, Any]],
    segment_overrides: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    candidate = copy.deepcopy(base_best)
    candidate["parameter_patches"] = _compiled_parameter_patches(
        candidate["parameter_patches"],
        latent_state_updates=latent_state_updates,
        constraint_program=constraint_program,
        tag=tag,
    )
    prompt_components = _render_candidate_prompt_components(
        candidate,
        latent_state_updates=latent_state_updates,
        constraint_program=constraint_program,
        segment_overrides=segment_overrides,
    )
    return {
        "candidate_id": candidate_id,
        "candidate_index": 1,
        "segment": candidate["segment"],
        "policy_id": candidate["policy_id"],
        "proxy_score": round(float(candidate["proxy_score"]), 12),
        "variant_tag": tag,
        "latent_state_updates": latent_state_updates,
        "constraint_program": constraint_program,
        "segment_overrides": segment_overrides,
        "parameter_patches": candidate["parameter_patches"],
        "candidate_prompt_components": prompt_components,
    }


def _compiled_parameter_patches(
    base_patches: list[dict[str, Any]],
    *,
    latent_state_updates: dict[str, float],
    constraint_program: list[dict[str, Any]],
    tag: str,
) -> list[dict[str, Any]]:
    smooth_cap = min(
        float(item["max_top1_probability"])
        for item in constraint_program
        if item["constraint_type"] == "distribution_smoothness"
    )
    patches = []
    for patch in copy.deepcopy(base_patches):
        name = patch["parameter_name"]
        lower = float(patch["parameter_bounds"]["min"])
        upper = float(patch["parameter_bounds"]["max"])
        if name == "prior_anchor_strength":
            value = float(patch["parameter_value"])
            value += latent_state_updates.get("institutional_trust", 0.0) * 0.05
            value -= latent_state_updates.get("household_cost_pressure", 0.0) * 0.02
            if smooth_cap <= 0.50:
                value -= 0.004
        elif name == "trust_multiplier":
            value = float(patch["parameter_value"])
            value += latent_state_updates.get("institutional_trust", 0.0) * 0.08
            value -= max(latent_state_updates.get("household_cost_pressure", 0.0), 0.0) * 0.02
            if smooth_cap <= 0.50:
                value -= 0.006
        else:
            value = float(patch["parameter_value"])
        patch["parameter_value"] = round(min(upper, max(lower, value)), 12)
        provenance = patch.setdefault("provenance", {})
        provenance["lcdu_l2_tag"] = tag
        provenance["latent_state_updates"] = copy.deepcopy(latent_state_updates)
        provenance["constraint_program"] = copy.deepcopy(constraint_program)
        patches.append(patch)
    return patches


def _render_candidate_prompt_components(
    candidate: dict[str, Any],
    *,
    latent_state_updates: dict[str, float],
    constraint_program: list[dict[str, Any]],
    segment_overrides: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    base_segment = candidate["segment"]
    policy_id = candidate["policy_id"]
    factor_ids = sorted({patch["factor_id"] for patch in candidate["parameter_patches"]})
    parameter_lines = [
        f"{patch['parameter_name']}={patch['parameter_value']}"
        for patch in candidate["parameter_patches"]
    ]
    latent_lines = [
        f"{name}={value:+.2f}" for name, value in sorted(latent_state_updates.items())
    ]
    segment_prompt = {
        base_segment: (
            "Use the persona's calibrated policy-reaction parameters for this segment. "
            "Interpret them through the segment-guarded latent program and preserve full-distribution coherence."
        )
    }
    calibration_anchor = {
        base_segment: (
            f"LCDU-L2 factors={','.join(factor_ids)}; "
            f"primary_policy={policy_id}; "
            f"latents={';'.join(latent_lines)}; "
            f"parameters={';'.join(parameter_lines)}"
        )
    }
    for segment, guard in segment_overrides.items():
        segment_prompt[segment] = (
            "Keep this segment close to its calibration-split baseline response profile. "
            f"Do not let food_subsidy_expansion exceed {guard['max_food_subsidy_probability']:.3f}. "
            f"Keep cash_cost_of_living_rebate at or above {guard['min_cash_rebate_probability']:.3f} when feasible."
        )
        calibration_anchor[segment] = (
            f"LCDU-L2 segment_guard={guard['guard_policy']}; "
            f"max_food_subsidy_probability={guard['max_food_subsidy_probability']}; "
            f"min_cash_rebate_probability={guard['min_cash_rebate_probability']}"
        )
    return {
        "segment_prompt": segment_prompt,
        "calibration_anchor": calibration_anchor,
        "response_contract": (
            "Return strict JSON probabilities over the available policy alternatives."
        ),
    }


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
