import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_trial_readiness_package import (
    R12_CUSTOMER_TRIAL_READINESS_PACKAGE_SCHEMA_VERSION,
    build_r12_customer_trial_readiness_package,
    write_r12_customer_trial_readiness_package,
)


def test_r12_customer_trial_readiness_package_is_ready_but_source_pending():
    package = build_r12_customer_trial_readiness_package(
        artifact_id="r12-customer-trial-readiness-package-test",
        run_id="r12-l28-test",
        package_generated_at="2026-06-28T12:30:00Z",
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        r12_customer_validation_workflow_status=_load_current_l27(),
    )

    assert package["schema_version"] == (
        R12_CUSTOMER_TRIAL_READINESS_PACKAGE_SCHEMA_VERSION
    )
    assert package["status"] == (
        "r12_customer_trial_readiness_package_ready_guarded_source_pending"
    )
    assert package["claim_level"] == (
        "customer_trial_readiness_package_ready_no_validation_claim"
    )
    assert package["trial_readiness_summary"] == {
        "package_generated_at": "2026-06-28T12:30:00Z",
        "current_stage": "source_arrival_pending",
        "next_action": "collect_customer_field_slice_or_wait_for_target_outcome",
        "customer_data_request_ready": True,
        "template_output_path": (
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-template-current-001.csv"
        ),
        "minimum_case_count": 10,
        "required_field_count": 7,
        "manual_approval_point_count": 2,
        "field_outcome_validated": False,
    }
    assert [item["check_id"] for item in package["customer_trial_checklist"]] == [
        "customer_approval_reference",
        "pseudonymous_case_ids",
        "minimum_case_count",
        "required_fields",
        "run_intake_validation",
    ]
    assert package["customer_trial_checklist"][0]["required"] is True
    assert package["operator_runbook"] == _load_current_l27()["operator_runbook"]
    assert package["acceptance_gates"] == {
        "trial_readiness_package_ready": True,
        "customer_data_request_ready": True,
        "workflow_status_package_ready": True,
        "customer_slice_ready_for_revalidation": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert package["next_required_artifact"] == (
        "customer_field_slice_submission_or_target_outcome_artifact"
    )
    assert "field validation 已完成" in package["blocked_claims"]
    assert "runtime_default_allowed=true" in package["blocked_claims"]
    json.dumps(package, allow_nan=False)


def test_r12_customer_trial_readiness_package_writer_and_cli(tmp_path):
    paths = _write_current_inputs(tmp_path)
    output = tmp_path / "trial-readiness-package.json"

    output_path = write_r12_customer_trial_readiness_package(
        output=output,
        artifact_id="r12-customer-trial-readiness-package-test",
        run_id="r12-l28-test",
        package_generated_at="2026-06-28T12:30:00Z",
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        r12_customer_validation_workflow_status=_load_current_l27(),
    )
    assert output_path == output
    assert json.loads(output.read_text())["trial_readiness_summary"][
        "current_stage"
    ] == "source_arrival_pending"

    cli_output = tmp_path / "trial-readiness-package-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_trial_readiness_package.py",
            "--artifact-id",
            "r12-customer-trial-readiness-package-cli",
            "--run-id",
            "r12-l28-cli-test",
            "--package-generated-at",
            "2026-06-28T12:30:00Z",
            "--r12-customer-field-slice-handoff-package-path",
            str(paths["l21"]),
            "--r12-customer-validation-workflow-status-path",
            str(paths["l27"]),
            "--output",
            str(cli_output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(cli_output.read_text())
    assert artifact["schema_version"] == "r12-customer-trial-readiness-package-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-customer-trial-readiness-package-cli",
        "current_stage": "source_arrival_pending",
        "output": str(cli_output),
        "status": "r12_customer_trial_readiness_package_ready_guarded_source_pending",
    }


def _load_current_l21():
    return _load_result(
        "r12_customer_field_slice_handoff_package/"
        "r12-customer-field-slice-handoff-package-current-001.json"
    )


def _load_current_l27():
    return _load_result(
        "r12_customer_validation_workflow_status/"
        "r12-customer-validation-workflow-status-current-001.json"
    )


def _load_result(relative_path: str) -> dict:
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads((repo_root / "experiments/results" / relative_path).read_text())


def _write_current_inputs(tmp_path: Path) -> dict[str, Path]:
    payloads = {
        "l21": _load_current_l21(),
        "l27": _load_current_l27(),
    }
    paths = {}
    for key, payload in payloads.items():
        path = tmp_path / f"{key}.json"
        path.write_text(json.dumps(payload, allow_nan=False))
        paths[key] = path
    return paths
