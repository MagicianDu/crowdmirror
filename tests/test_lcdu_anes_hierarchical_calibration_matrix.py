import json
import subprocess
import sys

from experiments.lcdu_anes_hierarchical_calibration_matrix import (
    build_lcdu_anes_hierarchical_calibration_matrix,
)


def test_hierarchical_calibration_beats_sparse_segment_anchor():
    artifact = build_lcdu_anes_hierarchical_calibration_matrix(
        microdata_artifact=_microdata_artifact(
            heldout_sparse_distribution="oppose",
            test_sparse_distribution="oppose",
        ),
        artifact_id="lcdu-hierarchical-test",
        k_grid=[1, 10, 50],
    )

    assert artifact["schema_version"] == (
        "lcdu-anes-hierarchical-calibration-matrix-v1"
    )
    assert artifact["overall_status"] == "hierarchical_lcdu_constrained_signal_positive"
    assert artifact["candidate_generation_split"] == "calibration"
    assert artifact["candidate_acceptance_split"] == "heldout"
    assert artifact["final_claim_check_split"] == "test"
    assert artifact["anchor_win_task_count"] == 1
    assert artifact["unconstrained_anchor_win_task_count"] == 1
    assert artifact["constrained_anchor_win_task_count"] == 1
    assert artifact["constrained_worst_guard_pass_task_count"] == 1
    assert artifact["task_count"] == 1

    task = artifact["task_results"]["task_sparse_party_prior"]
    assert task["selected_method_id"].startswith("lcdu_hierarchical_party_k_")
    assert task["beats_deterministic_anchor"] is True
    assert task["test_loss_delta_vs_anchor"] < 0
    assert task["selected_prior_family"] == "party_or_ideology"
    assert task["test_final_worst_segment_loss"] < task["test_anchor_worst_segment_loss"]
    assert task["unconstrained_selection"]["selected_method_id"] == (
        task["selected_method_id"]
    )
    assert task["constrained_selection"]["beats_deterministic_anchor"] is True
    assert task["constrained_selection"]["heldout_worst_guard_pass"] is True
    assert task["constrained_fallback_reason"] is None
    assert "not_customer_field_validation" in artifact["risk_flags"]
    json.dumps(artifact, allow_nan=False)


def test_constrained_selection_falls_back_when_worst_guard_blocks_candidate():
    artifact = build_lcdu_anes_hierarchical_calibration_matrix(
        microdata_artifact=_microdata_artifact_with_worst_regression(),
        artifact_id="lcdu-hierarchical-test",
        k_grid=[50],
        max_worst_segment_delta=0.0,
    )

    assert artifact["overall_status"] == "hierarchical_lcdu_constrained_not_leading"
    assert artifact["unconstrained_anchor_win_task_count"] == 1
    assert artifact["constrained_anchor_win_task_count"] == 0
    assert artifact["constrained_worst_guard_pass_task_count"] == 1
    assert "constrained_selection_reduced_anchor_wins" in artifact["risk_flags"]

    task = artifact["task_results"]["task_weighted_gain_worst_regression"]
    assert task["unconstrained_selection"]["selected_method_id"] == (
        "lcdu_hierarchical_global_k_50"
    )
    assert task["unconstrained_selection"]["beats_deterministic_anchor"] is True
    assert (
        task["unconstrained_selection"]["heldout_worst_segment_delta_vs_anchor"] > 0
    )
    assert task["constrained_selection"]["selected_method_id"] == (
        "calibration_segment_anchor"
    )
    assert task["constrained_selection"]["beats_deterministic_anchor"] is False
    assert task["constrained_selection"]["fallback_reason"] == (
        "no_candidate_passed_worst_segment_guard"
    )
    assert task["constrained_selection"]["heldout_worst_guard_pass"] is True
    assert task["constrained_fallback_reason"] == (
        "no_candidate_passed_worst_segment_guard"
    )


def test_hierarchical_calibration_selects_by_heldout_not_test_oracle():
    artifact = build_lcdu_anes_hierarchical_calibration_matrix(
        microdata_artifact=_microdata_artifact(
            heldout_sparse_distribution="oppose",
            test_sparse_distribution="support",
        ),
        artifact_id="lcdu-hierarchical-test",
        k_grid=[1, 10, 50],
    )

    task = artifact["task_results"]["task_sparse_party_prior"]
    assert task["selected_method_id"] == task["heldout_best_method_id"]
    assert task["test_oracle_best_method_id"] == "calibration_segment_anchor"
    assert task["selected_method_id"] != task["test_oracle_best_method_id"]
    assert task["beats_deterministic_anchor"] is False
    assert task["unconstrained_selection"]["selected_method_id"] == (
        task["selected_method_id"]
    )
    assert "candidate_selected_by_heldout_not_test" in artifact["risk_flags"]


def test_hierarchical_calibration_script_writes_json(tmp_path):
    microdata = tmp_path / "microdata.json"
    output = tmp_path / "hierarchical.json"
    microdata.write_text(
        json.dumps(
            _microdata_artifact(
                heldout_sparse_distribution="oppose",
                test_sparse_distribution="oppose",
            )
        )
    )

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_anes_hierarchical_calibration_matrix.py",
            "--microdata-artifact",
            str(microdata),
            "--output",
            str(output),
            "--artifact-id",
            "lcdu-hierarchical-test",
            "--k-grid",
            "1",
            "10",
            "50",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "anchor_win_task_count": 1,
        "constrained_anchor_win_task_count": 1,
        "artifact_id": "lcdu-hierarchical-test",
        "output": str(output),
        "status": "hierarchical_lcdu_constrained_signal_positive",
        "task_count": 1,
        "unconstrained_anchor_win_task_count": 1,
    }
    persisted = json.loads(output.read_text())
    assert persisted["source_artifact_id"] == "microdata-test"
    assert persisted["selection_modes"] == ["unconstrained", "constrained"]


