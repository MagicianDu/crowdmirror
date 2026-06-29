from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
CONSTRAINT_PROGRAM_L0_CANDIDATE_SET_SCHEMA_VERSION = (
    "policy-reaction-constraint-program-l0-candidate-set-v1"
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_constraint_program_l0_candidate_set(
    *,
    base_candidate: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_base_candidate(base_candidate)
    base_best = copy.deepcopy(base_candidate["best_candidate"])
    candidates = [
        _candidate(
            base_best,
            artifact_id=artifact_id,
            candidate_suffix="c01",
            variant_tag="relief_floor_low_income_guard",
            population_latents={
                "relief_activation": 0.16,
                "baseline_inertia": -0.08,
                "targeting_balance": 0.10,
                "price_signal_absorption": 0.04,
            },
            population_constraints=[
                {
                    "constraint_type": "baseline_share_cap",
                    "policy_id": "baseline_no_new_support",
                    "max_probability": 0.27,
                },
                {
                    "constraint_type": "relief_share_floor",
                    "policy_id": "cash_cost_of_living_rebate",
                    "min_probability": 0.29,
                },
                {
                    "constraint_type": "segment_guard",
                    "selector": "income_band=low",
                    "guard": "support_over_baseline",
                },
            ],
            segment_adjustments=[
                {
                    "selector": "income_band=low",
                    "adjustment_reason": "raise relief responsiveness for low-income households",
                    "latent_delta": {
                        "relief_activation": 0.10,
                        "baseline_inertia": -0.04,
                        "targeting_balance": 0.08,
                        "price_signal_absorption": 0.0,
                    },
                }
            ],
        ),
        _candidate(
            base_best,
            artifact_id=artifact_id,
            candidate_suffix="c02",
            variant_tag="price_stress_distribution_guard",
            population_latents={
                "relief_activation": 0.12,
                "baseline_inertia": -0.05,
                "targeting_balance": 0.06,
                "price_signal_absorption": 0.18,
            },
            population_constraints=[
                {
                    "constraint_type": "baseline_share_cap",
                    "policy_id": "baseline_no_new_support",
                    "max_probability": 0.25,
                },
                {
                    "constraint_type": "target_gap_band",
                    "primary_policy_id": "cash_cost_of_living_rebate",
                    "secondary_policy_id": "baseline_no_new_support",
                    "min_gap": 0.02,
                    "max_gap": 0.14,
                },
                {
                    "constraint_type": "segment_guard",
                    "selector": "price_stress_level=high",
                    "guard": "retain_relief_mass",
                },
            ],
            segment_adjustments=[
                {
                    "selector": "price_stress_level=high",
                    "adjustment_reason": "smooth price-stress response without collapsing relief support",
                    "latent_delta": {
                        "relief_activation": 0.06,
                        "baseline_inertia": -0.03,
                        "targeting_balance": 0.0,
                        "price_signal_absorption": 0.12,
                    },
                }
            ],
        ),
        _candidate(
            base_best,
            artifact_id=artifact_id,
            candidate_suffix="c03",
            variant_tag="dual_axis_balanced_population_program",
            population_latents={
                "relief_activation": 0.18,
                "baseline_inertia": -0.09,
                "targeting_balance": 0.12,
                "price_signal_absorption": 0.14,
            },
            population_constraints=[
                {
                    "constraint_type": "baseline_share_cap",
                    "policy_id": "baseline_no_new_support",
                    "max_probability": 0.245,
                },
                {
                    "constraint_type": "relief_share_floor",
                    "policy_id": "cash_cost_of_living_rebate",
                    "min_probability": 0.30,
                },
                {
                    "constraint_type": "target_gap_band",
                    "primary_policy_id": "cash_cost_of_living_rebate",
                    "secondary_policy_id": "baseline_no_new_support",
                    "min_gap": 0.03,
                    "max_gap": 0.16,
                },
            ],
            segment_adjustments=[
                {
                    "selector": "income_band=low",
                    "adjustment_reason": "preserve low-income relief ordering under population-level caps",
                    "latent_delta": {
                        "relief_activation": 0.08,
                        "baseline_inertia": -0.04,
                        "targeting_balance": 0.10,
                        "price_signal_absorption": 0.0,
                    },
                },
                {
                    "selector": "price_stress_level=high",
                    "adjustment_reason": "absorb price stress through smoother relief-biased response formation",
                    "latent_delta": {
                        "relief_activation": 0.04,
                        "baseline_inertia": -0.02,
                        "targeting_balance": 0.0,
                        "price_signal_absorption": 0.10,
                    },
                },
            ],
        ),
        _candidate(
            base_best,
            artifact_id=artifact_id,
            candidate_suffix="c04",
            variant_tag="strict_targeted_population_program",
            population_latents={
                "relief_activation": 0.20,
                "baseline_inertia": -0.12,
                "targeting_balance": 0.18,
                "price_signal_absorption": 0.10,
            },
            population_constraints=[
                {
                    "constraint_type": "baseline_share_cap",
                    "policy_id": "baseline_no_new_support",
                    "max_probability": 0.235,
                },
                {
                    "constraint_type": "relief_share_floor",
                    "policy_id": "cash_cost_of_living_rebate",
                    "min_probability": 0.31,
                },
                {
                    "constraint_type": "target_gap_band",
                    "primary_policy_id": "cash_cost_of_living_rebate",
                    "secondary_policy_id": "baseline_no_new_support",
                    "min_gap": 0.04,
                    "max_gap": 0.18,
                },
                {
                    "constraint_type": "segment_guard",
                    "selector": "income_band=low",
                    "guard": "strict_support_over_baseline",
                },
            ],
            segment_adjustments=[
                {
                    "selector": "income_band=low",
                    "adjustment_reason": "apply stronger low-income targeting in the population program",
                    "latent_delta": {
                        "relief_activation": 0.10,
                        "baseline_inertia": -0.05,
                        "targeting_balance": 0.12,
                        "price_signal_absorption": 0.0,
                    },
                },
                {
                    "selector": "price_stress_level=high",
                    "adjustment_reason": "retain relief support under higher price-stress salience",
                    "latent_delta": {
                        "relief_activation": 0.05,
                        "baseline_inertia": -0.02,
                        "targeting_balance": 0.02,
                        "price_signal_absorption": 0.08,
                    },
                },
            ],
        ),
    ]
    artifact = {
        "schema_version": CONSTRAINT_PROGRAM_L0_CANDIDATE_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "constraint_program_l0_population_compiler",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "candidate_count": len(candidates),
        "population_constraint_schema": [
            "baseline_share_cap",
            "relief_share_floor",
            "target_gap_band",
            "segment_guard",
        ],
        "population_latent_schema": [
            "relief_activation",
            "baseline_inertia",
            "targeting_balance",
            "price_signal_absorption",
        ],
        "candidates": candidates,
        "claim_boundary": "Constraint Program L0 is a candidate-generation artifact only.",
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_constraint_program_l0_candidate(
    candidate_set: dict[str, Any],
    *,
    candidate_id: str,
) -> dict[str, Any]:
    _validate_candidate_set(candidate_set)
    for candidate in candidate_set["candidates"]:
        if candidate["candidate_id"] == candidate_id:
            artifact = {
                "schema_version": S2PC_CANDIDATE_SCHEMA_VERSION,
                "candidate_id": candidate["candidate_id"],
                "generator": candidate_set["generator"],
                "source_split_contract": copy.deepcopy(
                    candidate_set["source_split_contract"]
                ),
                "best_candidate": {
                    "candidate_index": candidate["candidate_index"],
                    "segment": candidate["segment"],
                    "policy_id": candidate["policy_id"],
                    "proxy_score": candidate["proxy_score"],
                    "parameter_patches": copy.deepcopy(candidate["parameter_patches"]),
                },
                "candidate_prompt_components": copy.deepcopy(
                    candidate["candidate_prompt_components"]
                ),
                "claim_boundary": "Constraint Program L0 candidate is a runtime probe candidate only.",
            }
            _assert_strict_json(artifact)
            return artifact
    raise ValueError("candidate_id not found in candidate_set")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-candidate", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-constraint-program-l0-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-constraint-program-l0-current-001.json"
        ),
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()

    candidate_set = build_policy_reaction_constraint_program_l0_candidate_set(
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
        extracted = extract_policy_reaction_constraint_program_l0_candidate(
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
    if (
        artifact.get("schema_version")
        != CONSTRAINT_PROGRAM_L0_CANDIDATE_SET_SCHEMA_VERSION
    ):
        raise ValueError("candidate_set has unsupported schema_version")
    if not isinstance(artifact.get("candidates"), list) or not artifact["candidates"]:
        raise ValueError("candidate_set missing candidates")


def _candidate(
    base_best: dict[str, Any],
    *,
    artifact_id: str,
    candidate_suffix: str,
    variant_tag: str,
    population_latents: dict[str, float],
    population_constraints: list[dict[str, Any]],
    segment_adjustments: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate = copy.deepcopy(base_best)
    candidate["parameter_patches"] = _compiled_parameter_patches(
        candidate["parameter_patches"],
        population_latents=population_latents,
        population_constraints=population_constraints,
        segment_adjustments=segment_adjustments,
        variant_tag=variant_tag,
    )
    prompt_components = _render_candidate_prompt_components(
        candidate,
        population_latents=population_latents,
        population_constraints=population_constraints,
        segment_adjustments=segment_adjustments,
    )
    return {
        "candidate_id": f"{artifact_id}-{candidate_suffix}",
        "candidate_index": 1,
        "segment": candidate["segment"],
        "policy_id": candidate["policy_id"],
        "proxy_score": round(float(candidate["proxy_score"]), 12),
        "variant_tag": variant_tag,
        "population_constraint_program": {
            "population_latents": population_latents,
            "population_constraints": population_constraints,
            "segment_adjustments": segment_adjustments,
        },
        "parameter_patches": candidate["parameter_patches"],
        "candidate_prompt_components": prompt_components,
    }


def _compiled_parameter_patches(
    base_patches: list[dict[str, Any]],
    *,
    population_latents: dict[str, float],
    population_constraints: list[dict[str, Any]],
    segment_adjustments: list[dict[str, Any]],
    variant_tag: str,
) -> list[dict[str, Any]]:
    baseline_cap = _baseline_share_cap(population_constraints)
    relief_floor = _relief_share_floor(population_constraints)
    target_gap_max = _target_gap_max(population_constraints)
    patches = []
    for patch in copy.deepcopy(base_patches):
        name = patch["parameter_name"]
        lower = float(patch["parameter_bounds"]["min"])
        upper = float(patch["parameter_bounds"]["max"])
        value = float(patch["parameter_value"])
        if name == "prior_anchor_strength":
            value += population_latents.get("relief_activation", 0.0) * 0.10
            value += population_latents.get("targeting_balance", 0.0) * 0.05
            value -= max(population_latents.get("baseline_inertia", 0.0), 0.0) * 0.08
            if baseline_cap <= 0.245:
                value -= 0.015
        elif name == "price_salience_multiplier":
            value += population_latents.get("price_signal_absorption", 0.0) * 0.18
            value += population_latents.get("relief_activation", 0.0) * 0.03
            if target_gap_max >= 0.16:
                value += 0.01
        elif name == "relief_bias":
            value += population_latents.get("relief_activation", 0.0) * 0.25
            value += population_latents.get("targeting_balance", 0.0) * 0.08
            value -= max(population_latents.get("baseline_inertia", 0.0), 0.0) * 0.04
            if relief_floor >= 0.30:
                value += 0.015
        patch["parameter_value"] = round(min(upper, max(lower, value)), 12)
        provenance = patch.setdefault("provenance", {})
        provenance["constraint_program_l0_tag"] = variant_tag
        provenance["population_latents"] = copy.deepcopy(population_latents)
        provenance["population_constraints"] = copy.deepcopy(population_constraints)
        provenance["segment_adjustments"] = copy.deepcopy(segment_adjustments)
        patches.append(patch)
    return patches


def _render_candidate_prompt_components(
    candidate: dict[str, Any],
    *,
    population_latents: dict[str, float],
    population_constraints: list[dict[str, Any]],
    segment_adjustments: list[dict[str, Any]],
) -> dict[str, Any]:
    segment = candidate["segment"]
    policy_id = candidate["policy_id"]
    factor_ids = sorted({patch["factor_id"] for patch in candidate["parameter_patches"]})
    parameter_lines = [
        f"{patch['parameter_name']}={patch['parameter_value']}"
        for patch in candidate["parameter_patches"]
    ]
    latent_lines = [
        f"{name}={value:+.2f}" for name, value in sorted(population_latents.items())
    ]
    constraint_lines = [_constraint_text(item) for item in population_constraints]
    selector_lines = [item["selector"] for item in segment_adjustments]
    selector_text = ",".join(selector_lines) if selector_lines else "none"
    prompt_text = " ".join(
        [
            "Use the calibrated policy-reaction parameters for this segment.",
            "Interpret them through the population-level constraint program rather than a direct runtime patch.",
            f"Apply any selector-specific guards for {selector_text}.",
        ]
    )
    anchor_text = (
        f"CP-L0 factors={','.join(factor_ids)}; "
        f"primary_policy={policy_id}; "
        f"population_latents={';'.join(latent_lines)}; "
        f"population_constraints={' | '.join(constraint_lines)}; "
        f"segment_adjustments={_segment_adjustment_text(segment_adjustments)}; "
        f"parameters={';'.join(parameter_lines)}"
    )
    return {
        "segment_prompt": {
            key: prompt_text for key in candidate.get("candidate_prompt_components", {})
        }
        if False
        else {segment: prompt_text},
        "calibration_anchor": {segment: anchor_text},
        "response_contract": (
            "Return strict JSON probabilities over the available policy alternatives."
        ),
    }


def _segment_adjustment_text(segment_adjustments: list[dict[str, Any]]) -> str:
    parts = []
    for item in segment_adjustments:
        delta_text = ",".join(
            f"{name}={value:+.2f}" for name, value in sorted(item["latent_delta"].items())
        )
        parts.append(
            f"{item['selector']}[{item['adjustment_reason']};{delta_text}]"
        )
    return " | ".join(parts)


def _constraint_text(item: dict[str, Any]) -> str:
    constraint_type = item["constraint_type"]
    if constraint_type == "baseline_share_cap":
        return f"baseline_cap({item['policy_id']} <= {item['max_probability']})"
    if constraint_type == "relief_share_floor":
        return f"relief_floor({item['policy_id']} >= {item['min_probability']})"
    if constraint_type == "target_gap_band":
        return (
            "gap("
            f"{item['primary_policy_id']} - {item['secondary_policy_id']} in "
            f"[{item['min_gap']},{item['max_gap']}]"
            ")"
        )
    if constraint_type == "segment_guard":
        return f"segment_guard({item['selector']}:{item['guard']})"
    raise ValueError("unsupported constraint_type")


def _baseline_share_cap(constraints: list[dict[str, Any]]) -> float:
    caps = [
        float(item["max_probability"])
        for item in constraints
        if item["constraint_type"] == "baseline_share_cap"
    ]
    return min(caps) if caps else 1.0


def _relief_share_floor(constraints: list[dict[str, Any]]) -> float:
    floors = [
        float(item["min_probability"])
        for item in constraints
        if item["constraint_type"] == "relief_share_floor"
    ]
    return max(floors) if floors else 0.0


def _target_gap_max(constraints: list[dict[str, Any]]) -> float:
    values = [
        float(item["max_gap"])
        for item in constraints
        if item["constraint_type"] == "target_gap_band"
    ]
    return max(values) if values else 0.0


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
