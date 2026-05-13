"""
W3-W4 Deliverable: Individual Causal Calibration.
Demonstrates TextGrad + causal constraint optimization on Swissmetro semi-synthetic data.

Usage:
    python experiments/w3w4_causal_calibration.py [--max-iter 10] [--dry-run]
    python experiments/w3w4_causal_calibration.py --local  # use LM Studio local model

The --dry-run flag uses mock LLM responses for testing the pipeline without API costs.
The --local flag uses a local OpenAI-compatible server (default: localhost:1234).
"""

import argparse
import json
import time
from pathlib import Path
from urllib.parse import quote

try:
    from ._bootstrap import bootstrap_src_path
except ImportError:
    from _bootstrap import bootstrap_src_path

bootstrap_src_path()

try:
    from experiments.evidence_manifest import build_run_manifest, write_manifest
except ImportError:
    from evidence_manifest import build_run_manifest, write_manifest

from circe.dgp.counterfactual import generate_counterfactual_dataset
from circe.calibration.loop import CalibrationLoop, CalibrationConfig
from circe.calibration.loss import compute_causal_loss
from circe.simulator.llm_choice import LLMChoiceSimulator, SimulatorConfig
from circe.simulator.prompt_templates import CHOICE_SYSTEM_PROMPT


RESULTS_DIR = Path("experiments/results")
SCRIPT_COMMAND = ["python", "experiments/w3w4_causal_calibration.py"]
DEFAULT_SIMULATOR_MAX_TOKENS = 2000
DEFAULT_TEXTGRAD_MAX_TOKENS = 4000
DEFAULT_DATASET_SEED = 42
DEFAULT_PROMPT_BASELINE = "default"
PROMPT_BASELINES = {
    "default": CHOICE_SYSTEM_PROMPT,
    "compact": (
        "You simulate transportation choices. Return only strict JSON probabilities "
        "for train, swissmetro, and car. Weigh travel time, cost, headway, and "
        "convenience. Higher cost or travel time should lower utility; probabilities "
        "must be non-negative and sum to 1.0."
    ),
    "structured": (
        "You are a discrete-choice transportation simulator. For each alternative, "
        "compare travel time, monetary cost, headway, and convenience. Infer a "
        "relative utility, convert utilities into smooth probabilities, and return "
        "only JSON with train, swissmetro, and car probabilities summing to 1.0."
    ),
}
REQUIRED_RESULT_METRICS = (
    "initial_loss",
    "best_loss",
    "final_loss",
    "n_iterations",
    "total_llm_calls",
    "textgrad_call_count",
    "prompt_update_count",
)


