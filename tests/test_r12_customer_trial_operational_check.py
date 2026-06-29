import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_trial_operational_check import (
    R12_CUSTOMER_TRIAL_OPERATIONAL_CHECK_SCHEMA_VERSION,
    build_r12_customer_trial_operational_check,
    write_r12_customer_trial_operational_check,
)


def test_r12_customer_trial_operational_check_verifies_package_paths_and_runbook():
    check = build_r12_customer_trial_operational_check(
        artifact_id="r12-customer-trial-operational-check-test",
        run_id="r12-l29-test",
        checked_at="2026-06-28T13:20:00Z",
        r12_customer_trial_readiness_package=_load_current_l28(),
        repo_root=_repo_root(),
    )

    assert check["schema_version"] == (
        R12_CUSTOMER_TRIAL_OPERATIONAL_CHECK_SCHEMA_VERSION
    )
    assert check["status"] == (
        "r12_customer_trial_operational_check_ready_source_pending"
    )
    assert check["claim_level"] == (
        "operational_trial_readiness_verified_no_validation_claim"
    )
    assert check["operational_summary"] == {
        "checked_at": "2026-06-28T13:20:00Z",
        "trial_package_artifact_id": (
            "r12-customer-trial-readiness-package-current-001"
        ),
        "current_stage": "source_arrival_pending",
        "next_action": "collect_customer_field_slice_or_wait_for_target_outcome",
        "template_path": (
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-template-current-001.csv"
        ),
        "template_path_resolvable": True,
        "template_required_fields_present": True,
        "source_registry_entry_count": 4,
        "source_registry_resolvable_count": 4,
        "operator_command_count": 5,
        "manual_approval_point_count": 2,
    }
    assert check["template_check"] == {
        "required_fields": [
            "case_id",
            "segment_id",
            "scenario_id",
            "prediction_share_or_score",
            "observed_outcome",
            "outcome_timestamp",
            "customer_approval_reference",
        ],
        "template_header_fields": [
            "case_id",
            "segment_id",
            "scenario_id",
            "prediction_share_or_score",
            "observed_outcome",
            "outcome_timestamp",
            "customer_approval_reference",
        ],
        "missing_required_fields": [],
    }
    assert [item["step_id"] for item in check["operator_command_check"]] == [
        "intake_validation",
        "field_revalidation",
        "feedback_update_candidate",
        "shadow_replay",
        "holdout_review",
    ]
    assert check["unresolved_sources"] == []
    assert check["acceptance_gates"] == {
        "trial_readiness_package_loaded": True,
        "template_path_resolvable": True,
        "template_required_fields_present": True,
        "source_registry_resolvable": True,
        "operator_runbook_declared": True,
        "customer_trial_request_operationally_ready": True,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert check["next_required_artifact"] == (
        "customer_field_slice_submission_or_target_outcome_artifact"
    )
    assert "field validation 已完成" in check["blocked_claims"]
    assert "runtime_default_allowed=true" in check["blocked_claims"]
    json.dumps(check, allow_nan=False)


def test_r12_customer_trial_operational_check_writer_and_cli(tmp_path):
    input_path = tmp_path / "l28.json"
    input_path.write_text(json.dumps(_load_current_l28(), allow_nan=False))
    output = tmp_path / "operational-check.json"

    output_path = write_r12_customer_trial_operational_check(
        output=output,
        artifact_id="r12-customer-trial-operational-check-test",
        run_id="r12-l29-test",
        checked_at="2026-06-28T13:20:00Z",
        r12_customer_trial_readiness_package=_load_current_l28(),
        repo_root=_repo_root(),
    )

    assert output_path == output
    assert json.loads(output.read_text())["acceptance_gates"][
        "customer_trial_request_operationally_ready"
    ] is True

    cli_output = tmp_path / "operational-check-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_trial_operational_check.py",
            "--artifact-id",
            "r12-customer-trial-operational-check-cli",
            "--run-id",
            "r12-l29-cli-test",
            "--checked-at",
            "2026-06-28T13:20:00Z",
            "--r12-customer-trial-readiness-package-path",
            str(input_path),
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
        "r12-customer-trial-operational-check-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-customer-trial-operational-check-cli",
        "operationally_ready": True,
        "output": str(cli_output),
        "status": "r12_customer_trial_operational_check_ready_source_pending",
    }


def _load_current_l28():
    return _load_result(
        "r12_customer_trial_readiness_package/"
        "r12-customer-trial-readiness-package-current-001.json"
    )


def _load_result(relative_path: str) -> dict:
    return json.loads((_repo_root() / "experiments/results" / relative_path).read_text())


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
