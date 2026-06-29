import json
from pathlib import Path

try:
    from ._bootstrap import bootstrap_src_path
except ImportError:
    from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from circe.calibration.loss import compute_ece
from circe.simulator.llm_choice import LLMChoiceSimulator
from circe.abm.emergence_stats import EmergenceStats
from circe.calibration.edm import compute_edm


def _make_stats(entropy_trajectory: list[float]) -> EmergenceStats:
    return EmergenceStats(
        initial_entropy=entropy_trajectory[0],
        final_entropy=entropy_trajectory[-1],
        final_polarization=0.0,
        convergence_step=len(entropy_trajectory) - 1,
        opinion_trajectory=[{0: 0.5, 1: 0.5} for _ in entropy_trajectory],
        entropy_trajectory=entropy_trajectory,
    )


def run_validation(output_path: str | Path = "experiments/results/trust_chain_validation.json") -> dict:
    sim = object.__new__(LLMChoiceSimulator)
    probs = sim._parse_probs(
        '{"train": 0.7, "car": 0.3}',
        ["train", "swissmetro", "car"],
    )
    true_stats = _make_stats([1.0, 0.5, 0.0])
    pred_stats = _make_stats([1.0, 1.0, 0.0])
    edm = compute_edm(true_stats=true_stats, predicted_stats=pred_stats)
    report = {
        "ece": {
            "zero_probability_true_event": compute_ece([0.0], [1.0]),
            "soft_target_perfect_match": compute_ece([0.4, 0.35, 0.25], [0.4, 0.35, 0.25]),
        },
        "probability_contract": {
            "keys": sorted(probs.keys()),
            "has_all_alternatives": set(probs) == {"train", "swissmetro", "car"},
            "sum": sum(probs.values()),
        },
        "emergence": {
            "edm_score": edm.edm_score,
            "d_macro": edm.d_macro,
        },
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True))
    return report


if __name__ == "__main__":
    report = run_validation()
    print(json.dumps(report, indent=2, sort_keys=True))
