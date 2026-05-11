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


def run_experiment(max_iterations: int = 10, dry_run: bool = False,
                   local: bool = False, base_url: str = "http://localhost:1234/v1",
                   model: str = "google/gemma-4-31b", eval_size: int = 10,
                   run_id: str | None = None,
                   manifest_dir: str = "experiments/results/manifests"):
    print("=" * 60)
    print("CIRCE W3-W4: Individual Causal Calibration")
    print("=" * 60)

    # Generate ground-truth counterfactual dataset
    print("\n--- Generating counterfactual dataset ---")
    pairs = generate_counterfactual_dataset(
        n_scenarios=100, n_interventions=5, intervention_type="sm_cost_increase"
    )
    print(f"Generated {len(pairs)} counterfactual pairs")
    print(f"ATE range: [{min(p.ate for p in pairs):.4f}, {max(p.ate for p in pairs):.4f}]")

    # Split into train/test
    train_pairs = pairs[:400]
    test_pairs = pairs[400:]
    print(f"Train: {len(train_pairs)} pairs, Test: {len(test_pairs)} pairs")

    # Configure calibration
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
        eval_sample_size=eval_size,
        provider=provider,
        base_url=base_url,
    )

    if dry_run:
        print("\n[DRY RUN MODE — using mock responses]")
        summary = _run_dry(config, train_pairs, test_pairs)
        manifest_run_id = run_id or f"w3w4-dry-run-{int(time.time())}"
        manifest = build_causal_manifest(
            run_id=manifest_run_id,
            mode="dry-run",
            command=["python", "experiments/w3w4_causal_calibration.py", "--dry-run"],
            config={
                "max_iterations": config.max_iterations,
                "eval_size": config.eval_sample_size,
            },
            result_summary=summary,
            result_path="",
        )
        manifest_path = Path(manifest_dir) / f"{manifest_run_id}.json"
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
    output_dir = Path("experiments/results")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "w3w4_calibration_result.json"
    output_data = {
        "best_prompt": result.best_prompt,
        "best_loss": result.best_loss,
        "initial_loss": result.initial_loss,
        "final_loss": result.final_loss,
        "n_iterations": result.n_iterations,
        "total_llm_calls": result.total_llm_calls,
        "elapsed_seconds": elapsed,
        "history": [
            {"iteration": r.iteration, "total_loss": r.loss.total_loss,
             "ece": r.loss.ece, "ate_mae": r.loss.ate_mae}
            for r in result.history
        ],
    }
    output_path.write_text(json.dumps(output_data, indent=2))
    print(f"\nResults saved to {output_path}")
    manifest_run_id = run_id or f"w3w4-{'local' if local else 'live'}-{int(time.time())}"
    manifest = build_causal_manifest(
        run_id=manifest_run_id,
        mode="local" if local else "live",
        command=["python", "experiments/w3w4_causal_calibration.py"],
        config={
            "max_iterations": max_iterations,
            "eval_size": eval_size,
            "local": local,
            "provider": provider,
            "model": sim_model,
        },
        result_summary=output_data,
        result_path=str(output_path),
    )
    manifest_path = Path(manifest_dir) / f"{manifest_run_id}.json"
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
) -> dict:
    initial = float(result_summary.get("initial_loss", 0.0))
    best = float(result_summary.get("best_loss", initial))
    improvement_ratio = (initial - best) / initial if initial > 0 else 0.0
    return build_run_manifest(
        run_id=run_id,
        lane="causal",
        mode=mode,
        command=command,
        config=config,
        metrics={
            "initial_loss": initial,
            "best_loss": best,
            "final_loss": float(result_summary.get("final_loss", best)),
            "improvement_ratio": improvement_ratio,
            "n_iterations": int(result_summary.get("n_iterations", 0)),
            "total_llm_calls": int(result_summary.get("total_llm_calls", 0)),
        },
        artifacts={"result_json": result_path},
        notes=[
            "Causal calibration compares predicted mode probabilities and Swissmetro ATE.",
            "Dry-run mode uses mocked LLM responses and only validates execution plumbing.",
        ],
    )


def _run_dry(config, train_pairs, test_pairs):
    """Dry run: verify pipeline works without API calls."""
    from unittest.mock import patch, MagicMock
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
        config.max_iterations = 3
        config.eval_sample_size = 10
        loop = CalibrationLoop(config=config, dataset=train_pairs[:20])
        result = loop.run()

    print(f"  Pipeline OK: {result.n_iterations} iterations, {call_count[0]} mock LLM calls")
    print(f"  Initial loss: {result.initial_loss:.4f}")
    print(f"  Final loss: {result.final_loss:.4f}")
    print("  [Dry run complete — pipeline is functional]")
    summary = {
        "initial_loss": result.initial_loss,
        "best_loss": result.best_loss,
        "final_loss": result.final_loss,
        "n_iterations": result.n_iterations,
        "total_llm_calls": call_count[0],
    }
    return summary


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
    )
