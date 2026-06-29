"""Extract macro-level emergence statistics from ABM trajectories."""

from dataclasses import dataclass
import numpy as np


@dataclass
class EmergenceStats:
    initial_entropy: float
    final_entropy: float
    final_polarization: float
    convergence_step: int | None
    opinion_trajectory: list[dict[int, float]]
    entropy_trajectory: list[float]


def _entropy(dist: dict[int, float]) -> float:
    probs = np.array([v for v in dist.values() if v > 0])
    return float(-np.sum(probs * np.log2(probs)))


def _polarization(dist: dict[int, float]) -> float:
    probs = np.array(list(dist.values()))
    return float(1.0 - np.sum(probs**2))


def compute_emergence_stats(
    trajectory: list[dict[int, float]],
    consensus_threshold: float = 0.9,
) -> EmergenceStats:
    entropy_traj = [_entropy(t) for t in trajectory]
    initial_entropy = entropy_traj[0]
    final_entropy = entropy_traj[-1]
    final_polarization = _polarization(trajectory[-1])

    convergence_step = None
    for i, dist in enumerate(trajectory):
        if max(dist.values()) >= consensus_threshold:
            convergence_step = i
            break

    return EmergenceStats(
        initial_entropy=initial_entropy,
        final_entropy=final_entropy,
        final_polarization=final_polarization,
        convergence_step=convergence_step,
        opinion_trajectory=trajectory,
        entropy_trajectory=entropy_traj,
    )
