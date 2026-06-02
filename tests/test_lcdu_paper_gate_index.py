import json
import subprocess
import sys

import pytest

from experiments.lcdu_paper_gate_index import build_lcdu_paper_gate_index


def test_build_lcdu_paper_gate_index_keeps_ccf_a_gate_open_with_blockers():
    index = build_lcdu_paper_gate_index(
        artifact_id="lcdu-paper-gate-index-test",
        method_summary=_method_summary(),
        plan_ref="docs/superpowers/plans/2026-05-23-lcdu-ccf-a-research-plan.md",
        theory_ref="paper/LCDU_THEORY.md",
        algorithm_ref="paper/LCDU_ALGORITHM.md",
        claim_boundary_ref="paper/LCDU_CLAIM_BOUNDARY.md",
        data_audit_ref="paper/LCDU_PUBLIC_DATA_AUDIT.md",
        baseline_spec_ref="paper/LCDU_BASELINE_SPEC.md",
    )

    assert index["schema_version"] == "lcdu-paper-gate-index-v1"
    assert index["overall_status"] == "research_plan_ready_but_ccf_a_gate_open"
    assert index["method"]["method_id"] == "LCDU-L3"
    assert index["method"]["best_runtime_loss"] == 0.000092334757
    assert index["ccf_a_gate"] == {
        "status": "open",
        "blocking_gap_count": 3,
        "blocking_gaps": [
            "ccf_a_external_validity_missing",
            "cross_provider_generalization_missing",
            "theoretical_identification_needs_formalization",
        ],
    }
    assert "paper/LCDU_BASELINE_SPEC.md" in index["evidence_package_refs"]
    assert "paper/LCDU_ALGORITHM.md" in index["evidence_package_refs"]
    assert "paper/LCDU_CLAIM_BOUNDARY.md" in index["evidence_package_refs"]
    assert "run_strong_baseline_matrix" in index["required_next_gates"]
    json.dumps(index, allow_nan=False)


def test_build_lcdu_paper_gate_index_rejects_method_without_ccf_a_gaps():
    method_summary = _method_summary()
    method_summary["ccf_a_gaps"] = []

    with pytest.raises(ValueError, match="ccf_a_gaps"):
        build_lcdu_paper_gate_index(
            artifact_id="lcdu-paper-gate-index-test",
            method_summary=method_summary,
            plan_ref="docs/superpowers/plans/2026-05-23-lcdu-ccf-a-research-plan.md",
            theory_ref="paper/LCDU_THEORY.md",
            algorithm_ref="paper/LCDU_ALGORITHM.md",
            claim_boundary_ref="paper/LCDU_CLAIM_BOUNDARY.md",
            data_audit_ref="paper/LCDU_PUBLIC_DATA_AUDIT.md",
            baseline_spec_ref="paper/LCDU_BASELINE_SPEC.md",
        )


