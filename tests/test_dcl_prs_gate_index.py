import json
import subprocess
import sys

from experiments.dcl_prs_gate_index import build_dcl_prs_gate_index
from experiments.dcl_prs_cross_domain_task_slice_smoke import (
    build_cross_domain_task_slice_smoke,
)
from experiments.dcl_prs_cross_domain_microdata_slices import (
    build_cross_domain_microdata_access_audit,
)
from experiments.dcl_prs_dynamic_simulation import build_dynamic_simulation_trace
from experiments.dcl_prs_failure_attribution import build_failure_attribution_index
from experiments.dcl_prs_mechanism_ablation_matrix import (
    build_mechanism_ablation_matrix,
)
from experiments.dcl_prs_mechanism_ablation_repeat_matrix import (
    build_mechanism_ablation_repeat_matrix,
)
from experiments.dcl_prs_mechanism_program import build_mechanism_program_index
from experiments.dcl_prs_official_public_use_file_probe import (
    build_official_public_use_file_probe,
)
from experiments.dcl_prs_product_cohort_report import build_product_cohort_report
from experiments.dcl_prs_product_runtime_manifest import (
    build_product_runtime_manifest,
)
from experiments.dcl_prs_public_dataset_ingestion import (
    build_cross_domain_ingestion_index,
)
from experiments.dcl_prs_repair_repeat_acceptance_matrix import (
    build_repair_repeat_acceptance_matrix,
)
from experiments.dcl_prs_repair_effect_validation_matrix import (
    build_repair_effect_validation_matrix,
)
from experiments.dcl_prs_strong_baseline_matrix import (
    build_dcl_prs_strong_baseline_matrix,
)


def test_dcl_prs_gate_keeps_research_and_product_claims_open_for_ingestion_only():
    gate = build_dcl_prs_gate_index(
        artifact_id="dcl-prs-gate-test",
        cross_domain_ingestion=build_cross_domain_ingestion_index(
            artifact_id="dcl-prs-cross-domain-ingestion-test"
        ),
    )

    assert gate["schema_version"] == "dcl-prs-gate-index-v1"
    assert gate["overall_status"] == "dcl_prs_l0_started_but_claims_open"
    assert gate["ccf_a_gate"]["status"] == "open"
    assert gate["product_gate"]["status"] == "open"
    assert "cross_domain_public_dataset_ingestion_ready" in gate["completed_subgates"]
    assert "run_mechanism_program_l0" in gate["required_next_gates"]
    assert "run_failure_attribution_l0" in gate["required_next_gates"]
    assert "run_dynamic_simulation_l0" in gate["required_next_gates"]
    assert "dcl-prs-cross-domain-ingestion-test" in gate["evidence_refs"]
    json.dumps(gate, allow_nan=False)


def test_dcl_prs_gate_closes_l0_subgates_but_not_paper_or_product_claims():
    gate = build_dcl_prs_gate_index(
        artifact_id="dcl-prs-gate-test",
        cross_domain_ingestion=build_cross_domain_ingestion_index(
            artifact_id="dcl-prs-cross-domain-ingestion-test"
        ),
        mechanism_program={
            "schema_version": "dcl-prs-mechanism-program-index-v1",
            "artifact_id": "dcl-prs-mechanism-program-test",
            "overall_status": "mechanism_programs_ready_for_l0_gate",
        },
        failure_attribution={
            "schema_version": "dcl-prs-failure-attribution-index-v1",
            "artifact_id": "dcl-prs-failure-attribution-test",
            "overall_status": "failure_attribution_ready_for_l0_gate",
        },
        dynamic_simulation={
            "schema_version": "dcl-prs-dynamic-simulation-trace-v1",
            "artifact_id": "dcl-prs-dynamic-simulation-test",
            "overall_status": "dynamic_trace_ready_for_l0_gate",
        },
    )

    assert gate["completed_subgates"] == [
        "cross_domain_public_dataset_ingestion_ready",
        "mechanism_program_l0_ready",
        "failure_attribution_l0_ready",
        "dynamic_simulation_l0_ready",
    ]
    assert gate["required_next_gates"] == [
        "run_mechanism_ablation_matrix",
        "run_repair_repeat_acceptance_matrix",
        "run_cross_domain_task_slice_smoke",
        "run_product_cohort_report_evidence",
    ]
    assert gate["ccf_a_gate"]["status"] == "open"
    assert gate["product_gate"]["status"] == "open"


