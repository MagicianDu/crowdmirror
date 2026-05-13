from __future__ import annotations

import argparse
import json
from pathlib import Path


DOMAINS = ("semi_synthetic_choice", "swissmetro_choice", "voter_emergence")
ABLATIONS = ("causal_only", "emergence_only", "joint")
BASELINES = {
    "semi_synthetic_choice": ["mnl", "uncalibrated_llm", "prompt_only"],
    "swissmetro_choice": ["mnl", "uncalibrated_llm", "prompt_only"],
    "voter_emergence": ["abm_ground_truth", "mnl", "uncalibrated_llm", "prompt_only"],
}
VALID_MODES = {"dry-run", "local", "live"}
VALID_SCOPES = {"full", "smoke"}


def build_benchmark_plan(
    mode: str,
    manifest_dir: str,
    scope: str = "full",
) -> list[dict]:
    if mode not in VALID_MODES:
        raise ValueError("mode must be dry-run, local, or live")
    if scope not in VALID_SCOPES:
        raise ValueError("scope must be full or smoke")

    ablations = ABLATIONS if scope == "full" else ("joint",)
    return [
        {
            "run_id": f"paper-{mode}-{domain}-{ablation}",
            "mode": mode,
            "domain": domain,
            "ablation": ablation,
            "baselines": BASELINES[domain],
            "manifest_dir": manifest_dir,
            "scope": scope,
        }
        for domain in DOMAINS
        for ablation in ablations
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=sorted(VALID_MODES), default="dry-run")
    parser.add_argument("--scope", choices=sorted(VALID_SCOPES), default="full")
    parser.add_argument("--manifest-dir", default="experiments/results/manifests")
    parser.add_argument("--output", default="experiments/results/benchmark-plan.json")
    args = parser.parse_args()

    plan = build_benchmark_plan(
        mode=args.mode,
        manifest_dir=args.manifest_dir,
        scope=args.scope,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output), "run_count": len(plan)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
