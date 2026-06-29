from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
LRP_CANDIDATE_SET_SCHEMA_VERSION = "policy-reaction-lrp-candidate-set-v1"
LRP_L1_SET_SCHEMA_VERSION = "policy-reaction-lrp-l1-set-v1"
RUNTIME_EFFECT_MATRIX_SCHEMA_VERSION = "policy-reaction-s2pc-runtime-effect-matrix-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_lrp_l1_candidate_set(
    *,
    l0_candidate_set: dict[str, Any],
    l0_runtime_matrix: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_l0_candidate_set(l0_candidate_set)
    _validate_runtime_matrix(l0_runtime_matrix)

    candidates_by_id = {
        candidate["candidate_id"]: candidate
        for candidate in l0_candidate_set["candidates"]
    }
    improved_ids = [
        item["s2pc_candidate_id"]
        for item in l0_runtime_matrix["candidate_results"]
        if item["overall_status"] == "improved"
    ]
    if len(improved_ids) < 2:
        raise ValueError("LRP L1 requires at least two improved L0 candidates")

    p01 = copy.deepcopy(candidates_by_id[improved_ids[0]])
    p02 = copy.deepcopy(candidates_by_id[improved_ids[1]])
    candidates = [
        _candidate(
            source_candidate=p01,
            artifact_id=artifact_id,
            candidate_suffix="q01",
            variant_tag="low_income_milder_compensation",
            global_latent_scale=0.75,
            rule_scales={"income_band=low": 0.75},
            constraint_overrides={
                "relief_floor": 0.27,
            },
        ),
        _candidate(
            source_candidate=p01,
            artifact_id=artifact_id,
            candidate_suffix="q02",
            variant_tag="low_income_rank_only_minimal",
            global_latent_scale=0.55,
            rule_scales={"income_band=low": 0.65},
            constraint_overrides={
                "relief_floor": 0.26,
                "drop_non_rank_constraints": True,
            },
        ),
        _candidate(
            source_candidate=p02,
            artifact_id=artifact_id,
            candidate_suffix="q03",
            variant_tag="high_price_shape_only_softened",
            global_latent_scale=0.65,
            rule_scales={"price_stress_level=high": 0.65},
            constraint_overrides={
                "shape_guard": 0.245,
                "relief_floor": 0.285,
            },
        ),
        _candidate(
            source_candidate=_merge_candidates(p01, p02),
            artifact_id=artifact_id,
            candidate_suffix="q04",
            variant_tag="dual_axis_light_hybrid",
            global_latent_scale=0.50,
            rule_scales={
                "income_band=low": 0.55,
                "price_stress_level=high": 0.55,
            },
            constraint_overrides={
                "shape_guard": 0.247,
                "relief_floor": 0.275,
                "baseline_cap": 0.255,
            },
        ),
    ]
    artifact = {
        "schema_version": LRP_L1_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "lrp_l1_narrowed_family",
        "base_candidate_set_artifact_id": l0_candidate_set["artifact_id"],
        "base_runtime_matrix_artifact_id": l0_runtime_matrix["artifact_id"],
        "source_split_contract": copy.deepcopy(l0_candidate_set["source_split_contract"]),
        "candidate_count": len(candidates),
        "selected_l0_candidates": improved_ids,
        "candidates": candidates,
        "claim_boundary": "LRP L1 is a narrowed candidate-generation artifact only.",
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_lrp_l1_candidate(
    candidate_set: dict[str, Any],
    *,
    candidate_id: str,
) -> dict[str, Any]:
    _validate_l1_candidate_set(candidate_set)
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
    source_candidate: dict[str, Any],
    artifact_id: str,
    candidate_suffix: str,
    variant_tag: str,
    global_latent_scale: float,
    rule_scales: dict[str, float],
    constraint_overrides: dict[str, Any],
) -> dict[str, Any]:
    candidate = copy.deepcopy(source_candidate)
    program = candidate["latent_response_program"]
    program["global_latents"] = {
        key: round(float(value) * global_latent_scale, 12)
        for key, value in program["global_latents"].items()
    }
    scaled_rules = []
    for rule in program["regime_rules"]:
        scale = rule_scales.get(rule["selector"], 1.0)
        new_rule = copy.deepcopy(rule)
        new_rule["latent_delta"] = {
            key: round(float(value) * scale, 12)
            for key, value in new_rule["latent_delta"].items()
        }
        scaled_rules.append(new_rule)
    program["regime_rules"] = scaled_rules
    program["response_constraints"] = _rewrite_constraints(
        program["response_constraints"],
        constraint_overrides=constraint_overrides,
    )
    candidate["candidate_id"] = f"{artifact_id}-{candidate_suffix}"
    candidate["variant_tag"] = variant_tag
    candidate["latent_response_program"] = program
    candidate["parameter_patches"] = _rewrite_parameter_patches(
        candidate["parameter_patches"],
        global_latents=program["global_latents"],
        regime_rules=program["regime_rules"],
        response_constraints=program["response_constraints"],
        variant_tag=variant_tag,
    )
    candidate["candidate_prompt_components"] = _rewrite_prompt_components(
        candidate["candidate_prompt_components"],
        segment=candidate["segment"],
        policy_id=candidate["policy_id"],
        parameter_patches=candidate["parameter_patches"],
        global_latents=program["global_latents"],
        regime_rules=program["regime_rules"],
        response_constraints=program["response_constraints"],
    )
    return candidate


