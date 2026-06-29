from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
AXIS_WEAKNESS_SCHEMA_VERSION = "policy-reaction-axis-weakness-v1"
PROTOTYPE_PROGRAM_L0_SET_SCHEMA_VERSION = "policy-reaction-prototype-program-l0-set-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_prototype_program_l0_set(
    *,
    base_candidate: dict[str, Any],
    axis_weakness: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_base_candidate(base_candidate)
    _validate_axis_weakness(axis_weakness)

    base_best = copy.deepcopy(base_candidate["best_candidate"])
    prompt_components = copy.deepcopy(base_candidate["candidate_prompt_components"])
    persistent_weakness = copy.deepcopy(axis_weakness["persistent_weakness"])
    rank_selector = str(persistent_weakness["worst_rank_segment"])
    jsd_selector = str(persistent_weakness["worst_jsd_segment"])

    candidates = [
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="r01",
            variant_tag="accepted_rank_anchor",
            base_candidate=base_candidate,
            base_best=base_best,
            prompt_components=prompt_components,
            prototype_program=_prototype_program(
                retrieval_strategy="accepted_anchor_recomposition",
                axis_selectors=[rank_selector, jsd_selector],
                prototype_mix=[
                    _prototype_mix(
                        family="accepted",
                        prototype_id="accepted_family_rank_guard",
                        role="primary_anchor",
                        contribution="Preserve support-over-baseline ordering on the low-income weakness axis.",
                    ),
                    _prototype_mix(
                        family="accepted",
                        prototype_id="accepted_family_distribution_guard",
                        role="shape_stabilizer",
                        contribution="Retain the held-out-safe distribution shape discipline from the accepted family.",
                    ),
                ],
            ),
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="r02",
            variant_tag="accepted_with_weak_positive_bridge",
            base_candidate=base_candidate,
            base_best=base_best,
            prompt_components=prompt_components,
            prototype_program=_prototype_program(
                retrieval_strategy="accepted_plus_weak_positive_bridge",
                axis_selectors=[rank_selector, jsd_selector],
                prototype_mix=[
                    _prototype_mix(
                        family="accepted",
                        prototype_id="accepted_family_rank_guard",
                        role="rank_anchor",
                        contribution="Keep the low-income ordering fix tied to the accepted family.",
                    ),
                    _prototype_mix(
                        family="weak_positive",
                        prototype_id="weak_positive_family_cash_floor",
                        role="soft_bridge",
                        contribution="Import the weak-positive cash-floor tendency without treating it as accepted evidence.",
                    ),
                ],
            ),
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="r03",
            variant_tag="failure_aware_dual_axis_bridge",
            base_candidate=base_candidate,
            base_best=base_best,
            prompt_components=prompt_components,
            prototype_program=_prototype_program(
                retrieval_strategy="weak_positive_bridge_with_failure_counterexample",
                axis_selectors=[rank_selector, jsd_selector],
                prototype_mix=[
                    _prototype_mix(
                        family="accepted",
                        prototype_id="accepted_family_rank_guard",
                        role="safety_anchor",
                        contribution="Provide the conservative ranking anchor that remains compatible with held-out gating.",
                    ),
                    _prototype_mix(
                        family="weak_positive",
                        prototype_id="weak_positive_family_shape_bridge",
                        role="shape_bridge",
                        contribution="Borrow the partial high-price correction signal as a soft prototype only.",
                    ),
                    _prototype_mix(
                        family="failure",
                        prototype_id="failure_family_counterexample",
                        role="negative_retrieval",
                        contribution="Explicitly encode what not to do on the high-price axis to avoid baseline overshoot.",
                    ),
                ],
            ),
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="r04",
            variant_tag="tri_family_conservative_program",
            base_candidate=base_candidate,
            base_best=base_best,
            prompt_components=prompt_components,
            prototype_program=_prototype_program(
                retrieval_strategy="tri_family_conservative_recomposition",
                axis_selectors=[rank_selector, jsd_selector],
                prototype_mix=[
                    _prototype_mix(
                        family="accepted",
                        prototype_id="accepted_family_distribution_guard",
                        role="distribution_anchor",
                        contribution="Use the accepted family as the dominant retrieval prior.",
                    ),
                    _prototype_mix(
                        family="weak_positive",
                        prototype_id="weak_positive_family_cash_floor",
                        role="cash_floor_hint",
                        contribution="Carry over mild rebate support reinforcement as a non-binding hint.",
                    ),
                    _prototype_mix(
                        family="failure",
                        prototype_id="failure_family_rank_collapse",
                        role="counterexample_guard",
                        contribution="Keep the known rank-collapse pattern out of the recomposed program.",
                    ),
                ],
            ),
        ),
    ]
    artifact = {
        "schema_version": PROTOTYPE_PROGRAM_L0_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "prototype_program_l0_retrieval_family",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "axis_weakness_reference": axis_weakness["artifact_id"],
        "persistent_weakness": persistent_weakness,
        "retrieval_family_summary": {
            "accepted_family_count": 2,
            "weak_positive_family_count": 1,
            "failure_family_count": 1,
        },
        "candidate_count": len(candidates),
        "candidates": candidates,
        "claim_boundary": (
            "Prototype Program L0 is retrieval-side candidate-generation evidence only; "
            "accepted, weak-positive, and failure families are recomposed here without runtime claims."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_prototype_program_l0_candidate(
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-candidate", required=True)
    parser.add_argument("--axis-weakness", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-prototype-program-l0-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-prototype-program-l0-current-001.json"
        ),
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()

    candidate_set = build_policy_reaction_prototype_program_l0_set(
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
        extracted = extract_policy_reaction_prototype_program_l0_candidate(
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
        "generator": "prototype_program_l0_retrieval_family",
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
        "claim_boundary": "Prototype-program candidate is a runtime probe candidate only.",
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
        provenance["prototype_program_l0_variant_tag"] = variant_tag
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
            "Interpret this candidate through a retrieval-recomposed prototype program.",
            "Use accepted-family prototypes as anchors, weak-positive prototypes as soft hints, and failure-family prototypes as counterexamples only.",
        ]
    ).strip()
    calibration_anchor[base_segment] = (
        f"PROTOTYPE-L0 factors={','.join(factor_ids)}; "
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
            "For low-income personas, keep active support options ahead of the no-new-support baseline. "
            f"Retrieve and reconcile these prototypes: {prototype_names}."
        )
    if selector == "price_stress_level=high":
        return (
            "For high price-stress personas, preserve relief mass and avoid baseline overshoot. "
            f"Use failure-family prototypes only as negative retrieval cues: {prototype_names}."
        )
    return f"Apply retrieval-recomposed prototype control for {selector}: {prototype_names}."


def _selector_anchor(selector: str, prototype_mix: list[dict[str, Any]]) -> str:
    parts = []
    for item in prototype_mix:
        parts.append(f"{item['family']}:{item['prototype_id']}:{item['role']}")
    return f"PROTOTYPE-L0 selector={selector}; mix={' | '.join(parts)}"


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
    if candidate_set.get("schema_version") != PROTOTYPE_PROGRAM_L0_SET_SCHEMA_VERSION:
        raise ValueError("candidate_set has unsupported schema_version")
    if not isinstance(candidate_set.get("candidates"), list) or not candidate_set["candidates"]:
        raise ValueError("candidate_set missing candidates")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