def test_build_lcdu_paper_gate_index_tracks_closed_subgates():
    index = build_lcdu_paper_gate_index(
        artifact_id="lcdu-paper-gate-index-test",
        method_summary=_method_summary(),
        plan_ref="docs/superpowers/plans/2026-05-23-lcdu-ccf-a-research-plan.md",
        theory_ref="paper/LCDU_THEORY.md",
        algorithm_ref="paper/LCDU_ALGORITHM.md",
        claim_boundary_ref="paper/LCDU_CLAIM_BOUNDARY.md",
        data_audit_ref="paper/LCDU_PUBLIC_DATA_AUDIT.md",
        baseline_spec_ref="paper/LCDU_BASELINE_SPEC.md",
        theory_contract=_theory_contract(),
        public_task_card_index=_public_task_card_index(),
        public_task_ingestion_smoke_index=_public_task_ingestion_smoke_index(),
        public_task_microdata_ingestion=_public_task_microdata_ingestion(),
        cross_task_validation=_cross_task_validation(),
        llm_simulator_validation=_llm_simulator_validation(),
        llm_seed_scale_repeat_matrix=_llm_seed_scale_repeat_matrix(),
        llm_instability_diagnosis=_llm_instability_diagnosis(),
    )

    assert index["completed_subgates"] == [
        "complete_lcdu_theory_contract",
        "public_task_cards_ready",
        "public_task_ingestion_smoke_ready",
        "public_task_microdata_sample_slice_ready",
        "cross_task_anchor_validation_ready",
        "cross_task_llm_simulator_validation_ready",
        "cross_task_llm_seed_scale_repeat_matrix_ready",
        "cross_task_llm_seed_scale_repeat_signal_not_positive",
        "cross_task_llm_instability_diagnosis_ready",
        "cross_task_llm_instability_recovered_by_prompt_variant",
    ]
    assert "lcdu-theory-contract-current-001" in index["evidence_package_refs"]
    assert "lcdu-public-task-card-index-current-001" in index["evidence_package_refs"]
    assert (
        "lcdu-public-task-ingestion-smoke-index-current-001"
        in index["evidence_package_refs"]
    )
    assert "lcdu-anes-2024-sda-public-microdata-001" in index[
        "evidence_package_refs"
    ]
    assert "lcdu-anes-cross-task-validation-current-001" in index[
        "evidence_package_refs"
    ]
    assert "lcdu-anes-llm-simulator-validation-deepseek-v4-flash-2seg-current-001" in (
        index["evidence_package_refs"]
    )
    assert (
        "lcdu-anes-llm-seed-scale-repeat-deepseek-v4-flash-s2s4-o0o1-standard-001"
        in index["evidence_package_refs"]
    )
    assert "lcdu-anes-llm-instability-diagnosis-current-001" in (
        index["evidence_package_refs"]
    )
    assert "complete_lcdu_theory_contract" not in index["required_next_gates"]
    assert index["required_next_gates"][0] == "formalize_theoretical_identification_proof"
    assert "load_public_use_microdata_or_verified_sample_slice" not in (
        index["required_next_gates"]
    )
    assert "run_cross_task_public_data_validation" not in index["required_next_gates"]
    assert "run_cross_task_llm_simulator_validation" not in index["required_next_gates"]
    assert "run_cross_task_llm_seed_scale_repeat_validation" not in (
        index["required_next_gates"]
    )
    assert "diagnose_cross_task_llm_seed_scale_repeat_instability" not in (
        index["required_next_gates"]
    )
    assert "run_prompt_variant_seed_scale_repeat_matrix" in (
        index["required_next_gates"]
    )


def test_build_lcdu_paper_gate_index_closes_prompt_variant_repeat_gate():
    index = build_lcdu_paper_gate_index(
        artifact_id="lcdu-paper-gate-index-test",
        method_summary=_method_summary(),
        plan_ref="docs/superpowers/plans/2026-05-23-lcdu-ccf-a-research-plan.md",
        theory_ref="paper/LCDU_THEORY.md",
        algorithm_ref="paper/LCDU_ALGORITHM.md",
        claim_boundary_ref="paper/LCDU_CLAIM_BOUNDARY.md",
        data_audit_ref="paper/LCDU_PUBLIC_DATA_AUDIT.md",
        baseline_spec_ref="paper/LCDU_BASELINE_SPEC.md",
        theory_contract=_theory_contract(),
        public_task_card_index=_public_task_card_index(),
        public_task_ingestion_smoke_index=_public_task_ingestion_smoke_index(),
        public_task_microdata_ingestion=_public_task_microdata_ingestion(),
        cross_task_validation=_cross_task_validation(),
        llm_simulator_validation=_llm_simulator_validation(),
        llm_seed_scale_repeat_matrix=_llm_seed_scale_repeat_matrix(),
        llm_instability_diagnosis=_llm_instability_diagnosis(),
        llm_prompt_variant_repeat_matrix=_llm_prompt_variant_repeat_matrix(),
    )

    assert "cross_task_llm_prompt_variant_seed_scale_repeat_matrix_ready" in (
        index["completed_subgates"]
    )
    assert "cross_task_llm_prompt_variant_seed_scale_repeat_signal_positive" in (
        index["completed_subgates"]
    )
    assert (
        "lcdu-anes-llm-seed-scale-repeat-deepseek-v4-flash-s2s4-o0o1-promptvariants-001"
        in index["evidence_package_refs"]
    )
    assert "run_prompt_variant_seed_scale_repeat_matrix" not in (
        index["required_next_gates"]
    )
    assert "run_cross_provider_stability_matrix" in index["required_next_gates"]