def run_experiment(max_iterations: int = 10, dry_run: bool = False,
                   local: bool = False, base_url: str = "http://localhost:1234/v1",
                   model: str = "google/gemma-4-31b", eval_size: int = 10,
                   run_id: str | None = None,
                   manifest_dir: str = "experiments/results/manifests",
                   simulator_max_tokens: int = DEFAULT_SIMULATOR_MAX_TOKENS,
                   textgrad_max_tokens: int = DEFAULT_TEXTGRAD_MAX_TOKENS,
                   request_timeout: float | None = None,
                   dataset_seed: int = DEFAULT_DATASET_SEED,
                   prompt_baseline: str = DEFAULT_PROMPT_BASELINE):
    print("=" * 60)
    print("CIRCE W3-W4: Individual Causal Calibration")
    print("=" * 60)

    # Generate ground-truth counterfactual dataset
    print("\n--- Generating counterfactual dataset ---")
    pairs = generate_counterfactual_dataset(
        n_scenarios=100,
        n_interventions=5,
        intervention_type="sm_cost_increase",
        seed=dataset_seed,
    )
    print(f"Generated {len(pairs)} counterfactual pairs")
    print(f"ATE range: [{min(p.ate for p in pairs):.4f}, {max(p.ate for p in pairs):.4f}]")

    # Split into train/test
    train_pairs = pairs[:400]
    test_pairs = pairs[400:]
    print(f"Train: {len(train_pairs)} pairs, Test: {len(test_pairs)} pairs")

    # Configure calibration
    mode = "dry-run" if dry_run else "local" if local else "live"
    manifest_run_id = run_id or f"w3w4-{mode}-{int(time.time())}"
    command = _build_command(
        max_iterations=max_iterations,
        dry_run=dry_run,
        local=local,
        base_url=base_url,
        model=model,
        eval_size=eval_size,
        run_id=manifest_run_id,
        manifest_dir=manifest_dir,
        simulator_max_tokens=simulator_max_tokens,
        textgrad_max_tokens=textgrad_max_tokens,
        request_timeout=request_timeout,
        dataset_seed=dataset_seed,
        prompt_baseline=prompt_baseline,
    )

    if local:
        provider = "openai"
        sim_model = model
        tg_model = model
        print(f"\n[LOCAL MODE — using {model} via {base_url}]")
    else:
        provider = "anthropic"
        sim_model = "claude-haiku-4-5-20251001"
        tg_model = "claude-sonnet-4-6-20250514"
        base_url = None

    config = CalibrationConfig(
        max_iterations=max_iterations,
        patience=3,
        alpha=1.0,
        gamma=2.0,
        simulator_model=sim_model,
        textgrad_model=tg_model,
        simulator_max_tokens=simulator_max_tokens,
        textgrad_max_tokens=textgrad_max_tokens,
        eval_sample_size=eval_size,
        provider=provider,
        base_url=base_url,
        request_timeout=request_timeout,
        initial_prompt=_prompt_for_baseline(prompt_baseline),
    )

    if dry_run:
        print("\n[DRY RUN MODE — using mock responses]")
        summary = _run_dry(config, train_pairs, test_pairs)
        output_path = _write_result_summary(manifest_run_id, summary)
        textgrad_steps_path = _write_textgrad_steps(
            manifest_run_id,
            summary.get("textgrad_steps", []),
        )
        print(f"Results saved to {output_path}")
        print(f"TextGrad steps saved to {textgrad_steps_path}")
        manifest = build_causal_manifest(
            run_id=manifest_run_id,
            mode="dry-run",
            command=command,
            config={
                "max_iterations": config.max_iterations,
                "eval_size": config.eval_sample_size,
                "simulator_max_tokens": config.simulator_max_tokens,
                "textgrad_max_tokens": config.textgrad_max_tokens,
                "request_timeout": config.request_timeout,
                "dataset_seed": dataset_seed,
                "prompt_baseline": prompt_baseline,
            },
            result_summary=summary,
            result_path=str(output_path),
            textgrad_steps_path=str(textgrad_steps_path),
        )
        manifest_path = _manifest_path(manifest_dir, manifest_run_id)
        write_manifest(manifest_path, manifest)
        print(f"Evidence manifest saved to {manifest_path}")
        return

    # Run calibration loop
    print(f"\n--- Running calibration (max {max_iterations} iterations, eval_size={eval_size}) ---")
    loop = CalibrationLoop(config=config, dataset=train_pairs)
    start_time = time.time()
    result = loop.run()
    elapsed = time.time() - start_time

    # Report results
    print(f"\n--- Calibration Results ---")
    print(f"Iterations: {result.n_iterations}")
    print(f"Initial loss: {result.initial_loss:.4f}")
    print(f"Best loss: {result.best_loss:.4f}")
    print(f"Final loss: {result.final_loss:.4f}")
    print(f"Improvement: {(1 - result.best_loss / result.initial_loss) * 100:.1f}%")
    print(f"Total LLM calls: {result.total_llm_calls}")
    print(f"Time elapsed: {elapsed:.1f}s")

    # Show iteration history
    print(f"\n--- Loss History ---")
    for rec in result.history:
        marker = " *" if rec.loss.total_loss == result.best_loss else ""
        print(f"  Iter {rec.iteration}: loss={rec.loss.total_loss:.4f} "
              f"(ECE={rec.loss.ece:.4f}, ATE_MAE={rec.loss.ate_mae:.4f}){marker}")

    # Show best prompt
    print(f"\n--- Best Prompt ---")
    print(result.best_prompt[:500])
    if len(result.best_prompt) > 500:
        print(f"... ({len(result.best_prompt)} chars total)")

    # Save results
    textgrad_steps = _textgrad_steps_from_history(result.history)
    suspected_prompt_truncation_count = _suspected_prompt_truncation_count(
        textgrad_steps
    )
    textgrad_output_budget_saturated = _textgrad_output_budget_saturated(
        textgrad_output_tokens=result.textgrad_output_tokens,
        textgrad_call_count=result.textgrad_call_count,
        textgrad_max_tokens=textgrad_max_tokens,
    )
    output_data = {
        "best_prompt": result.best_prompt,
        "best_loss": result.best_loss,
        "initial_loss": result.initial_loss,
        "final_loss": result.final_loss,
        "n_iterations": result.n_iterations,
        "total_llm_calls": result.total_llm_calls,
        "simulator_llm_call_count": result.simulator_llm_call_count,
        "textgrad_call_count": result.textgrad_call_count,
        "textgrad_input_tokens": result.textgrad_input_tokens,
        "textgrad_output_tokens": result.textgrad_output_tokens,
        "prompt_update_count": _prompt_update_count(textgrad_steps),
        "suspected_prompt_truncation_count": suspected_prompt_truncation_count,
        "textgrad_output_budget_saturated": textgrad_output_budget_saturated,
        "min_edited_prompt_chars": _min_edited_prompt_chars(textgrad_steps),
        "textgrad_effect_status": _textgrad_effect_status(
            initial_loss=result.initial_loss,
            best_loss=result.best_loss,
            textgrad_call_count=result.textgrad_call_count,
            prompt_update_count=_prompt_update_count(textgrad_steps),
        ),
        "textgrad_steps": textgrad_steps,
        "dataset_seed": dataset_seed,
        "prompt_baseline": prompt_baseline,
        "elapsed_seconds": elapsed,
        "history": [
            {"iteration": r.iteration, "total_loss": r.loss.total_loss,
             "ece": r.loss.ece, "ate_mae": r.loss.ate_mae}
            for r in result.history
        ],
    }
    output_path = _write_result_summary(manifest_run_id, output_data)
    textgrad_steps_path = _write_textgrad_steps(manifest_run_id, textgrad_steps)
    print(f"\nResults saved to {output_path}")
    print(f"TextGrad steps saved to {textgrad_steps_path}")
    manifest = build_causal_manifest(
        run_id=manifest_run_id,
        mode=mode,
        command=command,
        config={
            "max_iterations": max_iterations,
            "eval_size": eval_size,
            "local": local,
            "provider": provider,
            "model": sim_model,
            "simulator_max_tokens": simulator_max_tokens,
            "textgrad_max_tokens": textgrad_max_tokens,
            "request_timeout": request_timeout,
            "dataset_seed": dataset_seed,
            "prompt_baseline": prompt_baseline,
        },
        result_summary=output_data,
        result_path=str(output_path),
        textgrad_steps_path=str(textgrad_steps_path),
    )
    manifest_path = _manifest_path(manifest_dir, manifest_run_id)
    write_manifest(manifest_path, manifest)
    print(f"Evidence manifest saved to {manifest_path}")

    print("\n" + "=" * 60)
    print("W3-W4 COMPLETE: Causal calibration demonstrated.")
    print("=" * 60)


