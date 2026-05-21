from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
LCDU_REPAIR_SET_SCHEMA_VERSION = "policy-reaction-lcdu-repair-set-v1"
RESIDUAL_WEAKNESS_SCHEMA_VERSION = "policy-reaction-lcdu-residual-weakness-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_lcdu_l4_low_income_repair_set(
    *,
    base_candidate: dict[str, Any],
    residual_weakness: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any]:
    _validate_base_candidate(base_candidate)
    _validate_residual_weakness(residual_weakness)
    prompt_components = base_candidate["candidate_prompt_components"]
    base_best = copy.deepcopy(base_candidate["best_candidate"])
    base_contract = copy.deepcopy(base_candidate["source_split_contract"])
    base_segment = base_best["segment"]
    low_income_segment = residual_weakness["segment_id"]

    candidates = [
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="r01",
            variant_tag="low_income_soft_cash_lift",
            base_best=base_best,
            base_contract=base_contract,
            base_segment=base_segment,
            base_segment_prompt=prompt_components["segment_prompt"][base_segment],
            base_segment_anchor=prompt_components["calibration_anchor"][base_segment],
            low_income_prompt=(
                "For this low-income food-insecure segment, move modestly toward "
                "cash_cost_of_living_rebate while keeping food_subsidy_expansion as the "
                "top choice. Keep baseline_no_new_support conservative."
            ),
            low_income_anchor=(
                "LCDU-L4 low_income_guard=soft; min_cash_rebate_probability=0.300; "
                "max_baseline_no_new_support_probability=0.175; "
                "max_food_subsidy_probability=0.535"
            ),
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="r02",
            variant_tag="low_income_mid_cash_lift",
            base_best=base_best,
            base_contract=base_contract,
            base_segment=base_segment,
            base_segment_prompt=prompt_components["segment_prompt"][base_segment],
            base_segment_anchor=prompt_components["calibration_anchor"][base_segment],
            low_income_prompt=(
                "For this low-income food-insecure segment, increase "
                "cash_cost_of_living_rebate enough to reduce the baseline gap, "
                "while preserving food_subsidy_expansion as the leading policy."
            ),
            low_income_anchor=(
                "LCDU-L4 low_income_guard=mid; min_cash_rebate_probability=0.305; "
                "max_baseline_no_new_support_probability=0.170; "
                "max_food_subsidy_probability=0.533"
            ),
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="r03",
            variant_tag="low_income_stronger_cash_lift",
            base_best=base_best,
            base_contract=base_contract,
            base_segment=base_segment,
            base_segment_prompt=prompt_components["segment_prompt"][base_segment],
            base_segment_anchor=prompt_components["calibration_anchor"][base_segment],
            low_income_prompt=(
                "For this low-income food-insecure segment, explicitly pull some "
                "probability mass from baseline_no_new_support into "
                "cash_cost_of_living_rebate, while lightly trimming food subsidy "
                "overshoot and preserving the overall ranking."
            ),
            low_income_anchor=(
                "LCDU-L4 low_income_guard=strong; min_cash_rebate_probability=0.310; "
                "max_baseline_no_new_support_probability=0.168; "
                "max_food_subsidy_probability=0.531"
            ),
        ),
        _candidate(
            artifact_id=artifact_id,
            candidate_suffix="r04",
            variant_tag="low_income_qualitative_cash_lift",
            base_best=base_best,
            base_contract=base_contract,
            base_segment=base_segment,
            base_segment_prompt=prompt_components["segment_prompt"][base_segment],
            base_segment_anchor=prompt_components["calibration_anchor"][base_segment],
            low_income_prompt=(
                "For this low-income food-insecure segment, reduce the baseline "
                "bias and bring cash_cost_of_living_rebate closer to the official "
                "distribution without breaking the food subsidy lead."
            ),
            low_income_anchor=(
                "LCDU-L4 low_income_guard=qualitative; preserve food subsidy lead, "
                "lift cash rebate, trim baseline bias."
            ),
        ),
    ]
    artifact = {
        "schema_version": LCDU_REPAIR_SET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "lcdu_l4_low_income_repair_family",
        "base_candidate_id": base_candidate["candidate_id"],
        "source_split_contract": base_contract,
        "segment_id": low_income_segment,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "repair_direction": residual_weakness["weakness_summary"][
            "recommended_repair_direction"
        ],
        "claim_boundary": "LCDU L4 low-income repair set is repair-candidate evidence only.",
    }
    _assert_strict_json(artifact)
    return artifact


def extract_policy_reaction_lcdu_l4_low_income_repair_candidate(
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
    parser.add_argument("--residual-weakness", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-lcdu-l4-low-income-repair-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-lcdu-l4-low-income-repair-current-001.json"
        ),
    )
    parser.add_argument("--extract-candidate-id")
    parser.add_argument("--extract-output")
    args = parser.parse_args()
    candidate_set = build_policy_reaction_lcdu_l4_low_income_repair_set(
        base_candidate=load_json_artifact(args.base_candidate),
        residual_weakness=load_json_artifact(args.residual_weakness),
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
        extracted = extract_policy_reaction_lcdu_l4_low_income_repair_candidate(
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
    if not isinstance(candidate.get("best_candidate"), dict):
        raise ValueError("base_candidate missing best_candidate")
    prompt_components = candidate.get("candidate_prompt_components")
    if not isinstance(prompt_components, dict):
        raise ValueError("base_candidate missing candidate_prompt_components")
    for namespace in ("segment_prompt", "calibration_anchor"):
        if not isinstance(prompt_components.get(namespace), dict):
            raise ValueError(f"base_candidate missing {namespace}")


def _validate_residual_weakness(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != RESIDUAL_WEAKNESS_SCHEMA_VERSION:
        raise ValueError("residual_weakness has unsupported schema_version")
    if not artifact.get("segment_id"):
        raise ValueError("residual_weakness missing segment_id")
    if not isinstance(artifact.get("weakness_summary"), dict):
        raise ValueError("residual_weakness missing weakness_summary")


def _validate_candidate_set(candidate_set: dict[str, Any]) -> None:
    if candidate_set.get("schema_version") != LCDU_REPAIR_SET_SCHEMA_VERSION:
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
    low_income_prompt: str,
    low_income_anchor: str,
) -> dict[str, Any]:
    candidate_id = f"{artifact_id}-{candidate_suffix}"
    artifact = {
        "schema_version": S2PC_CANDIDATE_SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "generator": "lcdu_l4_low_income_repair_family",
        "source_split_contract": copy.deepcopy(base_contract),
        "best_candidate": copy.deepcopy(base_best),
        "candidate_prompt_components": {
            "segment_prompt": {
                base_segment: base_segment_prompt,
                "low_income_food_insecure": low_income_prompt,
            },
            "calibration_anchor": {
                base_segment: base_segment_anchor,
                "low_income_food_insecure": low_income_anchor,
            },
            "response_contract": (
                "Return strict JSON probabilities over the available policy alternatives."
            ),
        },
        "claim_boundary": "LCDU L4 repair candidate is a runtime probe only.",
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