def test_dcl_prs_gate_tracks_l1_subgates_without_closing_claims():
    cross_domain = build_cross_domain_ingestion_index(
        artifact_id="dcl-prs-cross-domain-ingestion-test"
    )
    mechanism = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-test"
    )
    failure = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-test"
    )
    dynamic = build_dynamic_simulation_trace(
        artifact_id="dcl-prs-dynamic-simulation-test",
        mechanism_program_index=mechanism,
    )
    gate = build_dcl_prs_gate_index(
        artifact_id="dcl-prs-gate-test",
        cross_domain_ingestion=cross_domain,
        mechanism_program=mechanism,
        failure_attribution=failure,
        dynamic_simulation=dynamic,
        mechanism_ablation_matrix=build_mechanism_ablation_matrix(
            artifact_id="dcl-prs-mechanism-ablation-test",
            mechanism_program_index=mechanism,
        ),
        repair_repeat_acceptance_matrix=build_repair_repeat_acceptance_matrix(
            artifact_id="dcl-prs-repair-repeat-test",
            failure_attribution_index=failure,
        ),
        cross_domain_task_slice_smoke=build_cross_domain_task_slice_smoke(
            artifact_id="dcl-prs-cross-domain-task-slice-smoke-test",
            cross_domain_ingestion=cross_domain,
        ),
        product_cohort_report=build_product_cohort_report(
            artifact_id="dcl-prs-product-cohort-report-test",
            mechanism_program_index=mechanism,
            failure_attribution_index=failure,
            dynamic_simulation=dynamic,
        ),
    )

    assert "mechanism_ablation_matrix_ready" in gate["completed_subgates"]
    assert "repair_repeat_acceptance_matrix_ready" in gate["completed_subgates"]
    assert "cross_domain_task_slice_smoke_ready" in gate["completed_subgates"]
    assert "product_cohort_report_evidence_ready" in gate["completed_subgates"]
    assert gate["required_next_gates"] == [
        "run_mechanism_ablation_repeat_matrix",
        "run_repair_effect_validation_matrix",
        "load_cross_domain_public_microdata_slices",
        "connect_report_to_product_runtime_manifest",
        "run_strong_baseline_matrix",
    ]
    assert "mechanism_ablation_missing" not in gate["ccf_a_gate"]["blocking_gaps"]
    assert "repair_repeat_acceptance_missing" not in gate["ccf_a_gate"][
        "blocking_gaps"
    ]
    assert "cross_domain_smoke_missing" not in gate["ccf_a_gate"]["blocking_gaps"]
    assert "cohort_report_evidence_missing" not in gate["product_gate"][
        "blocking_gaps"
    ]
    assert gate["ccf_a_gate"]["status"] == "open"
    assert gate["product_gate"]["status"] == "open"