def test_build_lcdu_paper_gate_index_closes_cross_provider_gate():
    index = build_lcdu_paper_gate_index(
        artifact_id="lcdu-paper-gate-index-test",
        method_summary=_method_summary(),
        plan_ref="docs/superpowers/plans/2026-05-23-lcdu-ccf-a-research-plan.md",
        theory_ref="paper/LCDU_THEORY.md",
        algorithm_ref="paper/LCDU_ALGORITHM.md",
        claim_boundary_ref="paper/LCDU_CLAIM_BOUNDARY.md",
        data_audit_ref="paper/LCDU_PUBLIC_DATA_AUDIT.md",
        baseline_spec_ref="paper/LCDU_BASELINE_SPEC.md",
        theory_contract=_theory_contract(),
        public_task_card_index=_public_task_card_index(),
        public_task_ingestion_smoke_index=_public_task_ingestion_smoke_index(),
        public_task_microdata_ingestion=_public_task_microdata_ingestion(),
        cross_task_validation=_cross_task_validation(),
        llm_simulator_validation=_llm_simulator_validation(),
        llm_seed_scale_repeat_matrix=_llm_seed_scale_repeat_matrix(),
        llm_instability_diagnosis=_llm_instability_diagnosis(),
        llm_prompt_variant_repeat_matrix=_llm_prompt_variant_repeat_matrix(),
        llm_cross_provider_matrix=_llm_cross_provider_matrix(),
    )

    assert "cross_provider_stability_matrix_ready" in index["completed_subgates"]
    assert "cross_provider_stability_signal_positive" in index["completed_subgates"]
    assert "lcdu-anes-llm-cross-provider-matrix-current-001" in (
        index["evidence_package_refs"]
    )
    assert "run_cross_provider_stability_matrix" not in index["required_next_gates"]
    assert "run_strong_baseline_matrix" in index["required_next_gates"]


def test_build_lcdu_paper_gate_index_closes_scale_stability_gate():
    method_summary = _method_summary()
    method_summary["ccf_a_gaps"].append("full_population_scale_validation_missing")
    index = build_lcdu_paper_gate_index(
        artifact_id="lcdu-paper-gate-index-test",
        method_summary=method_summary,
        plan_ref="docs/superpowers/plans/2026-05-23-lcdu-ccf-a-research-plan.md",
        theory_ref="paper/LCDU_THEORY.md",
        algorithm_ref="paper/LCDU_ALGORITHM.md",
        claim_boundary_ref="paper/LCDU_CLAIM_BOUNDARY.md",
        data_audit_ref="paper/LCDU_PUBLIC_DATA_AUDIT.md",
        baseline_spec_ref="paper/LCDU_BASELINE_SPEC.md",
        theory_contract=_theory_contract(),
        public_task_card_index=_public_task_card_index(),
        public_task_ingestion_smoke_index=_public_task_ingestion_smoke_index(),
        public_task_microdata_ingestion=_public_task_microdata_ingestion(),
        cross_task_validation=_cross_task_validation(),
        llm_simulator_validation=_llm_simulator_validation(),
        llm_seed_scale_repeat_matrix=_llm_seed_scale_repeat_matrix(),
        llm_instability_diagnosis=_llm_instability_diagnosis(),
        llm_prompt_variant_repeat_matrix=_llm_prompt_variant_repeat_matrix(),
        llm_cross_provider_matrix=_llm_cross_provider_matrix(),
        llm_scale_stability_matrix=_llm_scale_stability_matrix(),
    )

    assert "scale_stability_matrix_ready" in index["completed_subgates"]
    assert "scale_stability_signal_positive" in index["completed_subgates"]
    assert "lcdu-anes-llm-scale-stability-matrix-current-001" in (
        index["evidence_package_refs"]
    )
    assert "run_scale_stability_matrix" not in index["required_next_gates"]
    assert "run_strong_baseline_matrix" in index["required_next_gates"]