def build_causal_manifest(
    *,
    run_id: str,
    mode: str,
    command: list[str],
    config: dict,
    result_summary: dict,
    result_path: str,
    textgrad_steps_path: str | None = None,
) -> dict:
    missing_metrics = [
        metric for metric in REQUIRED_RESULT_METRICS if metric not in result_summary
    ]
    if missing_metrics:
        raise ValueError(
            "result_summary missing required metrics: " + ", ".join(missing_metrics)
        )

    initial = float(result_summary["initial_loss"])
    best = float(result_summary["best_loss"])
    improvement_ratio = (initial - best) / initial if initial > 0 else 0.0
    metrics = {
        "initial_loss": initial,
        "best_loss": best,
        "final_loss": float(result_summary["final_loss"]),
        "improvement_ratio": improvement_ratio,
        "n_iterations": int(result_summary["n_iterations"]),
        "total_llm_calls": int(result_summary["total_llm_calls"]),
        "textgrad_call_count": int(result_summary["textgrad_call_count"]),
        "prompt_update_count": int(result_summary["prompt_update_count"]),
        "textgrad_effect_status": result_summary.get(
            "textgrad_effect_status",
            _textgrad_effect_status(
                initial_loss=initial,
                best_loss=best,
                textgrad_call_count=int(result_summary["textgrad_call_count"]),
                prompt_update_count=int(result_summary["prompt_update_count"]),
            ),
        ),
    }
    for token_metric in (
        "textgrad_input_tokens",
        "textgrad_output_tokens",
        "suspected_prompt_truncation_count",
        "min_edited_prompt_chars",
    ):
        if token_metric in result_summary:
            metrics[token_metric] = int(result_summary[token_metric])
    if "textgrad_output_budget_saturated" in result_summary:
        metrics["textgrad_output_budget_saturated"] = bool(
            result_summary["textgrad_output_budget_saturated"]
        )

    artifacts = {"result_json": result_path}
    if textgrad_steps_path is not None:
        artifacts["textgrad_steps_json"] = textgrad_steps_path

    return build_run_manifest(
        run_id=run_id,
        lane="causal",
        mode=mode,
        command=command,
        config=config,
        metrics=metrics,
        artifacts=artifacts,
        notes=[
            "Causal calibration compares predicted mode probabilities and Swissmetro ATE.",
            "TextGrad steps record prompt feedback and edited prompts; effectiveness is judged by subsequent loss re-evaluation.",
            "Dry-run mode uses mocked LLM responses and only validates execution plumbing.",
        ],
    )


