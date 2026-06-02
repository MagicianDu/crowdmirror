import json
import subprocess
import sys

from experiments.dcl_prs_multi_dataset_generalization_matrix import (
    build_multi_dataset_generalization_matrix,
)


def test_multi_dataset_generalization_matrix_records_gss_ready_and_eurobarometer_blocked():
    matrix = build_multi_dataset_generalization_matrix(
        artifact_id="dcl-prs-multi-dataset-generalization-test",
        gss_real_repair_effect_validation=_gss_real_effect_fixture(),
        official_public_use_file_probe=_official_probe_fixture(),
    )

    assert matrix["schema_version"] == "dcl-prs-multi-dataset-generalization-matrix-v1"
    assert matrix["overall_status"] == "multi_dataset_generalization_partial"
    assert matrix["required_dataset_count"] == 2
    assert matrix["available_real_effect_dataset_count"] == 1
    assert matrix["blocked_dataset_count"] == 1
    assert matrix["generalization_gate_closed"] is False
    assert matrix["source_results"]["gss"]["generalization_status"] == (
        "single_dataset_real_effect_ready"
    )
    assert matrix["source_results"]["gss"]["real_effect_promoted_count"] == 2
    assert matrix["source_results"]["eurobarometer"]["generalization_status"] == (
        "blocked_microdata_missing"
    )
    assert matrix["source_results"]["eurobarometer"]["blocking_condition"] == (
        "GESIS catalogue requires sign-in/registration for microdata analysis file download."
    )
    assert matrix["next_gate"] == "complete_eurobarometer_authenticated_download"
    assert "single_real_effect_dataset_only" in matrix["risk_flags"]
    json.dumps(matrix, allow_nan=False)


def test_multi_dataset_generalization_script_writes_artifact(tmp_path):
    gss_path = tmp_path / "gss_real_effect.json"
    gss_path.write_text(json.dumps(_gss_real_effect_fixture()))
    probe_path = tmp_path / "official_probe.json"
    probe_path.write_text(json.dumps(_official_probe_fixture()))
    output_dir = tmp_path / "generalization"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_multi_dataset_generalization_matrix.py",
            "--gss-real-repair-effect-validation-path",
            str(gss_path),
            "--official-public-use-file-probe-path",
            str(probe_path),
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-multi-dataset-generalization-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-multi-dataset-generalization-test.json"),
        "generalization_gate_closed": False,
        "overall_status": "multi_dataset_generalization_partial",
    }


def _gss_real_effect_fixture():
    return {
        "schema_version": "dcl-prs-gss-real-repair-effect-v1",
        "artifact_id": "dcl-prs-gss-real-repair-effect-test",
        "overall_status": "gss_real_repair_effect_validation_ready",
        "source_id": "gss",
        "task_slice_id": "gss_public_health_confidence_attitude_v1",
        "real_effect_promoted_count": 2,
        "accepted_candidate_count": 2,
        "real_target": {
            "valid_policy_response_count": 2610,
            "response_distribution": {
                "a great deal": 0.272,
                "only some": 0.539,
                "hardly any": 0.189,
            },
        },
    }


def _official_probe_fixture():
    return {
        "schema_version": "dcl-prs-official-public-use-file-probe-v1",
        "artifact_id": "dcl-prs-official-public-use-file-probe-test",
        "overall_status": "official_public_use_file_probe_partial",
        "gss_download_verified": True,
        "eurobarometer_download_verified": False,
        "source_results": {
            "gss": {
                "source_id": "gss",
                "download_status": "download_verified",
                "requires_login": False,
            },
            "eurobarometer": {
                "source_id": "eurobarometer",
                "download_status": "login_required_not_downloaded",
                "requires_login": True,
                "blocking_condition": (
                    "GESIS catalogue requires sign-in/registration for "
                    "microdata analysis file download."
                ),
            },
        },
    }