def test_dcl_prs_gate_tracks_l2_readiness_but_keeps_true_blockers_open():
    cross_domain = build_cross_domain_ingestion_index(
        artifact_id="dcl-prs-cross-domain-ingestion-test"
    )
    mechanism = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-test"
    )
    failure = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-test"
    )
    dynamic = build_dynamic_simulation_trace(
        artifact_id="dcl-prs-dynamic-simulation-test",
        mechanism_program_index=mechanism,
    )
    ablation = build_mechanism_ablation_matrix(
        artifact_id="dcl-prs-mechanism-ablation-test",
        mechanism_program_index=mechanism,
    )
    repeat_acceptance = build_repair_repeat_acceptance_matrix(
        artifact_id="dcl-prs-repair-repeat-test",
        failure_attribution_index=failure,
    )
    task_slice_smoke = build_cross_domain_task_slice_smoke(
        artifact_id="dcl-prs-cross-domain-task-slice-smoke-test",
        cross_domain_ingestion=cross_domain,
    )
    product_report = build_product_cohort_report(
        artifact_id="dcl-prs-product-cohort-report-test",
        mechanism_program_index=mechanism,
        failure_attribution_index=failure,
        dynamic_simulation=dynamic,
    )
    gate = build_dcl_prs_gate_index(
        artifact_id="dcl-prs-gate-test",
        cross_domain_ingestion=cross_domain,
        mechanism_program=mechanism,
        failure_attribution=failure,
        dynamic_simulation=dynamic,
        mechanism_ablation_matrix=ablation,
        repair_repeat_acceptance_matrix=repeat_acceptance,
        cross_domain_task_slice_smoke=task_slice_smoke,
        product_cohort_report=product_report,
        mechanism_ablation_repeat_matrix=build_mechanism_ablation_repeat_matrix(
            artifact_id="dcl-prs-mechanism-ablation-repeat-test",
            mechanism_ablation_matrix=ablation,
        ),
        repair_effect_validation_matrix=build_repair_effect_validation_matrix(
            artifact_id="dcl-prs-repair-effect-test",
            repair_repeat_acceptance_matrix=repeat_acceptance,
        ),
        cross_domain_microdata_access_audit=build_cross_domain_microdata_access_audit(
            artifact_id="dcl-prs-cross-domain-microdata-test",
            cross_domain_task_slice_smoke=task_slice_smoke,
        ),
        product_runtime_manifest=build_product_runtime_manifest(
            artifact_id="dcl-prs-product-runtime-manifest-test",
            product_cohort_report=product_report,
        ),
        strong_baseline_matrix=build_dcl_prs_strong_baseline_matrix(
            artifact_id="dcl-prs-strong-baseline-test"
        ),
    )

    assert "mechanism_ablation_repeat_matrix_ready" in gate["completed_subgates"]
    assert "repair_effect_validation_matrix_ready" in gate["completed_subgates"]
    assert "cross_domain_microdata_access_audit_ready" in gate["completed_subgates"]
    assert "product_runtime_manifest_connection_ready" in gate["completed_subgates"]
    assert "strong_baseline_matrix_ready" in gate["completed_subgates"]
    assert gate["required_next_gates"] == [
        "download_official_cross_domain_public_use_files",
        "run_real_repair_effect_validation",
        "run_multi_dataset_generalization_matrix",
        "run_product_runtime_validation",
        "improve_dcl_prs_until_strong_baseline_win",
    ]
    assert gate["ccf_a_gate"]["blocking_gaps"] == [
        "cross_domain_microdata_download_missing",
        "real_effect_validation_missing",
        "strong_baseline_win_missing",
        "multi_dataset_generalization_missing",
    ]
    assert gate["product_gate"]["blocking_gaps"] == [
        "customer_field_validation_missing",
        "product_runtime_validation_missing",
    ]


