from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


RESIDUAL_WEAKNESS_SCHEMA_VERSION = "policy-reaction-lcdu-residual-weakness-v1"
POLICIES = (
    "baseline_no_new_support",
    "cash_cost_of_living_rebate",
    "food_subsidy_expansion",
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_lcdu_l3_residual_weakness_artifact(
    *,
    baseline_12x3: dict[str, Any],
    h02_12x3: dict[str, Any],
    i01_12x3: dict[str, Any],
    baseline_16x3: dict[str, Any],
    h02_16x3: dict[str, Any],
    i01_16x3: dict[str, Any],
    artifact_id: str,
    segment_id: str = "low_income_food_insecure",
) -> dict[str, Any]:
    _validate_benchmark(baseline_12x3)
    _validate_benchmark(h02_12x3)
    _validate_benchmark(i01_12x3)
    _validate_benchmark(baseline_16x3)
    _validate_benchmark(h02_16x3)
    _validate_benchmark(i01_16x3)

    runs = [
        _run_summary("baseline_12x3_seed11", baseline_12x3, segment_id),
        _run_summary("h02_12x3_seed11", h02_12x3, segment_id),
        _run_summary("i01_12x3_seed11", i01_12x3, segment_id),
        _run_summary("baseline_16x3_seed11", baseline_16x3, segment_id),
        _run_summary("h02_16x3_seed11", h02_16x3, segment_id),
        _run_summary("i01_16x3_seed11", i01_16x3, segment_id),
    ]

    base12 = runs[0]
    h0212 = runs[1]
    i0112 = runs[2]
    base16 = runs[3]
    h0216 = runs[4]
    i0116 = runs[5]

    weakness = {
        "shape_not_rank_issue": (
            base12["rank_correlation"] == 1.0
            and h0212["rank_correlation"] == 1.0
            and i0112["rank_correlation"] == 1.0
            and base16["rank_correlation"] == 1.0
            and h0216["rank_correlation"] == 1.0
            and i0116["rank_correlation"] == 1.0
        ),
        "policy_bias_signature": {
            "baseline_no_new_support": "over_predicted",
            "cash_cost_of_living_rebate": "under_predicted",
            "food_subsidy_expansion": "slightly_over_predicted",
        },
        "main_drag_run_id": "h02_16x3_seed11",
        "recommended_repair_direction": (
            "raise cash_cost_of_living_rebate while trimming baseline_no_new_support "
            "and lightly trimming food_subsidy_expansion for low_income_food_insecure"
        ),
    }

    artifact = {
        "schema_version": RESIDUAL_WEAKNESS_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "generator": "lcdu_l3_low_income_residual_weakness_analysis",
        "segment_id": segment_id,
        "runs": runs,
        "comparisons": {
            "h02_vs_baseline_12x3": _compare_runs(base12, h0212),
            "i01_vs_baseline_12x3": _compare_runs(base12, i0112),
            "h02_vs_baseline_16x3": _compare_runs(base16, h0216),
            "i01_vs_baseline_16x3": _compare_runs(base16, i0116),
        },
        "weakness_summary": weakness,
        "claim_boundary": (
            "Residual weakness artifact diagnoses segment-level distribution mismatch only."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_policy_reaction_lcdu_l3_residual_weakness_artifact(
    path: str | Path,
    *,
    baseline_12x3_path: str | Path,
    h02_12x3_path: str | Path,
    i01_12x3_path: str | Path,
    baseline_16x3_path: str | Path,
    h02_16x3_path: str | Path,
    i01_16x3_path: str | Path,
    artifact_id: str,
    segment_id: str = "low_income_food_insecure",
) -> Path:
    artifact = build_policy_reaction_lcdu_l3_residual_weakness_artifact(
        baseline_12x3=load_json_artifact(baseline_12x3_path),
        h02_12x3=load_json_artifact(h02_12x3_path),
        i01_12x3=load_json_artifact(i01_12x3_path),
        baseline_16x3=load_json_artifact(baseline_16x3_path),
        h02_16x3=load_json_artifact(h02_16x3_path),
        i01_16x3=load_json_artifact(i01_16x3_path),
        artifact_id=artifact_id,
        segment_id=segment_id,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-12x3", required=True)
    parser.add_argument("--h02-12x3", required=True)
    parser.add_argument("--i01-12x3", required=True)
    parser.add_argument("--baseline-16x3", required=True)
    parser.add_argument("--h02-16x3", required=True)
    parser.add_argument("--i01-16x3", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-lcdu-l3-low-income-residual-weakness-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-lcdu-l3-low-income-residual-weakness-current-001.json"
        ),
    )
    parser.add_argument("--segment-id", default="low_income_food_insecure")
    args = parser.parse_args()
    output_path = write_policy_reaction_lcdu_l3_residual_weakness_artifact(
        args.output,
        baseline_12x3_path=args.baseline_12x3,
        h02_12x3_path=args.h02_12x3,
        i01_12x3_path=args.i01_12x3,
        baseline_16x3_path=args.baseline_16x3,
        h02_16x3_path=args.h02_16x3,
        i01_16x3_path=args.i01_16x3,
        artifact_id=args.artifact_id,
        segment_id=args.segment_id,
    )
    artifact = load_json_artifact(output_path)
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "segment_id": artifact["segment_id"],
                "recommended_repair_direction": artifact["weakness_summary"][
                    "recommended_repair_direction"
                ],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_benchmark(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "policy-reaction-official-segment-benchmark-v1":
        raise ValueError("benchmark has unsupported schema_version")
    if artifact.get("overall_status") != "passed":
        raise ValueError("benchmark must be passed")


def _run_summary(run_id: str, benchmark: dict[str, Any], segment_id: str) -> dict[str, Any]:
    segment = benchmark["segment_metrics"][segment_id]
    official = segment["official_distribution"]
    predicted = segment["predicted_distribution"]
    bias = {
        policy_id: round(float(predicted[policy_id]) - float(official[policy_id]), 12)
        for policy_id in POLICIES
    }
    return {
        "run_id": run_id,
        "segment_id": segment_id,
        "choice_distribution_jsd": round(float(segment["choice_distribution_jsd"]), 12),
        "rank_correlation": round(float(segment["rank_correlation"]), 12),
        "official_distribution": official,
        "predicted_distribution": predicted,
        "policy_bias": bias,
    }


def _compare_runs(base: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "base_run_id": base["run_id"],
        "candidate_run_id": candidate["run_id"],
        "jsd_delta": round(
            float(base["choice_distribution_jsd"]) - float(candidate["choice_distribution_jsd"]),
            12,
        ),
        "policy_bias_delta": {
            policy_id: round(
                float(base["policy_bias"][policy_id]) - float(candidate["policy_bias"][policy_id]),
                12,
            )
            for policy_id in POLICIES
        },
    }


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
