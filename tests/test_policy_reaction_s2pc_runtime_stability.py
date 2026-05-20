import json

import pytest

from experiments.policy_reaction_s2pc_runtime_stability import (
    build_policy_reaction_s2pc_runtime_stability_matrix,
    write_policy_reaction_s2pc_runtime_stability_matrix,
)


def test_build_s2pc_runtime_stability_matrix_summarizes_repeats():
    matrix = build_policy_reaction_s2pc_runtime_stability_matrix(
        [
            _effect("run-a", seed=11, persona_count=12, runtime_loss=0.0001115),
            _effect("run-b", seed=17, persona_count=12, runtime_loss=0.0001120),
            _effect("run-c", seed=11, persona_count=16, runtime_loss=0.0001122),
        ],
        artifact_id="s2pc-runtime-stability-test",
    )

    assert matrix["schema_version"] == "policy-reaction-s2pc-runtime-stability-v1"
    assert matrix["artifact_id"] == "s2pc-runtime-stability-test"
    assert matrix["overall_status"] == "stable_improvement"
    assert matrix["effect_count"] == 3
    assert matrix["improved_count"] == 3
    assert matrix["regressed_count"] == 0
    assert matrix["candidate_ids"] == ["policy-reaction-s2pc-l1-candidate-set-current-001-c01"]
    assert matrix["scale_axes"] == {
        "persona_counts": [12, 16],
        "scenario_counts": [36, 48],
        "seeds": [11, 17],
    }
    assert matrix["best_candidate_id"] == "policy-reaction-s2pc-l1-candidate-set-current-001-c01"
    assert [run["product_runtime_run_id"] for run in matrix["runs"]] == [
        "run-a",
        "run-b",
        "run-c",
    ]
    json.dumps(matrix, allow_nan=False)


def test_build_s2pc_runtime_stability_matrix_marks_mixed_results():
    matrix = build_policy_reaction_s2pc_runtime_stability_matrix(
        [
            _effect("run-a", seed=11, persona_count=12, runtime_loss=0.0001115),
            _effect("run-b", seed=17, persona_count=12, runtime_loss=0.0003000),
        ],
        artifact_id="s2pc-runtime-stability-mixed-test",
    )

    assert matrix["overall_status"] == "mixed"
    assert matrix["improved_count"] == 1
    assert matrix["regressed_count"] == 1
    assert "s2pc_runtime_candidate_not_stable_across_repeats" in matrix["risk_flags"]


def test_build_s2pc_runtime_stability_matrix_rejects_mismatched_candidate_ids():
    with pytest.raises(ValueError, match="same candidate_id"):
        build_policy_reaction_s2pc_runtime_stability_matrix(
            [
                _effect("run-a", seed=11, persona_count=12, runtime_loss=0.0001115),
                _effect(
                    "run-b",
                    seed=17,
                    persona_count=12,
                    runtime_loss=0.0001120,
                    candidate_id="policy-reaction-s2pc-l1-candidate-set-current-001-c02",
                ),
            ],
            artifact_id="s2pc-runtime-stability-test",
        )


def test_write_s2pc_runtime_stability_matrix(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    output = tmp_path / "matrix.json"
    first.write_text(json.dumps(_effect("run-a", seed=11, persona_count=12, runtime_loss=0.0001115)))
    second.write_text(json.dumps(_effect("run-b", seed=17, persona_count=12, runtime_loss=0.0001120)))

    written = write_policy_reaction_s2pc_runtime_stability_matrix(
        output,
        effect_artifact_paths=[first, second],
        artifact_id="s2pc-runtime-stability-test",
    )

    assert written == output
    persisted = json.loads(output.read_text())
    assert persisted["artifact_id"] == "s2pc-runtime-stability-test"
    assert persisted["overall_status"] == "stable_improvement"


def _effect(
    run_id: str,
    *,
    seed: int,
    persona_count: int,
    runtime_loss: float,
    candidate_id: str = "policy-reaction-s2pc-l1-candidate-set-current-001-c01",
) -> dict:
    baseline_loss = 0.000112890954
    absolute_delta = baseline_loss - runtime_loss
    scenario_count = persona_count * 3
    return {
        "schema_version": "policy-reaction-s2pc-runtime-effect-v1",
        "artifact_id": f"effect-{run_id}",
        "overall_status": (
            "improved" if absolute_delta > 0 else "regressed" if absolute_delta < 0 else "no_change"
        ),
        "loss_metric": "weighted_choice_distribution_jsd",
        "baseline_loss": baseline_loss,
        "s2pc_runtime_loss": runtime_loss,
        "absolute_loss_delta": absolute_delta,
        "relative_loss_reduction": absolute_delta / baseline_loss,
        "s2pc_candidate_id": candidate_id,
        "s2pc_product_run_id": run_id,
        "product_runtime_model": "openai/gpt-oss-20b",
        "product_runtime_scale": {
            "domain": "policy_reaction",
            "persona_count": persona_count,
            "policy_count": 3,
            "strategy_count": 3,
            "scenario_count": scenario_count,
            "seed": seed,
        },
        "coverage": {
            "baseline_coverage_rate": 1.0,
            "s2pc_runtime_coverage_rate": 1.0,
        },
        "source_split_contract": {
            "residual_mining": "calibration",
            "semantic_factor_retrieval": "calibration",
            "parameter_search": "calibration",
            "candidate_acceptance": "heldout_required",
            "runtime_effect_evaluation": "heldout",
        },
        "risk_flags": ["s2pc_runtime_effect_not_field_validation"],
        "claim_boundaries": ["effect boundary"],
    }
