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
import sys
import time
import uuid
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

from circe.abm.voter_model import VoterModel, VoterModelConfig
from circe.abm.emergence_stats import compute_emergence_stats
from circe.simulator.multi_agent import MultiAgentSimulator, MultiAgentConfig
from circe.simulator.interaction_templates import BAD_INTERACTION_PROMPT
from circe.calibration.edm import compute_edm
from circe.calibration.emergence_loop import (
    EmergenceCalibrationLoop,
    EmergenceCalibrationConfig,
)


RESULTS_DIR = Path("experiments/results")
SCRIPT_COMMAND = ["python", "experiments/w5w6_emergence_calibration.py"]
REQUIRED_RESULT_METRICS = (
    "initial_edm",
    "best_edm",
    "final_edm",
    "n_iterations",
)


def run_experiment(
    n_agents: int = 20,
    n_steps: int = 10,
    max_iterations: int = 5,
    dry_run: bool = False,
    local: bool = False,
    bad_init: bool = False,
    update_mode: str = "asynchronous",
    run_id: str | None = None,
    manifest_dir: str = "experiments/results/manifests",
    command: list[str] | None = None,
):
    print("=" * 60)
    print("CIRCE W5-W6: Emergence Calibration")
    print("=" * 60)

    mode = "dry-run" if dry_run else "local" if local else "live"
    manifest_run_id = run_id or _generate_run_id(mode)
    manifest_command = (
        _command_with_run_id(command, manifest_run_id)
        if command is not None
        else _build_command(
            n_agents=n_agents,
            n_steps=n_steps,
            max_iterations=max_iterations,
            dry_run=dry_run,
            local=local,
            bad_init=bad_init,
            run_id=manifest_run_id,
            manifest_dir=manifest_dir,
            update_mode=update_mode,
        )
    )

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
        summary = _run_dry(n_agents, n_steps, max_iterations, update_mode)
        output_path = _write_result_summary(manifest_run_id, summary)
        print(f"Results saved to {output_path}")
        effective_config = summary.get(
            "effective_config",
            {
                "n_agents": min(n_agents, 5),
                "n_steps": min(n_steps, 3),
                "max_iterations": min(max_iterations, 2),
                "update_mode": update_mode,
            },
        )
        manifest = build_emergence_manifest(
            run_id=manifest_run_id,
            mode="dry-run",
            command=manifest_command,
            config=effective_config,
            result_summary=summary,
            result_path=str(output_path),
        )
        manifest_path = _manifest_path(manifest_dir, manifest_run_id)
        write_manifest(manifest_path, manifest)
        print(f"Evidence manifest saved to {manifest_path}")
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
        update_mode=update_mode,
        textgrad_model=model,
        initial_prompt=BAD_INTERACTION_PROMPT if bad_init else None,
    )

    if bad_init:
        print("\n[BAD-INIT MODE — starting from deliberately stubborn prompt]")

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
            "update_mode": update_mode,
        },
        "ground_truth": {
            "initial_entropy": true_stats.initial_entropy,
            "final_entropy": true_stats.final_entropy,
            "final_polarization": true_stats.final_polarization,
            "convergence_step": true_stats.convergence_step,
        },
        "history": result.history,
    }
    output_path = _write_result_summary(manifest_run_id, output_data)
    print(f"\nResults saved to {output_path}")
    manifest = build_emergence_manifest(
        run_id=manifest_run_id,
        mode=mode,
        command=manifest_command,
        config={
            "n_agents": n_agents,
            "n_steps": n_steps,
            "max_iterations": max_iterations,
            "local": local,
            "provider": provider,
            "model": model,
            "update_mode": update_mode,
            "bad_init": bad_init,
        },
        result_summary=output_data,
        result_path=str(output_path),
    )
    manifest_path = _manifest_path(manifest_dir, manifest_run_id)
    write_manifest(manifest_path, manifest)
    print(f"Evidence manifest saved to {manifest_path}")

    print("\n" + "=" * 60)
    print("W5-W6 COMPLETE: Emergence calibration demonstrated.")
    print("=" * 60)


def build_emergence_manifest(
    *,
    run_id: str,
    mode: str,
    command: list[str],
    config: dict,
    result_summary: dict,
    result_path: str,
) -> dict:
    missing_metrics = [
        metric for metric in REQUIRED_RESULT_METRICS if metric not in result_summary
    ]
    if missing_metrics:
        raise ValueError(
            "result_summary missing required metrics: " + ", ".join(missing_metrics)
        )

    initial = float(result_summary["initial_edm"])
    best = float(result_summary["best_edm"])
    improvement_ratio = (initial - best) / initial if initial > 0 else 0.0
    return build_run_manifest(
        run_id=run_id,
        lane="emergence",
        mode=mode,
        command=command,
        config=config,
        metrics={
            "initial_edm": initial,
            "best_edm": best,
            "final_edm": float(result_summary["final_edm"]),
            "improvement_ratio": improvement_ratio,
            "n_iterations": int(result_summary["n_iterations"]),
        },
        artifacts={"result_json": result_path},
        notes=[
            "Emergence calibration compares LLM-agent dynamics with Voter Model ground truth.",
            "Dry-run mode uses mocked LLM responses and only validates execution plumbing.",
        ],
    )


