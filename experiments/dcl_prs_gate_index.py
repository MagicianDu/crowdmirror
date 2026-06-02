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


GATE_SCHEMA_VERSION = "dcl-prs-gate-index-v1"


def build_dcl_prs_gate_index(
    *,
    artifact_id: str,
    cross_domain_ingestion: dict[str, Any] | None = None,
    mechanism_program: dict[str, Any] | None = None,
    failure_attribution: dict[str, Any] | None = None,
    dynamic_simulation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    completed_subgates = _completed_subgates(
        cross_domain_ingestion=cross_domain_ingestion,
        mechanism_program=mechanism_program,
        failure_attribution=failure_attribution,
        dynamic_simulation=dynamic_simulation,
    )
    required_next_gates = _required_next_gates(completed_subgates)
    evidence_refs = _evidence_refs(
        cross_domain_ingestion=cross_domain_ingestion,
        mechanism_program=mechanism_program,
        failure_attribution=failure_attribution,
        dynamic_simulation=dynamic_simulation,
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
            "blocking_gaps": [
                "mechanism_ablation_missing",
                "repair_repeat_acceptance_missing",
                "cross_domain_smoke_missing",
                "strong_baseline_win_missing",
                "multi_dataset_generalization_missing",
            ],
        },
        "product_gate": {
            "status": "open",
            "blocking_gaps": [
                "cohort_report_evidence_missing",
                "runtime_manifest_missing",
                "customer_field_validation_missing",
                "uncertainty_disclosure_missing",
            ],
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
    mechanism_program = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-current-001"
    )
    gate = build_dcl_prs_gate_index(
        artifact_id=artifact_id,
        cross_domain_ingestion=build_cross_domain_ingestion_index(
            artifact_id="dcl-prs-cross-domain-ingestion-current-001"
        ),
        mechanism_program=mechanism_program,
        failure_attribution=build_failure_attribution_index(
            artifact_id="dcl-prs-failure-attribution-current-001"
        ),
        dynamic_simulation=build_dynamic_simulation_trace(
            artifact_id="dcl-prs-dynamic-simulation-current-001",
            mechanism_program_index=mechanism_program,
        ),
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
    return completed


def _required_next_gates(completed_subgates: list[str]) -> list[str]:
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


def _evidence_refs(
    *,
    cross_domain_ingestion: dict[str, Any] | None,
    mechanism_program: dict[str, Any] | None,
    failure_attribution: dict[str, Any] | None,
    dynamic_simulation: dict[str, Any] | None,
) -> list[str]:
    refs = []
    for artifact in (
        cross_domain_ingestion,
        mechanism_program,
        failure_attribution,
        dynamic_simulation,
    ):
        if artifact is not None and isinstance(artifact.get("artifact_id"), str):
            refs.append(artifact["artifact_id"])
    return refs


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
