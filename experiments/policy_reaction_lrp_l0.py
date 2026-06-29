from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
LRP_CANDIDATE_SET_SCHEMA_VERSION = "policy-reaction-lrp-candidate-set-v1"
AXIS_WEAKNESS_SCHEMA_VERSION = "policy-reaction-axis-weakness-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_lrp_l0_candidate_set(
    *,
    base_candidate: dict[str, Any],
    axis_weakness: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_base_candidate(base_candidate)
    _validate_axis_weakness(axis_weakness)
    base_best = copy.deepcopy(base_candidate["best_candidate"])
    persistent_weakness = copy.deepcopy(axis_weakness["persistent_weakness"])
    worst_rank_selector = str(persistent_weakness["worst_rank_segment"])
    worst_jsd_selector = str(persistent_weakness["worst_jsd_segment"])

    candidates = [
        _candidate(
            base_candidate=base_candidate,
            base_best=base_best,
            artifact_id=artifact_id,
            candidate_suffix="p01",
            variant_tag="low_income_compensatory_program",
            global_latents={
                "baseline_inertia": -0.10,
                "relief_preference": 0.22,
                "price_stress_reactivity": 0.04,
                "targeting_sensitivity": 0.18,
            },
            regime_rules=[
                {
                    "selector": worst_rank_selector,
                    "program_intent": "compensate low-income ranking drift through relief-oriented response formation",
                    "latent_delta": {
                        "baseline_inertia": -0.08,
                        "relief_preference": 0.12,
                        "price_stress_reactivity": 0.0,
                        "targeting_sensitivity": 0.10,
                    },
                }
            ],
            response_constraints=[
                {"constraint_type": "rank_guard", "selector": worst_rank_selector, "guard": "support_options_over_baseline"},
                {"constraint_type": "relief_floor", "policy_id": "cash_cost_of_living_rebate", "min_probability": 0.28},
            ],
        ),
        _candidate(
            base_candidate=base_candidate,
            base_best=base_best,
            artifact_id=artifact_id,
            candidate_suffix="p02",
            variant_tag="high_price_reactive_program",
            global_latents={
                "baseline_inertia": -0.06,
                "relief_preference": 0.16,
                "price_stress_reactivity": 0.24,
                "targeting_sensitivity": 0.06,
            },
            regime_rules=[
                {
                    "selector": worst_jsd_selector,
                    "program_intent": "react to price-stress distortion by reducing baseline drift and preserving relief mass",
                    "latent_delta": {
                        "baseline_inertia": -0.06,
                        "relief_preference": 0.10,
                        "price_stress_reactivity": 0.14,
                        "targeting_sensitivity": 0.0,
                    },
                }
            ],
            response_constraints=[
                {"constraint_type": "distribution_shape_guard", "selector": worst_jsd_selector, "max_baseline_probability": 0.24},
                {"constraint_type": "relief_floor", "policy_id": "cash_cost_of_living_rebate", "min_probability": 0.30},
            ],
        ),
        _candidate(
            base_candidate=base_candidate,
            base_best=base_best,
            artifact_id=artifact_id,
            candidate_suffix="p03",
            variant_tag="dual_axis_balanced_program",
            global_latents={
                "baseline_inertia": -0.08,
                "relief_preference": 0.18,
                "price_stress_reactivity": 0.16,
                "targeting_sensitivity": 0.14,
            },
            regime_rules=[
                {
                    "selector": worst_rank_selector,
                    "program_intent": "stabilize low-income ordering without making the response fully targeted-only",
                    "latent_delta": {
                        "baseline_inertia": -0.05,
                        "relief_preference": 0.08,
                        "price_stress_reactivity": 0.0,
                        "targeting_sensitivity": 0.08,
                    },
                },
                {
                    "selector": worst_jsd_selector,
                    "program_intent": "smooth price-stress response while keeping cash rebate support from collapsing",
                    "latent_delta": {
                        "baseline_inertia": -0.04,
                        "relief_preference": 0.06,
                        "price_stress_reactivity": 0.10,
                        "targeting_sensitivity": 0.0,
                    },
                },
            ],
            response_constraints=[
                {"constraint_type": "rank_guard", "selector": worst_rank_selector, "guard": "preserve_relief_ordering"},
                {"constraint_type": "distribution_shape_guard", "selector": worst_jsd_selector, "max_baseline_probability": 0.245},
                {"constraint_type": "baseline_cap", "policy_id": "baseline_no_new_support", "max_probability": 0.26},
            ],
        ),
        _candidate(
            base_candidate=base_candidate,
            base_best=base_best,
            artifact_id=artifact_id,
            candidate_suffix="p04",
            variant_tag="dual_axis_targeted_program",
            global_latents={
                "baseline_inertia": -0.12,
                "relief_preference": 0.24,
                "price_stress_reactivity": 0.18,
                "targeting_sensitivity": 0.20,
            },
            regime_rules=[
                {
                    "selector": worst_rank_selector,
                    "program_intent": "apply low-income compensatory regime through stronger targeting sensitivity",
                    "latent_delta": {
                        "baseline_inertia": -0.08,
                        "relief_preference": 0.12,
                        "price_stress_reactivity": 0.0,
                        "targeting_sensitivity": 0.12,
                    },
                },
                {
                    "selector": worst_jsd_selector,
                    "program_intent": "apply high-price compensatory regime with stronger relief stabilization",
                    "latent_delta": {
                        "baseline_inertia": -0.06,
                        "relief_preference": 0.10,
                        "price_stress_reactivity": 0.12,
                        "targeting_sensitivity": 0.02,
                    },
                },
            ],
            response_constraints=[
                {"constraint_type": "rank_guard", "selector": worst_rank_selector, "guard": "strict_support_over_baseline"},
                {"constraint_type": "distribution_shape_guard", "selector": worst_jsd_selector, "max_baseline_probability": 0.235},
                {"constraint_type": "relief_floor", "policy_id": "cash_cost_of_living_rebate", "min_probability": 0.31},
                {"constraint_type": "baseline_cap", "policy_id": "baseline_no_new_support", "max_probability": 0.245},
            ],
        ),
    ]
    artifact = {
        "schema_version": LRP_CANDIDATE_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "lrp_l0_latent_response_program_compiler",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "axis_weakness_reference": axis_weakness["artifact_id"],
        "persistent_weakness": persistent_weakness,
        "candidate_count": len(candidates),
        "latent_response_schema": [
            "baseline_inertia",
            "relief_preference",
            "price_stress_reactivity",
            "targeting_sensitivity",
        ],
        "candidates": candidates,
        "claim_boundary": "LRP L0 candidate set is representation and candidate-generation evidence only.",
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_lrp_candidate(
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
                "source_split_contract": copy.deepcopy(candidate_set["source_split_contract"]),
                "best_candidate": {
                    "candidate_index": candidate["candidate_index"],
                    "segment": candidate["segment"],
                    "policy_id": candidate["policy_id"],
                    "proxy_score": candidate["proxy_score"],
                    "parameter_patches": copy.deepcopy(candidate["parameter_patches"]),
                },
                "candidate_prompt_components": copy.deepcopy(candidate["candidate_prompt_components"]),
                "claim_boundary": "LRP candidate is a runtime probe candidate only.",
            }
            _assert_strict_json(artifact)
            return artifact
    raise ValueError("candidate_id not found in candidate_set")


def _candidate(
    *,
    base_candidate: dict[str, Any],
    base_best: dict[str, Any],
    artifact_id: str,
    candidate_suffix: str,
    variant_tag: str,
    global_latents: dict[str, float],
    regime_rules: list[dict[str, Any]],
    response_constraints: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate = copy.deepcopy(base_best)
    candidate["parameter_patches"] = _compiled_parameter_patches(
        candidate["parameter_patches"],
        global_latents=global_latents,
        regime_rules=regime_rules,
        response_constraints=response_constraints,
        variant_tag=variant_tag,
    )
    prompt_components = _render_candidate_prompt_components(
        base_prompt_components=base_candidate["candidate_prompt_components"],
        candidate=candidate,
        global_latents=global_latents,
        regime_rules=regime_rules,
        response_constraints=response_constraints,
    )
    return {
        "candidate_id": f"{artifact_id}-{candidate_suffix}",
        "candidate_index": 1,
        "segment": candidate["segment"],
        "policy_id": candidate["policy_id"],
        "proxy_score": round(float(candidate["proxy_score"]), 12),
        "variant_tag": variant_tag,
        "latent_response_program": {
            "global_latents": global_latents,
            "regime_rules": regime_rules,
            "response_constraints": response_constraints,
        },
        "parameter_patches": candidate["parameter_patches"],
        "candidate_prompt_components": prompt_components,
    }


def _compiled_parameter_patches(
    base_patches: list[dict[str, Any]],
    *,
    global_latents: dict[str, float],
    regime_rules: list[dict[str, Any]],
    response_constraints: list[dict[str, Any]],
    variant_tag: str,
) -> list[dict[str, Any]]:
    patches: list[dict[str, Any]] = []
    for patch in copy.deepcopy(base_patches):
        name = patch["parameter_name"]
        value = float(patch["parameter_value"])
        bounds = patch.get("parameter_bounds")
        lower = float(bounds["min"]) if isinstance(bounds, dict) and "min" in bounds else value - 1.0
        upper = float(bounds["max"]) if isinstance(bounds, dict) and "max" in bounds else value + 1.0
        if name == "prior_anchor_strength":
            value += global_latents.get("relief_preference", 0.0) * 0.05
            value -= global_latents.get("baseline_inertia", 0.0) * 0.03
            value += global_latents.get("targeting_sensitivity", 0.0) * 0.04
        elif name == "trust_multiplier":
            value += global_latents.get("relief_preference", 0.0) * 0.04
            value += global_latents.get("price_stress_reactivity", 0.0) * 0.03
            value -= global_latents.get("baseline_inertia", 0.0) * 0.02
        patch["parameter_value"] = round(min(upper, max(lower, value)), 12)
        provenance = patch.setdefault("provenance", {})
        provenance["lrp_l0_variant_tag"] = variant_tag
        provenance["global_latents"] = copy.deepcopy(global_latents)
        provenance["regime_rules"] = copy.deepcopy(regime_rules)
        provenance["response_constraints"] = copy.deepcopy(response_constraints)
        patches.append(patch)
    return patches


def _render_candidate_prompt_components(
    *,
    base_prompt_components: dict[str, Any],
    candidate: dict[str, Any],
    global_latents: dict[str, float],
    regime_rules: list[dict[str, Any]],
    response_constraints: list[dict[str, Any]],
) -> dict[str, Any]:
    prompt_components = copy.deepcopy(base_prompt_components)
    factor_ids = sorted({patch["factor_id"] for patch in candidate["parameter_patches"]})
    parameter_lines = [
        f"{patch['parameter_name']}={patch['parameter_value']}"
        for patch in candidate["parameter_patches"]
    ]
    latent_lines = [
        f"{name}={value:+.2f}" for name, value in sorted(global_latents.items())
    ]
    constraint_lines = [_constraint_text(item) for item in response_constraints]

    segment_prompt = prompt_components.setdefault("segment_prompt", {})
    calibration_anchor = prompt_components.setdefault("calibration_anchor", {})

    for selector, text in list(segment_prompt.items()):
        if selector in calibration_anchor or selector == candidate["segment"]:
            segment_prompt[selector] = " ".join(
                [
                    str(text),
                    "Interpret this response through the latent response program instead of a direct local patch.",
                    "Keep full-distribution coherence under the declared regime rules.",
                ]
            )

    calibration_anchor[candidate["segment"]] = (
        f"LRP-L0 factors={','.join(factor_ids)}; "
        f"primary_policy={candidate['policy_id']}; "
        f"globals={';'.join(latent_lines)}; "
        f"constraints={' | '.join(constraint_lines)}; "
        f"parameters={';'.join(parameter_lines)}"
    )

    for rule in regime_rules:
        selector = rule["selector"]
        deltas = ";".join(
            f"{name}={value:+.2f}" for name, value in sorted(rule["latent_delta"].items())
        )
        segment_prompt[selector] = " ".join(
            [
                f"Apply the latent response regime for {selector}.",
                f"Intent: {rule['program_intent']}.",
                "Do not treat this as a local prompt rewrite; treat it as a coordinated response-program shift.",
            ]
        )
        calibration_anchor[selector] = (
            f"LRP-L0 selector={selector}; intent={rule['program_intent']}; deltas={deltas}"
        )

    prompt_components["response_contract"] = (
        "Return strict JSON probabilities over the available policy alternatives."
    )
    return prompt_components


def _constraint_text(item: dict[str, Any]) -> str:
    constraint_type = item["constraint_type"]
    if constraint_type == "rank_guard":
        return f"rank_guard({item['selector']} -> {item['guard']})"
    if constraint_type == "distribution_shape_guard":
        return (
            f"shape_guard({item['selector']}; "
            f"max_baseline={item['max_baseline_probability']})"
        )
    if constraint_type == "baseline_cap":
        return f"baseline_cap({item['policy_id']} <= {item['max_probability']})"
    if constraint_type == "relief_floor":
        return f"relief_floor({item['policy_id']} >= {item['min_probability']})"
    raise ValueError("unsupported constraint_type")


def _validate_base_candidate(candidate: dict[str, Any]) -> None:
    if candidate.get("schema_version") != S2PC_CANDIDATE_SCHEMA_VERSION:
        raise ValueError("base_candidate has unsupported schema_version")
    if not isinstance(candidate.get("best_candidate"), dict):
        raise ValueError("base_candidate missing best_candidate")
    if not isinstance(candidate.get("candidate_prompt_components"), dict):
        raise ValueError("base_candidate missing candidate_prompt_components")


def _validate_axis_weakness(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != AXIS_WEAKNESS_SCHEMA_VERSION:
        raise ValueError("axis_weakness has unsupported schema_version")
    if not isinstance(artifact.get("persistent_weakness"), dict):
        raise ValueError("axis_weakness missing persistent_weakness")


def _validate_candidate_set(candidate_set: dict[str, Any]) -> None:
    if candidate_set.get("schema_version") != LRP_CANDIDATE_SET_SCHEMA_VERSION:
        raise ValueError("candidate_set has unsupported schema_version")
    if not isinstance(candidate_set.get("candidates"), list) or not candidate_set["candidates"]:
        raise ValueError("candidate_set missing candidates")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-candidate", required=True)
    parser.add_argument("--axis-weakness", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-lrp-l0-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-lrp-l0-current-001.json"
        ),
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()
    candidate_set = build_policy_reaction_lrp_l0_candidate_set(
        base_candidate=load_json_artifact(args.base_candidate),
        axis_weakness=load_json_artifact(args.axis_weakness),
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
        extracted = extract_policy_reaction_lrp_candidate(
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


if __name__ == "__main__":
    raise SystemExit(main())
