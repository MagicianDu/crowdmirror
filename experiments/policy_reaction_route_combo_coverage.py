from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
ROUTE_COMBO_SET_SCHEMA_VERSION = "policy-reaction-route-combo-coverage-set-v1"

COMBO_DEFINITIONS: dict[str, dict[str, Any]] = {
    "r2b-lrp-narrowed": {
        "label": "R2-B narrowed latent response program",
        "primary_role": "lrp",
        "secondary_role": None,
        "representation": "latent response program",
        "optimizer": "conservative latent recomposition",
        "system_level": "axis/segment hybrid",
        "selectors": ["income_band=low", "price_stress_level=high"],
    },
    "r2c-constraint-narrowed": {
        "label": "R2-C narrowed constraint program",
        "primary_role": "constraint",
        "secondary_role": None,
        "representation": "distribution/ordering constraint program",
        "optimizer": "conservative constraint recomposition",
        "system_level": "population/axis hybrid",
        "selectors": ["income_band=low", "price_stress_level=high"],
    },
    "r3a-segment-latent": {
        "label": "R3-A segment + latent hybrid",
        "primary_role": "segment",
        "secondary_role": "lrp",
        "representation": "segment program plus latent response program",
        "optimizer": "cross-family recomposition",
        "system_level": "segment/axis hybrid",
        "selectors": ["working_family_price_stressed", "income_band=low"],
    },
    "r3b-segment-constraint": {
        "label": "R3-B segment + constraint hybrid",
        "primary_role": "segment",
        "secondary_role": "constraint",
        "representation": "segment program plus constraint program",
        "optimizer": "cross-family recomposition",
        "system_level": "segment/population hybrid",
        "selectors": ["working_family_price_stressed", "price_stress_level=high"],
    },
    "r3c-latent-prototype": {
        "label": "R3-C latent + prototype hybrid",
        "primary_role": "lrp",
        "secondary_role": "prototype",
        "representation": "latent response program plus prototype retrieval",
        "optimizer": "cross-family recomposition",
        "system_level": "axis/persona hybrid",
        "selectors": ["income_band=low", "price_stress_level=high"],
    },
    "r3d-constraint-prototype": {
        "label": "R3-D constraint + prototype hybrid",
        "primary_role": "constraint",
        "secondary_role": "prototype",
        "representation": "constraint program plus prototype retrieval",
        "optimizer": "cross-family recomposition",
        "system_level": "population/persona hybrid",
        "selectors": ["income_band=low", "price_stress_level=high"],
    },
}

