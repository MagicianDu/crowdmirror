import json

import pytest

from experiments.policy_reaction_update_method_gate import (
    build_heldout_benchmark_method_record,
    build_policy_reaction_update_method_gate,
    build_runtime_stability_method_record,
    build_s2pc_gate_method_record,
    build_s2pc_runtime_effect_matrix_method_record,
    build_s2pc_runtime_effect_method_record,
    build_textgrad_manifest_method_record,
    write_policy_reaction_update_method_gate,
)


def test_update_method_gate_accepts_and_rejects_matched_heldout_candidates():
    accepted = build_heldout_benchmark_method_record(
        method_id="deepseek_flash_calibration_split",
        generator="calibration_split_prompting",
        baseline_benchmark=_heldout_benchmark(
            "baseline-heldout",
            loss=0.159,
            model="deepseek-v4-flash",
        ),
        candidate_benchmark=_heldout_benchmark(
            "candidate-heldout",
            loss=0.011,
            model="deepseek-v4-flash",
        ),
    )
    rejected = build_heldout_benchmark_method_record(
        method_id="regressed_prompt_patch",
        generator="structured_persona_parameter_patch",
        baseline_benchmark=_heldout_benchmark("patch-baseline", loss=0.100),
        candidate_benchmark=_heldout_benchmark("patch-candidate", loss=0.120),
    )

    gate = build_policy_reaction_update_method_gate(
        [accepted, rejected],
        artifact_id="update-method-gate-test",
    )

    assert gate["schema_version"] == "policy-reaction-update-method-gate-v1"
    assert gate["overall_status"] == "accepted_methods_available"
    assert gate["candidate_update_policy"] == (
        "accept_matched_heldout_loss_improvement_with_complete_segment_coverage_"
        "else_reject_or_mark_diagnostic"
    )
    assert gate["candidate_update_count"] == 2
    assert gate["candidate_accepted_count"] == 1
    assert gate["candidate_rejected_count"] == 1
    assert gate["diagnostic_only_count"] == 0
    assert gate["accepted_method_ids"] == ["deepseek_flash_calibration_split"]
    assert gate["best_method_id"] == "deepseek_flash_calibration_split"
    assert gate["initial_loss"] == 0.159
    assert gate["best_loss"] == 0.011
    assert gate["final_loss"] == 0.011
    assert gate["method_updates"][0]["status"] == "accepted"
    assert gate["method_updates"][1]["status"] == "rejected"
    assert gate["generator_summaries"]["calibration_split_prompting"] == {
        "record_count": 1,
        "heldout_candidate_count": 1,
        "accepted_count": 1,
        "rejected_count": 0,
        "diagnostic_only_count": 0,
        "best_method_id": "deepseek_flash_calibration_split",
        "best_loss": 0.011,
    }
    assert gate["generator_summaries"]["structured_persona_parameter_patch"] == {
        "record_count": 1,
        "heldout_candidate_count": 1,
        "accepted_count": 0,
        "rejected_count": 1,
        "diagnostic_only_count": 0,
        "best_method_id": None,
        "best_loss": None,
    }
    json.dumps(gate, allow_nan=False)


def test_update_method_gate_marks_textgrad_without_policy_heldout_as_diagnostic():
    record = build_textgrad_manifest_method_record(
        method_id="deepseek_v4_pro_textgrad",
        generator="deepseek_v4_pro_textgrad_candidate_update",
        manifest=_textgrad_manifest(),
    )

    gate = build_policy_reaction_update_method_gate(
        [record],
        artifact_id="update-method-textgrad-diagnostic-test",
    )

    assert gate["overall_status"] == "diagnostic_only"
    assert gate["candidate_update_count"] == 0
    assert gate["candidate_accepted_count"] == 0
    assert gate["candidate_rejected_count"] == 0
    assert gate["diagnostic_only_count"] == 1
    assert gate["method_updates"][0]["status"] == "diagnostic_only"
    assert gate["method_updates"][0]["reason"] == "missing_policy_reaction_heldout_evaluation"
    assert gate["method_updates"][0]["initial_loss"] == 0.3003150770148567
    assert gate["method_updates"][0]["best_loss"] == 0.3003150770148567
    assert gate["method_updates"][0]["final_loss"] == 0.4522002190868819
    assert gate["generator_summaries"]["deepseek_v4_pro_textgrad_candidate_update"][
        "diagnostic_only_count"
    ] == 1
    assert "policy_reaction_heldout_evidence_missing" in gate["risk_flags"]


