from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.dcl_prs_public_dataset_ingestion import (
    build_cross_domain_ingestion_index,
)  # noqa: E402
from experiments.dcl_prs_mechanism_program import (  # noqa: E402
    build_mechanism_program_index,
)
from experiments.dcl_prs_failure_attribution import (  # noqa: E402
    build_failure_attribution_index,
)
from experiments.dcl_prs_dynamic_simulation import (  # noqa: E402
    build_dynamic_simulation_trace,
)
from experiments.dcl_prs_mechanism_ablation_matrix import (  # noqa: E402
    build_mechanism_ablation_matrix,
)
from experiments.dcl_prs_repair_repeat_acceptance_matrix import (  # noqa: E402
    build_repair_repeat_acceptance_matrix,
)
from experiments.dcl_prs_cross_domain_task_slice_smoke import (  # noqa: E402
    build_cross_domain_task_slice_smoke,
)
from experiments.dcl_prs_product_cohort_report import (  # noqa: E402
    build_product_cohort_report,
)
from experiments.dcl_prs_mechanism_ablation_repeat_matrix import (  # noqa: E402
    build_mechanism_ablation_repeat_matrix,
)
from experiments.dcl_prs_repair_effect_validation_matrix import (  # noqa: E402
    build_repair_effect_validation_matrix,
)
from experiments.dcl_prs_cross_domain_microdata_slices import (  # noqa: E402
    build_cross_domain_microdata_access_audit,
)
from experiments.dcl_prs_product_runtime_manifest import (  # noqa: E402
    build_product_runtime_manifest,
)
from experiments.dcl_prs_strong_baseline_matrix import (  # noqa: E402
    build_dcl_prs_strong_baseline_matrix,
)
from experiments.dcl_prs_strong_baseline_decision_matrix import (  # noqa: E402
    DEFAULT_LCDU_STRONG_BASELINE_MATRIX_PATHS,
    build_dcl_prs_strong_baseline_decision_matrix,
)
from experiments.dcl_prs_runtime_strong_baseline_trial import (  # noqa: E402
    build_dcl_prs_runtime_strong_baseline_trial,
)
from experiments.dcl_prs_official_public_use_file_probe import (  # noqa: E402
    build_official_public_use_file_probe,
)


GATE_SCHEMA_VERSION = "dcl-prs-gate-index-v1"
DEFAULT_GSS_PUBLIC_USE_DOWNLOAD_MANIFEST_PATH = Path(
    "experiments/results/dcl_prs_gss_public_use_download/"
    "dcl-prs-gss-public-use-download-current-001.json"
)
DEFAULT_OFFICIAL_PUBLIC_USE_FILE_PROBE_PATH = Path(
    "experiments/results/dcl_prs_official_public_use_file_probe/"
    "dcl-prs-official-public-use-file-probe-current-001.json"
)
DEFAULT_GSS_POLICY_TASK_BINDING_PATH = Path(
    "experiments/results/dcl_prs_gss_policy_task_binding/"
    "dcl-prs-gss-policy-task-binding-current-001.json"
)
DEFAULT_GSS_POLICY_TASK_INGESTION_SMOKE_PATH = Path(
    "experiments/results/dcl_prs_gss_policy_task_ingestion_smoke/"
    "dcl-prs-gss-policy-task-smoke-current-001.json"
)
DEFAULT_GSS_REAL_REPAIR_EFFECT_VALIDATION_PATH = Path(
    "experiments/results/dcl_prs_gss_real_repair_effect_validation/"
    "dcl-prs-gss-real-repair-effect-current-001.json"
)
DEFAULT_MULTI_DATASET_GENERALIZATION_MATRIX_PATH = Path(
    "experiments/results/dcl_prs_multi_dataset_generalization_matrix/"
    "dcl-prs-multi-dataset-generalization-current-001.json"
)
DEFAULT_RUNTIME_STRONG_BASELINE_TRIAL_PATH = Path(
    "experiments/results/dcl_prs_runtime_strong_baseline_trial/"
    "dcl-prs-runtime-strong-baseline-trial-current-001.json"
)