VARIANTS = [
    {
        "suffix": "v01",
        "tag": "conservative_bridge",
        "strength": 0.35,
        "intent": "Use only the shared signal between source families and avoid hard output forcing.",
    },
    {
        "suffix": "v02",
        "tag": "balanced_bridge",
        "strength": 0.50,
        "intent": "Balance the primary route signal with the secondary route signal.",
    },
    {
        "suffix": "v03",
        "tag": "axis_focus_bridge",
        "strength": 0.62,
        "intent": "Focus the route combination on the persistent axis-level weaknesses.",
    },
    {
        "suffix": "v04",
        "tag": "strong_counterfactual_bridge",
        "strength": 0.78,
        "intent": "Stress-test whether a stronger combined correction can break the weak ceiling.",
    },
]


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_route_combo_candidate_set(
    *,
    combo_id: str,
    artifact_id: str,
    primary_candidate: dict[str, Any],
    secondary_candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if combo_id not in COMBO_DEFINITIONS:
        raise ValueError("unsupported combo_id")
    _validate_candidate(primary_candidate)
    if secondary_candidate is not None:
        _validate_candidate(secondary_candidate)
    definition = COMBO_DEFINITIONS[combo_id]
    if definition["secondary_role"] is not None and secondary_candidate is None:
        raise ValueError("secondary_candidate is required for this combo_id")

    candidates = [
        _candidate(
            artifact_id=artifact_id,
            combo_id=combo_id,
            definition=definition,
            primary_candidate=primary_candidate,
            secondary_candidate=secondary_candidate,
            variant=variant,
        )
        for variant in VARIANTS
    ]
    artifact = {
        "schema_version": ROUTE_COMBO_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "route_combo_coverage_candidate_builder",
        "combo_id": combo_id,
        "combo_label": definition["label"],
        "representation": definition["representation"],
        "optimizer": definition["optimizer"],
        "system_level": definition["system_level"],
        "primary_candidate_id": primary_candidate["candidate_id"],
        "secondary_candidate_id": (
            secondary_candidate["candidate_id"] if secondary_candidate else None
        ),
        "source_split_contract": copy.deepcopy(primary_candidate["source_split_contract"]),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "claim_boundary": (
            "Route-combo coverage candidates are finite-grid probes for route coverage; "
            "they are not accepted method evidence until held-out runtime gates pass."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_route_combo_candidate(
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


def _candidate(
    *,
    artifact_id: str,
    combo_id: str,
    definition: dict[str, Any],
    primary_candidate: dict[str, Any],
    secondary_candidate: dict[str, Any] | None,
    variant: dict[str, Any],
) -> dict[str, Any]:
    candidate_id = f"{artifact_id}-{variant['suffix']}"
    best_candidate = _patched_best_candidate(
        primary_candidate["best_candidate"],
        combo_id=combo_id,
        definition=definition,
        secondary_candidate=secondary_candidate,
        variant=variant,
    )
    prompt_components = _render_candidate_prompt_components(
        primary_components=primary_candidate["candidate_prompt_components"],
        secondary_components=(
            secondary_candidate["candidate_prompt_components"]
            if secondary_candidate
            else None
        ),
        best_candidate=best_candidate,
        combo_id=combo_id,
        definition=definition,
        secondary_candidate=secondary_candidate,
        variant=variant,
    )
    candidate_artifact = {
        "schema_version": S2PC_CANDIDATE_SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "generator": "route_combo_coverage_candidate_builder",
        "source_split_contract": copy.deepcopy(primary_candidate["source_split_contract"]),
        "best_candidate": best_candidate,
        "candidate_prompt_components": prompt_components,
        "claim_boundary": "Route-combo candidate is a runtime probe candidate only.",
    }
    _assert_strict_json(candidate_artifact)
    return {
        "candidate_id": candidate_id,
        "variant_tag": variant["tag"],
        "combo_id": combo_id,
        "combo_label": definition["label"],
        "combo_program": {
            "representation": definition["representation"],
            "optimizer": definition["optimizer"],
            "system_level": definition["system_level"],
            "selectors": copy.deepcopy(definition["selectors"]),
            "variant": copy.deepcopy(variant),
            "secondary_candidate_id": (
                secondary_candidate["candidate_id"] if secondary_candidate else None
            ),
        },
        "candidate_artifact": candidate_artifact,
    }


def _patched_best_candidate(
    base_best: dict[str, Any],
    *,
    combo_id: str,
    definition: dict[str, Any],
    secondary_candidate: dict[str, Any] | None,
    variant: dict[str, Any],
) -> dict[str, Any]:
    best_candidate = copy.deepcopy(base_best)
    patched = []
    strength = float(variant["strength"])
    for patch in copy.deepcopy(base_best["parameter_patches"]):
        value = float(patch["parameter_value"])
        bounds = patch.get("parameter_bounds", {})
        lower = float(bounds.get("min", value - 1.0)) if isinstance(bounds, dict) else value - 1.0
        upper = float(bounds.get("max", value + 1.0)) if isinstance(bounds, dict) else value + 1.0
        name = str(patch["parameter_name"])
        secondary_hint = _secondary_patch_value(secondary_candidate, name)
        if secondary_hint is not None:
            value = value * (1.0 - strength * 0.18) + secondary_hint * (strength * 0.18)
        if "constraint" in definition["representation"] and name in {
            "prior_anchor_strength",
            "relief_bias",
        }:
            value += strength * 0.012
        if "latent" in definition["representation"] and name in {
            "trust_multiplier",
            "price_salience_multiplier",
        }:
            value += strength * 0.01
        if variant["tag"] == "strong_counterfactual_bridge":
            value += strength * 0.008
        patch["parameter_value"] = round(min(upper, max(lower, value)), 12)
        provenance = patch.setdefault("provenance", {})
        provenance["route_combo_id"] = combo_id
        provenance["route_combo_variant_tag"] = variant["tag"]
        provenance["representation"] = definition["representation"]
        provenance["optimizer"] = definition["optimizer"]
        provenance["system_level"] = definition["system_level"]
        if secondary_candidate is not None:
            provenance["secondary_candidate_id"] = secondary_candidate["candidate_id"]
        patched.append(patch)
    best_candidate["parameter_patches"] = patched
    return best_candidate


def _secondary_patch_value(
    secondary_candidate: dict[str, Any] | None,
    parameter_name: str,
) -> float | None:
    if secondary_candidate is None:
        return None
    for patch in secondary_candidate["best_candidate"].get("parameter_patches", []):
        if patch.get("parameter_name") == parameter_name:
            return float(patch["parameter_value"])
    return None


def _render_candidate_prompt_components(
    *,
    primary_components: dict[str, Any],
    secondary_components: dict[str, Any] | None,
    best_candidate: dict[str, Any],
    combo_id: str,
    definition: dict[str, Any],
    secondary_candidate: dict[str, Any] | None,
    variant: dict[str, Any],
) -> dict[str, Any]:
    components = copy.deepcopy(primary_components)
    segment_prompt = components.setdefault("segment_prompt", {})
    calibration_anchor = components.setdefault("calibration_anchor", {})
    base_segment = str(best_candidate["segment"])
    policy_id = str(best_candidate["policy_id"])
    factor_ids = sorted({patch["factor_id"] for patch in best_candidate["parameter_patches"]})
    parameter_lines = [
        f"{patch['parameter_name']}={patch['parameter_value']}"
        for patch in best_candidate["parameter_patches"]
    ]
    secondary_summary = (
        secondary_candidate["candidate_id"] if secondary_candidate is not None else "none"
    )
    segment_prompt[base_segment] = " ".join(
        [
            str(segment_prompt.get(base_segment, "")),
            "Interpret this candidate through the finite route-combo coverage program.",
            f"Combo: {definition['label']}. Variant: {variant['tag']}.",
            variant["intent"],
        ]
    ).strip()
    calibration_anchor[base_segment] = (
        f"ROUTE-COMBO combo_id={combo_id}; variant={variant['tag']}; "
        f"representation={definition['representation']}; optimizer={definition['optimizer']}; "
        f"system_level={definition['system_level']}; primary_policy={policy_id}; "
        f"secondary={secondary_summary}; factors={','.join(factor_ids)}; "
        f"parameters={';'.join(parameter_lines)}"
    )
    secondary_prompts = (
        secondary_components.get("segment_prompt", {}) if secondary_components else {}
    )
    secondary_anchors = (
        secondary_components.get("calibration_anchor", {}) if secondary_components else {}
    )
    for selector in definition["selectors"]:
        borrowed_prompt = str(secondary_prompts.get(selector, "")).strip()
        borrowed_anchor = str(secondary_anchors.get(selector, "")).strip()
        segment_prompt[selector] = " ".join(
            [
                f"Apply route-combo coverage control for {selector}.",
                f"Combo: {definition['label']}.",
                f"Variant intent: {variant['intent']}",
                f"Secondary prompt hint: {borrowed_prompt}" if borrowed_prompt else "",
            ]
        ).strip()
        calibration_anchor[selector] = " ".join(
            [
                f"ROUTE-COMBO selector={selector}; combo_id={combo_id}; variant={variant['tag']}; strength={variant['strength']}.",
                f"Secondary anchor hint: {borrowed_anchor}" if borrowed_anchor else "",
            ]
        ).strip()
    components["response_contract"] = (
        "Return strict JSON probabilities over the available policy alternatives."
    )
    return components


def _validate_candidate(candidate: dict[str, Any]) -> None:
    if candidate.get("schema_version") != S2PC_CANDIDATE_SCHEMA_VERSION:
        raise ValueError("candidate has unsupported schema_version")
    if not isinstance(candidate.get("best_candidate"), dict):
        raise ValueError("candidate missing best_candidate")
    if not isinstance(candidate.get("candidate_prompt_components"), dict):
        raise ValueError("candidate missing candidate_prompt_components")
    if not isinstance(candidate.get("source_split_contract"), dict):
        raise ValueError("candidate missing source_split_contract")


def _validate_candidate_set(candidate_set: dict[str, Any]) -> None:
    if candidate_set.get("schema_version") != ROUTE_COMBO_SET_SCHEMA_VERSION:
        raise ValueError("candidate_set has unsupported schema_version")
    if not isinstance(candidate_set.get("candidates"), list) or not candidate_set["candidates"]:
        raise ValueError("candidate_set missing candidates")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--combo-id", required=True, choices=sorted(COMBO_DEFINITIONS))
    parser.add_argument("--primary-candidate", required=True)
    parser.add_argument("--secondary-candidate")
    parser.add_argument("--artifact-id")
    parser.add_argument("--output")
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()

    artifact_id = args.artifact_id or f"policy-reaction-route-combo-{args.combo_id}-current-001"
    output = args.output or (
        "experiments/results/policy_reaction_benchmark/"
        f"{artifact_id}.json"
    )
    candidate_set = build_policy_reaction_route_combo_candidate_set(
        combo_id=args.combo_id,
        artifact_id=artifact_id,
        primary_candidate=load_json_artifact(args.primary_candidate),
        secondary_candidate=(
            load_json_artifact(args.secondary_candidate)
            if args.secondary_candidate
            else None
        ),
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(candidate_set, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    summary = {
        "artifact_id": candidate_set["artifact_id"],
        "combo_id": args.combo_id,
        "candidate_count": candidate_set["candidate_count"],
        "output": str(output_path),
        "status": "generated",
    }
    if args.extract_candidate_id and args.extract_output:
        extracted = extract_policy_reaction_route_combo_candidate(
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