def test_dcl_prs_gate_tracks_l3_official_data_without_overclaiming():
    cross_domain = build_cross_domain_ingestion_index(
        artifact_id="dcl-prs-cross-domain-ingestion-test"
    )
    mechanism = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-test"
    )
    failure = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-test"
    )
    dynamic = build_dynamic_simulation_trace(
        artifact_id="dcl-prs-dynamic-simulation-test",
        mechanism_program_index=mechanism,
    )
    ablation = build_mechanism_ablation_matrix(
        artifact_id="dcl-prs-mechanism-ablation-test",
        mechanism_program_index=mechanism,
    )
    repeat_acceptance = build_repair_repeat_acceptance_matrix(
        artifact_id="dcl-prs-repair-repeat-test",
        failure_attribution_index=failure,
    )
    task_slice_smoke = build_cross_domain_task_slice_smoke(
        artifact_id="dcl-prs-cross-domain-task-slice-smoke-test",
        cross_domain_ingestion=cross_domain,
    )
    product_report = build_product_cohort_report(
        artifact_id="dcl-prs-product-cohort-report-test",
        mechanism_program_index=mechanism,
        failure_attribution_index=failure,
        dynamic_simulation=dynamic,
    )
    gss_manifest = {
        "schema_version": "dcl-prs-gss-public-use-download-v1",
        "artifact_id": "dcl-prs-gss-public-use-download-test",
        "overall_status": "gss_public_use_download_verified",
        "download_verified": True,
        "byte_count": 123,
        "sha256": "abc",
    }
    official_file_probe = build_official_public_use_file_probe(
        artifact_id="dcl-prs-official-public-use-file-probe-test",
        gss_download_manifest=gss_manifest,
    )

    gate = build_dcl_prs_gate_index(
        artifact_id="dcl-prs-gate-test",
        cross_domain_ingestion=cross_domain,
        mechanism_program=mechanism,
        failure_attribution=failure,
        dynamic_simulation=dynamic,
        mechanism_ablation_matrix=ablation,
        repair_repeat_acceptance_matrix=repeat_acceptance,
        cross_domain_task_slice_smoke=task_slice_smoke,
        product_cohort_report=product_report,
        mechanism_ablation_repeat_matrix=build_mechanism_ablation_repeat_matrix(
            artifact_id="dcl-prs-mechanism-ablation-repeat-test",
            mechanism_ablation_matrix=ablation,
        ),
        repair_effect_validation_matrix=build_repair_effect_validation_matrix(
            artifact_id="dcl-prs-repair-effect-test",
            repair_repeat_acceptance_matrix=repeat_acceptance,
        ),
        cross_domain_microdata_access_audit=build_cross_domain_microdata_access_audit(
            artifact_id="dcl-prs-cross-domain-microdata-test",
            cross_domain_task_slice_smoke=task_slice_smoke,
        ),
        product_runtime_manifest=build_product_runtime_manifest(
            artifact_id="dcl-prs-product-runtime-manifest-test",
            product_cohort_report=product_report,
        ),
        strong_baseline_matrix=build_dcl_prs_strong_baseline_matrix(
            artifact_id="dcl-prs-strong-baseline-test"
        ),
        gss_public_use_download_manifest=gss_manifest,
        official_public_use_file_probe=official_file_probe,
    )

    assert "gss_public_use_download_verified" in gate["completed_subgates"]
    assert "official_public_use_file_probe_partial" in gate["completed_subgates"]
    assert "dcl-prs-gss-public-use-download-test" in gate["evidence_refs"]
    assert "dcl-prs-official-public-use-file-probe-test" in gate["evidence_refs"]
    assert gate["required_next_gates"] == [
        "complete_eurobarometer_authenticated_download",
        "bind_gss_public_use_variables_to_policy_tasks",
        "run_real_repair_effect_validation",
        "run_multi_dataset_generalization_matrix",
        "run_product_runtime_validation",
        "improve_dcl_prs_until_strong_baseline_win",
    ]
    assert gate["ccf_a_gate"]["blocking_gaps"] == [
        "eurobarometer_microdata_download_missing",
        "gss_variable_binding_missing",
        "real_effect_validation_missing",
        "strong_baseline_win_missing",
        "multi_dataset_generalization_missing",
    ]
    assert gate["product_gate"]["blocking_gaps"] == [
        "customer_field_validation_missing",
        "product_runtime_validation_missing",
    ]


