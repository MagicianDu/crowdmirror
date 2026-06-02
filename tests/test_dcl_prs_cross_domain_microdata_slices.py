import json
import subprocess
import sys

from experiments.dcl_prs_cross_domain_microdata_slices import (
    build_cross_domain_microdata_access_audit,
)
from experiments.dcl_prs_cross_domain_task_slice_smoke import (
    build_cross_domain_task_slice_smoke,
)
from experiments.dcl_prs_public_dataset_ingestion import (
    build_cross_domain_ingestion_index,
)


def test_cross_domain_microdata_access_audit_does_not_fake_downloaded_rows():
    ingestion = build_cross_domain_ingestion_index(
        artifact_id="dcl-prs-cross-domain-ingestion-test"
    )
    audit = build_cross_domain_microdata_access_audit(
        artifact_id="dcl-prs-cross-domain-microdata-test",
        cross_domain_task_slice_smoke=build_cross_domain_task_slice_smoke(
            artifact_id="dcl-prs-cross-domain-task-slice-smoke-test",
            cross_domain_ingestion=ingestion,
        ),
    )

    assert audit["schema_version"] == "dcl-prs-cross-domain-microdata-slices-v1"
    assert audit["overall_status"] == "cross_domain_microdata_access_audit_ready"
    assert audit["official_source_ids"] == ["gss", "eurobarometer"]
    assert audit["official_microdata_loaded"] is False
    assert audit["sample_slice_type"] == "schema_fixture_not_official_microdata"
    assert audit["next_gate"] == "download_official_cross_domain_public_use_files"
    json.dumps(audit, allow_nan=False)


def test_cross_domain_microdata_access_script_writes_artifact(tmp_path):
    output_dir = tmp_path / "dcl_prs_cross_domain_microdata"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_cross_domain_microdata_slices.py",
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-cross-domain-microdata-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-cross-domain-microdata-test.json"),
        "official_microdata_loaded": False,
        "overall_status": "cross_domain_microdata_access_audit_ready",
    }