def test_runtime_stability_method_record_rejects_stable_regression():
    record = build_runtime_stability_method_record(
        method_id="runtime_prompt_patch",
        generator="structured_persona_parameter_patch",
        stability_matrix=_runtime_stability_matrix(),
    )

    assert record["status"] == "rejected"
    assert record["reason"] == "runtime_patch_stability_not_improved"
    assert record["initial_loss"] == 0.000111404795
    assert record["candidate_loss"] == 0.005108707956
    assert record["relative_loss_reduction"] == -45.052587741358


def test_s2pc_gate_method_record_can_be_accepted():
    record = build_s2pc_gate_method_record(
        method_id="s2pc_l0_deepseek_flash_candidate",
        s2pc_gate=_s2pc_gate(
            status="accepted",
            initial_loss=0.159,
            candidate_loss=0.009,
        ),
    )

    assert record["method_id"] == "s2pc_l0_deepseek_flash_candidate"
    assert record["generator"] == "s2pc_l0_deterministic_catalog_beam_search"
    assert record["status"] == "accepted"
    assert record["reason"] == "s2pc_heldout_loss_improved"
    assert record["initial_loss"] == 0.159
    assert record["candidate_loss"] == 0.009
    assert record["source_split_contract"]["candidate_acceptance"] == "heldout"


def test_s2pc_runtime_effect_method_record_rejects_regression():
    record = build_s2pc_runtime_effect_method_record(
        method_id="s2pc_l0_runtime_probe",
        s2pc_runtime_effect=_s2pc_runtime_effect(
            status="regressed",
            baseline_loss=0.000112890954,
            s2pc_runtime_loss=0.000211185317,
        ),
    )

    assert record["method_id"] == "s2pc_l0_runtime_probe"
    assert record["generator"] == "s2pc_l0_deterministic_catalog_beam_search_runtime"
    assert record["status"] == "rejected"
    assert record["reason"] == "s2pc_runtime_loss_not_improved"
    assert record["initial_loss"] == 0.000112890954
    assert record["candidate_loss"] == 0.000211185317
    assert record["final_loss"] == 0.000112890954
    assert record["source_split_contract"]["runtime_effect_evaluation"] == "heldout"


def test_s2pc_runtime_effect_matrix_method_record_accepts_best_improvement():
    record = build_s2pc_runtime_effect_matrix_method_record(
        method_id="s2pc_l1_runtime_matrix",
        s2pc_runtime_effect_matrix=_s2pc_runtime_effect_matrix(),
    )

    assert record["method_id"] == "s2pc_l1_runtime_matrix"
    assert record["generator"] == "s2pc_l1_multi_candidate_runtime_search_runtime"
    assert record["status"] == "accepted"
    assert record["reason"] == "s2pc_runtime_matrix_best_candidate_improved"
    assert record["initial_loss"] == 0.000112890954
    assert record["candidate_loss"] == 0.000111545213
    assert record["candidate_count"] == 6
    assert record["improved_count"] == 1
    assert record["regressed_count"] == 5
    assert record["candidate_id"] == "policy-reaction-s2pc-l1-candidate-set-current-001-c01"


