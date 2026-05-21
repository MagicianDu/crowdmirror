from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
LCDU_CANDIDATE_SET_SCHEMA_VERSION = "policy-reaction-lcdu-candidate-set-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_lcdu_l0_candidate_set(
    *,
    base_candidate: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_base_candidate(base_candidate)
    base_best = copy.deepcopy(base_candidate["best_candidate"])
    candidates = [
        _candidate(
            base_best,
            candidate_id=f"{artifact_id}-l01",
            tag="trust_urgency_smooth",
            latent_state_updates={
                "institutional_trust": 0.18,
                "household_cost_pressure": 0.0,
                "policy_relief_urgency": 0.16,
            },
            constraint_program=[
                {"constraint_type": "primary_policy_floor", "policy_id": "food_subsidy_expansion", "min_probability": 0.22},
                {"constraint_type": "distribution_smoothness", "max_top1_probability": 0.58},
            ],
        ),
        _candidate(
            base_best,
            candidate_id=f"{artifact_id}-l02",
            tag="cost_urgency_pair_balance",
            latent_state_updates={
                "institutional_trust": 0.02,
                "household_cost_pressure": 0.22,
                "policy_relief_urgency": 0.14,
            },
            constraint_program=[
                {"constraint_type": "primary_vs_secondary_gap", "primary_policy_id": "food_subsidy_expansion", "secondary_policy_id": "cash_cost_of_living_rebate", "min_gap": -0.02, "max_gap": 0.12},
                {"constraint_type": "segment_rank_guard", "guard": "no_policy_rank_collapse"},
            ],
        ),
        _candidate(
            base_best,
            candidate_id=f"{artifact_id}-l03",
            tag="trust_up_cost_down_guarded_gap",
            latent_state_updates={
                "institutional_trust": 0.15,
                "household_cost_pressure": -0.10,
                "policy_relief_urgency": 0.08,
            },
            constraint_program=[
                {"constraint_type": "primary_vs_secondary_gap", "primary_policy_id": "food_subsidy_expansion", "secondary_policy_id": "baseline_no_new_support", "min_gap": -0.06, "max_gap": 0.08},
                {"constraint_type": "distribution_smoothness", "max_top1_probability": 0.55},
            ],
        ),
        _candidate(
            base_best,
            candidate_id=f"{artifact_id}-l04",
            tag="trust_down_distribution_guard",
            latent_state_updates={
                "institutional_trust": -0.12,
                "household_cost_pressure": 0.06,
                "policy_relief_urgency": 0.0,
            },
            constraint_program=[
                {"constraint_type": "distribution_smoothness", "max_top1_probability": 0.50},
                {"constraint_type": "segment_rank_guard", "guard": "retain_current_ordering_bias"},
            ],
        ),
    ]
    artifact = {
        "schema_version": LCDU_CANDIDATE_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "lcdu_l0_latent_constraint_compiler",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "candidate_count": len(candidates),
        "latent_state_schema": [
            "institutional_trust",
            "household_cost_pressure",
            "policy_relief_urgency",
        ],
        "candidates": candidates,
        "claim_boundary": (
            "LCDU L0 candidate set is a latent-constraint compilation artifact only."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_lcdu_candidate(
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
        default="policy-reaction-lcdu-l0-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-lcdu-l0-current-001.json"
        ),
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()
    candidate_set = build_policy_reaction_lcdu_l0_candidate_set(
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
        extracted = extract_policy_reaction_lcdu_candidate(
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
    if artifact.get("schema_version") != LCDU_CANDIDATE_SET_SCHEMA_VERSION:
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
    smooth_cap = _max_top1_probability(constraint_program)
    patches = []
    for patch in copy.deepcopy(base_patches):
        name = patch["parameter_name"]
        lower = float(patch["parameter_bounds"]["min"])
        upper = float(patch["parameter_bounds"]["max"])
        span = upper - lower
        if name == "prior_anchor_strength":
            value = float(patch["parameter_value"])
            value += latent_state_updates.get("institutional_trust", 0.0) * 0.08
            value += latent_state_updates.get("policy_relief_urgency", 0.0) * 0.05
            value -= latent_state_updates.get("household_cost_pressure", 0.0) * 0.03
            if smooth_cap <= 0.55:
                value -= 0.02
        elif name == "trust_multiplier":
            value = float(patch["parameter_value"])
            value += latent_state_updates.get("institutional_trust", 0.0) * 0.12
            value += latent_state_updates.get("policy_relief_urgency", 0.0) * 0.03
            value -= max(latent_state_updates.get("household_cost_pressure", 0.0), 0.0) * 0.04
            if smooth_cap <= 0.50:
                value -= 0.03
        else:
            value = float(patch["parameter_value"])
        patch["parameter_value"] = round(min(upper, max(lower, value)), 12)
        provenance = patch.setdefault("provenance", {})
        provenance["lcdu_l0_tag"] = tag
        provenance["latent_state_updates"] = copy.deepcopy(latent_state_updates)
        provenance["constraint_program"] = copy.deepcopy(constraint_program)
        patches.append(patch)
    return patches


def _render_candidate_prompt_components(
    candidate: dict[str, Any],
    *,
    latent_state_updates: dict[str, float],
    constraint_program: list[dict[str, Any]],
) -> dict[str, Any]:
    segment = candidate["segment"]
    policy_id = candidate["policy_id"]
    factor_ids = sorted({patch["factor_id"] for patch in candidate["parameter_patches"]})
    parameter_lines = [
        f"{patch['parameter_name']}={patch['parameter_value']}"
        for patch in candidate["parameter_patches"]
    ]
    latent_lines = [
        f"{name}={value:+.2f}" for name, value in sorted(latent_state_updates.items())
    ]
    constraint_lines = [_constraint_text(item) for item in constraint_program]
    return {
        "segment_prompt": {
            segment: " ".join(
                [
                    "Use the persona's calibrated policy-reaction parameters for this segment.",
                    "Interpret them through the latent social-state program rather than a direct prompt patch.",
                    "Keep the full policy distribution coherent under the declared constraints.",
                ]
            )
        },
        "calibration_anchor": {
            segment: (
                f"LCDU factors={','.join(factor_ids)}; "
                f"primary_policy={policy_id}; "
                f"latents={';'.join(latent_lines)}; "
                f"constraints={' | '.join(constraint_lines)}; "
                f"parameters={';'.join(parameter_lines)}"
            )
        },
        "response_contract": (
            "Return strict JSON probabilities over the available policy alternatives."
        ),
    }


def _constraint_text(item: dict[str, Any]) -> str:
    constraint_type = item["constraint_type"]
    if constraint_type == "primary_policy_floor":
        return f"primary_floor({item['policy_id']} >= {item['min_probability']})"
    if constraint_type == "primary_vs_secondary_gap":
        return (
            "gap("
            f"{item['primary_policy_id']} - {item['secondary_policy_id']} in "
            f"[{item['min_gap']},{item['max_gap']}]"
            ")"
        )
    if constraint_type == "distribution_smoothness":
        return f"smooth(max_top1 <= {item['max_top1_probability']})"
    if constraint_type == "segment_rank_guard":
        return f"rank_guard({item['guard']})"
    raise ValueError("unsupported constraint_type")


def _max_top1_probability(constraint_program: list[dict[str, Any]]) -> float:
    caps = [
        float(item["max_top1_probability"])
        for item in constraint_program
        if item["constraint_type"] == "distribution_smoothness"
    ]
    return min(caps) if caps else 1.0


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
