import json
import subprocess
import sys

from experiments.dcl_prs_gss_policy_task_ingestion_smoke import (
    build_gss_policy_task_ingestion_smoke,
)


def test_gss_policy_task_ingestion_smoke_computes_response_and_cohort_distributions():
    binding = _binding_fixture()
    records = [
        {
            "age": "25",
            "educ": "college",
            "realinc": "50000",
            "polviews": "liberal",
            "conmedic": "a great deal",
        },
        {
            "age": "40",
            "educ": "college",
            "realinc": "60000",
            "polviews": "liberal",
            "conmedic": "only some",
        },
        {
            "age": "65",
            "educ": "high school",
            "realinc": "30000",
            "polviews": "conservative",
            "conmedic": "hardly any",
        },
    ]

    smoke = build_gss_policy_task_ingestion_smoke(
        artifact_id="dcl-prs-gss-policy-task-smoke-test",
        gss_policy_task_binding=binding,
        records=records,
    )

    assert smoke["schema_version"] == "dcl-prs-gss-policy-task-ingestion-smoke-v1"
    assert smoke["overall_status"] == "gss_policy_task_ingestion_smoke_ready"
    assert smoke["source_artifact_id"] == "dcl-prs-gss-policy-task-binding-test"
    assert smoke["row_count"] == 3
    assert smoke["valid_policy_response_count"] == 3
    assert smoke["response_distribution"]["counts"] == {
        "a great deal": 1,
        "hardly any": 1,
        "only some": 1,
    }
    liberal_slice = smoke["cohort_slice_distributions"]["political_views"]["liberal"]
    assert liberal_slice["valid_policy_response_count"] == 2
    assert liberal_slice["response_distribution"]["counts"] == {
        "a great deal": 1,
        "only some": 1,
    }
    assert "not_model_quality_evidence" in smoke["risk_flags"]
    json.dumps(smoke, allow_nan=False)


def test_gss_policy_task_ingestion_smoke_script_writes_artifact(tmp_path):
    source_file = tmp_path / "gss_rows.csv"
    source_file.write_text(
        "\n".join(
            [
                "age,educ,realinc,polviews,conmedic",
                "25,college,50000,liberal,a great deal",
                "40,college,60000,liberal,only some",
                "65,high school,30000,conservative,hardly any",
            ]
        )
    )
    binding_path = tmp_path / "binding.json"
    binding_path.write_text(json.dumps(_binding_fixture()))
    output_dir = tmp_path / "smoke"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_gss_policy_task_ingestion_smoke.py",
            "--gss-policy-task-binding-path",
            str(binding_path),
            "--source-path",
            str(source_file),
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-gss-policy-task-smoke-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-gss-policy-task-smoke-test.json"),
        "overall_status": "gss_policy_task_ingestion_smoke_ready",
        "valid_policy_response_count": 3,
    }


def _binding_fixture():
    return {
        "schema_version": "dcl-prs-gss-policy-task-binding-v1",
        "artifact_id": "dcl-prs-gss-policy-task-binding-test",
        "overall_status": "gss_policy_task_variables_bound",
        "required_fields_bound": True,
        "field_bindings": {
            "cohort": {
                "age_group": {"variable_name": "age"},
                "education": {"variable_name": "educ"},
                "income": {"variable_name": "realinc"},
                "political_views": {"variable_name": "polviews"},
            },
            "policy_or_question": {"variable_name": "conmedic"},
            "response_distribution": {"source_variable_name": "conmedic"},
        },
    }
