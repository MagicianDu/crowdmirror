import copy
import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_validation_workflow_status import (
    R12_CUSTOMER_VALIDATION_WORKFLOW_STATUS_SCHEMA_VERSION,
    build_r12_customer_validation_workflow_status,
    write_r12_customer_validation_workflow_status,
)


def test_r12_customer_validation_workflow_status_waits_for_source():
    report = build_r12_customer_validation_workflow_status(
        artifact_id="r12-customer-validation-workflow-status-test",
        run_id="r12-l27-test",
        workflow_generated_at="2026-06-28T12:00:00Z",
        r12_target_outcome_or_customer_field_slice_arrival=_load_current_l20(),
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        r12_customer_field_slice_intake_validation=_load_current_l22(),
        r12_customer_field_slice_revalidation=_load_current_l23(),
        r12_customer_field_outcome_feedback_update=_load_current_l24(),
        r12_customer_feedback_update_shadow_replay=_load_current_l25(),
        r12_customer_feedback_shadow_replay_holdout_review=_load_current_l26(),
    )

    assert report["schema_version"] == (
        R12_CUSTOMER_VALIDATION_WORKFLOW_STATUS_SCHEMA_VERSION
    )
    assert report["status"] == "r12_customer_validation_workflow_waiting_for_source"
    assert report["claim_level"] == (
        "customer_validation_workflow_ready_source_pending"
    )
    assert report["workflow_summary"] == {
        "workflow_generated_at": "2026-06-28T12:00:00Z",
        "current_stage": "source_arrival_pending",
        "next_action": "collect_customer_field_slice_or_wait_for_target_outcome",
        "blocking_artifact_id": (
            "r12-target-outcome-or-customer-field-slice-arrival-current-001"
        ),
        "source_arrived": False,
        "customer_slice_ready_for_revalidation": False,
        "metrics_computed": False,
        "field_outcome_validated": False,
        "feedback_candidate_count": 0,
        "shadow_replay_executed": False,
        "holdout_review_executed": False,
    }
    assert [step["step_id"] for step in report["workflow_steps"]] == [
        "source_arrival",
        "handoff_package",
        "intake_validation",
        "field_revalidation",
        "feedback_update_candidate",
        "shadow_replay",
        "holdout_review",
    ]
    assert report["workflow_steps"][0]["step_status"] == "pending"
    assert report["workflow_steps"][1]["step_status"] == "ready"
    assert report["workflow_steps"][-1]["step_status"] == "blocked"
    assert report["acceptance_gates"] == {
        "workflow_status_package_ready": True,
        "source_arrival_gate_ready": True,
        "customer_data_request_ready": True,
        "customer_slice_ready_for_revalidation": False,
        "field_outcome_validated": False,
        "feedback_candidates_present": False,
        "shadow_replay_executed": False,
        "holdout_review_executed": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert report["next_required_artifact"] == (
        "customer_field_slice_submission_or_target_outcome_artifact"
    )
    assert any(
        command["command"].startswith(
            ".venv/bin/python experiments/r12_customer_field_slice_intake_validation.py"
        )
        for command in report["operator_runbook"]["commands_after_source_arrival"]
    )
    assert "field validation 已完成" in report["blocked_claims"]
    assert "runtime_default_allowed=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_customer_validation_workflow_status_moves_to_intake_when_source_arrives():
    arrival = copy.deepcopy(_load_current_l20())
    arrival["status"] = "r12_target_outcome_or_customer_field_slice_arrival_ready_for_revalidation"
    arrival["acceptance_gates"].update(
        {
            "customer_approval_present": True,
            "customer_field_slice_present": True,
            "field_or_pre_outcome_revalidation_ready": True,
            "outcome_source_arrived": True,
        }
    )

    report = build_r12_customer_validation_workflow_status(
        artifact_id="r12-customer-validation-workflow-status-test",
        run_id="r12-l27-test",
        workflow_generated_at="2026-06-28T12:00:00Z",
        r12_target_outcome_or_customer_field_slice_arrival=arrival,
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        r12_customer_field_slice_intake_validation=_load_current_l22(),
        r12_customer_field_slice_revalidation=_load_current_l23(),
        r12_customer_field_outcome_feedback_update=_load_current_l24(),
        r12_customer_feedback_update_shadow_replay=_load_current_l25(),
        r12_customer_feedback_shadow_replay_holdout_review=_load_current_l26(),
    )

    assert report["status"] == "r12_customer_validation_workflow_waiting_for_intake"
    assert report["workflow_summary"]["current_stage"] == "intake_pending"
    assert report["workflow_summary"]["next_action"] == (
        "run_customer_field_slice_intake_validation"
    )
    assert report["workflow_summary"]["blocking_artifact_id"] == (
        "r12-customer-field-slice-intake-validation-current-001"
    )
    assert report["workflow_steps"][0]["step_status"] == "ready"
    assert report["workflow_steps"][2]["step_status"] == "pending"
    assert report["acceptance_gates"][
        "customer_slice_ready_for_revalidation"
    ] is False
    assert report["next_required_artifact"] == (
        "r12_customer_field_slice_intake_validation"
    )


def test_r12_customer_validation_workflow_status_writer_and_cli(tmp_path):
    paths = _write_current_inputs(tmp_path)
    output = tmp_path / "workflow-status.json"

    output_path = write_r12_customer_validation_workflow_status(
        output=output,
        artifact_id="r12-customer-validation-workflow-status-test",
        run_id="r12-l27-test",
        workflow_generated_at="2026-06-28T12:00:00Z",
        r12_target_outcome_or_customer_field_slice_arrival=_load_current_l20(),
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        r12_customer_field_slice_intake_validation=_load_current_l22(),
        r12_customer_field_slice_revalidation=_load_current_l23(),
        r12_customer_field_outcome_feedback_update=_load_current_l24(),
        r12_customer_feedback_update_shadow_replay=_load_current_l25(),
        r12_customer_feedback_shadow_replay_holdout_review=_load_current_l26(),
    )
    assert output_path == output
    assert json.loads(output.read_text())["workflow_summary"][
        "current_stage"
    ] == "source_arrival_pending"

    cli_output = tmp_path / "workflow-status-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_validation_workflow_status.py",
            "--artifact-id",
            "r12-customer-validation-workflow-status-cli",
            "--run-id",
            "r12-l27-cli-test",
            "--workflow-generated-at",
            "2026-06-28T12:00:00Z",
            "--r12-target-outcome-or-customer-field-slice-arrival-path",
            str(paths["l20"]),
            "--r12-customer-field-slice-handoff-package-path",
            str(paths["l21"]),
            "--r12-customer-field-slice-intake-validation-path",
            str(paths["l22"]),
            "--r12-customer-field-slice-revalidation-path",
            str(paths["l23"]),
            "--r12-customer-field-outcome-feedback-update-path",
            str(paths["l24"]),
            "--r12-customer-feedback-update-shadow-replay-path",
            str(paths["l25"]),
            "--r12-customer-feedback-shadow-replay-holdout-review-path",
            str(paths["l26"]),
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
        "r12-customer-validation-workflow-status-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-customer-validation-workflow-status-cli",
        "current_stage": "source_arrival_pending",
        "output": str(cli_output),
        "status": "r12_customer_validation_workflow_waiting_for_source",
    }


