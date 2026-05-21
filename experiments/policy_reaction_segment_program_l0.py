from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
SEGMENT_PROGRAM_L0_SET_SCHEMA_VERSION = "policy-reaction-segment-program-l0-set-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_segment_program_l0_candidate_set(
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
            candidate_suffix="s01",
            variant_tag="soft_guard_family",
            synchronized_program={
                "global_program_intent": (
                    "Keep the accepted LCDU L3 profile, but add a soft synchronized "
                    "guard so vulnerable and working-family segments move together."
                ),
                "synchronized_segments": [
                    {
                        "selector": "fixed_income_inflation_stressed",
                        "anchor_mode": "soft_guard",
                        "instruction": (
                            "Preserve the fixed-income relief preference while avoiding "
                            "a sharp rebound to baseline_no_new_support."
                        ),
                        "anchor_text": (
                            "food_subsidy_expansion stays primary; cash_cost_of_living_rebate "
                            "remains viable as secondary support."
                        ),
                    },
                    {
                        "selector": "working_family_price_stressed",
                        "anchor_mode": "soft_guard",
                        "instruction": (
                            "Mirror the fixed-income support ordering without forcing a "
                            "full low-income response pattern."
                        ),
                        "anchor_text": (
                            "cash_cost_of_living_rebate should not collapse below the guarded "
                            "working-family band."
                        ),
                    },
                ],
                "coordination_rules": [
                    {
                        "rule_type": "support_order_guard",
                        "source_selector": "fixed_income_inflation_stressed",
                        "target_selector": "working_family_price_stressed",
                        "guard": "shared_relief_ordering",
                    }
                ],
                "response_constraints": [
                    {
                        "constraint_type": "max_baseline_probability",
                        "selector": "working_family_price_stressed",
                        "policy_id": "baseline_no_new_support",
                        "max_probability": 0.255,
                    },
                    {
                        "constraint_type": "min_policy_probability",
                        "selector": "working_family_price_stressed",
                        "policy_id": "cash_cost_of_living_rebate",
                        "min_probability": 0.405,
                    },
                ],
            },
        ),
        _candidate(
            base_candidate=base_candidate,
            base_best=base_best,
            artifact_id=artifact_id,
            candidate_suffix="s02",
            variant_tag="mixed_numeric_qualitative_family",
            synchronized_program={
                "global_program_intent": (
                    "Combine numeric guardrails with qualitative synchronized guidance so "
                    "high-price and low-income stress signals stay aligned."
                ),
                "synchronized_segments": [
                    {
                        "selector": "fixed_income_inflation_stressed",
                        "anchor_mode": "numeric_anchor",
                        "instruction": (
                            "Keep the accepted relief-first ordering as the numeric anchor "
                            "for the synchronized program."
                        ),
                        "anchor_text": (
                            "food_subsidy_expansion primary, baseline_no_new_support capped "
                            "below the accepted guard band."
                        ),
                    },
                    {
                        "selector": "income_band=low",
                        "anchor_mode": "qualitative_guard",
                        "instruction": (
                            "When low-income pressure is active, phrase support as compensatory "
                            "rather than punitive or status-quo preserving."
                        ),
                        "anchor_text": "support-oriented wording should dominate baseline-retention wording.",
                    },
                    {
                        "selector": "price_stress_level=high",
                        "anchor_mode": "numeric_anchor",
                        "instruction": (
                            "Under high price stress, keep rebate support visible while "
                            "avoiding a single-policy spike."
                        ),
                        "anchor_text": (
                            "cash_cost_of_living_rebate remains above a stability floor and "
                            "baseline stays under a local cap."
                        ),
                    },
                ],
                "coordination_rules": [
                    {
                        "rule_type": "dual_axis_sync",
                        "selectors": ["income_band=low", "price_stress_level=high"],
                        "guard": "qualitative_numeric_balance",
                    }
                ],
                "response_constraints": [
                    {
                        "constraint_type": "min_policy_probability",
                        "selector": "price_stress_level=high",
                        "policy_id": "cash_cost_of_living_rebate",
                        "min_probability": 0.295,
                    },
                    {
                        "constraint_type": "max_baseline_probability",
                        "selector": "price_stress_level=high",
                        "policy_id": "baseline_no_new_support",
                        "max_probability": 0.245,
                    },
                ],
            },
        ),
        _candidate(
            base_candidate=base_candidate,
            base_best=base_best,
            artifact_id=artifact_id,
            candidate_suffix="s03",
            variant_tag="segment_crossover_family",
            synchronized_program={
                "global_program_intent": (
                    "Transfer the accepted working-family guard into a wider synchronized "
                    "program and let low-income relief cues cross over into price-stress handling."
                ),
                "synchronized_segments": [
                    {
                        "selector": "fixed_income_inflation_stressed",
                        "anchor_mode": "crossover_anchor",
                        "instruction": (
                            "Use the accepted fixed-income anchor as the control segment for "
                            "cross-segment redistribution wording."
                        ),
                        "anchor_text": "fixed-income segment remains the stable anchor for family-level synchronization.",
                    },
                    {
                        "selector": "working_family_price_stressed",
                        "anchor_mode": "crossover_anchor",
                        "instruction": (
                            "Borrow the fixed-income relief ordering while keeping the "
                            "working-family cash-rebate floor explicit."
                        ),
                        "anchor_text": "carry forward the accepted LCDU L3 h02 guard profile.",
                    },
                    {
                        "selector": "income_band=low",
                        "anchor_mode": "crossover_anchor",
                        "instruction": (
                            "Let low-income compensation language propagate into the synchronized "
                            "program only when it reinforces relief-first ordering."
                        ),
                        "anchor_text": "import support-over-baseline logic from the vulnerable-segment pathway.",
                    },
                ],
                "coordination_rules": [
                    {
                        "rule_type": "segment_crossover",
                        "source_selector": "income_band=low",
                        "target_selector": "working_family_price_stressed",
                        "guard": "relief_bias_transfer",
                    },
                    {
                        "rule_type": "segment_crossover",
                        "source_selector": "fixed_income_inflation_stressed",
                        "target_selector": "income_band=low",
                        "guard": "anchor_stability_transfer",
                    },
                ],
                "response_constraints": [
                    {
                        "constraint_type": "min_policy_probability",
                        "selector": "working_family_price_stressed",
                        "policy_id": "cash_cost_of_living_rebate",
                        "min_probability": 0.41,
                    },
                    {
                        "constraint_type": "max_baseline_probability",
                        "selector": "income_band=low",
                        "policy_id": "baseline_no_new_support",
                        "max_probability": 0.25,
                    },
                ],
            },
        ),
        _candidate(
            base_candidate=base_candidate,
            base_best=base_best,
            artifact_id=artifact_id,
            candidate_suffix="s04",
            variant_tag="selective_anchor_heavy_family",
            synchronized_program={
                "global_program_intent": (
                    "Use anchor-heavy synchronization on the few segments that matter most "
                    "and keep the rest of the distribution governed by the accepted base profile."
                ),
                "synchronized_segments": [
                    {
                        "selector": "fixed_income_inflation_stressed",
                        "anchor_mode": "anchor_heavy",
                        "instruction": (
                            "Treat the accepted fixed-income parameterization as the central "
                            "anchor and keep all local edits subordinate to it."
                        ),
                        "anchor_text": "primary relief anchor must stay stable and fully specified.",
                    },
                    {
                        "selector": "working_family_price_stressed",
                        "anchor_mode": "anchor_heavy",
                        "instruction": (
                            "Keep the working-family prompt tightly coupled to explicit guard "
                            "numbers instead of qualitative drift."
                        ),
                        "anchor_text": (
                            "max food_subsidy_expansion 0.247; min cash_cost_of_living_rebate 0.414."
                        ),
                    },
                    {
                        "selector": "price_stress_level=high",
                        "anchor_mode": "anchor_heavy",
                        "instruction": (
                            "Give high-price contexts a compact, explicit anchor so rebate "
                            "support remains synchronized with the working-family guard."
                        ),
                        "anchor_text": (
                            "cash_cost_of_living_rebate should remain an explicit stabilizer under "
                            "high price stress."
                        ),
                    },
                ],
                "coordination_rules": [
                    {
                        "rule_type": "anchor_priority",
                        "selectors": [
                            "fixed_income_inflation_stressed",
                            "working_family_price_stressed",
                            "price_stress_level=high",
                        ],
                        "guard": "anchor_heavy",
                    }
                ],
                "response_constraints": [
                    {
                        "constraint_type": "min_policy_probability",
                        "selector": "working_family_price_stressed",
                        "policy_id": "cash_cost_of_living_rebate",
                        "min_probability": 0.414,
                    },
                    {
                        "constraint_type": "max_policy_probability",
                        "selector": "working_family_price_stressed",
                        "policy_id": "food_subsidy_expansion",
                        "max_probability": 0.247,
                    },
                    {
                        "constraint_type": "max_baseline_probability",
                        "selector": "price_stress_level=high",
                        "policy_id": "baseline_no_new_support",
                        "max_probability": 0.24,
                    },
                ],
            },
        ),
    ]
    artifact = {
        "schema_version": SEGMENT_PROGRAM_L0_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "segment_program_l0_family_builder",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "candidate_count": len(candidates),
        "program_axes": [
            "soft_guard",
            "qualitative_anchor",
            "cross_segment_transfer",
            "numeric_anchor",
        ],
        "candidates": candidates,
        "claim_boundary": (
            "Segment Program L0 is a segment-level synchronized prompt-anchor family only."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_segment_program_candidate(
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
                "claim_boundary": "Segment Program candidate is a runtime probe candidate only.",
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
    synchronized_program: dict[str, Any],
) -> dict[str, Any]:
    candidate = copy.deepcopy(base_best)
    candidate["parameter_patches"] = _annotated_parameter_patches(
        candidate["parameter_patches"],
        variant_tag=variant_tag,
        synchronized_program=synchronized_program,
    )
    prompt_components = _render_candidate_prompt_components(
        base_prompt_components=base_candidate["candidate_prompt_components"],
        candidate=candidate,
        variant_tag=variant_tag,
        synchronized_program=synchronized_program,
    )
    return {
        "candidate_id": f"{artifact_id}-{candidate_suffix}",
        "candidate_index": 1,
        "segment": candidate["segment"],
        "policy_id": candidate["policy_id"],
        "proxy_score": round(float(candidate["proxy_score"]), 12),
        "variant_tag": variant_tag,
        "synchronized_program": synchronized_program,
        "parameter_patches": candidate["parameter_patches"],
        "candidate_prompt_components": prompt_components,
    }


def _annotated_parameter_patches(
    parameter_patches: list[dict[str, Any]],
    *,
    variant_tag: str,
    synchronized_program: dict[str, Any],
) -> list[dict[str, Any]]:
    patches = []
    for patch in copy.deepcopy(parameter_patches):
        provenance = patch.setdefault("provenance", {})
        provenance["segment_program_l0_variant_tag"] = variant_tag
        provenance["synchronized_program"] = copy.deepcopy(synchronized_program)
        patches.append(patch)
    return patches


def _render_candidate_prompt_components(
    *,
    base_prompt_components: dict[str, Any],
    candidate: dict[str, Any],
    variant_tag: str,
    synchronized_program: dict[str, Any],
) -> dict[str, Any]:
    prompt_components = copy.deepcopy(base_prompt_components)
    factor_ids = sorted({patch["factor_id"] for patch in candidate["parameter_patches"]})
    parameter_lines = [
        f"{patch['parameter_name']}={patch['parameter_value']}"
        for patch in candidate["parameter_patches"]
    ]
    constraint_lines = [
        _constraint_text(item)
        for item in synchronized_program["response_constraints"]
    ]
    segment_prompt = prompt_components.setdefault("segment_prompt", {})
    calibration_anchor = prompt_components.setdefault("calibration_anchor", {})

    segment_prompt[candidate["segment"]] = " ".join(
        [
            str(segment_prompt.get(candidate["segment"], "")),
            "Interpret this candidate through a synchronized segment program.",
            "Keep prompt wording and numeric anchors coordinated across declared selectors.",
        ]
    ).strip()
    calibration_anchor[candidate["segment"]] = (
        f"SEGMENT-PROGRAM-L0 variant={variant_tag}; "
        f"factors={','.join(factor_ids)}; "
        f"primary_policy={candidate['policy_id']}; "
        f"constraints={' | '.join(constraint_lines)}; "
        f"parameters={';'.join(parameter_lines)}"
    )

    for item in synchronized_program["synchronized_segments"]:
        selector = item["selector"]
        segment_prompt[selector] = " ".join(
            [
                f"Apply synchronized program for {selector}.",
                f"Mode: {item['anchor_mode']}.",
                item["instruction"],
            ]
        )
        calibration_anchor[selector] = (
            f"SEGMENT-PROGRAM-L0 selector={selector}; "
            f"mode={item['anchor_mode']}; "
            f"variant={variant_tag}; "
            f"anchor={item['anchor_text']}"
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
    if constraint_type == "max_policy_probability":
        return (
            f"max_policy_probability({item['selector']}; "
            f"{item['policy_id']} <= {item['max_probability']})"
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
    if candidate_set.get("schema_version") != SEGMENT_PROGRAM_L0_SET_SCHEMA_VERSION:
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
        default="policy-reaction-segment-program-l0-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-segment-program-l0-current-001.json"
        ),
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()
    candidate_set = build_policy_reaction_segment_program_l0_candidate_set(
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
        extracted = extract_policy_reaction_segment_program_candidate(
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
