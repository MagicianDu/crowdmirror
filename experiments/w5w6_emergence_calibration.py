"""
W5-W6 Deliverable: Emergence Calibration.
Demonstrates that TextGrad can optimize interaction prompts (θ_ρ) to reduce
Emergence Distortion Metric (EDM) against Voter Model ground truth.

Usage:
    python experiments/w5w6_emergence_calibration.py [--dry-run] [--local] \
        [--agents N] [--steps S] [--max-iter I]

Modes:
    --dry-run   Use mocked LLM responses (no API calls, pipeline verification)
    --local     Use LM Studio at localhost:1234 (OpenAI-compatible)
    (default)   Use configured provider (openai-compatible)
"""

import argparse
import json
import time
from pathlib import Path
from circe.abm.voter_model import VoterModel, VoterModelConfig
from circe.abm.emergence_stats import compute_emergence_stats
from circe.simulator.multi_agent import MultiAgentSimulator, MultiAgentConfig
from circe.calibration.edm import compute_edm
from circe.calibration.emergence_loop import (
    EmergenceCalibrationLoop,
    EmergenceCalibrationConfig,
)


def run_experiment(
    n_agents: int = 20,
    n_steps: int = 10,
    max_iterations: int = 5,
    dry_run: bool = False,
    local: bool = False,
):
    print("=" * 60)
    print("CIRCE W5-W6: Emergence Calibration")
    print("=" * 60)

    provider = "openai"
    base_url = None
    model = "google/gemma-4-31b"
    if local:
        base_url = "http://localhost:1234/v1"
        model = "google/gemma-4-31b"
        print(f"\n[LOCAL MODE — LM Studio at {base_url}]")

    print(f"\n--- Generating Voter Model ground truth ---")
    print(f"  Agents: {n_agents}, Opinions: 2, Network: complete, Steps: {n_steps}")
    vm_config = VoterModelConfig(n_agents=n_agents, n_opinions=2, seed=42)
    vm = VoterModel(vm_config)
    vm.run(steps=n_steps)
    true_stats = compute_emergence_stats(vm.get_trajectory())
    print(f"  Initial entropy: {true_stats.initial_entropy:.4f}")
    print(f"  Final entropy: {true_stats.final_entropy:.4f}")
    print(f"  Final polarization: {true_stats.final_polarization:.4f}")
    print(f"  Convergence step: {true_stats.convergence_step}")

    if dry_run:
        print("\n[DRY RUN MODE — using mock responses]")
        _run_dry(n_agents, n_steps, max_iterations)
        return

    print(f"\n--- Running emergence calibration (max {max_iterations} iterations) ---")
    config = EmergenceCalibrationConfig(
        n_agents=n_agents,
        n_opinions=2,
        network="complete",
        n_steps=n_steps,
        seed=42,
        max_iterations=max_iterations,
        patience=3,
        edm_threshold=0.05,
        model=model,
        provider=provider,
        base_url=base_url,
        textgrad_model=model,
    )

    loop = EmergenceCalibrationLoop(config)
    start_time = time.time()
    result = loop.run()
    elapsed = time.time() - start_time

    print(f"\n--- Emergence Calibration Results ---")
    print(f"  Iterations: {result.n_iterations}")
    print(f"  Initial EDM: {result.initial_edm:.4f}")
    print(f"  Best EDM: {result.best_edm:.4f}")
    print(f"  Final EDM: {result.final_edm:.4f}")
    improvement = (1 - result.best_edm / result.initial_edm) * 100 if result.initial_edm > 0 else 0
    print(f"  Improvement: {improvement:.1f}%")
    print(f"  Time elapsed: {elapsed:.1f}s")

    print(f"\n--- EDM History ---")
    for rec in result.history:
        marker = " *" if rec["edm_score"] == result.best_edm else ""
        print(f"  Iter {rec['iteration']}: EDM={rec['edm_score']:.4f} "
              f"(d_macro={rec['d_macro']:.4f}){marker}")

    print(f"\n--- Best Interaction Prompt (θ_ρ) ---")
    print(result.best_prompt[:500])
    if len(result.best_prompt) > 500:
        print(f"  ... ({len(result.best_prompt)} chars total)")

    output_dir = Path("experiments/results")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "w5w6_emergence_result.json"
    output_data = {
        "best_prompt": result.best_prompt,
        "best_edm": result.best_edm,
        "initial_edm": result.initial_edm,
        "final_edm": result.final_edm,
        "n_iterations": result.n_iterations,
        "elapsed_seconds": elapsed,
        "config": {
            "n_agents": n_agents,
            "n_steps": n_steps,
            "max_iterations": max_iterations,
            "model": model,
        },
        "ground_truth": {
            "initial_entropy": true_stats.initial_entropy,
            "final_entropy": true_stats.final_entropy,
            "final_polarization": true_stats.final_polarization,
            "convergence_step": true_stats.convergence_step,
        },
        "history": result.history,
    }
    output_path.write_text(json.dumps(output_data, indent=2))
    print(f"\nResults saved to {output_path}")

    print("\n" + "=" * 60)
    print("W5-W6 COMPLETE: Emergence calibration demonstrated.")
    print("=" * 60)