def test_heldout_method_record_requires_same_heldout_target():
    baseline = _heldout_benchmark(
        "baseline-heldout",
        loss=0.159,
        source_ingestion_artifact_id="policy-reaction-evaluation-a",
    )
    candidate = _heldout_benchmark(
        "candidate-heldout",
        loss=0.011,
        source_ingestion_artifact_id="policy-reaction-evaluation-b",
    )

    with pytest.raises(ValueError, match="same held-out target"):
        build_heldout_benchmark_method_record(
            method_id="bad-target",
            generator="calibration_split_prompting",
            baseline_benchmark=baseline,
            candidate_benchmark=candidate,
        )


def test_write_policy_reaction_update_method_gate(tmp_path):
    output = tmp_path / "gate.json"

    written = write_policy_reaction_update_method_gate(
        output,
        method_records=[
            build_heldout_benchmark_method_record(
                method_id="deepseek_flash_calibration_split",
                generator="calibration_split_prompting",
                baseline_benchmark=_heldout_benchmark(
                    "baseline-heldout",
                    loss=0.159,
                    model="deepseek-v4-flash",
                ),
                candidate_benchmark=_heldout_benchmark(
                    "candidate-heldout",
                    loss=0.011,
                    model="deepseek-v4-flash",
                ),
            )
        ],
        artifact_id="update-method-gate-test",
    )

    assert written == output
    persisted = json.loads(output.read_text())
    assert persisted["artifact_id"] == "update-method-gate-test"
    assert persisted["overall_status"] == "accepted_methods_available"


def _heldout_benchmark(
    artifact_id: str,
    *,
    loss: float,
    model: str = "openai/gpt-oss-20b",
    source_ingestion_artifact_id: str = "policy-reaction-htops-evaluation-ingestion",
) -> dict:
    return {
        "schema_version": "policy-reaction-official-segment-benchmark-v1",
        "artifact_id": artifact_id,
        "source_ingestion_artifact_id": source_ingestion_artifact_id,
        "prediction_artifact_id": f"{artifact_id}-predictions",
        "prediction_model": model,
        "overall_status": "passed",
        "benchmark_metrics": {
            "weighted_choice_distribution_jsd": loss,
            "segment_rank_correlation": 0.75,
        },
        "segment_coverage": {
            "coverage_rate": 1.0,
            "matched_segment_count": 4,
        },
        "segment_metrics": {},
    }


def _runtime_stability_matrix() -> dict:
    return {
        "schema_version": "policy-reaction-runtime-patch-stability-v1",
        "artifact_id": "runtime-patch-stability-test",
        "overall_status": "stable_regression",
        "effect_count": 3,
        "improved_count": 0,
        "regressed_count": 3,
        "loss_metric": "weighted_choice_distribution_jsd",
        "model_ids": ["openai/gpt-oss-20b"],
        "scale_axes": {
            "persona_counts": [12, 16],
            "scenario_counts": [36, 48],
            "seeds": [11, 17],
        },
        "loss_summary": {
            "baseline_loss_mean": 0.000111404795,
            "runtime_patch_loss_mean": 0.005108707956,
            "relative_loss_reduction_mean": -45.052587741358,
        },
        "claim_boundaries": ["runtime patch stability boundary"],
    }


def _textgrad_manifest() -> dict:
    return {
        "schema_version": "circe-evidence-v1",
        "run_id": "w3w4-deepseek-v4-pro-eval2-seed42-structured-smoke-001",
        "lane": "causal",
        "mode": "local",
        "config": {
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-v4-pro",
            "dataset_seed": 42,
            "eval_size": 2,
            "prompt_baseline": "structured",
        },
        "metrics": {
            "initial_loss": 0.3003150770148567,
            "best_loss": 0.3003150770148567,
            "final_loss": 0.4522002190868819,
            "candidate_update_count": 1,
            "candidate_evaluated_count": 1,
            "candidate_accepted_count": 0,
            "candidate_rejected_count": 1,
            "candidate_pending_count": 0,
            "candidate_acceptance_rate": 0.0,
            "candidate_update_policy": "accept_if_loss_improves_else_revert",
            "textgrad_effect_status": "rejected_no_improvement",
            "textgrad_output_budget_saturated": False,
        },
        "claim_boundary": "local-model calibration evidence; not cross-provider evidence",
    }


