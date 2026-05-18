import json

import pytest

from experiments.policy_reaction_runtime_patch_stability import (
    build_policy_reaction_runtime_patch_stability_matrix,
    write_policy_reaction_runtime_patch_stability_matrix,
)


def test_build_runtime_patch_stability_matrix_summarizes_repeats():
    matrix = build_policy_reaction_runtime_patch_stability_matrix(
        [_effect("run-a", seed=11, persona_count=12, runtime_loss=0.004), _effect("run-b", seed=17, persona_count=12, runtime_loss=0.006)],
        artifact_id="runtime-patch-stability-test",
    )

    assert matrix["schema_version"] == "policy-reaction-runtime-patch-stability-v1"
    assert matrix["artifact_id"] == "runtime-patch-stability-test"
    assert matrix["overall_status"] == "stable_improvement"
    assert matrix["effect_count"] == 2
    assert matrix["improved_count"] == 2
    assert matrix["regressed_count"] == 0
    assert matrix["model_ids"] == ["openai/gpt-oss-20b"]
    assert matrix["scale_axes"] == {
        "persona_counts": [12],
        "scenario_counts": [36],
        "seeds": [11, 17],
    }
    assert matrix["loss_summary"] == {
        "baseline_loss_mean": 0.188,
        "runtime_patch_loss_mean": 0.005,
        "absolute_loss_delta_mean": 0.183,
        "relative_loss_reduction_mean": 0.973404255319,
        "relative_loss_reduction_min": 0.968085106383,
        "relative_loss_reduction_max": 0.978723404255,
    }
    assert [run["product_runtime_run_id"] for run in matrix["runs"]] == [
        "run-a",
        "run-b",
    ]
    assert (
        "Runtime-patch stability matrix is repeat evidence over local held-out public-data alignment, not field validation."
        in matrix["claim_boundaries"]
    )
    json.dumps(matrix, allow_nan=False)


def test_build_runtime_patch_stability_matrix_marks_mixed_results():
    matrix = build_policy_reaction_runtime_patch_stability_matrix(
        [
            _effect("run-a", seed=11, persona_count=12, runtime_loss=0.004),
            _effect("run-b", seed=17, persona_count=12, runtime_loss=0.20),
        ],
        artifact_id="runtime-patch-stability-mixed-test",
    )

    assert matrix["overall_status"] == "mixed"
    assert matrix["improved_count"] == 1
    assert matrix["regressed_count"] == 1
    assert "runtime_patch_not_stable_across_repeats" in matrix["risk_flags"]


def test_build_runtime_patch_stability_matrix_rejects_non_effect_artifact():
    effect = _effect("run-a", seed=11, persona_count=12, runtime_loss=0.004)
    effect["schema_version"] = "wrong"

    with pytest.raises(ValueError, match="schema_version"):
        build_policy_reaction_runtime_patch_stability_matrix(
            [effect],
            artifact_id="runtime-patch-stability-test",
        )


def test_write_runtime_patch_stability_matrix(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    output = tmp_path / "matrix.json"
    first.write_text(json.dumps(_effect("run-a", seed=11, persona_count=12, runtime_loss=0.004)))
    second.write_text(json.dumps(_effect("run-b", seed=17, persona_count=12, runtime_loss=0.006)))

    written = write_policy_reaction_runtime_patch_stability_matrix(
        output,
        effect_artifact_paths=[first, second],
        artifact_id="runtime-patch-stability-test",
    )

    assert written == output
    persisted = json.loads(output.read_text())
    assert persisted["artifact_id"] == "runtime-patch-stability-test"
    assert persisted["overall_status"] == "stable_improvement"


def _effect(
    run_id: str,
    *,
    seed: int,
    persona_count: int,
    runtime_loss: float,
) -> dict:
    baseline_loss = 0.188
    absolute_delta = baseline_loss - runtime_loss
    scenario_count = persona_count * 3
    return {
        "schema_version": "policy-reaction-runtime-patch-effect-v1",
        "artifact_id": f"effect-{run_id}",
        "overall_status": "improved" if absolute_delta > 0 else "regressed",
        "loss_metric": "weighted_choice_distribution_jsd",
        "baseline_loss": baseline_loss,
        "runtime_patch_loss": runtime_loss,
        "absolute_loss_delta": absolute_delta,
        "relative_loss_reduction": absolute_delta / baseline_loss,
        "prompt_patch_gate_artifact_id": "prompt-patch-gate-test",
        "product_runtime_run_id": run_id,
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
            "runtime_patch_coverage_rate": 1.0,
        },
        "source_split_contract": {
            "candidate_generation": "calibration",
            "candidate_acceptance": "heldout",
            "runtime_effect_evaluation": "heldout",
        },
        "risk_flags": ["runtime_patch_effect_not_field_validation"],
        "claim_boundaries": ["effect boundary"],
    }