def test_dcl_prs_gate_tracks_gss_variable_binding_as_next_data_step():
    cross_domain = build_cross_domain_ingestion_index(
        artifact_id="dcl-prs-cross-domain-ingestion-test"
    )
    mechanism = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-test"
    )
    failure = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-test"
    )
    dynamic = build_dynamic_simulation_trace(
        artifact_id="dcl-prs-dynamic-simulation-test",
        mechanism_program_index=mechanism,
    )
    ablation = build_mechanism_ablation_matrix(
        artifact_id="dcl-prs-mechanism-ablation-test",
        mechanism_program_index=mechanism,
    )
    repeat_acceptance = build_repair_repeat_acceptance_matrix(
        artifact_id="dcl-prs-repair-repeat-test",
        failure_attribution_index=failure,
    )
    task_slice_smoke = build_cross_domain_task_slice_smoke(
        artifact_id="dcl-prs-cross-domain-task-slice-smoke-test",
        cross_domain_ingestion=cross_domain,
    )
    product_report = build_product_cohort_report(
        artifact_id="dcl-prs-product-cohort-report-test",
        mechanism_program_index=mechanism,
        failure_attribution_index=failure,
        dynamic_simulation=dynamic,
    )
    gss_manifest = {
        "schema_version": "dcl-prs-gss-public-use-download-v1",
        "artifact_id": "dcl-prs-gss-public-use-download-test",
        "overall_status": "gss_public_use_download_verified",
        "download_verified": True,
    }
    official_file_probe = build_official_public_use_file_probe(
        artifact_id="dcl-prs-official-public-use-file-probe-test",
        gss_download_manifest=gss_manifest,
    )
    gss_binding = {
        "schema_version": "dcl-prs-gss-policy-task-binding-v1",
        "artifact_id": "dcl-prs-gss-policy-task-binding-test",
        "overall_status": "gss_policy_task_variables_bound",
        "required_fields_bound": True,
    }

    gate = build_dcl_prs_gate_index(
        artifact_id="dcl-prs-gate-test",
        cross_domain_ingestion=cross_domain,
        mechanism_program=mechanism,
        failure_attribution=failure,
        dynamic_simulation=dynamic,
        mechanism_ablation_matrix=ablation,
        repair_repeat_acceptance_matrix=repeat_acceptance,
        cross_domain_task_slice_smoke=task_slice_smoke,
        product_cohort_report=product_report,
        mechanism_ablation_repeat_matrix=build_mechanism_ablation_repeat_matrix(
            artifact_id="dcl-prs-mechanism-ablation-repeat-test",
            mechanism_ablation_matrix=ablation,
        ),
        repair_effect_validation_matrix=build_repair_effect_validation_matrix(
            artifact_id="dcl-prs-repair-effect-test",
            repair_repeat_acceptance_matrix=repeat_acceptance,
        ),
        cross_domain_microdata_access_audit=build_cross_domain_microdata_access_audit(
            artifact_id="dcl-prs-cross-domain-microdata-test",
            cross_domain_task_slice_smoke=task_slice_smoke,
        ),
        product_runtime_manifest=build_product_runtime_manifest(
            artifact_id="dcl-prs-product-runtime-manifest-test",
            product_cohort_report=product_report,
        ),
        strong_baseline_matrix=build_dcl_prs_strong_baseline_matrix(
            artifact_id="dcl-prs-strong-baseline-test"
        ),
        gss_public_use_download_manifest=gss_manifest,
        official_public_use_file_probe=official_file_probe,
        gss_policy_task_binding=gss_binding,
    )

    assert "gss_policy_task_variables_bound" in gate["completed_subgates"]
    assert "dcl-prs-gss-policy-task-binding-test" in gate["evidence_refs"]
    assert gate["required_next_gates"] == [
        "complete_eurobarometer_authenticated_download",
        "run_gss_policy_task_ingestion_smoke",
        "run_real_repair_effect_validation",
        "run_multi_dataset_generalization_matrix",
        "run_product_runtime_validation",
        "improve_dcl_prs_until_strong_baseline_win",
    ]
    assert gate["ccf_a_gate"]["blocking_gaps"] == [
        "eurobarometer_microdata_download_missing",
        "gss_ingestion_smoke_missing",
        "real_effect_validation_missing",
        "strong_baseline_win_missing",
        "multi_dataset_generalization_missing",
    ]