def _s2pc_gate(*, status: str, initial_loss: float, candidate_loss: float) -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-gate-v1",
        "artifact_id": "policy-reaction-s2pc-gate-test",
        "overall_status": status,
        "candidate_id": "policy-reaction-s2pc-candidate-test",
        "generator": "s2pc_l0_deterministic_catalog_beam_search",
        "loss_metric": "weighted_choice_distribution_jsd",
        "initial_loss": initial_loss,
        "candidate_loss": candidate_loss,
        "best_loss": min(initial_loss, candidate_loss),
        "final_loss": candidate_loss if status == "accepted" else initial_loss,
        "candidate_accepted_count": 1 if status == "accepted" else 0,
        "candidate_rejected_count": 0 if status == "accepted" else 1,
        "candidate_pending_count": 0,
        "coverage_rate": 1.0,
        "source_split_contract": {
            "residual_mining": "calibration",
            "semantic_factor_retrieval": "calibration",
            "parameter_search": "calibration",
            "candidate_acceptance": "heldout",
        },
        "claim_boundaries": ["s2pc boundary"],
    }


def _s2pc_runtime_effect(
    *,
    status: str,
    baseline_loss: float,
    s2pc_runtime_loss: float,
) -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-runtime-effect-v1",
        "artifact_id": "s2pc-runtime-effect-test",
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
        "s2pc_candidate_id": "s2pc-candidate-test",
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
    }


def _s2pc_runtime_effect_matrix() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-runtime-effect-matrix-v1",
        "artifact_id": (
            "policy-reaction-s2pc-runtime-effect-matrix-gpt-oss-20b-12x3-"
            "calibration-split-l1-heldout-001"
        ),
        "overall_status": "candidate_improvements_available",
        "loss_metric": "weighted_choice_distribution_jsd",
        "candidate_count": 6,
        "improved_count": 1,
        "regressed_count": 5,
        "no_change_count": 0,
        "best_candidate_id": "policy-reaction-s2pc-l1-candidate-set-current-001-c01",
        "best_s2pc_runtime_loss": 0.000111545213,
        "candidate_results": [
            {
                "artifact_id": (
                    "policy-reaction-s2pc-runtime-effect-gpt-oss-20b-12x3-"
                    "calibration-split-l1-c01-heldout-001"
                ),
                "overall_status": "improved",
                "s2pc_candidate_id": (
                    "policy-reaction-s2pc-l1-candidate-set-current-001-c01"
                ),
                "s2pc_product_run_id": (
                    "llm-cohort-policy-local-gpt-oss-20b-12x3-calibration-split-"
                    "s2pc-l1-c01-001"
                ),
                "baseline_loss": 0.000112890954,
                "s2pc_runtime_loss": 0.000111545213,
                "absolute_loss_delta": 0.000001345741,
                "relative_loss_reduction": 0.011920716018,
            },
            {
                "artifact_id": (
                    "policy-reaction-s2pc-runtime-effect-gpt-oss-20b-12x3-"
                    "calibration-split-l1-c04-heldout-001"
                ),
                "overall_status": "regressed",
                "s2pc_candidate_id": (
                    "policy-reaction-s2pc-l1-candidate-set-current-001-c04"
                ),
                "s2pc_product_run_id": (
                    "llm-cohort-policy-local-gpt-oss-20b-12x3-calibration-split-"
                    "s2pc-l1-c04-001"
                ),
                "baseline_loss": 0.000112890954,
                "s2pc_runtime_loss": 0.000904895192,
                "absolute_loss_delta": -0.000792004238,
                "relative_loss_reduction": -7.015657252421,
            },
        ],
        "claim_boundaries": ["s2pc l1 matrix boundary"],
    }