def _run_dry(config, train_pairs, test_pairs):
    """Dry run: verify pipeline works without API calls."""
    from unittest.mock import patch
    from circe.llm_client import LLMResponse

    call_count = [0]

    def mock_chat(system, user):
        call_count[0] += 1
        if "optimization engine" in system.lower() or "improve" in system.lower():
            return LLMResponse(
                content=(
                    "FEEDBACK: The prompt needs more cost sensitivity.\n\n"
                    "EDITED PROMPT: You are simulating a cost-sensitive commuter. "
                    "Consider that price changes strongly affect mode choice."
                ),
                input_tokens=500,
                output_tokens=200,
            )
        return LLMResponse(
            content='{"train": 0.35, "swissmetro": 0.40, "car": 0.25}',
            input_tokens=100,
            output_tokens=20,
        )

    with patch("circe.llm_client.LLMClient.chat", side_effect=mock_chat):
        loop = CalibrationLoop(config=config, dataset=train_pairs[:20])
        result = loop.run()

    textgrad_steps = _textgrad_steps_from_history(result.history)
    suspected_prompt_truncation_count = _suspected_prompt_truncation_count(
        textgrad_steps
    )
    textgrad_output_budget_saturated = _textgrad_output_budget_saturated(
        textgrad_output_tokens=result.textgrad_output_tokens,
        textgrad_call_count=result.textgrad_call_count,
        textgrad_max_tokens=config.textgrad_max_tokens,
    )
    print(f"  Pipeline OK: {result.n_iterations} iterations, {call_count[0]} mock LLM calls")
    print(f"  Initial loss: {result.initial_loss:.4f}")
    print(f"  Final loss: {result.final_loss:.4f}")
    print("  [Dry run complete — pipeline is functional]")
    summary = {
        "initial_loss": result.initial_loss,
        "best_loss": result.best_loss,
        "final_loss": result.final_loss,
        "n_iterations": result.n_iterations,
        "total_llm_calls": result.total_llm_calls,
        "mock_llm_call_count": call_count[0],
        "simulator_llm_call_count": result.simulator_llm_call_count,
        "textgrad_call_count": result.textgrad_call_count,
        "textgrad_input_tokens": result.textgrad_input_tokens,
        "textgrad_output_tokens": result.textgrad_output_tokens,
        "prompt_update_count": _prompt_update_count(textgrad_steps),
        "suspected_prompt_truncation_count": suspected_prompt_truncation_count,
        "textgrad_output_budget_saturated": textgrad_output_budget_saturated,
        "min_edited_prompt_chars": _min_edited_prompt_chars(textgrad_steps),
        "textgrad_effect_status": _textgrad_effect_status(
            initial_loss=result.initial_loss,
            best_loss=result.best_loss,
            textgrad_call_count=result.textgrad_call_count,
            prompt_update_count=_prompt_update_count(textgrad_steps),
        ),
        "textgrad_steps": textgrad_steps,
    }
    return summary