def test_dcl_prs_gate_tracks_gss_ingestion_smoke_without_claiming_generalization():
    cross_domain = build_cross_domain_ingestion_index(
        artifact_id="dcl-prs-cross-domain-ingestion-test"
    )
    mechanism = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-test"
    )
    failure = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-test"
    )
    dynamic = build_dynamic_simulation_trace(
        artifact_id="dcl-prs-dynamic-simulation-test",
        mechanism_program_index=mechanism,
    )
    ablation = build_mechanism_ablation_matrix(
        artifact_id="dcl-prs-mechanism-ablation-test",
        mechanism_program_index=mechanism,
    )
    repeat_acceptance = build_repair_repeat_acceptance_matrix(
        artifact_id="dcl-prs-repair-repeat-test",
        failure_attribution_index=failure,
    )
    task_slice_smoke = build_cross_domain_task_slice_smoke(
        artifact_id="dcl-prs-cross-domain-task-slice-smoke-test",
        cross_domain_ingestion=cross_domain,
    )
    product_report = build_product_cohort_report(
        artifact_id="dcl-prs-product-cohort-report-test",
        mechanism_program_index=mechanism,
        failure_attribution_index=failure,
        dynamic_simulation=dynamic,
    )
    gss_manifest = {
        "schema_version": "dcl-prs-gss-public-use-download-v1",
        "artifact_id": "dcl-prs-gss-public-use-download-test",
        "overall_status": "gss_public_use_download_verified",
        "download_verified": True,
    }
    official_file_probe = build_official_public_use_file_probe(
        artifact_id="dcl-prs-official-public-use-file-probe-test",
        gss_download_manifest=gss_manifest,
    )
    gss_binding = {
        "schema_version": "dcl-prs-gss-policy-task-binding-v1",
        "artifact_id": "dcl-prs-gss-policy-task-binding-test",
        "overall_status": "gss_policy_task_variables_bound",
        "required_fields_bound": True,
    }
    gss_smoke = {
        "schema_version": "dcl-prs-gss-policy-task-ingestion-smoke-v1",
        "artifact_id": "dcl-prs-gss-policy-task-smoke-test",
        "overall_status": "gss_policy_task_ingestion_smoke_ready",
        "valid_policy_response_count": 2610,
    }

    gate = build_dcl_prs_gate_index(
        artifact_id="dcl-prs-gate-test",
        cross_domain_ingestion=cross_domain,
        mechanism_program=mechanism,
        failure_attribution=failure,
        dynamic_simulation=dynamic,
        mechanism_ablation_matrix=ablation,
        repair_repeat_acceptance_matrix=repeat_acceptance,
        cross_domain_task_slice_smoke=task_slice_smoke,
        product_cohort_report=product_report,
        mechanism_ablation_repeat_matrix=build_mechanism_ablation_repeat_matrix(
            artifact_id="dcl-prs-mechanism-ablation-repeat-test",
            mechanism_ablation_matrix=ablation,
        ),
        repair_effect_validation_matrix=build_repair_effect_validation_matrix(
            artifact_id="dcl-prs-repair-effect-test",
            repair_repeat_acceptance_matrix=repeat_acceptance,
        ),
        cross_domain_microdata_access_audit=build_cross_domain_microdata_access_audit(
            artifact_id="dcl-prs-cross-domain-microdata-test",
            cross_domain_task_slice_smoke=task_slice_smoke,
        ),
        product_runtime_manifest=build_product_runtime_manifest(
            artifact_id="dcl-prs-product-runtime-manifest-test",
            product_cohort_report=product_report,
        ),
        strong_baseline_matrix=build_dcl_prs_strong_baseline_matrix(
            artifact_id="dcl-prs-strong-baseline-test"
        ),
        gss_public_use_download_manifest=gss_manifest,
        official_public_use_file_probe=official_file_probe,
        gss_policy_task_binding=gss_binding,
        gss_policy_task_ingestion_smoke=gss_smoke,
    )

    assert "gss_policy_task_ingestion_smoke_ready" in gate["completed_subgates"]
    assert "dcl-prs-gss-policy-task-smoke-test" in gate["evidence_refs"]
    assert gate["required_next_gates"] == [
        "complete_eurobarometer_authenticated_download",
        "run_real_repair_effect_validation",
        "run_multi_dataset_generalization_matrix",
        "run_product_runtime_validation",
        "improve_dcl_prs_until_strong_baseline_win",
    ]
    assert gate["ccf_a_gate"]["blocking_gaps"] == [
        "eurobarometer_microdata_download_missing",
        "real_effect_validation_missing",
        "strong_baseline_win_missing",
        "multi_dataset_generalization_missing",
    ]