def _microdata_artifact(
    *,
    heldout_sparse_distribution: str,
    test_sparse_distribution: str,
) -> dict:
    return {
        "schema_version": "lcdu-anes-public-microdata-ingestion-v1",
        "artifact_id": "microdata-test",
        "overall_status": "segment_target_distributions_materialized_with_partial_schema",
        "target_distributions": {
            "task_sparse_party_prior": _task_distribution(
                sparse_distribution="support"
            )
        },
        "splits": {
            "calibration": {
                "target_distributions": {
                    "task_sparse_party_prior": _task_distribution(
                        sparse_distribution="support"
                    )
                }
            },
            "heldout": {
                "target_distributions": {
                    "task_sparse_party_prior": _task_distribution(
                        sparse_distribution=heldout_sparse_distribution
                    )
                }
            },
            "test": {
                "target_distributions": {
                    "task_sparse_party_prior": _task_distribution(
                        sparse_distribution=test_sparse_distribution
                    )
                }
            },
        },
    }


def _microdata_artifact_with_worst_regression() -> dict:
    return {
        "schema_version": "lcdu-anes-public-microdata-ingestion-v1",
        "artifact_id": "microdata-test",
        "overall_status": "segment_target_distributions_materialized_with_partial_schema",
        "target_distributions": {
            "task_weighted_gain_worst_regression": _worst_regression_task(
                large_segment_support_probability=0.7,
                small_segment_support_probability=1.0,
            )
        },
        "splits": {
            "calibration": {
                "target_distributions": {
                    "task_weighted_gain_worst_regression": _worst_regression_task(
                        large_segment_support_probability=0.7,
                        small_segment_support_probability=1.0,
                    )
                }
            },
            "heldout": {
                "target_distributions": {
                    "task_weighted_gain_worst_regression": _worst_regression_task(
                        large_segment_support_probability=0.4,
                        small_segment_support_probability=1.0,
                    )
                }
            },
            "test": {
                "target_distributions": {
                    "task_weighted_gain_worst_regression": _worst_regression_task(
                        large_segment_support_probability=0.4,
                        small_segment_support_probability=1.0,
                    )
                }
            },
        },
    }


def _worst_regression_task(
    *,
    large_segment_support_probability: float,
    small_segment_support_probability: float,
) -> dict:
    return {
        "task_id": "task_weighted_gain_worst_regression",
        "target_variable_id": "synthetic_policy_target",
        "segment_schema_coverage": {
            "coverage_status": "complete_for_task_card_axes",
            "missing_required_axes": [],
        },
        "overall": {
            "row_count": 1010,
            "policy_counts": {"support": 0, "oppose": 1010},
            "policy_probabilities": {"support": 0.0, "oppose": 1.0},
        },
        "by_segment": {
            "party_or_ideology=liberal|income=lower": _binary_segment(
                support_probability=large_segment_support_probability,
                row_count=1000,
            ),
            "party_or_ideology=conservative|income=upper": _binary_segment(
                support_probability=small_segment_support_probability,
                row_count=10,
            ),
        },
    }


def _binary_segment(*, support_probability: float, row_count: int) -> dict:
    support_count = int(round(support_probability * row_count))
    oppose_count = row_count - support_count
    return {
        "row_count": row_count,
        "policy_counts": {"support": support_count, "oppose": oppose_count},
        "policy_probabilities": {
            "support": support_probability,
            "oppose": 1.0 - support_probability,
        },
    }


def _task_distribution(*, sparse_distribution: str) -> dict:
    sparse_counts = (
        {"support": 50, "oppose": 0}
        if sparse_distribution == "support"
        else {"support": 0, "oppose": 50}
    )
    sparse_probabilities = (
        {"support": 1.0, "oppose": 0.0}
        if sparse_distribution == "support"
        else {"support": 0.0, "oppose": 1.0}
    )
    return {
        "task_id": "task_sparse_party_prior",
        "target_variable_id": "synthetic_policy_target",
        "segment_schema_coverage": {
            "coverage_status": "complete_for_task_card_axes",
            "missing_required_axes": [],
        },
        "overall": {
            "row_count": 81,
            "policy_counts": {"support": 41, "oppose": 40},
            "policy_probabilities": {
                "support": 41 / 81,
                "oppose": 40 / 81,
            },
        },
        "by_segment": {
            "party_or_ideology=liberal|income=lower": {
                "row_count": 50,
                "policy_counts": sparse_counts,
                "policy_probabilities": sparse_probabilities,
            },
            "party_or_ideology=liberal|income=upper": {
                "row_count": 40,
                "policy_counts": {"support": 0, "oppose": 40},
                "policy_probabilities": {"support": 0.0, "oppose": 1.0},
            },
            "party_or_ideology=conservative|income=lower": {
                "row_count": 40,
                "policy_counts": {"support": 40, "oppose": 0},
                "policy_probabilities": {"support": 1.0, "oppose": 0.0},
            },
        },
    }
