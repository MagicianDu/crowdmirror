import json
import subprocess
import sys

from experiments.dcl_prs_public_dataset_ingestion import (
    build_cross_domain_dataset_audit,
    build_cross_domain_ingestion_index,
)


def test_cross_domain_audit_includes_required_gss_and_eurobarometer_sources():
    audit = build_cross_domain_dataset_audit()

    assert audit["schema_version"] == "dcl-prs-public-dataset-audit-v1"
    assert audit["overall_status"] == "cross_domain_public_sources_audited"
    assert audit["required_source_count"] == 2
    assert audit["required_source_ids"] == ["gss", "eurobarometer"]
    assert audit["backup_source_ids"] == ["wvs"]
    assert "not_model_quality_evidence" in audit["risk_flags"]
    assert audit["claim_boundary"]["ccf_a_claim_status"] == "not_claimable"
    json.dumps(audit, allow_nan=False)


def test_cross_domain_index_has_two_runnable_task_slices_and_open_claim_boundary():
    index = build_cross_domain_ingestion_index(
        artifact_id="dcl-prs-cross-domain-ingestion-test"
    )

    assert index["schema_version"] == "dcl-prs-cross-domain-ingestion-index-v1"
    assert index["overall_status"] == "cross_domain_task_slices_ready_for_smoke"
    assert index["required_dataset_count"] == 2
    assert index["task_slice_count"] == 2
    assert index["task_slice_ids"] == [
        "gss_public_health_confidence_attitude_v1",
        "eurobarometer_eu_policy_trust_attitude_v1",
    ]
    assert index["ccf_a_claim_status"] == "not_claimable"
    assert index["next_gate"] == "run_cross_domain_task_slice_smoke"
    assert "cross_domain_smoke_only" in index["risk_flags"]
    json.dumps(index, allow_nan=False)


def test_cross_domain_ingestion_script_writes_artifacts(tmp_path):
    output_dir = tmp_path / "dcl_prs_public_dataset_ingestion"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_public_dataset_ingestion.py",
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-cross-domain-ingestion-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "audit": str(output_dir / "dcl-prs-public-dataset-audit-current-001.json"),
        "index": str(output_dir / "dcl-prs-cross-domain-ingestion-test.json"),
        "task_slice_count": 2,
    }
    assert (output_dir / "dcl-prs-public-dataset-audit-current-001.json").exists()
    assert (output_dir / "dcl-prs-cross-domain-ingestion-test.json").exists()
