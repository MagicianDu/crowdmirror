import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_trial_launch_handoff_package import (
    R12_CUSTOMER_TRIAL_LAUNCH_HANDOFF_PACKAGE_SCHEMA_VERSION,
    build_r12_customer_trial_launch_handoff_package,
    write_r12_customer_trial_launch_handoff_package,
)


def test_r12_customer_trial_launch_handoff_package_is_customer_launch_ready():
    package = build_r12_customer_trial_launch_handoff_package(
        artifact_id="r12-customer-trial-launch-handoff-package-test",
        run_id="r12-l30-test",
        generated_at="2026-06-28T13:50:00Z",
        r12_customer_trial_readiness_package=_load_current_l28(),
        r12_customer_trial_operational_check=_load_current_l29(),
    )

    assert package["schema_version"] == (
        R12_CUSTOMER_TRIAL_LAUNCH_HANDOFF_PACKAGE_SCHEMA_VERSION
    )
    assert package["status"] == (
        "r12_customer_trial_launch_handoff_package_ready_source_pending"
    )
    assert package["claim_level"] == "customer_trial_launch_ready_no_validation_claim"
    assert package["launch_summary"] == {
        "generated_at": "2026-06-28T13:50:00Z",
        "trial_readiness_artifact_id": (
            "r12-customer-trial-readiness-package-current-001"
        ),
        "operational_check_artifact_id": (
            "r12-customer-trial-operational-check-current-001"
        ),
        "current_stage": "source_arrival_pending",
        "next_action": "collect_customer_field_slice_or_wait_for_target_outcome",
        "launch_handoff_ready": True,
        "template_path": (
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-template-current-001.csv"
        ),
        "minimum_case_count": 10,
        "required_field_count": 7,
        "operator_command_count": 5,
        "manual_approval_point_count": 2,
        "field_outcome_validated": False,
    }
    assert [item["bundle_item_id"] for item in package["customer_launch_bundle"]] == [
        "data_request_brief",
        "field_slice_template",
        "approval_checklist",
        "submission_and_runbook",
        "claim_boundary",
    ]
    assert package["customer_data_request"] == {
        "request_id": "r12_customer_field_slice_submission_request",
        "minimum_case_count": 10,
        "required_fields": [
            "case_id",
            "segment_id",
            "scenario_id",
            "prediction_share_or_score",
            "observed_outcome",
            "outcome_timestamp",
            "customer_approval_reference",
        ],
        "template_path": (
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-template-current-001.csv"
        ),
        "approval_reference_required": True,
        "direct_personal_identifiers_allowed": False,
    }
    assert package["submission_instructions"] == {
        "next_required_artifact": (
            "customer_field_slice_submission_or_target_outcome_artifact"
        ),
        "first_operator_step": "intake_validation",
        "first_operator_command": (
            ".venv/bin/python "
            "experiments/r12_customer_field_slice_intake_validation.py "
            "--customer-field-slice-path <customer-slice.csv>"
        ),
        "operator_step_ids": [
            "intake_validation",
            "field_revalidation",
            "feedback_update_candidate",
            "shadow_replay",
            "holdout_review",
        ],
    }
    assert package["acceptance_gates"] == {
        "launch_handoff_package_ready": True,
        "trial_readiness_package_ready": True,
        "operational_check_ready": True,
        "customer_trial_request_operationally_ready": True,
        "customer_field_slice_present": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert "r12-customer-trial-readiness-package-current-001" in package[
        "source_refs"
    ]
    assert "r12-customer-trial-operational-check-current-001" in package[
        "source_refs"
    ]
    assert "field validation 已完成" in package["blocked_claims"]
    assert "runtime_default_allowed=true" in package["blocked_claims"]
    json.dumps(package, allow_nan=False)


def test_r12_customer_trial_launch_handoff_package_writer_and_cli(tmp_path):
    l28_path = tmp_path / "l28.json"
    l29_path = tmp_path / "l29.json"
    l28_path.write_text(json.dumps(_load_current_l28(), allow_nan=False))
    l29_path.write_text(json.dumps(_load_current_l29(), allow_nan=False))
    output = tmp_path / "launch-handoff-package.json"

    output_path = write_r12_customer_trial_launch_handoff_package(
        output=output,
        artifact_id="r12-customer-trial-launch-handoff-package-test",
        run_id="r12-l30-test",
        generated_at="2026-06-28T13:50:00Z",
        r12_customer_trial_readiness_package=_load_current_l28(),
        r12_customer_trial_operational_check=_load_current_l29(),
    )

    assert output_path == output
    assert json.loads(output.read_text())["acceptance_gates"][
        "launch_handoff_package_ready"
    ] is True

    cli_output = tmp_path / "launch-handoff-package-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_trial_launch_handoff_package.py",
            "--artifact-id",
            "r12-customer-trial-launch-handoff-package-cli",
            "--run-id",
            "r12-l30-cli-test",
            "--generated-at",
            "2026-06-28T13:50:00Z",
            "--r12-customer-trial-readiness-package-path",
            str(l28_path),
            "--r12-customer-trial-operational-check-path",
            str(l29_path),
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
        "r12-customer-trial-launch-handoff-package-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-customer-trial-launch-handoff-package-cli",
        "launch_handoff_ready": True,
        "output": str(cli_output),
        "status": "r12_customer_trial_launch_handoff_package_ready_source_pending",
    }


def _load_current_l28():
    return _load_result(
        "r12_customer_trial_readiness_package/"
        "r12-customer-trial-readiness-package-current-001.json"
    )


def _load_current_l29():
    return _load_result(
        "r12_customer_trial_operational_check/"
        "r12-customer-trial-operational-check-current-001.json"
    )


def _load_result(relative_path: str) -> dict:
    return json.loads((_repo_root() / "experiments/results" / relative_path).read_text())


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