def test_build_lcdu_paper_gate_index_closes_finer_schema_gate():
    method_summary = _method_summary()
    method_summary["ccf_a_gaps"].append("finer_schema_robustness_open")
    index = build_lcdu_paper_gate_index(
        artifact_id="lcdu-paper-gate-index-test",
        method_summary=method_summary,
        plan_ref="docs/superpowers/plans/2026-05-23-lcdu-ccf-a-research-plan.md",
        theory_ref="paper/LCDU_THEORY.md",
        algorithm_ref="paper/LCDU_ALGORITHM.md",
        claim_boundary_ref="paper/LCDU_CLAIM_BOUNDARY.md",
        data_audit_ref="paper/LCDU_PUBLIC_DATA_AUDIT.md",
        baseline_spec_ref="paper/LCDU_BASELINE_SPEC.md",
        theory_contract=_theory_contract(),
        public_task_card_index=_public_task_card_index(),
        public_task_ingestion_smoke_index=_public_task_ingestion_smoke_index(),
        public_task_microdata_ingestion=_public_task_microdata_ingestion(),
        cross_task_validation=_cross_task_validation(),
        llm_simulator_validation=_llm_simulator_validation(),
        llm_seed_scale_repeat_matrix=_llm_seed_scale_repeat_matrix(),
        llm_instability_diagnosis=_llm_instability_diagnosis(),
        llm_prompt_variant_repeat_matrix=_llm_prompt_variant_repeat_matrix(),
        llm_cross_provider_matrix=_llm_cross_provider_matrix(),
        llm_scale_stability_matrix=_llm_scale_stability_matrix(),
        finer_schema_robustness_matrix=_finer_schema_robustness_matrix(),
    )

    assert "finer_schema_robustness_matrix_ready" in index["completed_subgates"]
    assert "finer_schema_robustness_signal_positive" in index["completed_subgates"]
    assert "lcdu-anes-finer-schema-robustness-current-001" in (
        index["evidence_package_refs"]
    )
    assert "run_finer_schema_robustness_matrix" not in index["required_next_gates"]


def test_build_lcdu_paper_gate_index_keeps_strong_baseline_gate_open_for_partial_matrix():
    method_summary = _method_summary()
    method_summary["ccf_a_gaps"].append("full_population_scale_validation_missing")
    index = build_lcdu_paper_gate_index(
        artifact_id="lcdu-paper-gate-index-test",
        method_summary=method_summary,
        plan_ref="docs/superpowers/plans/2026-05-23-lcdu-ccf-a-research-plan.md",
        theory_ref="paper/LCDU_THEORY.md",
        algorithm_ref="paper/LCDU_ALGORITHM.md",
        claim_boundary_ref="paper/LCDU_CLAIM_BOUNDARY.md",
        data_audit_ref="paper/LCDU_PUBLIC_DATA_AUDIT.md",
        baseline_spec_ref="paper/LCDU_BASELINE_SPEC.md",
        theory_contract=_theory_contract(),
        public_task_card_index=_public_task_card_index(),
        public_task_ingestion_smoke_index=_public_task_ingestion_smoke_index(),
        public_task_microdata_ingestion=_public_task_microdata_ingestion(),
        cross_task_validation=_cross_task_validation(),
        llm_simulator_validation=_llm_simulator_validation(),
        llm_seed_scale_repeat_matrix=_llm_seed_scale_repeat_matrix(),
        llm_instability_diagnosis=_llm_instability_diagnosis(),
        llm_prompt_variant_repeat_matrix=_llm_prompt_variant_repeat_matrix(),
        llm_cross_provider_matrix=_llm_cross_provider_matrix(),
        llm_scale_stability_matrix=_llm_scale_stability_matrix(),
        strong_baseline_matrix=_partial_strong_baseline_matrix(),
    )

    assert "strong_baseline_matrix_ready" in index["completed_subgates"]
    assert "strong_baseline_signal_partial" in index["completed_subgates"]
    assert "run_strong_baseline_matrix" in index["required_next_gates"]


