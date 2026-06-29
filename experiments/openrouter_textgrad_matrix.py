from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "circe-openrouter-textgrad-matrix-v1"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODELS = (
    "openai/gpt-oss-120b:free",
    "qwen/qwen3-coder:free",
    "meta-llama/llama-3.3-70b-instruct:free",
)
DEFAULT_EVAL_SIZES = (2,)
DEFAULT_DATASET_SEEDS = (42,)
DEFAULT_PROMPT_BASELINES = ("structured",)
DEFAULT_MAX_ITERATIONS = 2
DEFAULT_TEXTGRAD_MAX_TOKENS = 1024
DEFAULT_SIMULATOR_MAX_TOKENS = 256
DEFAULT_REQUEST_TIMEOUT = 180
CLAIM_BOUNDARY = (
    "OpenRouter free-model TextGrad candidate-generation diagnostics only; "
    "accepted candidates require recorded loss-gate improvement and are not "
    "field validation."
)
OPENROUTER_KEY_RE = re.compile(r"sk-or-v1-[A-Za-z0-9_-]+")
USER_ID_RE = re.compile(r"([\"']user_id[\"']\s*:\s*[\"'])[^\"']+([\"'])")


def build_openrouter_textgrad_plan(
    *,
    matrix_id: str = "openrouter-textgrad-smoke",
    models: tuple[str, ...] = DEFAULT_MODELS,
    eval_sizes: tuple[int, ...] = DEFAULT_EVAL_SIZES,
    dataset_seeds: tuple[int, ...] = DEFAULT_DATASET_SEEDS,
    prompt_baselines: tuple[str, ...] = DEFAULT_PROMPT_BASELINES,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    textgrad_max_tokens: int = DEFAULT_TEXTGRAD_MAX_TOKENS,
    simulator_max_tokens: int = DEFAULT_SIMULATOR_MAX_TOKENS,
    request_timeout: int = DEFAULT_REQUEST_TIMEOUT,
    manifest_dir: str = "experiments/results/manifests",
) -> list[dict[str, Any]]:
    _validate_non_empty(models, "models")
    _validate_non_empty(eval_sizes, "eval_sizes")
    _validate_non_empty(dataset_seeds, "dataset_seeds")
    _validate_non_empty(prompt_baselines, "prompt_baselines")

    plan = []
    for model in models:
        for eval_size in eval_sizes:
            for dataset_seed in dataset_seeds:
                for prompt_baseline in prompt_baselines:
                    run_id = _run_id(
                        matrix_id=matrix_id,
                        model=model,
                        eval_size=eval_size,
                        dataset_seed=dataset_seed,
                        prompt_baseline=prompt_baseline,
                    )
                    command = [
                        sys.executable,
                        "experiments/w3w4_causal_calibration.py",
                        "--local",
                        "--base-url",
                        OPENROUTER_BASE_URL,
                        "--model",
                        model,
                        "--max-iter",
                        str(max_iterations),
                        "--eval-size",
                        str(eval_size),
                        "--dataset-seed",
                        str(dataset_seed),
                        "--prompt-baseline",
                        prompt_baseline,
                        "--sim-max-tokens",
                        str(simulator_max_tokens),
                        "--textgrad-max-tokens",
                        str(textgrad_max_tokens),
                        "--request-timeout",
                        str(request_timeout),
                        "--run-id",
                        run_id,
                        "--manifest-dir",
                        manifest_dir,
                    ]
                    plan.append(
                        {
                            "run_id": run_id,
                            "mode": "local-openrouter",
                            "base_url": OPENROUTER_BASE_URL,
                            "model": model,
                            "eval_size": eval_size,
                            "dataset_seed": dataset_seed,
                            "prompt_baseline": prompt_baseline,
                            "max_iterations": max_iterations,
                            "simulator_max_tokens": simulator_max_tokens,
                            "textgrad_max_tokens": textgrad_max_tokens,
                            "request_timeout": request_timeout,
                            "manifest_dir": manifest_dir,
                            "command": command,
                        }
                    )
    return plan


