import json

from experiments.policy_reaction_s2pc_runtime_effect import (
    build_policy_reaction_s2pc_runtime_effect,
    build_policy_reaction_s2pc_runtime_effect_matrix,
    write_policy_reaction_s2pc_runtime_effect,
    write_policy_reaction_s2pc_runtime_effect_matrix,
)


def test_build_s2pc_runtime_effect_marks_regression_without_overclaiming():
    artifact = build_policy_reaction_s2pc_runtime_effect(
        baseline_heldout_benchmark=_heldout_benchmark(
            artifact_id="baseline-heldout",
            prediction_artifact_id="baseline-predictions",
            weighted_jsd=0.0001,
        ),
        baseline_product_manifest=_product_manifest(
            run_id="baseline-run",
            include_s2pc=False,
        ),
        s2pc_runtime_heldout_benchmark=_heldout_benchmark(
            artifact_id="s2pc-runtime-heldout",
            prediction_artifact_id="s2pc-runtime-predictions",
            weighted_jsd=0.0002,
        ),
        s2pc_product_manifest=_product_manifest(
            run_id="s2pc-runtime-run",
            include_s2pc=True,
        ),
        s2pc_candidate=_s2pc_candidate(),
        artifact_id="s2pc-runtime-effect-test",
    )

    assert artifact["schema_version"] == "policy-reaction-s2pc-runtime-effect-v1"
    assert artifact["overall_status"] == "regressed"
    assert artifact["baseline_loss"] == 0.0001
    assert artifact["s2pc_runtime_loss"] == 0.0002
    assert artifact["relative_loss_reduction"] == -1.0
    assert artifact["s2pc_candidate_id"] == "s2pc-candidate-test"
    assert artifact["source_split_contract"] == {
        "residual_mining": "calibration",
        "semantic_factor_retrieval": "calibration",
        "parameter_search": "calibration",
        "candidate_acceptance": "heldout_required",
        "runtime_effect_evaluation": "heldout",
    }
    assert "s2pc_runtime_did_not_improve_heldout_alignment" in artifact["risk_flags"]
    json.dumps(artifact, allow_nan=False)


def test_write_s2pc_runtime_effect(tmp_path):
    baseline_benchmark = tmp_path / "baseline-benchmark.json"
    baseline_manifest = tmp_path / "baseline-manifest.json"
    s2pc_benchmark = tmp_path / "s2pc-benchmark.json"
    s2pc_manifest = tmp_path / "s2pc-manifest.json"
    s2pc_candidate = tmp_path / "s2pc-candidate.json"
    output = tmp_path / "effect.json"
    baseline_benchmark.write_text(
        json.dumps(
            _heldout_benchmark(
                artifact_id="baseline-heldout",
                prediction_artifact_id="baseline-predictions",
                weighted_jsd=0.0001,
            )
        )
    )
    baseline_manifest.write_text(
        json.dumps(_product_manifest(run_id="baseline-run", include_s2pc=False))
    )
    s2pc_benchmark.write_text(
        json.dumps(
            _heldout_benchmark(
                artifact_id="s2pc-runtime-heldout",
                prediction_artifact_id="s2pc-runtime-predictions",
                weighted_jsd=0.00005,
            )
        )
    )
    s2pc_manifest.write_text(
        json.dumps(_product_manifest(run_id="s2pc-runtime-run", include_s2pc=True))
    )
    s2pc_candidate.write_text(json.dumps(_s2pc_candidate()))

    written = write_policy_reaction_s2pc_runtime_effect(
        output,
        baseline_heldout_benchmark_path=baseline_benchmark,
        baseline_product_manifest_path=baseline_manifest,
        s2pc_runtime_heldout_benchmark_path=s2pc_benchmark,
        s2pc_product_manifest_path=s2pc_manifest,
        s2pc_candidate_path=s2pc_candidate,
        artifact_id="s2pc-runtime-effect-test",
    )

    assert written == output
    persisted = json.loads(output.read_text())
    assert persisted["artifact_id"] == "s2pc-runtime-effect-test"
    assert persisted["overall_status"] == "improved"


def test_build_s2pc_runtime_effect_matrix_summarizes_candidates():
    matrix = build_policy_reaction_s2pc_runtime_effect_matrix(
        [
            _s2pc_runtime_effect(
                status="regressed",
                baseline_loss=0.0001,
                s2pc_runtime_loss=0.0002,
                candidate_id="candidate-a",
            ),
            _s2pc_runtime_effect(
                status="improved",
                baseline_loss=0.0001,
                s2pc_runtime_loss=0.00005,
                candidate_id="candidate-b",
            ),
        ],
        artifact_id="s2pc-runtime-effect-matrix-test",
    )

    assert matrix["schema_version"] == "policy-reaction-s2pc-runtime-effect-matrix-v1"
    assert matrix["overall_status"] == "candidate_improvements_available"
    assert matrix["candidate_count"] == 2
    assert matrix["improved_count"] == 1
    assert matrix["regressed_count"] == 1
    assert matrix["best_candidate_id"] == "candidate-b"
    assert matrix["best_s2pc_runtime_loss"] == 0.00005
    assert matrix["candidate_results"][0]["s2pc_candidate_id"] == "candidate-b"
    json.dumps(matrix, allow_nan=False)