def _run_dry(n_agents: int, n_steps: int, max_iterations: int):
    """Dry run: verify pipeline works without API calls."""
    from unittest.mock import patch
    from circe.llm_client import LLMResponse

    call_count = [0]

    def mock_chat(self, system="", user=""):
        call_count[0] += 1
        if "optimization" in system.lower() or "improve" in system.lower():
            return LLMResponse(
                content=(
                    "FEEDBACK: Agents are not conforming enough to neighbors.\n\n"
                    "EDITED PROMPT: You are agent {agent_id} in a social network.\n"
                    "Your current opinion: {agent_opinion}\n"
                    "Your neighbors' opinions: {neighbor_opinions}\n"
                    "Possible opinions: {possible_opinions}\n"
                    "You strongly tend to adopt the majority opinion among your "
                    "neighbors. Output JSON:"
                ),
                input_tokens=500,
                output_tokens=200,
            )
        return LLMResponse(
            content='{"new_opinion": 0}',
            input_tokens=80,
            output_tokens=10,
        )

    with patch("circe.llm_client.LLMClient.chat", mock_chat):
        config = EmergenceCalibrationConfig(
            n_agents=min(n_agents, 5),
            n_opinions=2,
            n_steps=min(n_steps, 3),
            max_iterations=min(max_iterations, 2),
            patience=3,
            seed=42,
        )
        loop = EmergenceCalibrationLoop(config)
        result = loop.run()

    print(f"  Pipeline OK: {result.n_iterations} iterations, {call_count[0]} mock LLM calls")
    print(f"  Initial EDM: {result.initial_edm:.4f}")
    print(f"  Final EDM: {result.final_edm:.4f}")
    print(f"  Ground truth entropy: {loop.ground_truth_stats.initial_entropy:.4f} → "
          f"{loop.ground_truth_stats.final_entropy:.4f}")
    print("  [Dry run complete — pipeline is functional]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIRCE W5-W6 Emergence Calibration")
    parser.add_argument("--agents", type=int, default=20, help="Number of agents")
    parser.add_argument("--steps", type=int, default=10, help="Simulation steps")
    parser.add_argument("--max-iter", type=int, default=5, help="Max calibration iterations")
    parser.add_argument("--dry-run", action="store_true", help="Mock LLM responses")
    parser.add_argument("--local", action="store_true", help="Use LM Studio (localhost:1234)")
    args = parser.parse_args()
    run_experiment(
        n_agents=args.agents,
        n_steps=args.steps,
        max_iterations=args.max_iter,
        dry_run=args.dry_run,
        local=args.local,
    )