def build_openrouter_textgrad_index(
    *,
    matrix_id: str,
    plan: list[dict[str, Any]],
    status: str,
    results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    recorded_results = results or []
    status_counts = _count_result_statuses(recorded_results)
    index = {
        "schema_version": SCHEMA_VERSION,
        "matrix_id": matrix_id,
        "status": status,
        "created_at": _utc_now(),
        "run_count": len(plan),
        "completed_count": status_counts["completed"],
        "rate_limited_count": status_counts["rate_limited"],
        "failed_count": status_counts["failed"],
        "base_url": OPENROUTER_BASE_URL,
        "models": sorted({item["model"] for item in plan}),
        "plan": plan,
        "results": recorded_results,
        "claim_boundary": CLAIM_BOUNDARY,
        "claim_boundaries": [
            CLAIM_BOUNDARY,
            "OpenRouter free model availability can change; failures are recorded "
            "as evidence, not silently discarded.",
            "API keys are read from environment variables and must not be written "
            "to command lines, manifests, or result artifacts.",
        ],
    }
    _assert_strict_json(index)
    return index


def write_openrouter_textgrad_plan(
    path: str | Path,
    *,
    matrix_id: str,
    plan: list[dict[str, Any]],
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    index = build_openrouter_textgrad_index(
        matrix_id=matrix_id,
        plan=plan,
        status="planned",
    )
    output_path.write_text(
        json.dumps(index, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def run_openrouter_textgrad_matrix(
    *,
    matrix_id: str = "openrouter-textgrad-smoke",
    output_dir: str | Path = "experiments/results/textgrad_matrix",
    models: tuple[str, ...] = DEFAULT_MODELS,
    eval_sizes: tuple[int, ...] = DEFAULT_EVAL_SIZES,
    dataset_seeds: tuple[int, ...] = DEFAULT_DATASET_SEEDS,
    prompt_baselines: tuple[str, ...] = DEFAULT_PROMPT_BASELINES,
    manifest_dir: str = "experiments/results/manifests",
) -> dict[str, Any]:
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise ValueError(
            "OPENROUTER_API_KEY must be set in the process environment before "
            "executing the OpenRouter TextGrad matrix"
        )

    plan = build_openrouter_textgrad_plan(
        matrix_id=matrix_id,
        models=models,
        eval_sizes=eval_sizes,
        dataset_seeds=dataset_seeds,
        prompt_baselines=prompt_baselines,
        manifest_dir=manifest_dir,
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath(env.get("PYTHONPATH", ""))
    results = []
    for item in plan:
        completed = subprocess.run(
            item["command"],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            text=True,
            capture_output=True,
        )
        results.append(
            {
                "run_id": item["run_id"],
                "model": item["model"],
                "status": _classify_run_status(completed),
                "returncode": completed.returncode,
                "stdout_tail": _artifact_tail(completed.stdout),
                "stderr_tail": _artifact_tail(completed.stderr),
            }
        )

    status = _matrix_status(results)
    index = build_openrouter_textgrad_index(
        matrix_id=matrix_id,
        plan=plan,
        status=status,
        results=results,
    )
    output_path = Path(output_dir) / f"{matrix_id}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(index, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OpenRouter TextGrad matrix")
    parser.add_argument("--matrix-id", default="openrouter-textgrad-smoke")
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        help="OpenRouter model id. Repeat to run multiple models.",
    )
    parser.add_argument("--output", default=None)
    parser.add_argument("--output-dir", default="experiments/results/textgrad_matrix")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    models = tuple(args.model) if args.model else DEFAULT_MODELS
    plan = build_openrouter_textgrad_plan(
        matrix_id=args.matrix_id,
        models=models,
    )
    if args.plan_only or not args.execute:
        output = args.output or str(Path(args.output_dir) / f"{args.matrix_id}-plan.json")
        output_path = write_openrouter_textgrad_plan(
            output,
            matrix_id=args.matrix_id,
            plan=plan,
        )
        print(
            json.dumps(
                {
                    "output": str(output_path),
                    "run_count": len(plan),
                    "status": "planned",
                },
                sort_keys=True,
                allow_nan=False,
            )
        )
        return 0

    index = run_openrouter_textgrad_matrix(
        matrix_id=args.matrix_id,
        output_dir=args.output_dir,
        models=models,
    )
    print(
        json.dumps(
            {
                "output": str(Path(args.output_dir) / f"{args.matrix_id}.json"),
                "run_count": index["run_count"],
                "status": index["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _run_id(
    *,
    matrix_id: str,
    model: str,
    eval_size: int,
    dataset_seed: int,
    prompt_baseline: str,
) -> str:
    model_token = (
        model.replace("/", "-")
        .replace(":", "-")
        .replace(".", "-")
        .replace("_", "-")
    )
    return (
        f"{matrix_id}-{model_token}-eval{eval_size}-seed{dataset_seed}-"
        f"{prompt_baseline}"
    )


def _validate_non_empty(values: tuple[Any, ...], name: str) -> None:
    if not values:
        raise ValueError(f"{name} must be non-empty")


def _pythonpath(existing: str) -> str:
    parts = ["src", "."]
    if existing:
        parts.append(existing)
    return os.pathsep.join(parts)


def _classify_run_status(completed: subprocess.CompletedProcess[str]) -> str:
    if completed.returncode == 0:
        return "completed"

    combined_output = f"{completed.stdout}\n{completed.stderr}".lower()
    rate_limit_markers = (
        "ratelimiterror",
        "rate limit",
        "rate-limited",
        "error code: 429",
        "retry-after",
        "retry_after",
    )
    if any(marker in combined_output for marker in rate_limit_markers):
        return "rate_limited"
    return "failed"


def _artifact_tail(value: str) -> str:
    return _sanitize_artifact_text(value)[-2000:]


def _sanitize_artifact_text(value: str) -> str:
    sanitized = OPENROUTER_KEY_RE.sub("[REDACTED_OPENROUTER_KEY]", value)
    return USER_ID_RE.sub(r"\1[REDACTED_USER_ID]\2", sanitized)


def _matrix_status(results: list[dict[str, Any]]) -> str:
    statuses = [item.get("status") for item in results]
    if statuses and all(status == "completed" for status in statuses):
        return "completed"
    if any(status == "completed" for status in statuses):
        return "partial"
    if statuses and all(status == "rate_limited" for status in statuses):
        return "rate_limited"
    return "failed"


def _count_result_statuses(results: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "completed": sum(1 for item in results if item.get("status") == "completed"),
        "rate_limited": sum(
            1 for item in results if item.get("status") == "rate_limited"
        ),
        "failed": sum(1 for item in results if item.get("status") == "failed"),
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
