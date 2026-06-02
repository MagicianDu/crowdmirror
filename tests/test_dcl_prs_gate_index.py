import json
import subprocess
import sys

from experiments.dcl_prs_gate_index import build_dcl_prs_gate_index
from experiments.dcl_prs_cross_domain_task_slice_smoke import (
    build_cross_domain_task_slice_smoke,
)
from experiments.dcl_prs_dynamic_simulation import build_dynamic_simulation_trace
from experiments.dcl_prs_failure_attribution import build_failure_attribution_index
from experiments.dcl_prs_mechanism_ablation_matrix import (
    build_mechanism_ablation_matrix,
)
from experiments.dcl_prs_mechanism_program import build_mechanism_program_index
from experiments.dcl_prs_product_cohort_report import build_product_cohort_report
from experiments.dcl_prs_public_dataset_ingestion import (
    build_cross_domain_ingestion_index,
)
from experiments.dcl_prs_repair_repeat_acceptance_matrix import (
    build_repair_repeat_acceptance_matrix,
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