def test_build_lcdu_paper_gate_index_closes_strong_baseline_gate_when_full_matrix_leads():
    method_summary = _method_summary()
    method_summary["ccf_a_gaps"].append("full_population_scale_validation_missing")
    index = build_lcdu_paper_gate_index(
        artifact_id="lcdu-paper-gate-index-test",
        method_summary=method_summary,
        plan_ref="docs/superpowers/plans/2026-05-23-lcdu-ccf-a-research-plan.md",
        theory_ref="paper/LCDU_THEORY.md",
        algorithm_ref="paper/LCDU_ALGORITHM.md",
        claim_boundary_ref="paper/LCDU_CLAIM_BOUNDARY.md",
        data_audit_ref="paper/LCDU_PUBLIC_DATA_AUDIT.md",
        baseline_spec_ref="paper/LCDU_BASELINE_SPEC.md",
        theory_contract=_theory_contract(),
        public_task_card_index=_public_task_card_index(),
        public_task_ingestion_smoke_index=_public_task_ingestion_smoke_index(),
        public_task_microdata_ingestion=_public_task_microdata_ingestion(),
        cross_task_validation=_cross_task_validation(),
        llm_simulator_validation=_llm_simulator_validation(),
        llm_seed_scale_repeat_matrix=_llm_seed_scale_repeat_matrix(),
        llm_instability_diagnosis=_llm_instability_diagnosis(),
        llm_prompt_variant_repeat_matrix=_llm_prompt_variant_repeat_matrix(),
        llm_cross_provider_matrix=_llm_cross_provider_matrix(),
        llm_scale_stability_matrix=_llm_scale_stability_matrix(),
        strong_baseline_matrix=_full_strong_baseline_matrix(),
    )

    assert "strong_baseline_signal_lcdu_leads" in index["completed_subgates"]
    assert "run_strong_baseline_matrix" not in index["required_next_gates"]
    assert "formalize_theoretical_identification_proof" in index["required_next_gates"]


def test_build_lcdu_paper_gate_index_records_anchor_fidelity_repair_without_closing_strong_baseline():
    method_summary = _method_summary()
    method_summary["ccf_a_gaps"].append("full_population_scale_validation_missing")
    index = build_lcdu_paper_gate_index(
        artifact_id="lcdu-paper-gate-index-test",
        method_summary=method_summary,
        plan_ref="docs/superpowers/plans/2026-05-23-lcdu-ccf-a-research-plan.md",
        theory_ref="paper/LCDU_THEORY.md",
        algorithm_ref="paper/LCDU_ALGORITHM.md",
        claim_boundary_ref="paper/LCDU_CLAIM_BOUNDARY.md",
        data_audit_ref="paper/LCDU_PUBLIC_DATA_AUDIT.md",
        baseline_spec_ref="paper/LCDU_BASELINE_SPEC.md",
        theory_contract=_theory_contract(),
        public_task_card_index=_public_task_card_index(),
        public_task_ingestion_smoke_index=_public_task_ingestion_smoke_index(),
        public_task_microdata_ingestion=_public_task_microdata_ingestion(),
        cross_task_validation=_cross_task_validation(),
        llm_simulator_validation=_llm_simulator_validation(),
        llm_seed_scale_repeat_matrix=_llm_seed_scale_repeat_matrix(),
        llm_instability_diagnosis=_llm_instability_diagnosis(),
        llm_prompt_variant_repeat_matrix=_llm_prompt_variant_repeat_matrix(),
        llm_cross_provider_matrix=_llm_cross_provider_matrix(),
        llm_scale_stability_matrix=_llm_scale_stability_matrix(),
        strong_baseline_matrix=_partial_strong_baseline_matrix(),
        anchor_fidelity_repair=_anchor_fidelity_repair(),
    )

    assert "anchor_fidelity_repair_ready" in index["completed_subgates"]
    assert "anchor_fidelity_repair_llm_copy_positive" in index["completed_subgates"]
    assert "lcdu-anes-anchor-fidelity-repair-current-001" in (
        index["evidence_package_refs"]
    )
    assert "run_strong_baseline_matrix" in index["required_next_gates"]


