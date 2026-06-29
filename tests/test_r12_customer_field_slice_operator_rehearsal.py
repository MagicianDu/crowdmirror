import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_field_slice_operator_rehearsal import (
    R12_CUSTOMER_FIELD_SLICE_OPERATOR_REHEARSAL_SCHEMA_VERSION,
    build_r12_customer_field_slice_operator_rehearsal,
    write_r12_customer_field_slice_operator_rehearsal,
)


def test_r12_customer_field_slice_operator_rehearsal_runs_l22_on_synthetic_slice_without_field_claim(
    tmp_path,
):
    work_dir = tmp_path / "operator-rehearsal"

    report = build_r12_customer_field_slice_operator_rehearsal(
        artifact_id="r12-customer-field-slice-operator-rehearsal-test",
        run_id="r12-l34-test",
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        r12_customer_field_slice_handoff_package_path=_current_l21_path(),
        rehearsal_started_at="2026-06-28T11:30:00Z",
        rehearsal_work_dir=work_dir,
    )

    assert report["schema_version"] == (
        R12_CUSTOMER_FIELD_SLICE_OPERATOR_REHEARSAL_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_customer_field_slice_operator_rehearsal_ready_no_field_claim"
    )
    assert report["claim_level"] == (
        "operator_rehearsal_only_no_customer_validation_claim"
    )
    assert report["rehearsal_summary"] == {
        "handoff_artifact_id": "r12-customer-field-slice-handoff-package-current-001",
        "rehearsal_started_at": "2026-06-28T11:30:00Z",
        "sample_slice_kind": "synthetic_rehearsal_fixture",
        "sample_slice_path": str(
            work_dir / "r12-customer-field-slice-rehearsal-sample.csv"
        ),
        "intake_output_path": str(
            work_dir / "r12-customer-field-slice-intake-validation-rehearsal.json"
        ),
        "case_count": 10,
        "minimum_case_count": 10,
        "required_field_count": 7,
        "operator_command_template_matches_demo": True,
        "intake_status": (
            "r12_customer_field_slice_intake_validation_ready_for_revalidation_guarded"
        ),
        "sample_slice_ready_for_revalidation": True,
    }
    assert Path(report["rehearsal_summary"]["sample_slice_path"]).exists()
    assert Path(report["rehearsal_summary"]["intake_output_path"]).exists()
    assert report["operator_command_template"].startswith(
        ".venv/bin/python experiments/r12_customer_field_slice_intake_validation.py"
    )
    assert "CUSTOMER_FIELD_SLICE_PATH" in report["operator_command_template"]
    assert report["intake_artifact_summary"] == {
        "artifact_id": "r12-customer-field-slice-intake-validation-rehearsal",
        "status": (
            "r12_customer_field_slice_intake_validation_ready_for_revalidation_guarded"
        ),
        "ready_for_revalidation": True,
        "validation_errors": [],
    }
    assert report["acceptance_gates"] == {
        "synthetic_rehearsal_fixture_generated": True,
        "operator_command_rehearsed": True,
        "intake_validator_executed": True,
        "sample_slice_intake_ready_for_revalidation": True,
        "real_customer_field_slice_submitted": False,
        "metrics_computed": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "accept_operator_rehearsal_keep_customer_validation_blocked"
    )
    assert report["next_required_artifact"] == (
        "real_customer_field_slice_intake_validation_or_target_outcome_revalidation"
    )
    assert "real_customer_field_slice_validated=true" in report["blocked_claims"]
    assert "runtime_default_allowed=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_customer_field_slice_operator_rehearsal_writer_and_cli(tmp_path):
    handoff_path = tmp_path / "r12-l21.json"
    handoff_path.write_text(json.dumps(_load_current_l21(), allow_nan=False))
    output = tmp_path / "operator-rehearsal.json"
    work_dir = tmp_path / "rehearsal-work"

    output_path = write_r12_customer_field_slice_operator_rehearsal(
        output=output,
        artifact_id="r12-customer-field-slice-operator-rehearsal-test",
        run_id="r12-l34-test",
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        r12_customer_field_slice_handoff_package_path=handoff_path,
        rehearsal_started_at="2026-06-28T11:30:00Z",
        rehearsal_work_dir=work_dir,
    )

    assert output_path == output
    assert json.loads(output.read_text())["acceptance_gates"][
        "operator_command_rehearsed"
    ] is True

    cli_output = tmp_path / "operator-rehearsal-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_field_slice_operator_rehearsal.py",
            "--artifact-id",
            "r12-customer-field-slice-operator-rehearsal-cli",
            "--run-id",
            "r12-l34-cli-test",
            "--r12-customer-field-slice-handoff-package-path",
            str(handoff_path),
            "--rehearsal-started-at",
            "2026-06-28T11:30:00Z",
            "--rehearsal-work-dir",
            str(work_dir / "cli"),
            "--output",
            str(cli_output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(cli_output.read_text())
    assert artifact["schema_version"] == (
        "r12-customer-field-slice-operator-rehearsal-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-customer-field-slice-operator-rehearsal-cli",
        "operator_command_rehearsed": True,
        "output": str(cli_output),
        "sample_slice_ready_for_revalidation": True,
        "status": (
            "r12_customer_field_slice_operator_rehearsal_ready_no_field_claim"
        ),
    }


def _load_current_l21():
    return json.loads(_current_l21_path().read_text())


def _current_l21_path() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    return (
        repo_root
        / "experiments/results/"
        "r12_customer_field_slice_handoff_package/"
        "r12-customer-field-slice-handoff-package-current-001.json"
    )
