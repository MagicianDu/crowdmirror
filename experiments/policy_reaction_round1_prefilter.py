from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def build_round1_prefilter_plan(
    *,
    candidate_paths: list[str],
    route_slug: str,
    model: str,
    base_url: str,
    persona_count: int,
    strategy_count: int,
    seed: int,
    product_root: str,
    research_root: str,
) -> dict[str, Any]:
    if not candidate_paths:
        raise ValueError("candidate_paths must not be empty")
    product_root_path = Path(product_root)
    research_root_path = Path(research_root)
    model_slug = _model_slug(model)
    entries = []
    for candidate_path_str in candidate_paths:
        candidate_path = Path(candidate_path_str)
        if not candidate_path.is_absolute():
            candidate_path = (research_root_path / candidate_path).resolve()
        candidate = json.loads(candidate_path.read_text())
        candidate_id = str(candidate["candidate_id"])
        short_id = candidate_id.split("-")[-1]
        run_suffix = f"{route_slug}-{short_id}"
        entries.append(
            {
                "candidate_id": candidate_id,
                "candidate_path": str(candidate_path),
                "run_id": f"llm-cohort-policy-local-{model_slug}-12x3-calibration-split-{run_suffix}-001",
                "model_slug": model_slug,
                "prediction_artifact_id": f"policy-reaction-segment-predictions-{run_suffix}-001",
                "benchmark_artifact_id": (
                    f"policy-reaction-official-segment-benchmark-{model_slug}-12x3-"
                    f"calibration-split-{run_suffix}-heldout-001"
                ),
                "effect_artifact_id": (
                    f"policy-reaction-s2pc-runtime-effect-{model_slug}-12x3-"
                    f"calibration-split-{run_suffix}-heldout-001"
                ),
                "manifest_path": str(
                    product_root_path
                    / "experiments/results/llm_cohort_gate"
                    / f"llm-cohort-policy-local-{model_slug}-12x3-calibration-split-{run_suffix}-001.json"
                ),
                "prediction_path": str(
                    product_root_path
                    / "experiments/results/policy_reports"
                    / f"policy-reaction-segment-predictions-{run_suffix}-001.json"
                ),
                "benchmark_path": str(
                    research_root_path
                    / "experiments/results/policy_reaction_benchmark"
                    / f"policy-reaction-official-segment-benchmark-{model_slug}-12x3-calibration-split-{run_suffix}-heldout-001.json"
                ),
                "effect_path": str(
                    research_root_path
                    / "experiments/results/policy_reaction_benchmark"
                    / f"policy-reaction-s2pc-runtime-effect-{model_slug}-12x3-calibration-split-{run_suffix}-heldout-001.json"
                ),
            }
        )
    return {
        "route_slug": route_slug,
        "model": model,
        "model_slug": model_slug,
        "base_url": base_url,
        "persona_count": persona_count,
        "strategy_count": strategy_count,
        "seed": seed,
        "product_root": str(product_root_path),
        "research_root": str(research_root_path),
        "entries": entries,
    }