def test_build_lcdu_paper_gate_index_records_hybrid_method_without_closing_strong_baseline():
    method_summary = _method_summary()
    method_summary["ccf_a_gaps"].append("full_population_scale_validation_missing")
    index = build_lcdu_paper_gate_index(
        artifact_id="lcdu-paper-gate-index-test",
        method_summary=method_summary,
        plan_ref="docs/superpowers/plans/2026-05-23-lcdu-ccf-a-research-plan.md",
        theory_ref="paper/LCDU_THEORY.md",
        algorithm_ref="paper/LCDU_ALGORITHM.md",
        claim_boundary_ref="paper/LCDU_CLAIM_BOUNDARY.md",
        data_audit_ref="paper/LCDU_PUBLIC_DATA_AUDIT.md",
        baseline_spec_ref="paper/LCDU_BASELINE_SPEC.md",
        theory_contract=_theory_contract(),
        public_task_card_index=_public_task_card_index(),
        public_task_ingestion_smoke_index=_public_task_ingestion_smoke_index(),
        public_task_microdata_ingestion=_public_task_microdata_ingestion(),
        cross_task_validation=_cross_task_validation(),
        llm_simulator_validation=_llm_simulator_validation(),
        llm_seed_scale_repeat_matrix=_llm_seed_scale_repeat_matrix(),
        llm_instability_diagnosis=_llm_instability_diagnosis(),
        llm_prompt_variant_repeat_matrix=_llm_prompt_variant_repeat_matrix(),
        llm_cross_provider_matrix=_llm_cross_provider_matrix(),
        llm_scale_stability_matrix=_llm_scale_stability_matrix(),
        strong_baseline_matrix=_partial_strong_baseline_matrix(),
        anchor_fidelity_repair=_anchor_fidelity_repair(),
        hybrid_method_validation=_hybrid_method_validation(),
    )

    assert "hybrid_method_validation_ready" in index["completed_subgates"]
    assert "hybrid_method_numeric_parity_not_accuracy_win" in (
        index["completed_subgates"]
    )
    assert "lcdu-anes-hybrid-method-validation-current-001" in (
        index["evidence_package_refs"]
    )
    assert "run_strong_baseline_matrix" in index["required_next_gates"]


def test_build_lcdu_paper_gate_index_closes_formal_theory_gate_with_bounded_proof():
    index = build_lcdu_paper_gate_index(
        artifact_id="lcdu-paper-gate-index-test",
        method_summary=_method_summary(),
        plan_ref="docs/superpowers/plans/2026-05-23-lcdu-ccf-a-research-plan.md",
        theory_ref="paper/LCDU_THEORY.md",
        algorithm_ref="paper/LCDU_ALGORITHM.md",
        claim_boundary_ref="paper/LCDU_CLAIM_BOUNDARY.md",
        data_audit_ref="paper/LCDU_PUBLIC_DATA_AUDIT.md",
        baseline_spec_ref="paper/LCDU_BASELINE_SPEC.md",
        theory_contract=_theory_contract(),
        theoretical_identification_proof=_theoretical_identification_proof(),
    )

    assert "theoretical_identification_proof_artifact_ready" in (
        index["completed_subgates"]
    )
    assert "theoretical_identification_proof_ready" in index["completed_subgates"]
    assert "lcdu-theoretical-identification-proof-current-001" in (
        index["evidence_package_refs"]
    )
    assert "formalize_theoretical_identification_proof" not in (
        index["required_next_gates"]
    )


def test_lcdu_paper_gate_index_script_writes_json(tmp_path):
    method_summary = tmp_path / "method-summary.json"
    output = tmp_path / "paper-gate-index.json"
    method_summary.write_text(json.dumps(_method_summary()))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_paper_gate_index.py",
            "--method-summary",
            str(method_summary),
            "--output",
            str(output),
            "--artifact-id",
            "lcdu-paper-gate-index-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "artifact_id": "lcdu-paper-gate-index-test",
        "blocking_gap_count": 3,
        "output": str(output),
        "status": "open",
    }
    assert json.loads(output.read_text())["method"]["method_id"] == "LCDU-L3"


def _method_summary() -> dict:
    return {
        "schema_version": "policy-reaction-lcdu-l3-method-summary-v1",
        "artifact_id": "policy-reaction-lcdu-l3-method-summary-current-001",
        "method_id": "LCDU-L3",
        "overall_status": "active_mainline_bounded",
        "product_transfer_status": "bounded_transfer_ready",
        "accepted_candidate_ids": [
            "policy-reaction-lcdu-l3-current-001-h02",
            "policy-reaction-lcdu-l3-interaction-current-001-i01",
        ],
        "evidence": {
            "mechanism": {"best_runtime_loss": 0.000092334757},
            "route_coverage": {
                "challenger_count": 6,
                "challenger_exceeds_lcdu_l3": False,
            },
        },
        "ccf_a_gaps": [
            "ccf_a_external_validity_missing",
            "cross_provider_generalization_missing",
            "theoretical_identification_needs_formalization",
        ],
        "product_gaps": ["customer_field_validation_missing"],
        "risk_flags": [
            "not_customer_field_validated",
            "finite_route_grid_not_algorithm_space",
        ],
        "claim_boundaries": [
            "LCDU L3 method summary supports bounded product transfer only; not field validation."
        ],
    }


