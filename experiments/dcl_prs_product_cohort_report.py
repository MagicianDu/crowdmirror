from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.dcl_prs_dynamic_simulation import (  # noqa: E402
    build_dynamic_simulation_trace,
)
from experiments.dcl_prs_failure_attribution import (  # noqa: E402
    build_failure_attribution_index,
)
from experiments.dcl_prs_mechanism_program import (  # noqa: E402
    build_mechanism_program_index,
)


PRODUCT_REPORT_SCHEMA_VERSION = "dcl-prs-product-cohort-report-v1"
REPORT_SECTIONS = [
    "cohort_reaction_summary",
    "mechanism_explanation",
    "failure_attribution",
    "dynamic_trace",
    "uncertainty_and_claim_boundary",
]


def build_product_cohort_report(
    *,
    artifact_id: str,
    mechanism_program_index: dict[str, Any],
    failure_attribution_index: dict[str, Any],
    dynamic_simulation: dict[str, Any],
) -> dict[str, Any]:
    _validate_inputs(
        mechanism_program_index=mechanism_program_index,
        failure_attribution_index=failure_attribution_index,
        dynamic_simulation=dynamic_simulation,
    )
    final_step = dynamic_simulation["time_steps"][-1]
    report = {
        "schema_version": PRODUCT_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "product_cohort_report_evidence_ready",
        "report_sections": REPORT_SECTIONS,
        "section_count": len(REPORT_SECTIONS),
        "cohort_reaction_summary": {
            "policy_count": len(mechanism_program_index["policy_ids"]),
            "cohort_count": mechanism_program_index["program_count"],
            "final_aggregate_support": final_step["aggregate_support"],
            "final_polarization_index": final_step["polarization_index"],
            "summary_status": "bounded_l0_summary_ready",
        },
        "mechanism_explanation": {
            "mechanism_count": mechanism_program_index["mechanism_count"],
            "program_ids": mechanism_program_index["program_ids"],
            "explanation_status": "structured_mechanism_refs_ready",
        },
        "failure_attribution": {
            "attribution_count": failure_attribution_index["attribution_count"],
            "repair_candidate_count": failure_attribution_index[
                "repair_candidate_count"
            ],
            "attribution_status": "repair_candidates_recorded_not_applied",
        },
        "dynamic_trace": {
            "trace_artifact_id": dynamic_simulation["artifact_id"],
            "time_step_count": dynamic_simulation["time_step_count"],
            "trace_status": dynamic_simulation["overall_status"],
        },
        "uncertainty_disclosure": {
            "field_validated": False,
            "microdata_loaded_for_cross_domain_sources": False,
            "llm_runtime_validated": False,
            "customer_ready_claim": False,
        },
        "runtime_manifest": {
            "llm_calls_required": 0,
            "artifact_refs": [
                mechanism_program_index["artifact_id"],
                failure_attribution_index["artifact_id"],
                dynamic_simulation["artifact_id"],
            ],
            "runtime_status": "artifact_only_l0_report",
        },
        "product_claim_status": "demo_evidence_only",
        "ccf_a_claim_status": "not_claimable",
        "next_gate": "connect_report_to_product_runtime_manifest",
        "risk_flags": [
            "demo_evidence_only",
            "not_customer_field_validated",
            "no_live_llm_runtime_in_report",
            "uncertainty_disclosure_required",
        ],
        "claim_boundary": {
            "uses_test_split_for_current_claim": False,
            "summary": (
                "Product cohort report evidence proves section and manifest "
                "coverage only. It is not a customer-ready field validation."
            ),
        },
    }
    _assert_strict_json(report)
    return report


def write_product_cohort_report(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-product-cohort-report-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    mechanism = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-current-001"
    )
    failure = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-current-001"
    )
    dynamic = build_dynamic_simulation_trace(
        artifact_id="dcl-prs-dynamic-simulation-current-001",
        mechanism_program_index=mechanism,
    )
    report = build_product_cohort_report(
        artifact_id=artifact_id,
        mechanism_program_index=mechanism,
        failure_attribution_index=failure,
        dynamic_simulation=dynamic,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "report": report}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_product_cohort_report",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-product-cohort-report-current-001",
    )
    args = parser.parse_args()
    written = write_product_cohort_report(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "overall_status": written["report"]["overall_status"],
                "section_count": written["report"]["section_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_inputs(
    *,
    mechanism_program_index: dict[str, Any],
    failure_attribution_index: dict[str, Any],
    dynamic_simulation: dict[str, Any],
) -> None:
    if mechanism_program_index.get("schema_version") != (
        "dcl-prs-mechanism-program-index-v1"
    ):
        raise ValueError("mechanism_program_index has unsupported schema_version")
    if failure_attribution_index.get("schema_version") != (
        "dcl-prs-failure-attribution-index-v1"
    ):
        raise ValueError("failure_attribution_index has unsupported schema_version")
    if dynamic_simulation.get("schema_version") != (
        "dcl-prs-dynamic-simulation-trace-v1"
    ):
        raise ValueError("dynamic_simulation has unsupported schema_version")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
