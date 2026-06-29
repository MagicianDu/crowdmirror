import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_real_source_validation_execution_packet import (
    R12_REAL_SOURCE_VALIDATION_EXECUTION_PACKET_SCHEMA_VERSION,
    build_r12_real_source_validation_execution_packet,
    write_r12_real_source_validation_execution_packet,
)


def test_r12_real_source_validation_execution_packet_declares_full_source_arrival_runbook():
    packet = build_r12_real_source_validation_execution_packet(
        artifact_id="r12-real-source-validation-execution-packet-test",
        run_id="r12-l37-test",
        packet_created_at="2026-06-28T17:00:00Z",
        r12_customer_validation_workflow_status=_load_current_l27(),
        r12_customer_validation_workflow_status_path=_current_l27_path(),
        r12_customer_trial_evidence_ledger=_load_current_l36(),
        r12_customer_trial_evidence_ledger_path=_current_l36_path(),
    )

    assert packet["schema_version"] == (
        R12_REAL_SOURCE_VALIDATION_EXECUTION_PACKET_SCHEMA_VERSION
    )
    assert packet["status"] == (
        "r12_real_source_validation_execution_packet_ready_source_pending"
    )
    assert packet["claim_level"] == (
        "real_source_execution_packet_ready_no_validation_claim"
    )
    assert packet["execution_summary"] == {
        "packet_created_at": "2026-06-28T17:00:00Z",
        "workflow_artifact_id": "r12-customer-validation-workflow-status-current-001",
        "evidence_ledger_artifact_id": "r12-customer-trial-evidence-ledger-current-001",
        "current_stage": "source_arrival_pending",
        "next_action": "collect_customer_field_slice_or_wait_for_target_outcome",
        "source_arrived": False,
        "execution_chain_declared": True,
        "executable_step_count": 5,
        "manual_approval_point_count": 2,
        "blocking_gap_count": 3,
        "next_required_artifact": "real_customer_field_slice_or_public_target_outcome",
    }
    assert packet["source_modes"] == [
        {
            "source_mode": "customer_field_slice",
            "required_placeholder": "CUSTOMER_FIELD_SLICE_PATH",
            "accepted_formats": ["csv", "jsonl"],
            "minimum_case_count": 10,
            "approval_reference_required": True,
        },
        {
            "source_mode": "public_target_outcome",
            "required_placeholder": "PUBLIC_TARGET_OUTCOME_ARTIFACT_PATH",
            "accepted_formats": ["json"],
            "minimum_case_count": 10,
            "approval_reference_required": False,
        },
    ]
    assert [step["step_id"] for step in packet["execution_steps"]] == [
        "l22_intake_validation",
        "l23_field_revalidation",
        "l24_feedback_update_candidate",
        "l25_shadow_replay",
        "l26_holdout_review",
    ]
    first_step = packet["execution_steps"][0]
    assert first_step == {
        "step_id": "l22_intake_validation",
        "requires_source_arrival": True,
        "requires_manual_approval": True,
        "input_artifact_placeholder": "CUSTOMER_FIELD_SLICE_PATH",
        "output_artifact_path": (
            "experiments/results/r12_customer_field_slice_intake_validation/"
            "r12-customer-field-slice-intake-validation-customer-001.json"
        ),
        "command_template": (
            ".venv/bin/python experiments/r12_customer_field_slice_intake_validation.py "
            "--artifact-id r12-customer-field-slice-intake-validation-customer-001 "
            "--run-id r12-customer-field-slice-intake-customer-001 "
            "--r12-customer-field-slice-handoff-package-path "
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-handoff-package-current-001.json "
            "--intake-checked-at CUSTOMER_FIELD_SLICE_INTAKE_TIMESTAMP "
            "--customer-field-slice-path CUSTOMER_FIELD_SLICE_PATH "
            "--output experiments/results/r12_customer_field_slice_intake_validation/"
            "r12-customer-field-slice-intake-validation-customer-001.json"
        ),
    }
    assert packet["execution_steps"][-1]["command_template"].endswith(
        "--output experiments/results/r12_customer_feedback_shadow_replay_holdout_review/"
        "r12-customer-feedback-shadow-replay-holdout-review-customer-001.json"
    )
    assert packet["acceptance_gates"] == {
        "real_source_validation_execution_packet_ready": True,
        "workflow_status_package_ready": True,
        "customer_trial_evidence_ledger_ready": True,
        "execution_chain_declared": True,
        "source_arrived": False,
        "metrics_computed_on_real_customer_slice": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert packet["next_required_artifact"] == (
        "real_customer_field_slice_or_public_target_outcome"
    )
    assert "runtime_default_allowed=true" in packet["blocked_claims"]
    json.dumps(packet, allow_nan=False)


def test_r12_real_source_validation_execution_packet_writer_and_cli(tmp_path):
    l27_path = tmp_path / "l27.json"
    l36_path = tmp_path / "l36.json"
    l27_path.write_text(json.dumps(_load_current_l27(), allow_nan=False))
    l36_path.write_text(json.dumps(_load_current_l36(), allow_nan=False))
    output = tmp_path / "execution-packet.json"

    output_path = write_r12_real_source_validation_execution_packet(
        output=output,
        artifact_id="r12-real-source-validation-execution-packet-test",
        run_id="r12-l37-test",
        packet_created_at="2026-06-28T17:00:00Z",
        r12_customer_validation_workflow_status=_load_current_l27(),
        r12_customer_validation_workflow_status_path=l27_path,
        r12_customer_trial_evidence_ledger=_load_current_l36(),
        r12_customer_trial_evidence_ledger_path=l36_path,
    )

    assert output_path == output
    assert json.loads(output.read_text())["acceptance_gates"][
        "real_source_validation_execution_packet_ready"
    ] is True

    cli_output = tmp_path / "execution-packet-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_real_source_validation_execution_packet.py",
            "--artifact-id",
            "r12-real-source-validation-execution-packet-cli",
            "--run-id",
            "r12-l37-cli-test",
            "--packet-created-at",
            "2026-06-28T17:00:00Z",
            "--r12-customer-validation-workflow-status-path",
            str(l27_path),
            "--r12-customer-trial-evidence-ledger-path",
            str(l36_path),
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
        "r12-real-source-validation-execution-packet-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-real-source-validation-execution-packet-cli",
        "execution_step_count": 5,
        "output": str(cli_output),
        "status": (
            "r12_real_source_validation_execution_packet_ready_source_pending"
        ),
    }


def _load_current_l27():
    return json.loads(_current_l27_path().read_text())


def _load_current_l36():
    return json.loads(_current_l36_path().read_text())


def _current_l27_path() -> Path:
    return (
        _repo_root()
        / "experiments/results/r12_customer_validation_workflow_status/"
        "r12-customer-validation-workflow-status-current-001.json"
    )


def _current_l36_path() -> Path:
    return (
        _repo_root()
        / "experiments/results/r12_customer_trial_evidence_ledger/"
        "r12-customer-trial-evidence-ledger-current-001.json"
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