def build_dcl_prs_gate_index(
    *,
    artifact_id: str,
    cross_domain_ingestion: dict[str, Any] | None = None,
    mechanism_program: dict[str, Any] | None = None,
    failure_attribution: dict[str, Any] | None = None,
    dynamic_simulation: dict[str, Any] | None = None,
    mechanism_ablation_matrix: dict[str, Any] | None = None,
    repair_repeat_acceptance_matrix: dict[str, Any] | None = None,
    cross_domain_task_slice_smoke: dict[str, Any] | None = None,
    product_cohort_report: dict[str, Any] | None = None,
    mechanism_ablation_repeat_matrix: dict[str, Any] | None = None,
    repair_effect_validation_matrix: dict[str, Any] | None = None,
    cross_domain_microdata_access_audit: dict[str, Any] | None = None,
    product_runtime_manifest: dict[str, Any] | None = None,
    strong_baseline_matrix: dict[str, Any] | None = None,
    gss_public_use_download_manifest: dict[str, Any] | None = None,
    official_public_use_file_probe: dict[str, Any] | None = None,
    gss_policy_task_binding: dict[str, Any] | None = None,
    gss_policy_task_ingestion_smoke: dict[str, Any] | None = None,
    gss_real_repair_effect_validation: dict[str, Any] | None = None,
    multi_dataset_generalization_matrix: dict[str, Any] | None = None,
    runtime_strong_baseline_trial: dict[str, Any] | None = None,
    strong_baseline_decision_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    completed_subgates = _completed_subgates(
        cross_domain_ingestion=cross_domain_ingestion,
        mechanism_program=mechanism_program,
        failure_attribution=failure_attribution,
        dynamic_simulation=dynamic_simulation,
        mechanism_ablation_matrix=mechanism_ablation_matrix,
        repair_repeat_acceptance_matrix=repair_repeat_acceptance_matrix,
        cross_domain_task_slice_smoke=cross_domain_task_slice_smoke,
        product_cohort_report=product_cohort_report,
        mechanism_ablation_repeat_matrix=mechanism_ablation_repeat_matrix,
        repair_effect_validation_matrix=repair_effect_validation_matrix,
        cross_domain_microdata_access_audit=cross_domain_microdata_access_audit,
        product_runtime_manifest=product_runtime_manifest,
        strong_baseline_matrix=strong_baseline_matrix,
        gss_public_use_download_manifest=gss_public_use_download_manifest,
        official_public_use_file_probe=official_public_use_file_probe,
        gss_policy_task_binding=gss_policy_task_binding,
        gss_policy_task_ingestion_smoke=gss_policy_task_ingestion_smoke,
        gss_real_repair_effect_validation=gss_real_repair_effect_validation,
        multi_dataset_generalization_matrix=multi_dataset_generalization_matrix,
        runtime_strong_baseline_trial=runtime_strong_baseline_trial,
        strong_baseline_decision_matrix=strong_baseline_decision_matrix,
    )
    required_next_gates = _required_next_gates(completed_subgates)
    evidence_refs = _evidence_refs(
        cross_domain_ingestion=cross_domain_ingestion,
        mechanism_program=mechanism_program,
        failure_attribution=failure_attribution,
        dynamic_simulation=dynamic_simulation,
        mechanism_ablation_matrix=mechanism_ablation_matrix,
        repair_repeat_acceptance_matrix=repair_repeat_acceptance_matrix,
        cross_domain_task_slice_smoke=cross_domain_task_slice_smoke,
        product_cohort_report=product_cohort_report,
        mechanism_ablation_repeat_matrix=mechanism_ablation_repeat_matrix,
        repair_effect_validation_matrix=repair_effect_validation_matrix,
        cross_domain_microdata_access_audit=cross_domain_microdata_access_audit,
        product_runtime_manifest=product_runtime_manifest,
        strong_baseline_matrix=strong_baseline_matrix,
        gss_public_use_download_manifest=gss_public_use_download_manifest,
        official_public_use_file_probe=official_public_use_file_probe,
        gss_policy_task_binding=gss_policy_task_binding,
        gss_policy_task_ingestion_smoke=gss_policy_task_ingestion_smoke,
        gss_real_repair_effect_validation=gss_real_repair_effect_validation,
        multi_dataset_generalization_matrix=multi_dataset_generalization_matrix,
        runtime_strong_baseline_trial=runtime_strong_baseline_trial,
        strong_baseline_decision_matrix=strong_baseline_decision_matrix,
    )
    gate = {
        "schema_version": GATE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "dcl_prs_l0_started_but_claims_open",
        "completed_subgates": completed_subgates,
        "required_next_gates": required_next_gates,
        "evidence_refs": evidence_refs,
        "ccf_a_gate": {
            "status": "open",
            "blocking_gaps": _ccf_a_blocking_gaps(completed_subgates),
        },
        "product_gate": {
            "status": "open",
            "blocking_gaps": _product_blocking_gaps(completed_subgates),
        },
        "risk_flags": [
            "dcl_prs_l0_only",
            "not_ccf_a_claimable",
            "not_product_runtime_ready",
            "lcdU_retained_as_calibration_and_audit_layer",
        ],
        "claim_boundary": (
            "DCL-PRS L0 gate records whether first-stage artifacts exist. It "
            "does not close CCF-A or product-readiness claims."
        ),
    }
    _assert_strict_json(gate)
    return gate


def write_dcl_prs_gate_index(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-gate-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    cross_domain_ingestion = build_cross_domain_ingestion_index(
        artifact_id="dcl-prs-cross-domain-ingestion-current-001"
    )
    mechanism_program = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-current-001"
    )
    failure_attribution = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-current-001"
    )
    dynamic_simulation = build_dynamic_simulation_trace(
        artifact_id="dcl-prs-dynamic-simulation-current-001",
        mechanism_program_index=mechanism_program,
    )
    mechanism_ablation = build_mechanism_ablation_matrix(
        artifact_id="dcl-prs-mechanism-ablation-current-001",
        mechanism_program_index=mechanism_program,
    )
    repair_repeat = build_repair_repeat_acceptance_matrix(
        artifact_id="dcl-prs-repair-repeat-acceptance-current-001",
        failure_attribution_index=failure_attribution,
    )
    task_slice_smoke = build_cross_domain_task_slice_smoke(
        artifact_id="dcl-prs-cross-domain-task-slice-smoke-current-001",
        cross_domain_ingestion=cross_domain_ingestion,
    )
    product_report = build_product_cohort_report(
        artifact_id="dcl-prs-product-cohort-report-current-001",
        mechanism_program_index=mechanism_program,
        failure_attribution_index=failure_attribution,
        dynamic_simulation=dynamic_simulation,
    )
    gss_manifest = _load_json_if_exists(DEFAULT_GSS_PUBLIC_USE_DOWNLOAD_MANIFEST_PATH)
    official_file_probe = _load_json_if_exists(
        DEFAULT_OFFICIAL_PUBLIC_USE_FILE_PROBE_PATH
    )
    if official_file_probe is None and gss_manifest is not None:
        official_file_probe = build_official_public_use_file_probe(
            artifact_id="dcl-prs-official-public-use-file-probe-current-001",
            gss_download_manifest=gss_manifest,
        )
    gss_policy_task_binding = _load_json_if_exists(
        DEFAULT_GSS_POLICY_TASK_BINDING_PATH
    )
    gss_policy_task_ingestion_smoke = _load_json_if_exists(
        DEFAULT_GSS_POLICY_TASK_INGESTION_SMOKE_PATH
    )
    gss_real_repair_effect_validation = _load_json_if_exists(
        DEFAULT_GSS_REAL_REPAIR_EFFECT_VALIDATION_PATH
    )
    multi_dataset_generalization_matrix = _load_json_if_exists(
        DEFAULT_MULTI_DATASET_GENERALIZATION_MATRIX_PATH
    )
    runtime_strong_baseline_trial = _load_json_if_exists(
        DEFAULT_RUNTIME_STRONG_BASELINE_TRIAL_PATH
    ) or build_dcl_prs_runtime_strong_baseline_trial(
        artifact_id="dcl-prs-runtime-strong-baseline-trial-current-001",
        benchmark_records=[],
    )
    strong_baseline_matrix = build_dcl_prs_strong_baseline_matrix(
        artifact_id="dcl-prs-strong-baseline-current-001",
        gss_real_repair_effect_validation=gss_real_repair_effect_validation,
        multi_dataset_generalization_matrix=multi_dataset_generalization_matrix,
    )
    lcdU_strong_baseline_matrices = [
        matrix
        for path in DEFAULT_LCDU_STRONG_BASELINE_MATRIX_PATHS
        if (matrix := _load_json_if_exists(path)) is not None
    ]
    strong_baseline_decision_matrix = (
        build_dcl_prs_strong_baseline_decision_matrix(
            artifact_id="dcl-prs-strong-baseline-decision-current-001",
            dcl_prs_strong_baseline_matrix=strong_baseline_matrix,
            gss_real_repair_effect_validation=gss_real_repair_effect_validation,
            multi_dataset_generalization_matrix=multi_dataset_generalization_matrix,
            runtime_strong_baseline_trial=runtime_strong_baseline_trial,
            lcdU_strong_baseline_matrices=lcdU_strong_baseline_matrices,
        )
    )
    gate = build_dcl_prs_gate_index(
        artifact_id=artifact_id,
        cross_domain_ingestion=cross_domain_ingestion,
        mechanism_program=mechanism_program,
        failure_attribution=failure_attribution,
        dynamic_simulation=dynamic_simulation,
        mechanism_ablation_matrix=mechanism_ablation,
        repair_repeat_acceptance_matrix=repair_repeat,
        cross_domain_task_slice_smoke=task_slice_smoke,
        product_cohort_report=product_report,
        mechanism_ablation_repeat_matrix=build_mechanism_ablation_repeat_matrix(
            artifact_id="dcl-prs-mechanism-ablation-repeat-current-001",
            mechanism_ablation_matrix=mechanism_ablation,
        ),
        repair_effect_validation_matrix=build_repair_effect_validation_matrix(
            artifact_id="dcl-prs-repair-effect-validation-current-001",
            repair_repeat_acceptance_matrix=repair_repeat,
        ),
        cross_domain_microdata_access_audit=build_cross_domain_microdata_access_audit(
            artifact_id="dcl-prs-cross-domain-microdata-current-001",
            cross_domain_task_slice_smoke=task_slice_smoke,
        ),
        product_runtime_manifest=build_product_runtime_manifest(
            artifact_id="dcl-prs-product-runtime-manifest-current-001",
            product_cohort_report=product_report,
        ),
        strong_baseline_matrix=strong_baseline_matrix,
        gss_public_use_download_manifest=gss_manifest,
        official_public_use_file_probe=official_file_probe,
        gss_policy_task_binding=gss_policy_task_binding,
        gss_policy_task_ingestion_smoke=gss_policy_task_ingestion_smoke,
        gss_real_repair_effect_validation=gss_real_repair_effect_validation,
        multi_dataset_generalization_matrix=multi_dataset_generalization_matrix,
        runtime_strong_baseline_trial=runtime_strong_baseline_trial,
        strong_baseline_decision_matrix=strong_baseline_decision_matrix,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(gate, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "index": gate}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="experiments/results/dcl_prs_gate_index")
    parser.add_argument("--artifact-id", default="dcl-prs-gate-current-001")
    args = parser.parse_args()

    written = write_dcl_prs_gate_index(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "overall_status": written["index"]["overall_status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _completed_subgates(
    *,
    cross_domain_ingestion: dict[str, Any] | None,
    mechanism_program: dict[str, Any] | None,
    failure_attribution: dict[str, Any] | None,
    dynamic_simulation: dict[str, Any] | None,
    mechanism_ablation_matrix: dict[str, Any] | None,
    repair_repeat_acceptance_matrix: dict[str, Any] | None,
    cross_domain_task_slice_smoke: dict[str, Any] | None,
    product_cohort_report: dict[str, Any] | None,
    mechanism_ablation_repeat_matrix: dict[str, Any] | None,
    repair_effect_validation_matrix: dict[str, Any] | None,
    cross_domain_microdata_access_audit: dict[str, Any] | None,
    product_runtime_manifest: dict[str, Any] | None,
    strong_baseline_matrix: dict[str, Any] | None,
    gss_public_use_download_manifest: dict[str, Any] | None,
    official_public_use_file_probe: dict[str, Any] | None,
    gss_policy_task_binding: dict[str, Any] | None,
    gss_policy_task_ingestion_smoke: dict[str, Any] | None,
    gss_real_repair_effect_validation: dict[str, Any] | None,
    multi_dataset_generalization_matrix: dict[str, Any] | None,
    runtime_strong_baseline_trial: dict[str, Any] | None,
    strong_baseline_decision_matrix: dict[str, Any] | None,
) -> list[str]:
    completed = []
    if _is_status(
        cross_domain_ingestion,
        schema_version="dcl-prs-cross-domain-ingestion-index-v1",
        status="cross_domain_task_slices_ready_for_smoke",
    ):
        completed.append("cross_domain_public_dataset_ingestion_ready")
    if _is_status(
        mechanism_program,
        schema_version="dcl-prs-mechanism-program-index-v1",
        status="mechanism_programs_ready_for_l0_gate",
    ):
        completed.append("mechanism_program_l0_ready")
    if _is_status(
        failure_attribution,
        schema_version="dcl-prs-failure-attribution-index-v1",
        status="failure_attribution_ready_for_l0_gate",
    ):
        completed.append("failure_attribution_l0_ready")
    if _is_status(
        dynamic_simulation,
        schema_version="dcl-prs-dynamic-simulation-trace-v1",
        status="dynamic_trace_ready_for_l0_gate",
    ):
        completed.append("dynamic_simulation_l0_ready")
    if _is_status(
        mechanism_ablation_matrix,
        schema_version="dcl-prs-mechanism-ablation-matrix-v1",
        status="mechanism_ablation_matrix_ready",
    ):
        completed.append("mechanism_ablation_matrix_ready")
    if _is_status(
        repair_repeat_acceptance_matrix,
        schema_version="dcl-prs-repair-repeat-acceptance-matrix-v1",
        status="repair_repeat_acceptance_matrix_ready",
    ):
        completed.append("repair_repeat_acceptance_matrix_ready")
    if _is_status(
        cross_domain_task_slice_smoke,
        schema_version="dcl-prs-cross-domain-task-slice-smoke-v1",
        status="cross_domain_task_slice_smoke_ready",
    ):
        completed.append("cross_domain_task_slice_smoke_ready")
    if _is_status(
        product_cohort_report,
        schema_version="dcl-prs-product-cohort-report-v1",
        status="product_cohort_report_evidence_ready",
    ):
        completed.append("product_cohort_report_evidence_ready")
    if _is_status(
        mechanism_ablation_repeat_matrix,
        schema_version="dcl-prs-mechanism-ablation-repeat-matrix-v1",
        status="mechanism_ablation_repeat_matrix_ready",
    ):
        completed.append("mechanism_ablation_repeat_matrix_ready")
    if _is_status(
        repair_effect_validation_matrix,
        schema_version="dcl-prs-repair-effect-validation-matrix-v1",
        status="repair_effect_validation_matrix_ready",
    ):
        completed.append("repair_effect_validation_matrix_ready")
    if _is_status(
        cross_domain_microdata_access_audit,
        schema_version="dcl-prs-cross-domain-microdata-slices-v1",
        status="cross_domain_microdata_access_audit_ready",
    ):
        completed.append("cross_domain_microdata_access_audit_ready")
    if _is_status(
        product_runtime_manifest,
        schema_version="dcl-prs-product-runtime-manifest-v1",
        status="product_runtime_manifest_connection_ready",
    ):
        completed.append("product_runtime_manifest_connection_ready")
    if _is_status(
        strong_baseline_matrix,
        schema_version="dcl-prs-strong-baseline-matrix-v1",
        status="strong_baseline_dcl_prs_not_leading",
    ) or _is_status(
        strong_baseline_matrix,
        schema_version="dcl-prs-strong-baseline-matrix-v1",
        status="strong_baseline_dcl_prs_leads",
    ):
        completed.append("strong_baseline_matrix_ready")
    if _is_status(
        gss_public_use_download_manifest,
        schema_version="dcl-prs-gss-public-use-download-v1",
        status="gss_public_use_download_verified",
    ):
        completed.append("gss_public_use_download_verified")
    if _is_status(
        official_public_use_file_probe,
        schema_version="dcl-prs-official-public-use-file-probe-v1",
        status="official_public_use_file_probe_partial",
    ):
        completed.append("official_public_use_file_probe_partial")
    if _is_status(
        gss_policy_task_binding,
        schema_version="dcl-prs-gss-policy-task-binding-v1",
        status="gss_policy_task_variables_bound",
    ) and gss_policy_task_binding.get("required_fields_bound") is True:
        completed.append("gss_policy_task_variables_bound")
    if _is_status(
        gss_policy_task_ingestion_smoke,
        schema_version="dcl-prs-gss-policy-task-ingestion-smoke-v1",
        status="gss_policy_task_ingestion_smoke_ready",
    ):
        completed.append("gss_policy_task_ingestion_smoke_ready")
    if _is_status(
        gss_real_repair_effect_validation,
        schema_version="dcl-prs-gss-real-repair-effect-v1",
        status="gss_real_repair_effect_validation_ready",
    ):
        completed.append("gss_real_repair_effect_validation_ready")
    if _is_status(
        multi_dataset_generalization_matrix,
        schema_version="dcl-prs-multi-dataset-generalization-matrix-v1",
        status="multi_dataset_generalization_partial",
    ) and multi_dataset_generalization_matrix.get("generalization_gate_closed") is False:
        completed.append("multi_dataset_generalization_matrix_partial")
    if _is_status(
        runtime_strong_baseline_trial,
        schema_version="dcl-prs-runtime-strong-baseline-trial-v1",
        status="runtime_strong_baseline_trial_blocked",
    ):
        completed.append("runtime_strong_baseline_trial_ready")
        completed.append("runtime_strong_baseline_trial_blocked")
    elif _is_status(
        runtime_strong_baseline_trial,
        schema_version="dcl-prs-runtime-strong-baseline-trial-v1",
        status="runtime_strong_baseline_trial_dcl_prs_not_leading",
    ):
        completed.append("runtime_strong_baseline_trial_ready")
        completed.append("runtime_strong_baseline_trial_not_leading")
    elif _is_status(
        runtime_strong_baseline_trial,
        schema_version="dcl-prs-runtime-strong-baseline-trial-v1",
        status="runtime_strong_baseline_trial_dcl_prs_leads",
    ):
        completed.append("runtime_strong_baseline_trial_ready")
        completed.append("runtime_strong_baseline_trial_leads")
    if _is_status(
        strong_baseline_decision_matrix,
        schema_version="dcl-prs-strong-baseline-decision-matrix-v1",
        status="decision_boundary_stoploss_recommended",
    ):
        completed.append("strong_baseline_decision_ready")
        completed.append("strong_baseline_decision_stoploss_recommended")
    elif _is_status(
        strong_baseline_decision_matrix,
        schema_version="dcl-prs-strong-baseline-decision-matrix-v1",
        status="decision_boundary_research_candidate",
    ):
        completed.append("strong_baseline_decision_ready")
        completed.append("strong_baseline_decision_research_candidate")
    return completed


def _required_next_gates(completed_subgates: list[str]) -> list[str]:
    completed = set(completed_subgates)
    if "strong_baseline_decision_research_candidate" in completed:
        strong_baseline_next_gate = "promote_to_full_paper_gate_audit"
    elif "strong_baseline_decision_stoploss_recommended" in completed:
        strong_baseline_next_gate = (
            "run_dcl_prs_runtime_strong_baseline_trial_or_retire_algorithm_main_claim"
        )
    else:
        strong_baseline_next_gate = "improve_dcl_prs_until_strong_baseline_win"
    if {
        "mechanism_ablation_repeat_matrix_ready",
        "repair_effect_validation_matrix_ready",
        "cross_domain_microdata_access_audit_ready",
        "product_runtime_manifest_connection_ready",
        "strong_baseline_matrix_ready",
    }.issubset(completed):
        if "official_public_use_file_probe_partial" in completed:
            gates = [
                "complete_eurobarometer_authenticated_download",
            ]
            if "gss_policy_task_ingestion_smoke_ready" in completed:
                pass
            elif "gss_policy_task_variables_bound" in completed:
                gates.append("run_gss_policy_task_ingestion_smoke")
            elif "gss_public_use_download_verified" in completed:
                gates.append("bind_gss_public_use_variables_to_policy_tasks")
            else:
                gates.append("download_gss_public_use_file")
            gates.extend(
                [
                    (
                        "complete_multi_dataset_generalization_matrix"
                        if "multi_dataset_generalization_matrix_partial" in completed
                        else "run_multi_dataset_generalization_matrix"
                    ),
                    "run_product_runtime_validation",
                    strong_baseline_next_gate,
                ]
            )
            if "gss_real_repair_effect_validation_ready" not in completed:
                gates.insert(
                    len(gates) - 3,
                    "run_real_repair_effect_validation",
                )
            return gates
        return [
            "download_official_cross_domain_public_use_files",
            "run_real_repair_effect_validation",
            "run_multi_dataset_generalization_matrix",
            "run_product_runtime_validation",
            strong_baseline_next_gate,
        ]

    if {
        "mechanism_ablation_matrix_ready",
        "repair_repeat_acceptance_matrix_ready",
        "cross_domain_task_slice_smoke_ready",
        "product_cohort_report_evidence_ready",
    }.issubset(completed):
        return [
            "run_mechanism_ablation_repeat_matrix",
            "run_repair_effect_validation_matrix",
            "load_cross_domain_public_microdata_slices",
            "connect_report_to_product_runtime_manifest",
            "run_strong_baseline_matrix",
        ]

    if {
        "cross_domain_public_dataset_ingestion_ready",
        "mechanism_program_l0_ready",
        "failure_attribution_l0_ready",
        "dynamic_simulation_l0_ready",
    }.issubset(set(completed_subgates)):
        return [
            "run_mechanism_ablation_matrix",
            "run_repair_repeat_acceptance_matrix",
            "run_cross_domain_task_slice_smoke",
            "run_product_cohort_report_evidence",
        ]

    required = []
    if "cross_domain_public_dataset_ingestion_ready" not in completed_subgates:
        required.append("run_cross_domain_public_dataset_ingestion_l0")
    if "mechanism_program_l0_ready" not in completed_subgates:
        required.append("run_mechanism_program_l0")
    if "failure_attribution_l0_ready" not in completed_subgates:
        required.append("run_failure_attribution_l0")
    if "dynamic_simulation_l0_ready" not in completed_subgates:
        required.append("run_dynamic_simulation_l0")
    return required


def _ccf_a_blocking_gaps(completed_subgates: list[str]) -> list[str]:
    completed = set(completed_subgates)
    gaps = []
    if "cross_domain_task_slice_smoke_ready" not in completed:
        gaps.append("cross_domain_smoke_missing")
    elif "cross_domain_microdata_access_audit_ready" not in completed:
        gaps.append("cross_domain_microdata_missing")
    elif "official_public_use_file_probe_partial" in completed:
        gaps.append("eurobarometer_microdata_download_missing")
        if "gss_policy_task_ingestion_smoke_ready" in completed:
            pass
        elif "gss_policy_task_variables_bound" in completed:
            gaps.append("gss_ingestion_smoke_missing")
        elif "gss_public_use_download_verified" in completed:
            gaps.append("gss_variable_binding_missing")
        else:
            gaps.append("gss_public_use_download_missing")
    else:
        gaps.append("cross_domain_microdata_download_missing")
    if "mechanism_ablation_matrix_ready" not in completed:
        gaps.append("mechanism_ablation_missing")
    elif "mechanism_ablation_repeat_matrix_ready" not in completed:
        gaps.append("mechanism_ablation_repeat_missing")
    else:
        pass
    if "repair_repeat_acceptance_matrix_ready" not in completed:
        gaps.append("repair_repeat_acceptance_missing")
    elif "repair_effect_validation_matrix_ready" not in completed:
        gaps.append("repair_effect_validation_missing")
    elif "gss_real_repair_effect_validation_ready" in completed:
        pass
    else:
        gaps.append("real_effect_validation_missing")
    gaps.append("strong_baseline_win_missing")
    if "runtime_strong_baseline_trial_blocked" in completed:
        gaps.append("dcl_prs_runtime_prediction_missing")
    elif "runtime_strong_baseline_trial_not_leading" in completed:
        gaps.append("dcl_prs_runtime_strong_baseline_trial_not_leading")
    if "strong_baseline_decision_stoploss_recommended" in completed:
        gaps.append("dcl_prs_algorithm_main_claim_stoploss_recommended")
    gaps.append(
        "multi_dataset_generalization_incomplete"
        if "multi_dataset_generalization_matrix_partial" in completed
        else "multi_dataset_generalization_missing"
    )
    return gaps


def _product_blocking_gaps(completed_subgates: list[str]) -> list[str]:
    completed = set(completed_subgates)
    gaps = []
    if "product_cohort_report_evidence_ready" not in completed:
        gaps.append("cohort_report_evidence_missing")
    elif "product_runtime_manifest_connection_ready" not in completed:
        gaps.append("product_runtime_manifest_connection_missing")
    else:
        pass
    gaps.extend(
        [
            "customer_field_validation_missing",
            "product_runtime_validation_missing",
        ]
    )
    return gaps


def _evidence_refs(
    *,
    cross_domain_ingestion: dict[str, Any] | None,
    mechanism_program: dict[str, Any] | None,
    failure_attribution: dict[str, Any] | None,
    dynamic_simulation: dict[str, Any] | None,
    mechanism_ablation_matrix: dict[str, Any] | None,
    repair_repeat_acceptance_matrix: dict[str, Any] | None,
    cross_domain_task_slice_smoke: dict[str, Any] | None,
    product_cohort_report: dict[str, Any] | None,
    mechanism_ablation_repeat_matrix: dict[str, Any] | None,
    repair_effect_validation_matrix: dict[str, Any] | None,
    cross_domain_microdata_access_audit: dict[str, Any] | None,
    product_runtime_manifest: dict[str, Any] | None,
    strong_baseline_matrix: dict[str, Any] | None,
    gss_public_use_download_manifest: dict[str, Any] | None,
    official_public_use_file_probe: dict[str, Any] | None,
    gss_policy_task_binding: dict[str, Any] | None,
    gss_policy_task_ingestion_smoke: dict[str, Any] | None,
    gss_real_repair_effect_validation: dict[str, Any] | None,
    multi_dataset_generalization_matrix: dict[str, Any] | None,
    runtime_strong_baseline_trial: dict[str, Any] | None,
    strong_baseline_decision_matrix: dict[str, Any] | None,
) -> list[str]:
    refs = []
    for artifact in (
        cross_domain_ingestion,
        mechanism_program,
        failure_attribution,
        dynamic_simulation,
        mechanism_ablation_matrix,
        repair_repeat_acceptance_matrix,
        cross_domain_task_slice_smoke,
        product_cohort_report,
        mechanism_ablation_repeat_matrix,
        repair_effect_validation_matrix,
        cross_domain_microdata_access_audit,
        product_runtime_manifest,
        strong_baseline_matrix,
        gss_public_use_download_manifest,
        official_public_use_file_probe,
        gss_policy_task_binding,
        gss_policy_task_ingestion_smoke,
        gss_real_repair_effect_validation,
        multi_dataset_generalization_matrix,
        runtime_strong_baseline_trial,
        strong_baseline_decision_matrix,
    ):
        if artifact is not None and isinstance(artifact.get("artifact_id"), str):
            refs.append(artifact["artifact_id"])
    return refs


def _load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _is_status(
    artifact: dict[str, Any] | None,
    *,
    schema_version: str,
    status: str,
) -> bool:
    return (
        artifact is not None
        and artifact.get("schema_version") == schema_version
        and artifact.get("overall_status") == status
    )


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