def test_dcl_prs_gate_tracks_gss_real_effect_without_closing_baselines():
    cross_domain = build_cross_domain_ingestion_index(
        artifact_id="dcl-prs-cross-domain-ingestion-test"
    )
    mechanism = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-test"
    )
    failure = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-test"
    )
    dynamic = build_dynamic_simulation_trace(
        artifact_id="dcl-prs-dynamic-simulation-test",
        mechanism_program_index=mechanism,
    )
    ablation = build_mechanism_ablation_matrix(
        artifact_id="dcl-prs-mechanism-ablation-test",
        mechanism_program_index=mechanism,
    )
    repeat_acceptance = build_repair_repeat_acceptance_matrix(
        artifact_id="dcl-prs-repair-repeat-test",
        failure_attribution_index=failure,
    )
    task_slice_smoke = build_cross_domain_task_slice_smoke(
        artifact_id="dcl-prs-cross-domain-task-slice-smoke-test",
        cross_domain_ingestion=cross_domain,
    )
    product_report = build_product_cohort_report(
        artifact_id="dcl-prs-product-cohort-report-test",
        mechanism_program_index=mechanism,
        failure_attribution_index=failure,
        dynamic_simulation=dynamic,
    )
    gss_manifest = {
        "schema_version": "dcl-prs-gss-public-use-download-v1",
        "artifact_id": "dcl-prs-gss-public-use-download-test",
        "overall_status": "gss_public_use_download_verified",
        "download_verified": True,
    }
    official_file_probe = build_official_public_use_file_probe(
        artifact_id="dcl-prs-official-public-use-file-probe-test",
        gss_download_manifest=gss_manifest,
    )
    gss_binding = {
        "schema_version": "dcl-prs-gss-policy-task-binding-v1",
        "artifact_id": "dcl-prs-gss-policy-task-binding-test",
        "overall_status": "gss_policy_task_variables_bound",
        "required_fields_bound": True,
    }
    gss_smoke = {
        "schema_version": "dcl-prs-gss-policy-task-ingestion-smoke-v1",
        "artifact_id": "dcl-prs-gss-policy-task-smoke-test",
        "overall_status": "gss_policy_task_ingestion_smoke_ready",
        "valid_policy_response_count": 2610,
    }
    gss_real_effect = {
        "schema_version": "dcl-prs-gss-real-repair-effect-v1",
        "artifact_id": "dcl-prs-gss-real-repair-effect-test",
        "overall_status": "gss_real_repair_effect_validation_ready",
        "real_effect_promoted_count": 2,
    }

    gate = build_dcl_prs_gate_index(
        artifact_id="dcl-prs-gate-test",
        cross_domain_ingestion=cross_domain,
        mechanism_program=mechanism,
        failure_attribution=failure,
        dynamic_simulation=dynamic,
        mechanism_ablation_matrix=ablation,
        repair_repeat_acceptance_matrix=repeat_acceptance,
        cross_domain_task_slice_smoke=task_slice_smoke,
        product_cohort_report=product_report,
        mechanism_ablation_repeat_matrix=build_mechanism_ablation_repeat_matrix(
            artifact_id="dcl-prs-mechanism-ablation-repeat-test",
            mechanism_ablation_matrix=ablation,
        ),
        repair_effect_validation_matrix=build_repair_effect_validation_matrix(
            artifact_id="dcl-prs-repair-effect-test",
            repair_repeat_acceptance_matrix=repeat_acceptance,
        ),
        cross_domain_microdata_access_audit=build_cross_domain_microdata_access_audit(
            artifact_id="dcl-prs-cross-domain-microdata-test",
            cross_domain_task_slice_smoke=task_slice_smoke,
        ),
        product_runtime_manifest=build_product_runtime_manifest(
            artifact_id="dcl-prs-product-runtime-manifest-test",
            product_cohort_report=product_report,
        ),
        strong_baseline_matrix=build_dcl_prs_strong_baseline_matrix(
            artifact_id="dcl-prs-strong-baseline-test"
        ),
        gss_public_use_download_manifest=gss_manifest,
        official_public_use_file_probe=official_file_probe,
        gss_policy_task_binding=gss_binding,
        gss_policy_task_ingestion_smoke=gss_smoke,
        gss_real_repair_effect_validation=gss_real_effect,
    )

    assert "gss_real_repair_effect_validation_ready" in gate["completed_subgates"]
    assert "dcl-prs-gss-real-repair-effect-test" in gate["evidence_refs"]
    assert gate["required_next_gates"] == [
        "complete_eurobarometer_authenticated_download",
        "run_multi_dataset_generalization_matrix",
        "run_product_runtime_validation",
        "improve_dcl_prs_until_strong_baseline_win",
    ]
    assert gate["ccf_a_gate"]["blocking_gaps"] == [
        "eurobarometer_microdata_download_missing",
        "strong_baseline_win_missing",
        "multi_dataset_generalization_missing",
    ]