def _build_command(
    *,
    max_iterations: int,
    dry_run: bool,
    local: bool,
    base_url: str,
    model: str,
    eval_size: int,
    run_id: str,
    manifest_dir: str,
    simulator_max_tokens: int = DEFAULT_SIMULATOR_MAX_TOKENS,
    textgrad_max_tokens: int = DEFAULT_TEXTGRAD_MAX_TOKENS,
    request_timeout: float | None = None,
    dataset_seed: int = DEFAULT_DATASET_SEED,
    prompt_baseline: str = DEFAULT_PROMPT_BASELINE,
) -> list[str]:
    command = [
        *SCRIPT_COMMAND,
        "--max-iter",
        str(max_iterations),
        "--eval-size",
        str(eval_size),
    ]
    if dry_run:
        command.append("--dry-run")
    if local:
        command.append("--local")
    if simulator_max_tokens != DEFAULT_SIMULATOR_MAX_TOKENS:
        command.extend(["--sim-max-tokens", str(simulator_max_tokens)])
    if textgrad_max_tokens != DEFAULT_TEXTGRAD_MAX_TOKENS:
        command.extend(["--textgrad-max-tokens", str(textgrad_max_tokens)])
    if request_timeout is not None:
        command.extend(["--request-timeout", _format_timeout(request_timeout)])
    if dataset_seed != DEFAULT_DATASET_SEED:
        command.extend(["--dataset-seed", str(dataset_seed)])
    if prompt_baseline != DEFAULT_PROMPT_BASELINE:
        command.extend(["--prompt-baseline", prompt_baseline])
    command.extend(
        [
            "--base-url",
            base_url,
            "--model",
            model,
            "--run-id",
            run_id,
            "--manifest-dir",
            manifest_dir,
        ]
    )
    return command


def _manifest_path(manifest_dir: str, run_id: str) -> Path:
    return Path(manifest_dir) / f"{_safe_run_id_token(run_id)}.json"


def _write_result_summary(run_id: str, result_summary: dict) -> Path:
    output_path = RESULTS_DIR / f"w3w4_{_safe_run_id_token(run_id)}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result_summary, indent=2))
    return output_path


def _write_textgrad_steps(run_id: str, textgrad_steps: list[dict]) -> Path:
    output_path = RESULTS_DIR / f"w3w4_{_safe_run_id_token(run_id)}_textgrad_steps.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(textgrad_steps, indent=2))
    return output_path


def _textgrad_steps_from_history(history) -> list[dict]:
    steps = []
    for record in history:
        step = getattr(record, "gradient_step", None)
        if step is None:
            continue
        prompt_before = getattr(record, "prompt", "")
        edited_prompt = getattr(step, "edited_prompt", "")
        steps.append(
            {
                "iteration": int(getattr(step, "iteration", record.iteration)),
                "loss_before": float(
                    getattr(step, "loss_before", record.loss.total_loss)
                ),
                "feedback": getattr(step, "feedback", ""),
                "edited_prompt": edited_prompt,
                "edited_prompt_changed": edited_prompt != prompt_before,
            }
        )
    return steps