def _load_current_l20():
    return _load_result(
        "r12_target_outcome_or_customer_field_slice_arrival/"
        "r12-target-outcome-or-customer-field-slice-arrival-current-001.json"
    )


def _load_current_l21():
    return _load_result(
        "r12_customer_field_slice_handoff_package/"
        "r12-customer-field-slice-handoff-package-current-001.json"
    )


def _load_current_l22():
    return _load_result(
        "r12_customer_field_slice_intake_validation/"
        "r12-customer-field-slice-intake-validation-current-001.json"
    )


def _load_current_l23():
    return _load_result(
        "r12_customer_field_slice_revalidation/"
        "r12-customer-field-slice-revalidation-current-001.json"
    )


def _load_current_l24():
    return _load_result(
        "r12_customer_field_outcome_feedback_update/"
        "r12-customer-field-outcome-feedback-update-current-001.json"
    )


def _load_current_l25():
    return _load_result(
        "r12_customer_feedback_update_shadow_replay/"
        "r12-customer-feedback-update-shadow-replay-current-001.json"
    )


def _load_current_l26():
    return _load_result(
        "r12_customer_feedback_shadow_replay_holdout_review/"
        "r12-customer-feedback-shadow-replay-holdout-review-current-001.json"
    )


def _load_result(relative_path: str) -> dict:
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads((repo_root / "experiments/results" / relative_path).read_text())


def _write_current_inputs(tmp_path: Path) -> dict[str, Path]:
    payloads = {
        "l20": _load_current_l20(),
        "l21": _load_current_l21(),
        "l22": _load_current_l22(),
        "l23": _load_current_l23(),
        "l24": _load_current_l24(),
        "l25": _load_current_l25(),
        "l26": _load_current_l26(),
    }
    paths = {}
    for key, payload in payloads.items():
        path = tmp_path / f"{key}.json"
        path.write_text(json.dumps(payload, allow_nan=False))
        paths[key] = path
    return paths
