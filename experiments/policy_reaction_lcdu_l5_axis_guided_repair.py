from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
LCDU_AXIS_GUIDED_REPAIR_SET_SCHEMA_VERSION = "policy-reaction-lcdu-axis-repair-set-v1"
AXIS_WEAKNESS_SCHEMA_VERSION = "policy-reaction-axis-weakness-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_lcdu_l5_axis_guided_repair_set(
    *,
    base_candidate: dict[str, Any],
    axis_weakness: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_base_candidate(base_candidate)
    _validate_axis_weakness(axis_weakness)
    base_best = copy.deepcopy(base_candidate["best_candidate"])
    prompt_components = copy.deepcopy(base_candidate["candidate_prompt_components"])

    candidates = [
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="x01",
            variant_tag="income_low_rank_guard",
            base_candidate=base_candidate,
            base_best=base_best,
            prompt_components=prompt_components,
            axis_prompt_overrides={
                "income_band=low": (
                    "For low-income personas, preserve the official ordering bias. "
                    "Do not let baseline_no_new_support outrank cash_cost_of_living_rebate "
                    "when cost pressure is salient."
                ),
            },
            axis_anchor_overrides={
                "income_band=low": (
                    "LCDU-L5 axis_guard=income_low_rank; "
                    "baseline_rank_cap=2; cash_rebate_rank_floor=2"
                ),
            },
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="x02",
            variant_tag="high_price_shape_guard",
            base_candidate=base_candidate,
            base_best=base_best,
            prompt_components=prompt_components,
            axis_prompt_overrides={
                "price_stress_level=high": (
                    "For high price-stress personas, reduce baseline drift and keep the "
                    "cash rebate share closer to the official distribution while preserving "
                    "overall distribution coherence."
                ),
            },
            axis_anchor_overrides={
                "price_stress_level=high": (
                    "LCDU-L5 axis_guard=high_price_shape; "
                    "max_baseline_no_new_support_probability=0.24; "
                    "min_cash_cost_of_living_rebate_probability=0.31"
                ),
            },
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="x03",
            variant_tag="dual_axis_soft_guard",
            base_candidate=base_candidate,
            base_best=base_best,
            prompt_components=prompt_components,
            axis_prompt_overrides={
                "income_band=low": (
                    "For low-income personas, preserve the public ranking bias toward "
                    "active support options over the no-new-support baseline."
                ),
                "price_stress_level=high": (
                    "For high price-stress personas, avoid overshooting the baseline and "
                    "keep cash rebate support from collapsing."
                ),
            },
            axis_anchor_overrides={
                "income_band=low": (
                    "LCDU-L5 axis_guard=income_low_soft_rank; baseline_rank_cap=2"
                ),
                "price_stress_level=high": (
                    "LCDU-L5 axis_guard=high_price_soft_shape; "
                    "max_baseline_no_new_support_probability=0.245"
                ),
            },
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="x04",
            variant_tag="dual_axis_numeric_guard",
            base_candidate=base_candidate,
            base_best=base_best,
            prompt_components=prompt_components,
            axis_prompt_overrides={
                "income_band=low": (
                    "For low-income personas, keep cash_cost_of_living_rebate competitive "
                    "with the baseline and do not let baseline_no_new_support dominate."
                ),
                "price_stress_level=high": (
                    "For high price-stress personas, keep baseline_no_new_support controlled "
                    "and preserve a stronger cash rebate floor."
                ),
            },
            axis_anchor_overrides={
                "income_band=low": (
                    "LCDU-L5 axis_guard=income_low_numeric_rank; "
                    "max_baseline_rank=2; min_cash_rebate_rank=2"
                ),
                "price_stress_level=high": (
                    "LCDU-L5 axis_guard=high_price_numeric_shape; "
                    "max_baseline_no_new_support_probability=0.235; "
                    "min_cash_cost_of_living_rebate_probability=0.325"
                ),
            },
        ),
    ]
    artifact = {
        "schema_version": LCDU_AXIS_GUIDED_REPAIR_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "lcdu_l5_axis_guided_repair_family",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "candidate_count": len(candidates),
        "axis_weakness_reference": axis_weakness["artifact_id"],
        "persistent_weakness": copy.deepcopy(axis_weakness["persistent_weakness"]),
        "candidates": candidates,
        "claim_boundary": (
            "LCDU L5 axis-guided repair set is candidate-generation evidence only."
        ),
    }
    json.dumps(artifact, allow_nan=False)
    return artifact


def extract_policy_reaction_lcdu_l5_axis_guided_repair_candidate(
    candidate_set: dict[str, Any],
    *,
    candidate_id: str,
) -> dict[str, Any]:
    _validate_candidate_set(candidate_set)
    for candidate in candidate_set["candidates"]:
        if candidate["candidate_id"] == candidate_id:
            artifact = copy.deepcopy(candidate["candidate_artifact"])
            json.dumps(artifact, allow_nan=False)
            return artifact
    raise ValueError("candidate_id not found in candidate_set")


def _candidate(
    *,
    artifact_id: str,
    candidate_suffix: str,
    variant_tag: str,
    base_candidate: dict[str, Any],
    base_best: dict[str, Any],
    prompt_components: dict[str, Any],
    axis_prompt_overrides: dict[str, str],
    axis_anchor_overrides: dict[str, str],
) -> dict[str, Any]:
    candidate_id = f"{artifact_id}-{candidate_suffix}"
    patched_components = copy.deepcopy(prompt_components)
    patched_components.setdefault("segment_prompt", {}).update(axis_prompt_overrides)
    patched_components.setdefault("calibration_anchor", {}).update(axis_anchor_overrides)
    candidate_artifact = {
        "schema_version": S2PC_CANDIDATE_SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "generator": "lcdu_l5_axis_guided_repair_family",
        "source_split_contract": copy.deepcopy(base_candidate["source_split_contract"]),
        "best_candidate": copy.deepcopy(base_best),
        "candidate_prompt_components": patched_components,
        "claim_boundary": "LCDU axis-guided candidate is a runtime probe candidate only.",
    }
    return {
        "candidate_id": candidate_id,
        "variant_tag": variant_tag,
        "axis_prompt_overrides": axis_prompt_overrides,
        "axis_anchor_overrides": axis_anchor_overrides,
        "candidate_artifact": candidate_artifact,
    }


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
    if candidate_set.get("schema_version") != LCDU_AXIS_GUIDED_REPAIR_SET_SCHEMA_VERSION:
        raise ValueError("candidate_set has unsupported schema_version")
    if not isinstance(candidate_set.get("candidates"), list) or not candidate_set["candidates"]:
        raise ValueError("candidate_set missing candidates")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-candidate", required=True)
    parser.add_argument("--axis-weakness", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-lcdu-l5-axis-guided-repair-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-lcdu-l5-axis-guided-repair-current-001.json"
        ),
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()
    candidate_set = build_policy_reaction_lcdu_l5_axis_guided_repair_set(
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
        extracted = extract_policy_reaction_lcdu_l5_axis_guided_repair_candidate(
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
