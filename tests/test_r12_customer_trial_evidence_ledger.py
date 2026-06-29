import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_trial_evidence_ledger import (
    R12_CUSTOMER_TRIAL_EVIDENCE_LEDGER_SCHEMA_VERSION,
    build_r12_customer_trial_evidence_ledger,
    write_r12_customer_trial_evidence_ledger,
)


def test_r12_customer_trial_evidence_ledger_aggregates_trial_and_rehearsal_chain():
    ledger = build_r12_customer_trial_evidence_ledger(
        artifact_id="r12-customer-trial-evidence-ledger-test",
        run_id="r12-l36-test",
        ledger_created_at="2026-06-28T16:10:00Z",
        r12_customer_trial_launch_bundle_verification=_load_current_l32(),
        r12_customer_trial_launch_bundle_verification_path=_current_l32_path(),
        r12_customer_field_slice_operator_rehearsal=_load_current_l34(),
        r12_customer_field_slice_operator_rehearsal_path=_current_l34_path(),
        r12_customer_feedback_loop_operator_rehearsal=_load_current_l35(),
        r12_customer_feedback_loop_operator_rehearsal_path=_current_l35_path(),
    )

    assert ledger["schema_version"] == (
        R12_CUSTOMER_TRIAL_EVIDENCE_LEDGER_SCHEMA_VERSION
    )
    assert ledger["status"] == (
        "r12_customer_trial_evidence_ledger_ready_source_pending"
    )
    assert ledger["claim_level"] == (
        "customer_trial_readiness_and_rehearsal_ledger_no_validation_claim"
    )
    assert ledger["ledger_summary"] == {
        "ledger_created_at": "2026-06-28T16:10:00Z",
        "launch_bundle_verified": True,
        "operator_rehearsal_executed": True,
        "feedback_loop_rehearsed_l22_to_l26": True,
        "customer_visible_readiness_evidence_count": 1,
        "operator_only_rehearsal_evidence_count": 2,
        "blocking_gap_count": 3,
        "next_required_artifact": "real_customer_field_slice_or_public_target_outcome",
    }
    assert ledger["evidence_rows"] == [
        {
            "evidence_id": "customer_launch_bundle_verified",
            "source_artifact_id": (
                "r12-customer-trial-launch-bundle-verification-current-001"
            ),
            "evidence_scope": "customer_visible_trial_readiness",
            "evidence_status": "ready_source_pending",
            "customer_visible": True,
            "validation_claim_allowed": False,
            "product_default_allowed": False,
        },
        {
            "evidence_id": "customer_field_slice_operator_rehearsed",
            "source_artifact_id": (
                "r12-customer-field-slice-operator-rehearsal-current-001"
            ),
            "evidence_scope": "operator_only_synthetic_rehearsal",
            "evidence_status": "rehearsed_no_field_claim",
            "customer_visible": False,
            "validation_claim_allowed": False,
            "product_default_allowed": False,
        },
        {
            "evidence_id": "customer_feedback_loop_rehearsed_l22_to_l26",
            "source_artifact_id": (
                "r12-customer-feedback-loop-operator-rehearsal-current-001"
            ),
            "evidence_scope": "operator_only_synthetic_rehearsal",
            "evidence_status": "rehearsed_no_field_claim",
            "customer_visible": False,
            "validation_claim_allowed": False,
            "product_default_allowed": False,
        },
    ]
    assert ledger["blocking_gaps"] == [
        {
            "gap_id": "real_customer_field_slice_missing",
            "required_artifact": "real_customer_field_slice",
            "blocks_claim": "metrics_computed_on_real_customer_slice=true",
        },
        {
            "gap_id": "public_target_outcome_missing",
            "required_artifact": "may_2026_dot_target_outcome_or_equivalent",
            "blocks_claim": "pre_outcome_field_validation_passed=true",
        },
        {
            "gap_id": "field_outcome_validation_missing",
            "required_artifact": "field_outcome_validation_report",
            "blocks_claim": "runtime_default_allowed=true",
        },
    ]
    assert ledger["acceptance_gates"] == {
        "customer_trial_evidence_ledger_ready": True,
        "launch_bundle_verified": True,
        "operator_rehearsal_executed": True,
        "feedback_loop_rehearsed_l22_to_l26": True,
        "real_customer_field_slice_submitted": False,
        "metrics_computed_on_real_customer_slice": False,
        "field_outcome_validated": False,
        "claim_boundary_machine_checkable": True,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert ledger["next_required_artifact"] == (
        "real_customer_field_slice_or_public_target_outcome"
    )
    assert "Product can show customer trial readiness evidence" in " ".join(
        ledger["allowed_claims"]
    )
    assert "runtime_default_allowed=true" in ledger["blocked_claims"]
    json.dumps(ledger, allow_nan=False)


def test_r12_customer_trial_evidence_ledger_writer_and_cli(tmp_path):
    l32_path = tmp_path / "l32.json"
    l34_path = tmp_path / "l34.json"
    l35_path = tmp_path / "l35.json"
    l32_path.write_text(json.dumps(_load_current_l32(), allow_nan=False))
    l34_path.write_text(json.dumps(_load_current_l34(), allow_nan=False))
    l35_path.write_text(json.dumps(_load_current_l35(), allow_nan=False))
    output = tmp_path / "trial-evidence-ledger.json"

    output_path = write_r12_customer_trial_evidence_ledger(
        output=output,
        artifact_id="r12-customer-trial-evidence-ledger-test",
        run_id="r12-l36-test",
        ledger_created_at="2026-06-28T16:10:00Z",
        r12_customer_trial_launch_bundle_verification=_load_current_l32(),
        r12_customer_trial_launch_bundle_verification_path=l32_path,
        r12_customer_field_slice_operator_rehearsal=_load_current_l34(),
        r12_customer_field_slice_operator_rehearsal_path=l34_path,
        r12_customer_feedback_loop_operator_rehearsal=_load_current_l35(),
        r12_customer_feedback_loop_operator_rehearsal_path=l35_path,
    )

    assert output_path == output
    assert json.loads(output.read_text())["acceptance_gates"][
        "customer_trial_evidence_ledger_ready"
    ] is True

    cli_output = tmp_path / "trial-evidence-ledger-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_trial_evidence_ledger.py",
            "--artifact-id",
            "r12-customer-trial-evidence-ledger-cli",
            "--run-id",
            "r12-l36-cli-test",
            "--ledger-created-at",
            "2026-06-28T16:10:00Z",
            "--r12-customer-trial-launch-bundle-verification-path",
            str(l32_path),
            "--r12-customer-field-slice-operator-rehearsal-path",
            str(l34_path),
            "--r12-customer-feedback-loop-operator-rehearsal-path",
            str(l35_path),
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
        "r12-customer-trial-evidence-ledger-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-customer-trial-evidence-ledger-cli",
        "customer_trial_evidence_ledger_ready": True,
        "output": str(cli_output),
        "status": "r12_customer_trial_evidence_ledger_ready_source_pending",
    }


def _load_current_l32():
    return json.loads(_current_l32_path().read_text())


def _load_current_l34():
    return json.loads(_current_l34_path().read_text())


def _load_current_l35():
    return json.loads(_current_l35_path().read_text())


def _current_l32_path() -> Path:
    return (
        _repo_root()
        / "experiments/results/r12_customer_trial_launch_bundle_verification/"
        "r12-customer-trial-launch-bundle-verification-current-001.json"
    )


def _current_l34_path() -> Path:
    return (
        _repo_root()
        / "experiments/results/r12_customer_field_slice_operator_rehearsal/"
        "r12-customer-field-slice-operator-rehearsal-current-001.json"
    )


def _current_l35_path() -> Path:
    return (
        _repo_root()
        / "experiments/results/r12_customer_feedback_loop_operator_rehearsal/"
        "r12-customer-feedback-loop-operator-rehearsal-current-001.json"
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
