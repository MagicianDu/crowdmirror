import json

import pytest

from experiments.policy_reaction_runtime_patch_effect import (
    build_policy_reaction_runtime_patch_effect,
    write_policy_reaction_runtime_patch_effect,
)


def test_build_runtime_patch_effect_reports_heldout_improvement():
    artifact = build_policy_reaction_runtime_patch_effect(
        baseline_heldout_benchmark=_benchmark(
            artifact_id="baseline-heldout",
            prediction_artifact_id="baseline-predictions",
            weighted_jsd=0.20,
        ),
        runtime_patch_heldout_benchmark=_benchmark(
            artifact_id="runtime-patch-heldout",
            prediction_artifact_id="runtime-patch-predictions",
            weighted_jsd=0.05,
        ),
        prompt_patch_gate=_prompt_patch_gate(),
        product_workflow_report=_product_workflow_report(),
        artifact_id="runtime-patch-effect-test",
    )

    assert artifact["schema_version"] == "policy-reaction-runtime-patch-effect-v1"
    assert artifact["artifact_id"] == "runtime-patch-effect-test"
    assert artifact["overall_status"] == "improved"
    assert artifact["loss_metric"] == "weighted_choice_distribution_jsd"
    assert artifact["baseline_loss"] == 0.20
    assert artifact["runtime_patch_loss"] == 0.05
    assert artifact["absolute_loss_delta"] == 0.15
    assert artifact["relative_loss_reduction"] == 0.75
    assert artifact["baseline_prediction_artifact_id"] == "baseline-predictions"
    assert artifact["runtime_patch_prediction_artifact_id"] == (
        "runtime-patch-predictions"
    )
    assert artifact["prompt_patch_gate_artifact_id"] == "prompt-patch-gate-test"
    assert artifact["product_runtime_run_id"] == "runtime-patch-cohort-test"
    assert artifact["source_split_contract"] == {
        "candidate_generation": "calibration",
        "candidate_acceptance": "heldout",
        "runtime_effect_evaluation": "heldout",
    }
    assert (
        "Runtime-patch effect is a held-out public-data alignment comparison; not field validation."
        in artifact["claim_boundaries"]
    )
    json.dumps(artifact, allow_nan=False)


def test_build_runtime_patch_effect_marks_regression_without_overclaiming():
    artifact = build_policy_reaction_runtime_patch_effect(
        baseline_heldout_benchmark=_benchmark(
            artifact_id="baseline-heldout",
            prediction_artifact_id="baseline-predictions",
            weighted_jsd=0.10,
        ),
        runtime_patch_heldout_benchmark=_benchmark(
            artifact_id="runtime-patch-heldout",
            prediction_artifact_id="runtime-patch-predictions",
            weighted_jsd=0.12,
        ),
        prompt_patch_gate=_prompt_patch_gate(),
        product_workflow_report=_product_workflow_report(),
        artifact_id="runtime-patch-regression-test",
    )

    assert artifact["overall_status"] == "regressed"
    assert artifact["absolute_loss_delta"] == -0.02
    assert artifact["relative_loss_reduction"] == -0.2
    assert "runtime_patch_did_not_improve_heldout_alignment" in artifact["risk_flags"]


def test_build_runtime_patch_effect_rejects_non_heldout_baseline():
    baseline = _benchmark(
        artifact_id="baseline-calibration",
        prediction_artifact_id="baseline-predictions",
        weighted_jsd=0.20,
        source_ingestion_artifact_id="policy-reaction-htops-2506-calibration-ingestion",
    )

    with pytest.raises(ValueError, match="held-out"):
        build_policy_reaction_runtime_patch_effect(
            baseline_heldout_benchmark=baseline,
            runtime_patch_heldout_benchmark=_benchmark(
                artifact_id="runtime-patch-heldout",
                prediction_artifact_id="runtime-patch-predictions",
                weighted_jsd=0.05,
            ),
            prompt_patch_gate=_prompt_patch_gate(),
            product_workflow_report=_product_workflow_report(),
            artifact_id="runtime-patch-effect-test",
        )


def test_write_runtime_patch_effect(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    runtime_path = tmp_path / "runtime.json"
    gate_path = tmp_path / "gate.json"
    workflow_path = tmp_path / "workflow.json"
    output_path = tmp_path / "effect.json"
    baseline_path.write_text(json.dumps(_benchmark(weighted_jsd=0.20)))
    runtime_path.write_text(json.dumps(_benchmark(weighted_jsd=0.05)))
    gate_path.write_text(json.dumps(_prompt_patch_gate()))
    workflow_path.write_text(json.dumps(_product_workflow_report()))

    written = write_policy_reaction_runtime_patch_effect(
        output_path,
        baseline_heldout_benchmark_path=baseline_path,
        runtime_patch_heldout_benchmark_path=runtime_path,
        prompt_patch_gate_path=gate_path,
        product_workflow_report_path=workflow_path,
        artifact_id="runtime-patch-effect-test",
    )

    assert written == output_path
    persisted = json.loads(output_path.read_text())
    assert persisted["artifact_id"] == "runtime-patch-effect-test"
    assert persisted["overall_status"] == "improved"


def _benchmark(
    *,
    artifact_id: str = "heldout-benchmark",
    prediction_artifact_id: str = "segment-predictions",
    weighted_jsd: float,
    source_ingestion_artifact_id: str = (
        "policy-reaction-htops-2506-evaluation-ingestion"
    ),
) -> dict:
    return {
        "schema_version": "policy-reaction-official-segment-benchmark-v1",
        "artifact_id": artifact_id,
        "overall_status": "passed",
        "source_ingestion_artifact_id": source_ingestion_artifact_id,
        "prediction_artifact_id": prediction_artifact_id,
        "benchmark_metrics": {
            "weighted_choice_distribution_jsd": weighted_jsd,
            "mean_choice_distribution_jsd": weighted_jsd,
            "segment_rank_correlation": 1.0,
        },
        "segment_coverage": {"coverage_rate": 1.0},
        "segment_metrics": {
            "general_population_cost_pressure": {
                "choice_distribution_jsd": weighted_jsd,
            }
        },
        "claim_boundaries": ["heldout benchmark boundary"],
    }


def _prompt_patch_gate() -> dict:
    return {
        "schema_version": "policy-reaction-prompt-patch-gate-v1",
        "artifact_id": "prompt-patch-gate-test",
        "overall_status": "accepted",
        "accepted_candidate_id": "candidate-accepted-001",
        "candidate_accepted_count": 1,
        "candidate_rejected_count": 0,
        "patch_count": 2,
        "source_split_contract": {
            "candidate_generation": "calibration",
            "candidate_acceptance": "heldout",
        },
        "claim_boundaries": ["prompt patch gate boundary"],
    }


def _product_workflow_report() -> dict:
    return {
        "schema_version": "crowdmirror-policy-workflow-report-v1",
        "workflow_status": "research_gate_passed",
        "source_run_id": "runtime-patch-cohort-test",
        "evidence_chain": {
            "prompt_patch_gate": {
                "artifact_id": "prompt-patch-gate-test",
                "patch_count": 2,
                "status": "accepted",
            }
        },
        "risk_flags": ["local_llm_only"],
    }
