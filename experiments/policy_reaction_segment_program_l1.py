from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
SEGMENT_PROGRAM_L1_SET_SCHEMA_VERSION = "policy-reaction-segment-program-l1-set-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_segment_program_l1_candidate_set(
    *,
    base_candidate: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_base_candidate(base_candidate)
    base_best = copy.deepcopy(base_candidate["best_candidate"])
    candidates = [
        _candidate(
            base_candidate=base_candidate,
            base_best=base_best,
            artifact_id=artifact_id,
            candidate_suffix="t01",
            variant_tag="working_family_cash_floor_focus",
            narrowing_program={
                "narrowing_intent": (
                    "Keep the mixed numeric-qualitative family, but collapse it onto the "
                    "working-family cash-floor signal and remove low-value narrative spread."
                ),
                "target_selectors": [
                    "working_family_price_stressed",
                    "price_stress_level=high",
                ],
                "coordination_mode": "cash_floor_primary",
                "response_constraints": [
                    {
                        "constraint_type": "min_policy_probability",
                        "selector": "working_family_price_stressed",
                        "policy_id": "cash_cost_of_living_rebate",
                        "min_probability": 0.412,
                    },
                    {
                        "constraint_type": "max_baseline_probability",
                        "selector": "price_stress_level=high",
                        "policy_id": "baseline_no_new_support",
                        "max_probability": 0.238,
                    },
                ],
            },
        ),
        _candidate(
            base_candidate=base_candidate,
            base_best=base_best,
            artifact_id=artifact_id,
            candidate_suffix="t02",
            variant_tag="low_income_support_order_focus",
            narrowing_program={
                "narrowing_intent": (
                    "Retain the round1 mixed family but focus on low-income support ordering "
                    "and reduce the direct high-price numeric burden."
                ),
                "target_selectors": [
                    "income_band=low",
                    "working_family_price_stressed",
                ],
                "coordination_mode": "support_order_primary",
                "response_constraints": [
                    {
                        "constraint_type": "max_baseline_probability",
                        "selector": "income_band=low",
                        "policy_id": "baseline_no_new_support",
                        "max_probability": 0.242,
                    },
                    {
                        "constraint_type": "min_policy_probability",
                        "selector": "working_family_price_stressed",
                        "policy_id": "cash_cost_of_living_rebate",
                        "min_probability": 0.404,
                    },
                ],
            },
        ),
        _candidate(
            base_candidate=base_candidate,
            base_best=base_best,
            artifact_id=artifact_id,
            candidate_suffix="t03",
            variant_tag="dual_axis_soft_sync",
            narrowing_program={
                "narrowing_intent": (
                    "Test whether the weak round1 signal survives after replacing hard numeric "
                    "balance with a softer dual-axis synchronized wording."
                ),
                "target_selectors": [
                    "income_band=low",
                    "price_stress_level=high",
                ],
                "coordination_mode": "soft_dual_axis_sync",
                "response_constraints": [
                    {
                        "constraint_type": "max_baseline_probability",
                        "selector": "price_stress_level=high",
                        "policy_id": "baseline_no_new_support",
                        "max_probability": 0.244,
                    }
                ],
            },
        ),
        _candidate(
            base_candidate=base_candidate,
            base_best=base_best,
            artifact_id=artifact_id,
            candidate_suffix="t04",
            variant_tag="high_price_numeric_push",
            narrowing_program={
                "narrowing_intent": (
                    "Push the round1 mixed family toward an explicit high-price numeric repair "
                    "to check whether the weak ceiling was caused by under-correction."
                ),
                "target_selectors": [
                    "price_stress_level=high",
                    "working_family_price_stressed",
                ],
                "coordination_mode": "numeric_high_price_push",
                "response_constraints": [
                    {
                        "constraint_type": "min_policy_probability",
                        "selector": "price_stress_level=high",
                        "policy_id": "cash_cost_of_living_rebate",
                        "min_probability": 0.318,
                    },
                    {
                        "constraint_type": "max_baseline_probability",
                        "selector": "price_stress_level=high",
                        "policy_id": "baseline_no_new_support",
                        "max_probability": 0.232,
                    },
                ],
            },
        ),
    ]
    artifact = {
        "schema_version": SEGMENT_PROGRAM_L1_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "segment_program_l1_narrowed_family",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "candidate_count": len(candidates),
        "program_axes": [
            "working_family_cash_floor",
            "low_income_support_order",
            "dual_axis_soft_sync",
            "high_price_numeric_push",
        ],
        "candidates": candidates,
        "claim_boundary": (
            "Segment Program L1 is a narrowed segment-program family that starts from the "
            "round1 weak-positive candidate and probes whether the weak ceiling can be exceeded."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_segment_program_l1_candidate(
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
                "candidate_prompt_components": copy.deepcopy(
                    candidate["candidate_prompt_components"]
                ),
                "claim_boundary": "Segment Program L1 candidate is a runtime probe candidate only.",
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
    narrowing_program: dict[str, Any],
) -> dict[str, Any]:
    candidate = copy.deepcopy(base_best)
    candidate["parameter_patches"] = _annotated_parameter_patches(
        candidate["parameter_patches"],
        variant_tag=variant_tag,
        narrowing_program=narrowing_program,
    )
    prompt_components = _render_candidate_prompt_components(
        base_prompt_components=base_candidate["candidate_prompt_components"],
        candidate=candidate,
        variant_tag=variant_tag,
        narrowing_program=narrowing_program,
    )
    return {
        "candidate_id": f"{artifact_id}-{candidate_suffix}",
        "candidate_index": 1,
        "segment": candidate["segment"],
        "policy_id": candidate["policy_id"],
        "proxy_score": round(float(candidate["proxy_score"]), 12),
        "variant_tag": variant_tag,
        "narrowing_program": narrowing_program,
        "parameter_patches": candidate["parameter_patches"],
        "candidate_prompt_components": prompt_components,
    }


def _annotated_parameter_patches(
    parameter_patches: list[dict[str, Any]],
    *,
    variant_tag: str,
    narrowing_program: dict[str, Any],
) -> list[dict[str, Any]]:
    patches = []
    for patch in copy.deepcopy(parameter_patches):
        provenance = patch.setdefault("provenance", {})
        provenance["segment_program_l1_variant_tag"] = variant_tag
        provenance["narrowing_program"] = copy.deepcopy(narrowing_program)
        patches.append(patch)
    return patches


def _render_candidate_prompt_components(
    *,
    base_prompt_components: dict[str, Any],
    candidate: dict[str, Any],
    variant_tag: str,
    narrowing_program: dict[str, Any],
) -> dict[str, Any]:
    prompt_components = copy.deepcopy(base_prompt_components)
    factor_ids = sorted({patch["factor_id"] for patch in candidate["parameter_patches"]})
    parameter_lines = [
        f"{patch['parameter_name']}={patch['parameter_value']}"
        for patch in candidate["parameter_patches"]
    ]
    constraint_lines = [
        _constraint_text(item)
        for item in narrowing_program["response_constraints"]
    ]
    segment_prompt = prompt_components.setdefault("segment_prompt", {})
    calibration_anchor = prompt_components.setdefault("calibration_anchor", {})
    base_segment = candidate["segment"]

    segment_prompt[base_segment] = " ".join(
        [
            str(segment_prompt.get(base_segment, "")),
            "Interpret this candidate through a narrowed segment program.",
            "Prefer the strongest synchronized signal only; drop weak decorative spread.",
        ]
    ).strip()
    calibration_anchor[base_segment] = (
        f"SEGMENT-PROGRAM-L1 variant={variant_tag}; "
        f"factors={','.join(factor_ids)}; "
        f"primary_policy={candidate['policy_id']}; "
        f"coordination_mode={narrowing_program['coordination_mode']}; "
        f"constraints={' | '.join(constraint_lines)}; "
        f"parameters={';'.join(parameter_lines)}"
    )
    for selector in narrowing_program["target_selectors"]:
        segment_prompt[selector] = (
            f"Apply narrowed synchronized control for {selector}. "
            f"Mode: {narrowing_program['coordination_mode']}. "
            f"{narrowing_program['narrowing_intent']}"
        )
        calibration_anchor[selector] = (
            f"SEGMENT-PROGRAM-L1 selector={selector}; "
            f"mode={narrowing_program['coordination_mode']}; "
            f"variant={variant_tag}; "
            f"constraints={' | '.join(constraint_lines)}"
        )
    prompt_components["response_contract"] = (
        "Return strict JSON probabilities over the available policy alternatives."
    )
    return prompt_components


def _constraint_text(item: dict[str, Any]) -> str:
    constraint_type = item["constraint_type"]
    if constraint_type == "min_policy_probability":
        return (
            f"min_policy_probability({item['selector']}; "
            f"{item['policy_id']} >= {item['min_probability']})"
        )
    if constraint_type == "max_baseline_probability":
        return (
            f"max_baseline_probability({item['selector']}; "
            f"{item['policy_id']} <= {item['max_probability']})"
        )
    raise ValueError("unsupported constraint_type")


def _validate_base_candidate(candidate: dict[str, Any]) -> None:
    if candidate.get("schema_version") != S2PC_CANDIDATE_SCHEMA_VERSION:
        raise ValueError("base_candidate has unsupported schema_version")
    if not isinstance(candidate.get("best_candidate"), dict):
        raise ValueError("base_candidate missing best_candidate")
    if not isinstance(candidate.get("candidate_prompt_components"), dict):
        raise ValueError("base_candidate missing candidate_prompt_components")


def _validate_candidate_set(candidate_set: dict[str, Any]) -> None:
    if candidate_set.get("schema_version") != SEGMENT_PROGRAM_L1_SET_SCHEMA_VERSION:
        raise ValueError("candidate_set has unsupported schema_version")
    if not isinstance(candidate_set.get("candidates"), list) or not candidate_set["candidates"]:
        raise ValueError("candidate_set missing candidates")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-candidate", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-segment-program-l1-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-segment-program-l1-current-001.json"
        ),
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()

    candidate_set = build_policy_reaction_segment_program_l1_candidate_set(
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
        extracted = extract_policy_reaction_segment_program_l1_candidate(
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