def execute_round1_prefilter_plan(plan: dict[str, Any]) -> dict[str, Any]:
    product_root = Path(plan["product_root"])
    research_root = Path(plan["research_root"])
    completed = []
    for entry in plan["entries"]:
        _run(
            [
                str(product_root / ".venv/bin/python"),
                "-m",
                "crowdmirror.cli",
                "llm-cohort-gate",
                "--domain",
                "policy_reaction",
                "--persona-count",
                str(plan["persona_count"]),
                "--strategy-count",
                str(plan["strategy_count"]),
                "--base-url",
                plan["base_url"],
                "--model",
                plan["model"],
                "--seed",
                str(plan["seed"]),
                "--execute",
                "--output-dir",
                "experiments/results/llm_cohort_gate",
                "--run-id",
                entry["run_id"],
                "--calibration-profile",
                "official_htops_2506_calibration_split",
                "--calibration-profile-artifact",
                str(
                    research_root
                    / "experiments/results/policy_reaction_benchmark/policy-reaction-htops-2506-calibration-ingestion-001.json"
                ),
                "--calibration-candidate-artifact",
                entry["candidate_path"],
            ],
            cwd=product_root,
        )
        _run(
            [
                str(product_root / ".venv/bin/python"),
                "-m",
                "crowdmirror.cli",
                "policy-segment-predictions",
                "--cohort-manifest",
                entry["manifest_path"],
                "--output",
                entry["prediction_path"],
                "--artifact-id",
                entry["prediction_artifact_id"],
                "--prediction-scope",
                "htops_hps_2506_segment_alignment",
            ],
            cwd=product_root,
        )
        _run(
            [
                "python",
                "experiments/policy_reaction_official_benchmark.py",
                "--ingestion-artifact",
                "experiments/results/policy_reaction_benchmark/policy-reaction-htops-2506-evaluation-ingestion-001.json",
                "--predictions-artifact",
                entry["prediction_path"],
                "--artifact-id",
                entry["benchmark_artifact_id"],
                "--output",
                entry["benchmark_path"],
            ],
            cwd=research_root,
        )
        _run(
            [
                "python",
                "experiments/policy_reaction_s2pc_runtime_effect.py",
                "--baseline-heldout-benchmark",
                "experiments/results/policy_reaction_benchmark/policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-calibration-split-heldout-001.json",
                "--baseline-product-manifest",
                str(
                    product_root
                    / "experiments/results/llm_cohort_gate/llm-cohort-policy-local-gpt-oss-20b-12x3-calibration-split-001.json"
                ),
                "--s2pc-runtime-heldout-benchmark",
                entry["benchmark_path"],
                "--s2pc-product-manifest",
                entry["manifest_path"],
                "--s2pc-candidate",
                entry["candidate_path"],
                "--artifact-id",
                entry["effect_artifact_id"],
                "--output",
                entry["effect_path"],
            ],
            cwd=research_root,
        )
        completed.append(entry["effect_path"])
    matrix_path = (
        research_root
        / "experiments/results/policy_reaction_benchmark"
        / f"policy-reaction-{plan['route_slug']}-matrix-{plan['model_slug']}-12x3-heldout-001.json"
    )
    _run(
        [
            "python",
            "experiments/policy_reaction_s2pc_runtime_effect.py",
            "--mode",
            "matrix",
            *[
                item
                for effect_path in completed
                for item in ("--effect-artifact", effect_path)
            ],
            "--artifact-id",
            f"policy-reaction-{plan['route_slug']}-matrix-{plan['model_slug']}-12x3-heldout-001",
            "--output",
            str(matrix_path),
        ],
        cwd=research_root,
    )
    return {
        "route_slug": plan["route_slug"],
        "effect_count": len(completed),
        "matrix_path": str(matrix_path),
    }


def _run(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def _model_slug(model: str) -> str:
    normalized = model.rsplit("/", 1)[-1]
    return normalized.replace("/", "-").replace(".", "-").replace("_", "-")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route-slug", required=True)
    parser.add_argument("--candidate-path", action="append", required=True)
    parser.add_argument("--product-root", default="/Users/dm/Documents/cc-社会计算器-worktrees/product")
    parser.add_argument("--research-root", default="/Users/dm/Documents/cc-社会计算器-worktrees/research")
    parser.add_argument("--base-url", default="http://127.0.0.1:1234/v1")
    parser.add_argument("--model", default="openai/gpt-oss-20b")
    parser.add_argument("--persona-count", type=int, default=12)
    parser.add_argument("--strategy-count", type=int, default=3)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    plan = build_round1_prefilter_plan(
        candidate_paths=args.candidate_path,
        route_slug=args.route_slug,
        model=args.model,
        base_url=args.base_url,
        persona_count=args.persona_count,
        strategy_count=args.strategy_count,
        seed=args.seed,
        product_root=args.product_root,
        research_root=args.research_root,
    )
    if args.execute:
        result = execute_round1_prefilter_plan(plan)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 0
    print(json.dumps(plan, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
