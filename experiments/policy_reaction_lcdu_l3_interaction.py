from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
LCDU_INTERACTION_SET_SCHEMA_VERSION = "policy-reaction-lcdu-interaction-set-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_lcdu_l3_interaction_set(
    *,
    base_candidate: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_base_candidate(base_candidate)
    prompt_components = base_candidate["candidate_prompt_components"]
    base_best = copy.deepcopy(base_candidate["best_candidate"])
    base_contract = copy.deepcopy(base_candidate["source_split_contract"])
    base_segment = base_best["segment"]
    working_family = "working_family_price_stressed"

    quantitative_prompt = prompt_components["segment_prompt"][working_family]
    quantitative_anchor = prompt_components["calibration_anchor"][working_family]
    qualitative_prompt = (
        "Keep this segment near its calibration-split baseline response profile. "
        "Prefer cash_cost_of_living_rebate over food_subsidy_expansion when they conflict, "
        "and avoid food-subsidy overshoot."
    )
    qualitative_anchor = (
        "LCDU-L3 interaction_guard=working_family; preserve baseline-like policy ordering."
    )

    candidates = [
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="i01",
            variant_tag="numeric_prompt_numeric_anchor",
            base_best=base_best,
            base_contract=base_contract,
            base_segment=base_segment,
            base_segment_prompt=prompt_components["segment_prompt"][base_segment],
            base_segment_anchor=prompt_components["calibration_anchor"][base_segment],
            working_family_prompt=quantitative_prompt,
            working_family_anchor=quantitative_anchor,
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="i02",
            variant_tag="numeric_prompt_qualitative_anchor",
            base_best=base_best,
            base_contract=base_contract,
            base_segment=base_segment,
            base_segment_prompt=prompt_components["segment_prompt"][base_segment],
            base_segment_anchor=prompt_components["calibration_anchor"][base_segment],
            working_family_prompt=quantitative_prompt,
            working_family_anchor=qualitative_anchor,
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="i03",
            variant_tag="qualitative_prompt_numeric_anchor",
            base_best=base_best,
            base_contract=base_contract,
            base_segment=base_segment,
            base_segment_prompt=prompt_components["segment_prompt"][base_segment],
            base_segment_anchor=prompt_components["calibration_anchor"][base_segment],
            working_family_prompt=qualitative_prompt,
            working_family_anchor=quantitative_anchor,
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="i04",
            variant_tag="qualitative_prompt_qualitative_anchor",
            base_best=base_best,
            base_contract=base_contract,
            base_segment=base_segment,
            base_segment_prompt=prompt_components["segment_prompt"][base_segment],
            base_segment_anchor=prompt_components["calibration_anchor"][base_segment],
            working_family_prompt=qualitative_prompt,
            working_family_anchor=qualitative_anchor,
        ),
    ]
    artifact = {
        "schema_version": LCDU_INTERACTION_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "lcdu_l3_prompt_anchor_interaction_family",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": base_contract,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "claim_boundary": "LCDU L3 interaction set is explanation evidence only.",
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_lcdu_l3_interaction_candidate(
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
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-lcdu-l3-interaction-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-lcdu-l3-interaction-current-001.json"
        ),
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()

    candidate_set = build_policy_reaction_lcdu_l3_interaction_set(
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
        extracted = extract_policy_reaction_lcdu_l3_interaction_candidate(
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
    prompt_components = candidate.get("candidate_prompt_components")
    if not isinstance(prompt_components, dict):
        raise ValueError("base_candidate missing candidate_prompt_components")
    for namespace in ("segment_prompt", "calibration_anchor"):
        if not isinstance(prompt_components.get(namespace), dict):
            raise ValueError(f"base_candidate missing {namespace}")
    working_family = "working_family_price_stressed"
    if working_family not in prompt_components["segment_prompt"]:
        raise ValueError("base_candidate missing working_family segment_prompt")
    if working_family not in prompt_components["calibration_anchor"]:
        raise ValueError("base_candidate missing working_family calibration_anchor")


def _validate_candidate_set(candidate_set: dict[str, Any]) -> None:
    if candidate_set.get("schema_version") != LCDU_INTERACTION_SET_SCHEMA_VERSION:
        raise ValueError("candidate_set has unsupported schema_version")
    candidates = candidate_set.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidate_set missing candidates")


def _candidate(
    *,
    artifact_id: str,
    candidate_suffix: str,
    variant_tag: str,
    base_best: dict[str, Any],
    base_contract: dict[str, Any],
    base_segment: str,
    base_segment_prompt: str,
    base_segment_anchor: str,
    working_family_prompt: str,
    working_family_anchor: str,
) -> dict[str, Any]:
    candidate_id = f"{artifact_id}-{candidate_suffix}"
    artifact = {
        "schema_version": S2PC_CANDIDATE_SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "generator": "lcdu_l3_prompt_anchor_interaction_family",
        "source_split_contract": copy.deepcopy(base_contract),
        "best_candidate": copy.deepcopy(base_best),
        "candidate_prompt_components": {
            "segment_prompt": {
                base_segment: base_segment_prompt,
                "working_family_price_stressed": working_family_prompt,
            },
            "calibration_anchor": {
                base_segment: base_segment_anchor,
                "working_family_price_stressed": working_family_anchor,
            },
            "response_contract": (
                "Return strict JSON probabilities over the available policy alternatives."
            ),
        },
        "claim_boundary": "LCDU interaction candidate is a runtime probe only.",
    }
    _assert_strict_json(artifact)
    return {
        "candidate_id": candidate_id,
        "variant_tag": variant_tag,
        "candidate_artifact": artifact,
    }


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