def _theory_contract() -> dict:
    return {
        "schema_version": "lcdu-theory-contract-v1",
        "artifact_id": "lcdu-theory-contract-current-001",
        "overall_status": "formal_objects_mapped",
        "formal_object_count": 8,
        "closed_gate_ids": ["complete_lcdu_theory_contract"],
    }


def _theoretical_identification_proof() -> dict:
    return {
        "schema_version": "lcdu-theoretical-identification-proof-v1",
        "artifact_id": "lcdu-theoretical-identification-proof-current-001",
        "overall_status": "bounded_hybrid_identification_proof_ready",
        "validation_type": "lcdu_theoretical_identification_proof",
        "closed_gate_ids": ["theoretical_identification_proof_ready"],
    }


def _public_task_card_index() -> dict:
    return {
        "schema_version": "lcdu-public-task-card-index-v1",
        "artifact_id": "lcdu-public-task-card-index-current-001",
        "overall_status": "recommended_task_cards_ready",
        "task_count": 2,
        "task_ids": [
            "public_health_medical_insurance_attitude_v1",
            "climate_energy_regulation_attitude_v1",
        ],
    }


def _public_task_ingestion_smoke_index() -> dict:
    return {
        "schema_version": "lcdu-public-task-ingestion-smoke-index-v1",
        "artifact_id": "lcdu-public-task-ingestion-smoke-index-current-001",
        "overall_status": "target_distribution_skeletons_ready",
        "task_count": 2,
        "task_ids": [
            "public_health_medical_insurance_attitude_v1",
            "climate_energy_regulation_attitude_v1",
        ],
    }


def _public_task_microdata_ingestion() -> dict:
    return {
        "schema_version": "lcdu-anes-public-microdata-ingestion-v1",
        "artifact_id": "lcdu-anes-2024-sda-public-microdata-001",
        "overall_status": (
            "segment_target_distributions_materialized_with_partial_schema"
        ),
        "target_distributions": {
            "public_health_medical_insurance_attitude_v1": {},
            "climate_energy_regulation_attitude_v1": {},
        },
        "splits": {
            "calibration": {},
            "heldout": {},
            "test": {},
        },
    }


def _cross_task_validation() -> dict:
    return {
        "schema_version": "lcdu-anes-cross-task-validation-v1",
        "artifact_id": "lcdu-anes-cross-task-validation-current-001",
        "overall_status": "cross_task_anchor_signal_positive",
        "validation_type": "split_gated_segment_anchor_transfer_smoke",
        "task_count": 2,
    }


def _llm_simulator_validation() -> dict:
    return {
        "schema_version": "lcdu-anes-llm-simulator-validation-v1",
        "artifact_id": (
            "lcdu-anes-llm-simulator-validation-deepseek-v4-flash-2seg-current-001"
        ),
        "overall_status": "cross_task_llm_signal_positive",
        "validation_type": "split_gated_llm_segment_simulator_smoke",
        "task_count": 2,
    }


def _llm_seed_scale_repeat_matrix() -> dict:
    return {
        "schema_version": "lcdu-anes-llm-seed-scale-repeat-matrix-v1",
        "artifact_id": (
            "lcdu-anes-llm-seed-scale-repeat-deepseek-v4-flash-s2s4-o0o1-standard-001"
        ),
        "overall_status": "seed_scale_repeat_signal_mixed",
        "validation_type": "llm_seed_scale_repeat_matrix",
        "run_count": 4,
    }


def _llm_instability_diagnosis() -> dict:
    return {
        "schema_version": "lcdu-anes-llm-instability-diagnosis-v1",
        "artifact_id": "lcdu-anes-llm-instability-diagnosis-current-001",
        "overall_status": "instability_recovered_by_prompt_variant",
        "source_matrix_artifact_id": (
            "lcdu-anes-llm-seed-scale-repeat-deepseek-v4-flash-s2s4-o0o1-standard-001"
        ),
        "failure_count": 1,
        "recovered_failure_count": 1,
        "persistent_failure_count": 0,
        "failure_cases": [
            {
                "task_id": "public_health_medical_insurance_attitude_v1",
                "max_segments_per_task": 2,
                "segment_offset": 1,
                "prompt_variant": "standard",
            }
        ],
        "recovery_cases": [
            {
                "task_id": "public_health_medical_insurance_attitude_v1",
                "recovered_by_prompt_variant": "compact",
            }
        ],
    }


