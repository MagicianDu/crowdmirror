from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
PROTOTYPE_PROGRAM_L1_SET_SCHEMA_VERSION = "policy-reaction-prototype-program-l1-set-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_prototype_program_l1_set(
    *,
    base_candidate: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_base_candidate(base_candidate)
    base_best = copy.deepcopy(base_candidate["best_candidate"])
    prompt_components = copy.deepcopy(base_candidate["candidate_prompt_components"])
    candidates = [
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="u01",
            variant_tag="accepted_plus_cash_floor_conservative",
            base_candidate=base_candidate,
            base_best=base_best,
            prompt_components=prompt_components,
            prototype_program=_prototype_program(
                retrieval_strategy="accepted_cash_floor_conservative",
                axis_selectors=["income_band=low", "price_stress_level=high"],
                prototype_mix=[
                    _prototype_mix(
                        family="accepted",
                        prototype_id="accepted_family_rank_guard",
                        role="rank_anchor",
                        contribution="Keep the accepted low-income ordering anchor intact.",
                    ),
                    _prototype_mix(
                        family="weak_positive",
                        prototype_id="weak_positive_family_cash_floor",
                        role="cash_floor_hint",
                        contribution="Carry only the rebate-floor hint that survived round1.",
                    ),
                ],
            ),
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="u02",
            variant_tag="accepted_plus_failure_guard",
            base_candidate=base_candidate,
            base_best=base_best,
            prompt_components=prompt_components,
            prototype_program=_prototype_program(
                retrieval_strategy="accepted_with_failure_guard",
                axis_selectors=["price_stress_level=high", "income_band=low"],
                prototype_mix=[
                    _prototype_mix(
                        family="accepted",
                        prototype_id="accepted_family_distribution_guard",
                        role="distribution_anchor",
                        contribution="Use the accepted distribution guard as the dominant retrieval prior.",
                    ),
                    _prototype_mix(
                        family="failure",
                        prototype_id="failure_family_counterexample",
                        role="negative_guard",
                        contribution="Block the baseline-overshoot pattern on the high-price axis.",
                    ),
                ],
            ),
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="u03",
            variant_tag="accepted_rank_shape_bridge",
            base_candidate=base_candidate,
            base_best=base_best,
            prompt_components=prompt_components,
            prototype_program=_prototype_program(
                retrieval_strategy="accepted_rank_shape_bridge",
                axis_selectors=["income_band=low", "price_stress_level=high"],
                prototype_mix=[
                    _prototype_mix(
                        family="accepted",
                        prototype_id="accepted_family_rank_guard",
                        role="rank_anchor",
                        contribution="Preserve low-income ordering from the accepted route.",
                    ),
                    _prototype_mix(
                        family="weak_positive",
                        prototype_id="weak_positive_family_shape_bridge",
                        role="shape_bridge",
                        contribution="Bring over only the high-price shape correction hint.",
                    ),
                ],
            ),
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="u04",
            variant_tag="tri_family_hard_recomposition",
            base_candidate=base_candidate,
            base_best=base_best,
            prompt_components=prompt_components,
            prototype_program=_prototype_program(
                retrieval_strategy="tri_family_hard_recomposition",
                axis_selectors=["income_band=low", "price_stress_level=high"],
                prototype_mix=[
                    _prototype_mix(
                        family="accepted",
                        prototype_id="accepted_family_distribution_guard",
                        role="hard_anchor",
                        contribution="Force a stricter accepted-family anchor.",
                    ),
                    _prototype_mix(
                        family="weak_positive",
                        prototype_id="weak_positive_family_cash_floor",
                        role="hard_bridge",
                        contribution="Treat the rebate-floor hint as a direct control signal.",
                    ),
                    _prototype_mix(
                        family="failure",
                        prototype_id="failure_family_rank_collapse",
                        role="hard_counterexample",
                        contribution="Explicitly penalize rank collapse through retrieval phrasing.",
                    ),
                ],
            ),
        ),
    ]
    artifact = {
        "schema_version": PROTOTYPE_PROGRAM_L1_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "prototype_program_l1_narrowed_family",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "claim_boundary": (
            "Prototype Program L1 is a narrowed retrieval-recomposition family that starts "
            "from the round1 keep/observe line and tests whether conservative recomposition "
            "can exceed the weak round1 ceiling."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_prototype_program_l1_candidate(
    candidate_set: dict[str, Any],
    *,
    candidate_id: str,
) -> dict[str, Any]:
    _validate_candidate_set(candidate_set)
    for candidate in candidate_set["candidates"]:
        if candidate["candidate_id"] == candidate_id:
            artifact = copy.deepcopy(candidate["candidate_artifact"])
            _assert_strict_json(artifact)
            return artifact
    raise ValueError("candidate_id not found in candidate_set")


def _prototype_program(
    *,
    retrieval_strategy: str,
    axis_selectors: list[str],
    prototype_mix: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "retrieval_strategy": retrieval_strategy,
        "axis_selectors": axis_selectors,
        "prototype_mix": prototype_mix,
    }


def _prototype_mix(
    *,
    family: str,
    prototype_id: str,
    role: str,
    contribution: str,
) -> dict[str, str]:
    return {
        "family": family,
        "prototype_id": prototype_id,
        "role": role,
        "contribution": contribution,
    }


def _candidate(
    *,
    artifact_id: str,
    candidate_suffix: str,
    variant_tag: str,
    base_candidate: dict[str, Any],
    base_best: dict[str, Any],
    prompt_components: dict[str, Any],
    prototype_program: dict[str, Any],
) -> dict[str, Any]:
    candidate_id = f"{artifact_id}-{candidate_suffix}"
    candidate_artifact = {
        "schema_version": S2PC_CANDIDATE_SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "generator": "prototype_program_l1_narrowed_family",
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "best_candidate": _patched_best_candidate(
            base_best,
            variant_tag=variant_tag,
            prototype_program=prototype_program,
        ),
        "candidate_prompt_components": _render_candidate_prompt_components(
            prompt_components=prompt_components,
            best_candidate=base_best,
            prototype_program=prototype_program,
        ),
        "claim_boundary": "Prototype Program L1 candidate is a runtime probe candidate only.",
    }
    _assert_strict_json(candidate_artifact)
    return {
        "candidate_id": candidate_id,
        "variant_tag": variant_tag,
        "prototype_program": prototype_program,
        "candidate_artifact": candidate_artifact,
    }


def _patched_best_candidate(
    base_best: dict[str, Any],
    *,
    variant_tag: str,
    prototype_program: dict[str, Any],
) -> dict[str, Any]:
    best_candidate = copy.deepcopy(base_best)
    patched = []
    for patch in copy.deepcopy(base_best["parameter_patches"]):
        provenance = patch.setdefault("provenance", {})
        provenance["prototype_program_l1_variant_tag"] = variant_tag
        provenance["retrieval_strategy"] = prototype_program["retrieval_strategy"]
        provenance["prototype_mix"] = copy.deepcopy(prototype_program["prototype_mix"])
        patched.append(patch)
    best_candidate["parameter_patches"] = patched
    return best_candidate


def _render_candidate_prompt_components(
    *,
    prompt_components: dict[str, Any],
    best_candidate: dict[str, Any],
    prototype_program: dict[str, Any],
) -> dict[str, Any]:
    components = copy.deepcopy(prompt_components)
    segment_prompt = components.setdefault("segment_prompt", {})
    calibration_anchor = components.setdefault("calibration_anchor", {})
    base_segment = str(best_candidate["segment"])
    policy_id = str(best_candidate["policy_id"])
    factor_ids = sorted({patch["factor_id"] for patch in best_candidate["parameter_patches"]})
    parameter_lines = [
        f"{patch['parameter_name']}={patch['parameter_value']}"
        for patch in best_candidate["parameter_patches"]
    ]
    mix_summary = " | ".join(
        f"{item['family']}:{item['prototype_id']}->{item['role']}"
        for item in prototype_program["prototype_mix"]
    )

    segment_prompt[base_segment] = " ".join(
        [
            str(segment_prompt.get(base_segment, "")),
            "Interpret this candidate through a narrowed retrieval-recomposed prototype program.",
            "Keep only the prototype signals that survived round1; suppress hard over-composition.",
        ]
    ).strip()
    calibration_anchor[base_segment] = (
        f"PROTOTYPE-L1 factors={','.join(factor_ids)}; "
        f"primary_policy={policy_id}; "
        f"retrieval_strategy={prototype_program['retrieval_strategy']}; "
        f"prototype_mix={mix_summary}; "
        f"parameters={';'.join(parameter_lines)}"
    )
    for selector in prototype_program["axis_selectors"]:
        segment_prompt[selector] = _selector_prompt(selector, prototype_program["prototype_mix"])
        calibration_anchor[selector] = _selector_anchor(selector, prototype_program["prototype_mix"])
    components["response_contract"] = (
        "Return strict JSON probabilities over the available policy alternatives."
    )
    return components


def _selector_prompt(selector: str, prototype_mix: list[dict[str, Any]]) -> str:
    prototype_names = ", ".join(item["prototype_id"] for item in prototype_mix)
    if selector == "income_band=low":
        return (
            "For low-income personas, preserve support-over-baseline ordering through a "
            f"conservative recomposed prototype set: {prototype_names}."
        )
    if selector == "price_stress_level=high":
        return (
            "For high price-stress personas, stabilize relief mass without forcing a hard "
            f"single-policy spike: {prototype_names}."
        )
    return f"Apply narrowed prototype recomposition for {selector}: {prototype_names}."


def _selector_anchor(selector: str, prototype_mix: list[dict[str, Any]]) -> str:
    parts = []
    for item in prototype_mix:
        parts.append(f"{item['family']}:{item['prototype_id']}:{item['role']}")
    return f"PROTOTYPE-L1 selector={selector}; mix={' | '.join(parts)}"


def _validate_base_candidate(candidate: dict[str, Any]) -> None:
    if candidate.get("schema_version") != S2PC_CANDIDATE_SCHEMA_VERSION:
        raise ValueError("base_candidate has unsupported schema_version")
    if not isinstance(candidate.get("best_candidate"), dict):
        raise ValueError("base_candidate missing best_candidate")
    if not isinstance(candidate.get("candidate_prompt_components"), dict):
        raise ValueError("base_candidate missing candidate_prompt_components")


def _validate_candidate_set(candidate_set: dict[str, Any]) -> None:
    if candidate_set.get("schema_version") != PROTOTYPE_PROGRAM_L1_SET_SCHEMA_VERSION:
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
        default="policy-reaction-prototype-program-l1-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-prototype-program-l1-current-001.json"
        ),
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()

    candidate_set = build_policy_reaction_prototype_program_l1_set(
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
        extracted = extract_policy_reaction_prototype_program_l1_candidate(
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