def _run_dry(
    n_agents: int,
    n_steps: int,
    max_iterations: int,
    update_mode: str,
):
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

    requested_config = {
        "n_agents": n_agents,
        "n_steps": n_steps,
        "max_iterations": max_iterations,
        "update_mode": update_mode,
    }
    effective_config = {
        "n_agents": min(n_agents, 5),
        "n_steps": min(n_steps, 3),
        "max_iterations": min(max_iterations, 2),
        "update_mode": update_mode,
    }
    with patch("circe.llm_client.LLMClient.chat", mock_chat):
        config = EmergenceCalibrationConfig(
            n_agents=effective_config["n_agents"],
            n_opinions=2,
            n_steps=effective_config["n_steps"],
            max_iterations=effective_config["max_iterations"],
            patience=3,
            seed=42,
            update_mode=effective_config["update_mode"],
        )
        loop = EmergenceCalibrationLoop(config)
        result = loop.run()

    print(f"  Pipeline OK: {result.n_iterations} iterations, {call_count[0]} mock LLM calls")
    print(f"  Initial EDM: {result.initial_edm:.4f}")
    print(f"  Final EDM: {result.final_edm:.4f}")
    print(f"  Ground truth entropy: {loop.ground_truth_stats.initial_entropy:.4f} → "
          f"{loop.ground_truth_stats.final_entropy:.4f}")
    print("  [Dry run complete — pipeline is functional]")
    return {
        "initial_edm": result.initial_edm,
        "best_edm": result.best_edm,
        "final_edm": result.final_edm,
        "n_iterations": result.n_iterations,
        "mock_llm_call_count": call_count[0],
        "requested_config": requested_config,
        "effective_config": effective_config,
        "history": result.history,
        "audit": {
            "mode": "dry-run",
            "mocked_llm": True,
            "cap_reason": (
                "dry-run caps agent, step, and iteration counts for fast "
                "plumbing verification"
            ),
        },
    }


def _generate_run_id(mode: str) -> str:
    timestamp_ms = int(time.time() * 1000)
    random_suffix = uuid.uuid4().hex[:12]
    return f"w5w6-{mode}-{timestamp_ms}-{random_suffix}"


def _build_command(
    *,
    n_agents: int,
    n_steps: int,
    max_iterations: int,
    dry_run: bool,
    local: bool,
    bad_init: bool,
    run_id: str,
    manifest_dir: str,
    update_mode: str,
) -> list[str]:
    command = [
        *SCRIPT_COMMAND,
        "--agents",
        str(n_agents),
        "--steps",
        str(n_steps),
        "--max-iter",
        str(max_iterations),
    ]
    if dry_run:
        command.append("--dry-run")
    if local:
        command.append("--local")
    if bad_init:
        command.append("--bad-init")
    command.extend(
        [
            "--run-id",
            run_id,
            "--manifest-dir",
            manifest_dir,
            "--update-mode",
            update_mode,
        ]
    )
    return command


def _command_with_run_id(command: list[str], run_id: str) -> list[str]:
    if any(part == "--run-id" or part.startswith("--run-id=") for part in command):
        return command
    return [*command, "--run-id", run_id]


def _manifest_path(manifest_dir: str, run_id: str) -> Path:
    return Path(manifest_dir) / f"{_safe_run_id_token(run_id)}.json"


def _write_result_summary(run_id: str, result_summary: dict) -> Path:
    output_path = RESULTS_DIR / f"w5w6_{_safe_run_id_token(run_id)}.json"
    result_json = json.dumps(result_summary, allow_nan=False, indent=2)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result_json)
    return output_path


def _safe_run_id_token(run_id: str) -> str:
    token = quote(run_id, safe="._-")
    if not token or token in {".", ".."}:
        raise ValueError("run_id must contain at least one path-safe character")
    return token


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIRCE W5-W6 Emergence Calibration")
    parser.add_argument("--agents", type=int, default=20, help="Number of agents")
    parser.add_argument("--steps", type=int, default=10, help="Simulation steps")
    parser.add_argument("--max-iter", type=int, default=5, help="Max calibration iterations")
    parser.add_argument("--dry-run", action="store_true", help="Mock LLM responses")
    parser.add_argument("--local", action="store_true", help="Use LM Studio (localhost:1234)")
    parser.add_argument("--bad-init", action="store_true",
                        help="Start from deliberately stubborn prompt (ablation)")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--manifest-dir", default="experiments/results/manifests")
    parser.add_argument(
        "--update-mode",
        choices=["synchronous", "asynchronous"],
        default="asynchronous",
    )
    args = parser.parse_args()
    run_experiment(
        n_agents=args.agents,
        n_steps=args.steps,
        max_iterations=args.max_iter,
        dry_run=args.dry_run,
        local=args.local,
        bad_init=args.bad_init,
        update_mode=args.update_mode,
        run_id=args.run_id,
        manifest_dir=args.manifest_dir,
        command=[*SCRIPT_COMMAND, *sys.argv[1:]],
    )