def _llm_prompt_variant_repeat_matrix() -> dict:
    return {
        "schema_version": "lcdu-anes-llm-seed-scale-repeat-matrix-v1",
        "artifact_id": (
            "lcdu-anes-llm-seed-scale-repeat-deepseek-v4-flash-s2s4-o0o1-promptvariants-001"
        ),
        "overall_status": "seed_scale_repeat_signal_positive",
        "validation_type": "llm_seed_scale_repeat_matrix",
        "run_count": 8,
        "prompt_variants": ["compact", "deliberative"],
    }


def _llm_cross_provider_matrix() -> dict:
    return {
        "schema_version": "lcdu-anes-llm-cross-provider-matrix-v1",
        "artifact_id": "lcdu-anes-llm-cross-provider-matrix-current-001",
        "overall_status": "cross_provider_selected_variant_positive",
        "provider_environment_count": 2,
        "positive_provider_environment_count": 1,
        "provider_environments": [
            "https://api.deepseek.com::deepseek-v4-flash",
            "http://127.0.0.1:1234/v1::openai/gpt-oss-20b",
        ],
        "selected_prompt_variant": "deliberative",
    }


def _llm_scale_stability_matrix() -> dict:
    return {
        "schema_version": "lcdu-anes-llm-scale-stability-matrix-v1",
        "artifact_id": "lcdu-anes-llm-scale-stability-matrix-current-001",
        "overall_status": "scale_stability_signal_positive",
        "validation_type": "llm_segment_scale_stability_matrix",
        "max_segment_scale": 16,
        "min_max_segment_scale": 8,
        "run_count": 3,
        "positive_run_count": 3,
    }


def _finer_schema_robustness_matrix() -> dict:
    return {
        "schema_version": "lcdu-anes-finer-schema-robustness-matrix-v1",
        "artifact_id": "lcdu-anes-finer-schema-robustness-current-001",
        "overall_status": "finer_schema_robustness_signal_positive",
        "validation_type": "lcdu_finer_schema_robustness_matrix",
        "schema_count": 4,
        "positive_schema_count": 4,
        "max_axis_count": 4,
    }


def _partial_strong_baseline_matrix() -> dict:
    return {
        "schema_version": "lcdu-anes-strong-baseline-matrix-v1",
        "artifact_id": "lcdu-anes-strong-baseline-matrix-current-001",
        "overall_status": "strong_baseline_partial_lcdu_leads",
        "validation_type": "lcdu_strong_baseline_matrix",
        "lcdU_leads_covered_baselines": True,
        "missing_baseline_families": ["textgrad_or_prompt_optimizer"],
    }


def _full_strong_baseline_matrix() -> dict:
    baseline = _partial_strong_baseline_matrix()
    baseline["overall_status"] = "strong_baseline_lcdu_leads"
    baseline["missing_baseline_families"] = []
    return baseline


def _anchor_fidelity_repair() -> dict:
    return {
        "schema_version": "lcdu-anes-anchor-fidelity-repair-v1",
        "artifact_id": "lcdu-anes-anchor-fidelity-repair-current-001",
        "overall_status": "llm_anchor_copy_repair_positive",
        "validation_type": "lcdu_anchor_fidelity_repair_diagnostic",
        "task_count": 2,
        "deterministic_closes_count": 2,
        "llm_copy_closes_count": 2,
    }


def _hybrid_method_validation() -> dict:
    return {
        "schema_version": "lcdu-anes-hybrid-method-validation-v1",
        "artifact_id": "lcdu-anes-hybrid-method-validation-current-001",
        "overall_status": "hybrid_candidate_numeric_parity_soft_not_leading",
        "validation_type": "lcdu_hybrid_method_validation",
        "task_count": 2,
        "numeric_parity_count": 2,
        "strict_copy_positive_count": 2,
        "research_decision": (
            "reframe_as_hybrid_auditable_constraint_framework_not_accuracy_win"
        ),
    }
