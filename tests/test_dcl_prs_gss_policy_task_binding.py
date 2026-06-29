import json
import subprocess
import sys

from experiments.dcl_prs_gss_policy_task_binding import (
    build_gss_policy_task_binding,
)


def test_gss_policy_task_binding_maps_real_variables_to_required_fields():
    gss_manifest = {
        "schema_version": "dcl-prs-gss-public-use-download-v1",
        "artifact_id": "dcl-prs-gss-public-use-download-test",
        "overall_status": "gss_public_use_download_verified",
        "download_verified": True,
        "byte_count": 123,
        "sha256": "abc",
    }
    stata_metadata = {
        "variable_count": 8,
        "variables": {
            "age": {"name": "age"},
            "educ": {"name": "educ"},
            "realinc": {"name": "realinc"},
            "polviews": {"name": "polviews"},
            "partyid": {"name": "partyid"},
            "conmedic": {
                "name": "conmedic",
                "observed_response_values": ["a great deal", "only some", "hardly any"],
            },
            "health": {"name": "health"},
        },
    }

    binding = build_gss_policy_task_binding(
        artifact_id="dcl-prs-gss-policy-task-binding-test",
        gss_download_manifest=gss_manifest,
        stata_metadata=stata_metadata,
    )

    assert binding["schema_version"] == "dcl-prs-gss-policy-task-binding-v1"
    assert binding["overall_status"] == "gss_policy_task_variables_bound"
    assert binding["source_artifact_id"] == "dcl-prs-gss-public-use-download-test"
    assert binding["task_slice_id"] == "gss_public_health_confidence_attitude_v1"
    assert binding["required_fields_bound"] is True
    assert binding["field_bindings"]["policy_or_question"]["variable_name"] == (
        "conmedic"
    )
    assert binding["field_bindings"]["response_distribution"][
        "source_variable_name"
    ] == "conmedic"
    assert sorted(binding["field_bindings"]["cohort"].keys()) == [
        "age_group",
        "education",
        "income",
        "political_views",
    ]
    assert "not_model_quality_evidence" in binding["risk_flags"]
    json.dumps(binding, allow_nan=False)


def test_gss_policy_task_binding_script_writes_artifact(tmp_path):
    source_file = tmp_path / "gss_2024_fixture.dta"
    source_file.write_text(
        "\n".join(["age,educ,realinc,polviews,partyid,conmedic,health", "1,2,3,4,5,6,7"])
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "dcl-prs-gss-public-use-download-v1",
                "artifact_id": "dcl-prs-gss-public-use-download-test",
                "overall_status": "gss_public_use_download_verified",
                "download_verified": True,
            }
        )
    )
    output_dir = tmp_path / "binding"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_gss_policy_task_binding.py",
            "--gss-download-manifest-path",
            str(manifest_path),
            "--source-path",
            str(source_file),
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-gss-policy-task-binding-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-gss-policy-task-binding-test.json"),
        "overall_status": "gss_policy_task_variables_bound",
        "required_fields_bound": True,
    }
