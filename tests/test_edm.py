import pytest
from circe.calibration.edm import compute_edm, EDMResult
from circe.abm.emergence_stats import EmergenceStats


def _make_stats(
    initial_entropy=1.0,
    final_entropy=0.0,
    final_polarization=0.0,
    convergence_step=50,
    n_steps=100,
) -> EmergenceStats:
    entropy_traj = [
        initial_entropy * (1 - i / n_steps) + final_entropy * (i / n_steps)
        for i in range(n_steps + 1)
    ]
    opinion_traj = [
        {0: 0.5 + 0.5 * (i / n_steps), 1: 0.5 - 0.5 * (i / n_steps)}
        for i in range(n_steps + 1)
    ]
    return EmergenceStats(
        initial_entropy=initial_entropy,
        final_entropy=final_entropy,
        final_polarization=final_polarization,
        convergence_step=convergence_step,
        opinion_trajectory=opinion_traj,
        entropy_trajectory=entropy_traj,
    )


def test_edm_result_dataclass():
    result = EDMResult(d_macro=0.5, edm_score=0.5)
    assert result.d_macro == 0.5
    assert result.edm_score == 0.5


def test_edm_perfect_match():
    stats = _make_stats()
    result = compute_edm(true_stats=stats, predicted_stats=stats)
    assert result.edm_score == pytest.approx(0.0, abs=1e-6)
    assert result.d_macro == pytest.approx(0.0, abs=1e-6)


def test_edm_total_mismatch():
    true_stats = _make_stats(final_entropy=0.0, final_polarization=0.0)
    pred_stats = _make_stats(final_entropy=1.0, final_polarization=1.0)
    result = compute_edm(true_stats=true_stats, predicted_stats=pred_stats)
    assert result.edm_score > 0.0
    assert result.d_macro > 0.0


def test_edm_uses_evaluate_emergence_distortion():
    true_stats = _make_stats(final_entropy=0.2, final_polarization=0.1)
    pred_stats = _make_stats(final_entropy=0.5, final_polarization=0.3)
    result = compute_edm(true_stats=true_stats, predicted_stats=pred_stats)
    assert result.edm_score > 0.0


def test_edm_custom_weights():
    true_stats = _make_stats(final_entropy=0.0)
    pred_stats = _make_stats(final_entropy=0.5)
    result_default = compute_edm(true_stats=true_stats, predicted_stats=pred_stats)
    result_entropy_heavy = compute_edm(
        true_stats=true_stats,
        predicted_stats=pred_stats,
        weights={"entropy": 5.0, "polarization": 1.0, "trajectory": 1.0},
    )
    assert result_entropy_heavy.edm_score >= result_default.edm_score


def test_edm_symmetric():
    stats_a = _make_stats(final_entropy=0.2, final_polarization=0.1)
    stats_b = _make_stats(final_entropy=0.6, final_polarization=0.4)
    result_ab = compute_edm(true_stats=stats_a, predicted_stats=stats_b)
    result_ba = compute_edm(true_stats=stats_b, predicted_stats=stats_a)
    assert result_ab.edm_score == pytest.approx(result_ba.edm_score, abs=1e-6)