def test_write_s2pc_runtime_effect_matrix(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    output = tmp_path / "matrix.json"
    first.write_text(
        json.dumps(
            _s2pc_runtime_effect(
                status="regressed",
                baseline_loss=0.0001,
                s2pc_runtime_loss=0.0002,
                candidate_id="candidate-a",
            )
        )
    )
    second.write_text(
        json.dumps(
            _s2pc_runtime_effect(
                status="improved",
                baseline_loss=0.0001,
                s2pc_runtime_loss=0.00005,
                candidate_id="candidate-b",
            )
        )
    )

    written = write_policy_reaction_s2pc_runtime_effect_matrix(
        output,
        effect_artifact_paths=[first, second],
        artifact_id="s2pc-runtime-effect-matrix-test",
    )

    assert written == output
    persisted = json.loads(output.read_text())
    assert persisted["artifact_id"] == "s2pc-runtime-effect-matrix-test"
    assert persisted["best_candidate_id"] == "candidate-b"


def _heldout_benchmark(
    *,
    artifact_id: str,
    prediction_artifact_id: str,
    weighted_jsd: float,
) -> dict:
    return {
        "schema_version": "policy-reaction-official-segment-benchmark-v1",
        "artifact_id": artifact_id,
        "overall_status": "passed",
        "source_ingestion_artifact_id": "policy-reaction-evaluation-ingestion",
        "prediction_artifact_id": prediction_artifact_id,
        "prediction_model": "openai/gpt-oss-20b",
        "benchmark_metrics": {"weighted_choice_distribution_jsd": weighted_jsd},
        "segment_coverage": {"coverage_rate": 1.0},
        "claim_boundaries": ["heldout benchmark boundary"],
    }


def _product_manifest(*, run_id: str, include_s2pc: bool) -> dict:
    manifest = {
        "schema_version": "crowdmirror-llm-cohort-gate-v1",
        "run_id": run_id,
        "status": "completed",
        "scale": {
            "domain": "policy_reaction",
            "persona_count": 12,
            "policy_count": 3,
            "strategy_count": 3,
            "scenario_count": 36,
            "seed": 11,
            "calibration_profile": "official_htops_2506_calibration_split",
        },
        "llm_accounting": {"model": "openai/gpt-oss-20b"},
        "report": {
            "scale": {
                "domain": "policy_reaction",
                "persona_count": 12,
                "policy_count": 3,
                "strategy_count": 3,
                "scenario_count": 36,
                "seed": 11,
                "calibration_profile": "official_htops_2506_calibration_split",
            }
        },
    }
    if include_s2pc:
        manifest["s2pc_context"] = {
            "s2pc_candidate": {"candidate_id": "s2pc-candidate-test"},
        }
    return manifest


def _s2pc_candidate() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-candidate-v1",
        "candidate_id": "s2pc-candidate-test",
        "generator": "s2pc_l0_deterministic_catalog_beam_search",
        "source_split_contract": {
            "residual_mining": "calibration",
            "semantic_factor_retrieval": "calibration",
            "parameter_search": "calibration",
            "candidate_acceptance": "heldout_required",
        },
        "candidate_prompt_components": {
            "calibration_anchor": {"fixed_income_inflation_stressed": "anchor"}
        },
        "claim_boundary": "s2pc boundary",
    }


def _s2pc_runtime_effect(
    *,
    status: str,
    baseline_loss: float,
    s2pc_runtime_loss: float,
    candidate_id: str,
) -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-runtime-effect-v1",
        "artifact_id": f"s2pc-runtime-effect-{candidate_id}",
        "overall_status": status,
        "loss_metric": "weighted_choice_distribution_jsd",
        "baseline_loss": baseline_loss,
        "s2pc_runtime_loss": s2pc_runtime_loss,
        "absolute_loss_delta": baseline_loss - s2pc_runtime_loss,
        "relative_loss_reduction": (
            (baseline_loss - s2pc_runtime_loss) / baseline_loss
            if baseline_loss > 0
            else None
        ),
        "s2pc_candidate_id": candidate_id,
        "s2pc_product_run_id": f"run-{candidate_id}",
        "product_runtime_model": "openai/gpt-oss-20b",
        "product_runtime_scale": {
            "domain": "policy_reaction",
            "persona_count": 12,
            "policy_count": 3,
            "strategy_count": 3,
            "scenario_count": 36,
            "seed": 11,
        },
        "source_split_contract": {
            "residual_mining": "calibration",
            "semantic_factor_retrieval": "calibration",
            "parameter_search": "calibration",
            "candidate_acceptance": "heldout_required",
            "runtime_effect_evaluation": "heldout",
        },
        "coverage": {
            "baseline_coverage_rate": 1.0,
            "s2pc_runtime_coverage_rate": 1.0,
        },
        "risk_flags": ["s2pc_runtime_effect_not_field_validation"],
        "claim_boundaries": ["s2pc effect boundary"],
    }
