import json
import subprocess
import sys

from experiments.dcl_prs_dynamic_simulation import build_dynamic_simulation_trace
from experiments.dcl_prs_failure_attribution import build_failure_attribution_index
from experiments.dcl_prs_mechanism_program import build_mechanism_program_index
from experiments.dcl_prs_product_cohort_report import build_product_cohort_report
from experiments.dcl_prs_product_runtime_manifest import (
    build_product_runtime_manifest,
)


def test_product_runtime_manifest_connects_report_sections_to_routes():
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
    manifest = build_product_runtime_manifest(
        artifact_id="dcl-prs-product-runtime-manifest-test",
        product_cohort_report=report,
    )

    assert manifest["schema_version"] == "dcl-prs-product-runtime-manifest-v1"
    assert manifest["overall_status"] == "product_runtime_manifest_connection_ready"
    assert manifest["report_artifact_id"] == report["artifact_id"]
    assert len(manifest["runtime_routes"]) == 5
    assert manifest["product_claim_status"] == "runtime_connection_only"
    assert manifest["customer_validation_status"] == "not_validated"
    json.dumps(manifest, allow_nan=False)


def test_product_runtime_manifest_script_writes_artifact(tmp_path):
    output_dir = tmp_path / "dcl_prs_product_runtime_manifest"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_product_runtime_manifest.py",
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-product-runtime-manifest-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-product-runtime-manifest-test.json"),
        "overall_status": "product_runtime_manifest_connection_ready",
        "route_count": 5,
    }