def test_dcl_prs_gate_tracks_partial_multi_dataset_generalization():
    cross_domain = build_cross_domain_ingestion_index(
        artifact_id="dcl-prs-cross-domain-ingestion-test"
    )
    mechanism = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-test"
    )
    failure = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-test"
    )
    dynamic = build_dynamic_simulation_trace(
        artifact_id="dcl-prs-dynamic-simulation-test",
        mechanism_program_index=mechanism,
    )
    ablation = build_mechanism_ablation_matrix(
        artifact_id="dcl-prs-mechanism-ablation-test",
        mechanism_program_index=mechanism,
    )
    repeat_acceptance = build_repair_repeat_acceptance_matrix(
        artifact_id="dcl-prs-repair-repeat-test",
        failure_attribution_index=failure,
    )
    task_slice_smoke = build_cross_domain_task_slice_smoke(
        artifact_id="dcl-prs-cross-domain-task-slice-smoke-test",
        cross_domain_ingestion=cross_domain,
    )
    product_report = build_product_cohort_report(
        artifact_id="dcl-prs-product-cohort-report-test",
        mechanism_program_index=mechanism,
        failure_attribution_index=failure,
        dynamic_simulation=dynamic,
    )
    gss_manifest = {
        "schema_version": "dcl-prs-gss-public-use-download-v1",
        "artifact_id": "dcl-prs-gss-public-use-download-test",
        "overall_status": "gss_public_use_download_verified",
        "download_verified": True,
    }
    official_file_probe = build_official_public_use_file_probe(
        artifact_id="dcl-prs-official-public-use-file-probe-test",
        gss_download_manifest=gss_manifest,
    )
    gss_binding = {
        "schema_version": "dcl-prs-gss-policy-task-binding-v1",
        "artifact_id": "dcl-prs-gss-policy-task-binding-test",
        "overall_status": "gss_policy_task_variables_bound",
        "required_fields_bound": True,
    }
    gss_smoke = {
        "schema_version": "dcl-prs-gss-policy-task-ingestion-smoke-v1",
        "artifact_id": "dcl-prs-gss-policy-task-smoke-test",
        "overall_status": "gss_policy_task_ingestion_smoke_ready",
        "valid_policy_response_count": 2610,
    }
    gss_real_effect = {
        "schema_version": "dcl-prs-gss-real-repair-effect-v1",
        "artifact_id": "dcl-prs-gss-real-repair-effect-test",
        "overall_status": "gss_real_repair_effect_validation_ready",
        "real_effect_promoted_count": 2,
    }
    generalization = {
        "schema_version": "dcl-prs-multi-dataset-generalization-matrix-v1",
        "artifact_id": "dcl-prs-multi-dataset-generalization-test",
        "overall_status": "multi_dataset_generalization_partial",
        "generalization_gate_closed": False,
    }

    gate = build_dcl_prs_gate_index(
        artifact_id="dcl-prs-gate-test",
        cross_domain_ingestion=cross_domain,
        mechanism_program=mechanism,
        failure_attribution=failure,
        dynamic_simulation=dynamic,
        mechanism_ablation_matrix=ablation,
        repair_repeat_acceptance_matrix=repeat_acceptance,
        cross_domain_task_slice_smoke=task_slice_smoke,
        product_cohort_report=product_report,
        mechanism_ablation_repeat_matrix=build_mechanism_ablation_repeat_matrix(
            artifact_id="dcl-prs-mechanism-ablation-repeat-test",
            mechanism_ablation_matrix=ablation,
        ),
        repair_effect_validation_matrix=build_repair_effect_validation_matrix(
            artifact_id="dcl-prs-repair-effect-test",
            repair_repeat_acceptance_matrix=repeat_acceptance,
        ),
        cross_domain_microdata_access_audit=build_cross_domain_microdata_access_audit(
            artifact_id="dcl-prs-cross-domain-microdata-test",
            cross_domain_task_slice_smoke=task_slice_smoke,
        ),
        product_runtime_manifest=build_product_runtime_manifest(
            artifact_id="dcl-prs-product-runtime-manifest-test",
            product_cohort_report=product_report,
        ),
        strong_baseline_matrix=build_dcl_prs_strong_baseline_matrix(
            artifact_id="dcl-prs-strong-baseline-test"
        ),
        gss_public_use_download_manifest=gss_manifest,
        official_public_use_file_probe=official_file_probe,
        gss_policy_task_binding=gss_binding,
        gss_policy_task_ingestion_smoke=gss_smoke,
        gss_real_repair_effect_validation=gss_real_effect,
        multi_dataset_generalization_matrix=generalization,
    )

    assert "multi_dataset_generalization_matrix_partial" in gate["completed_subgates"]
    assert "dcl-prs-multi-dataset-generalization-test" in gate["evidence_refs"]
    assert gate["required_next_gates"] == [
        "complete_eurobarometer_authenticated_download",
        "complete_multi_dataset_generalization_matrix",
        "run_product_runtime_validation",
        "improve_dcl_prs_until_strong_baseline_win",
    ]
    assert gate["ccf_a_gate"]["blocking_gaps"] == [
        "eurobarometer_microdata_download_missing",
        "strong_baseline_win_missing",
        "multi_dataset_generalization_incomplete",
    ]


def test_dcl_prs_gate_script_writes_artifact(tmp_path):
    output_dir = tmp_path / "dcl_prs_gate"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_gate_index.py",
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-gate-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-gate-test.json"),
        "overall_status": "dcl_prs_l0_started_but_claims_open",
    }
    assert (output_dir / "dcl-prs-gate-test.json").exists()
