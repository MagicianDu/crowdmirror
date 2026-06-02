import json
import subprocess
import sys

from experiments.dcl_prs_cross_domain_task_slice_smoke import (
    build_cross_domain_task_slice_smoke,
)
from experiments.dcl_prs_public_dataset_ingestion import (
    build_cross_domain_ingestion_index,
)


def test_cross_domain_task_slice_smoke_maps_required_fields_for_each_dataset():
    smoke = build_cross_domain_task_slice_smoke(
        artifact_id="dcl-prs-cross-domain-task-slice-smoke-test",
        cross_domain_ingestion=build_cross_domain_ingestion_index(
            artifact_id="dcl-prs-cross-domain-ingestion-test"
        ),
    )

    assert smoke["schema_version"] == "dcl-prs-cross-domain-task-slice-smoke-v1"
    assert smoke["overall_status"] == "cross_domain_task_slice_smoke_ready"
    assert smoke["dataset_count"] == 2
    assert smoke["mapped_task_slice_count"] == 2
    assert smoke["all_required_fields_mapped"] is True
    assert smoke["ccf_a_claim_status"] == "not_claimable"
    json.dumps(smoke, allow_nan=False)


def test_cross_domain_task_slice_smoke_records_source_specific_mappings():
    smoke = build_cross_domain_task_slice_smoke(
        artifact_id="dcl-prs-cross-domain-task-slice-smoke-test",
        cross_domain_ingestion=build_cross_domain_ingestion_index(
            artifact_id="dcl-prs-cross-domain-ingestion-test"
        ),
    )

    source_ids = [mapping["source_id"] for mapping in smoke["task_slice_mappings"]]
    assert source_ids == ["gss", "eurobarometer"]
    for mapping in smoke["task_slice_mappings"]:
        assert mapping["field_mapping"]["cohort"]
        assert mapping["field_mapping"]["policy_or_question"]
        assert mapping["field_mapping"]["response_distribution"]
        assert mapping["mapping_status"] == "required_fields_mapped"


def test_cross_domain_task_slice_smoke_script_writes_artifact(tmp_path):
    output_dir = tmp_path / "dcl_prs_cross_domain_smoke"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_cross_domain_task_slice_smoke.py",
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-cross-domain-task-slice-smoke-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-cross-domain-task-slice-smoke-test.json"),
        "mapped_task_slice_count": 2,
        "overall_status": "cross_domain_task_slice_smoke_ready",
    }
    assert (output_dir / "dcl-prs-cross-domain-task-slice-smoke-test.json").exists()
