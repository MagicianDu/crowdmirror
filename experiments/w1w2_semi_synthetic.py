"""
W1-W2 Deliverable: Semi-synthetic environment validation.
Demonstrates that ground-truth counterfactuals and emergence dynamics
are correctly generated and evaluable.
"""

try:
    from ._bootstrap import bootstrap_src_path
except ImportError:
    from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from circe.dgp.counterfactual import generate_counterfactual_dataset
from circe.abm.voter_model import VoterModel, VoterModelConfig
from circe.abm.emergence_stats import compute_emergence_stats
from circe.evaluation.ground_truth import (
    evaluate_counterfactual_accuracy,
    evaluate_emergence_distortion,
)
import numpy as np


def main():
    print("=" * 60)
    print("CIRCE W1-W2: Semi-Synthetic Environment Validation")
    print("=" * 60)

    print("\n--- Route A: Counterfactual Ground Truth (Swissmetro MNL) ---")
    pairs = generate_counterfactual_dataset(
        n_scenarios=100, n_interventions=5, intervention_type="sm_cost_increase"
    )
    print(f"Generated {len(pairs)} counterfactual pairs")
    print(f"ATE range: [{min(p.ate for p in pairs):.4f}, {max(p.ate for p in pairs):.4f}]")
    print(f"Mean ATE: {np.mean([p.ate for p in pairs]):.4f}")

    rng = np.random.default_rng(123)
    noisy_ates = [p.ate + rng.normal(0, 0.03) for p in pairs]
    result = evaluate_counterfactual_accuracy(
        [p.ate for p in pairs], noisy_ates
    )
    print(f"\nNoisy predictor evaluation:")
    print(f"  MAE: {result.mae:.4f}")
    print(f"  RMSE: {result.rmse:.4f}")
    print(f"  Correlation: {result.correlation:.4f}")
    print(f"  Bias: {result.bias:.4f}")

    print("\n--- Route B: Emergence Ground Truth (Voter Model) ---")
    configs = [
        ("complete_2op", VoterModelConfig(n_agents=100, n_opinions=2, network="complete", seed=42)),
        ("complete_3op", VoterModelConfig(n_agents=100, n_opinions=3, network="complete", seed=42)),
        ("grid_2op", VoterModelConfig(n_agents=100, n_opinions=2, network="grid", seed=42)),
    ]

    for name, config in configs:
        model = VoterModel(config)
        model.run(steps=200)
        stats = compute_emergence_stats(model.get_trajectory())
        print(f"\n  [{name}]")
        print(f"    Initial entropy: {stats.initial_entropy:.3f}")
        print(f"    Final entropy: {stats.final_entropy:.3f}")
        print(f"    Final polarization: {stats.final_polarization:.3f}")
        print(f"    Convergence step: {stats.convergence_step}")

    print("\n--- Emergence Distortion Evaluation (same model, different seeds) ---")
    true_model = VoterModel(VoterModelConfig(n_agents=100, n_opinions=2, seed=42))
    true_model.run(steps=200)
    true_stats = compute_emergence_stats(true_model.get_trajectory())

    shifted_model = VoterModel(VoterModelConfig(n_agents=100, n_opinions=2, seed=99))
    shifted_model.run(steps=200)
    shifted_stats = compute_emergence_stats(shifted_model.get_trajectory())

    edm = evaluate_emergence_distortion(true_stats, shifted_stats)
    print(f"  Entropy MAE: {edm.entropy_mae:.4f}")
    print(f"  Polarization error: {edm.polarization_error:.4f}")
    print(f"  Trajectory MSE: {edm.trajectory_mse:.6f}")

    print("\n" + "=" * 60)
    print("W1-W2 COMPLETE: Semi-synthetic environment operational.")
    print("Ready for W3-W4: TextGrad causal calibration.")
    print("=" * 60)


if __name__ == "__main__":
    main()