def _prompt_update_count(textgrad_steps: list[dict]) -> int:
    return sum(1 for step in textgrad_steps if step.get("edited_prompt_changed"))


def _suspected_prompt_truncation_count(textgrad_steps: list[dict]) -> int:
    return sum(
        1
        for step in textgrad_steps
        if _looks_like_truncated_prompt(step.get("edited_prompt", ""))
    )


def _looks_like_truncated_prompt(prompt: str) -> bool:
    stripped = prompt.strip()
    if not stripped:
        return True
    lower = stripped.lower()
    if len(stripped) < 200:
        return True
    if "json" not in lower or "probab" not in lower:
        return True
    incomplete_suffixes = (
        "your task",
        "utility calculation",
        "step 2:",
        "convenience",
        "####",
        "-",
        ":",
    )
    return lower.endswith(incomplete_suffixes)


def _textgrad_output_budget_saturated(
    *,
    textgrad_output_tokens: int,
    textgrad_call_count: int,
    textgrad_max_tokens: int,
) -> bool:
    if textgrad_call_count <= 0 or textgrad_max_tokens <= 0:
        return False
    return textgrad_output_tokens >= textgrad_call_count * textgrad_max_tokens


def _min_edited_prompt_chars(textgrad_steps: list[dict]) -> int:
    lengths = [
        len(step.get("edited_prompt", ""))
        for step in textgrad_steps
        if step.get("edited_prompt") is not None
    ]
    return min(lengths, default=0)


def _textgrad_effect_status(
    *,
    initial_loss: float,
    best_loss: float,
    textgrad_call_count: int,
    prompt_update_count: int,
) -> str:
    if textgrad_call_count <= 0:
        return "not_run"
    if best_loss < initial_loss:
        return "improved"
    if prompt_update_count > 0:
        return "updated_no_improvement"
    return "no_prompt_change"


def _safe_run_id_token(run_id: str) -> str:
    token = quote(run_id, safe="._-")
    if not token or token in {".", ".."}:
        raise ValueError("run_id must contain at least one path-safe character")
    return token


def _prompt_for_baseline(prompt_baseline: str) -> str:
    try:
        return PROMPT_BASELINES[prompt_baseline]
    except KeyError as exc:
        raise ValueError(
            f"prompt_baseline must be one of {sorted(PROMPT_BASELINES)}"
        ) from exc


def _format_timeout(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(value)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIRCE W3-W4 Causal Calibration")
    parser.add_argument("--max-iter", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--local", action="store_true", help="Use local LM Studio model")
    parser.add_argument("--base-url", default="http://localhost:1234/v1")
    parser.add_argument("--model", default="google/gemma-4-31b")
    parser.add_argument("--eval-size", type=int, default=10, help="Pairs per evaluation")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--manifest-dir", default="experiments/results/manifests")
    parser.add_argument("--sim-max-tokens", type=int, default=DEFAULT_SIMULATOR_MAX_TOKENS)
    parser.add_argument("--textgrad-max-tokens", type=int, default=DEFAULT_TEXTGRAD_MAX_TOKENS)
    parser.add_argument("--request-timeout", type=float, default=None)
    parser.add_argument("--dataset-seed", type=int, default=DEFAULT_DATASET_SEED)
    parser.add_argument(
        "--prompt-baseline",
        choices=sorted(PROMPT_BASELINES),
        default=DEFAULT_PROMPT_BASELINE,
    )
    args = parser.parse_args()
    run_experiment(
        max_iterations=args.max_iter,
        dry_run=args.dry_run,
        local=args.local,
        base_url=args.base_url,
        model=args.model,
        eval_size=args.eval_size,
        run_id=args.run_id,
        manifest_dir=args.manifest_dir,
        simulator_max_tokens=args.sim_max_tokens,
        textgrad_max_tokens=args.textgrad_max_tokens,
        request_timeout=args.request_timeout,
        dataset_seed=args.dataset_seed,
        prompt_baseline=args.prompt_baseline,
    )