def _merge_candidates(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(left)
    right_program = right["latent_response_program"]
    left_program = merged["latent_response_program"]
    merged_program = {
        "global_latents": {
            key: round(
                (float(left_program["global_latents"].get(key, 0.0)) + float(right_program["global_latents"].get(key, 0.0))) / 2.0,
                12,
            )
            for key in set(left_program["global_latents"]) | set(right_program["global_latents"])
        },
        "regime_rules": copy.deepcopy(left_program["regime_rules"]) + copy.deepcopy(right_program["regime_rules"]),
        "response_constraints": copy.deepcopy(left_program["response_constraints"]) + copy.deepcopy(right_program["response_constraints"]),
    }
    merged["latent_response_program"] = merged_program
    return merged


def _rewrite_constraints(
    constraints: list[dict[str, Any]],
    *,
    constraint_overrides: dict[str, Any],
) -> list[dict[str, Any]]:
    result = []
    for item in copy.deepcopy(constraints):
        if constraint_overrides.get("drop_non_rank_constraints") and item["constraint_type"] != "rank_guard":
            continue
        if item["constraint_type"] == "relief_floor" and "relief_floor" in constraint_overrides:
            item["min_probability"] = constraint_overrides["relief_floor"]
        if item["constraint_type"] == "distribution_shape_guard" and "shape_guard" in constraint_overrides:
            item["max_baseline_probability"] = constraint_overrides["shape_guard"]
        result.append(item)
    if "baseline_cap" in constraint_overrides:
        result.append(
            {
                "constraint_type": "baseline_cap",
                "policy_id": "baseline_no_new_support",
                "max_probability": constraint_overrides["baseline_cap"],
            }
        )
    return result


def _rewrite_parameter_patches(
    parameter_patches: list[dict[str, Any]],
    *,
    global_latents: dict[str, float],
    regime_rules: list[dict[str, Any]],
    response_constraints: list[dict[str, Any]],
    variant_tag: str,
) -> list[dict[str, Any]]:
    patches = []
    relief = float(global_latents.get("relief_preference", 0.0))
    price = float(global_latents.get("price_stress_reactivity", 0.0))
    targeting = float(global_latents.get("targeting_sensitivity", 0.0))
    baseline = float(global_latents.get("baseline_inertia", 0.0))
    for patch in copy.deepcopy(parameter_patches):
        name = patch["parameter_name"]
        lower = float(patch["parameter_bounds"]["min"])
        upper = float(patch["parameter_bounds"]["max"])
        value = float(patch["parameter_value"])
        if name == "prior_anchor_strength":
            value += relief * 0.02 + targeting * 0.02 - baseline * 0.01
        elif name == "trust_multiplier":
            value += relief * 0.015 + price * 0.015 - baseline * 0.01
        patch["parameter_value"] = round(min(upper, max(lower, value)), 12)
        provenance = patch.setdefault("provenance", {})
        provenance["lrp_l1_variant_tag"] = variant_tag
        provenance["global_latents"] = copy.deepcopy(global_latents)
        provenance["regime_rules"] = copy.deepcopy(regime_rules)
        provenance["response_constraints"] = copy.deepcopy(response_constraints)
        patches.append(patch)
    return patches


def _rewrite_prompt_components(
    prompt_components: dict[str, Any],
    *,
    segment: str,
    policy_id: str,
    parameter_patches: list[dict[str, Any]],
    global_latents: dict[str, float],
    regime_rules: list[dict[str, Any]],
    response_constraints: list[dict[str, Any]],
) -> dict[str, Any]:
    rewritten = copy.deepcopy(prompt_components)
    factor_ids = sorted({patch["factor_id"] for patch in parameter_patches})
    parameter_lines = [
        f"{patch['parameter_name']}={patch['parameter_value']}"
        for patch in parameter_patches
    ]
    latent_lines = [
        f"{name}={value:+.2f}" for name, value in sorted(global_latents.items())
    ]
    constraint_lines = [_constraint_text(item) for item in response_constraints]
    rewritten.setdefault("segment_prompt", {})
    rewritten.setdefault("calibration_anchor", {})
    rewritten["segment_prompt"][segment] = " ".join(
        [
            "Use the persona's calibrated policy-reaction parameters for this segment.",
            "Apply the narrowed latent response program with minimal coupling.",
            "Only preserve selector-specific compensatory behavior that survives the L0 prefilter.",
        ]
    )
    rewritten["calibration_anchor"][segment] = (
        f"LRP-L1 factors={','.join(factor_ids)}; "
        f"primary_policy={policy_id}; "
        f"globals={';'.join(latent_lines)}; "
        f"constraints={' | '.join(constraint_lines)}; "
        f"parameters={';'.join(parameter_lines)}"
    )
    for rule in regime_rules:
        selector = rule["selector"]
        deltas = ";".join(
            f"{name}={value:+.2f}" for name, value in sorted(rule["latent_delta"].items())
        )
        rewritten["segment_prompt"][selector] = " ".join(
            [
                f"Apply the narrowed latent regime for {selector}.",
                f"Intent: {rule['program_intent']}.",
                "Keep the response shift minimal and selector-local.",
            ]
        )
        rewritten["calibration_anchor"][selector] = (
            f"LRP-L1 selector={selector}; intent={rule['program_intent']}; deltas={deltas}"
        )
    return rewritten


def _constraint_text(item: dict[str, Any]) -> str:
    constraint_type = item["constraint_type"]
    if constraint_type == "rank_guard":
        return f"rank_guard({item['selector']} -> {item['guard']})"
    if constraint_type == "distribution_shape_guard":
        return f"shape_guard({item['selector']}; max_baseline={item['max_baseline_probability']})"
    if constraint_type == "baseline_cap":
        return f"baseline_cap({item['policy_id']} <= {item['max_probability']})"
    if constraint_type == "relief_floor":
        return f"relief_floor({item['policy_id']} >= {item['min_probability']})"
    raise ValueError("unsupported constraint_type")


def _validate_l0_candidate_set(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != LRP_CANDIDATE_SET_SCHEMA_VERSION:
        raise ValueError("l0_candidate_set has unsupported schema_version")
    if not isinstance(artifact.get("candidates"), list) or not artifact["candidates"]:
        raise ValueError("l0_candidate_set missing candidates")


def _validate_runtime_matrix(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != RUNTIME_EFFECT_MATRIX_SCHEMA_VERSION:
        raise ValueError("runtime_matrix has unsupported schema_version")
    if not isinstance(artifact.get("candidate_results"), list) or not artifact["candidate_results"]:
        raise ValueError("runtime_matrix missing candidate_results")


def _validate_l1_candidate_set(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != LRP_L1_SET_SCHEMA_VERSION:
        raise ValueError("candidate_set has unsupported schema_version")
    if not isinstance(artifact.get("candidates"), list) or not artifact["candidates"]:
        raise ValueError("candidate_set missing candidates")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--l0-candidate-set", required=True)
    parser.add_argument("--l0-runtime-matrix", required=True)
    parser.add_argument("--artifact-id", default="policy-reaction-lrp-l1-current-001")
    parser.add_argument(
        "--output",
        default="experiments/results/policy_reaction_benchmark/policy-reaction-lrp-l1-current-001.json",
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()
    candidate_set = build_policy_reaction_lrp_l1_candidate_set(
        l0_candidate_set=load_json_artifact(args.l0_candidate_set),
        l0_runtime_matrix=load_json_artifact(args.l0_runtime_matrix),
        artifact_id=args.artifact_id,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(candidate_set, indent=2, sort_keys=True, allow_nan=False) + "\n")
    summary = {
        "artifact_id": candidate_set["artifact_id"],
        "output": str(output_path),
        "status": "generated",
        "candidate_count": candidate_set["candidate_count"],
    }
    if args.extract_candidate_id and args.extract_output:
        extracted = extract_policy_reaction_lrp_l1_candidate(candidate_set, candidate_id=args.extract_candidate_id)
        extracted_path = Path(args.extract_output)
        extracted_path.parent.mkdir(parents=True, exist_ok=True)
        extracted_path.write_text(json.dumps(extracted, indent=2, sort_keys=True, allow_nan=False) + "\n")
        summary["extracted_candidate_id"] = args.extract_candidate_id
        summary["extracted_output"] = str(extracted_path)
    print(json.dumps(summary, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
