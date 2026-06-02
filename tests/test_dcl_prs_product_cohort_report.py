import json
import subprocess
import sys

from experiments.dcl_prs_dynamic_simulation import build_dynamic_simulation_trace
from experiments.dcl_prs_failure_attribution import build_failure_attribution_index
from experiments.dcl_prs_mechanism_program import build_mechanism_program_index
from experiments.dcl_prs_product_cohort_report import build_product_cohort_report


def test_product_cohort_report_contains_mechanism_repair_trace_and_uncertainty():
    mechanism = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-test"
    )
    report = build_product_cohort_report(
        artifact_id="dcl-prs-product-cohort-report-test",
        mechanism_program_index=mechanism,
        failure_attribution_index=build_failure_attribution_index(
            artifact_id="dcl-prs-failure-attribution-test"
        ),
        dynamic_simulation=build_dynamic_simulation_trace(
            artifact_id="dcl-prs-dynamic-simulation-test",
            mechanism_program_index=mechanism,
        ),
    )

    assert report["schema_version"] == "dcl-prs-product-cohort-report-v1"
    assert report["overall_status"] == "product_cohort_report_evidence_ready"
    assert report["report_sections"] == [
        "cohort_reaction_summary",
        "mechanism_explanation",
        "failure_attribution",
        "dynamic_trace",
        "uncertainty_and_claim_boundary",
    ]
    assert report["product_claim_status"] == "demo_evidence_only"
    assert report["ccf_a_claim_status"] == "not_claimable"
    json.dumps(report, allow_nan=False)


def test_product_cohort_report_has_manifest_and_evidence_refs():
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
    report = build_product_cohort_report(
        artifact_id="dcl-prs-product-cohort-report-test",
        mechanism_program_index=mechanism,
        failure_attribution_index=failure,
        dynamic_simulation=dynamic,
    )

    assert report["runtime_manifest"]["llm_calls_required"] == 0
    assert report["runtime_manifest"]["artifact_refs"] == [
        mechanism["artifact_id"],
        failure["artifact_id"],
        dynamic["artifact_id"],
    ]
    assert report["uncertainty_disclosure"]["field_validated"] is False


def test_product_cohort_report_script_writes_artifact(tmp_path):
    output_dir = tmp_path / "dcl_prs_product_cohort_report"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_product_cohort_report.py",
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-product-cohort-report-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-product-cohort-report-test.json"),
        "overall_status": "product_cohort_report_evidence_ready",
        "section_count": 5,
    }
    assert (output_dir / "dcl-prs-product-cohort-report-test.json").exists()
