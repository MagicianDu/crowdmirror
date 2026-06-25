import json
import subprocess
import sys

from experiments.r9_false_alarm_gate_redesign import (
    build_r9_false_alarm_gate_redesign,
)
from experiments.r9_holdout_guard import build_r9_holdout_guard


def test_r9_false_alarm_gate_redesign_defines_near_threshold_downgrade_rule():
    gate = build_r9_false_alarm_gate_redesign(
        artifact_id="r9-false-alarm-gate-redesign-test",
        run_id="r9-false-alarm-run",
    )

    assert gate["schema_version"] == "r9-false-alarm-gate-redesign-v1"
    assert gate["status"] == "r9_false_alarm_gate_redesign_ready_guarded"
    assert gate["candidate_combination_id"] == "A+B+C"
    assert gate["gate_contract"] == {
        "targets_near_threshold_false_alarm": True,
        "uses_strong_static_prior_guard": True,
        "requires_external_evidence_margin": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert gate["gate_rule"] == {
        "rule_id": "strong_prior_near_threshold_evidence_margin",
        "near_threshold_band": 0.03,
        "strong_static_prior_min_confidence": 0.7,
        "minimum_external_evidence_margin": 0.08,
        "action_when_triggered": "downgrade_high_risk_to_diagnostic_watch",
    }
    assert gate["near_threshold_trial_after_gate"] == {
        "trial_id": "anes_health_near_threshold_false_alarm",
        "risk_signal_before_guard": 0.51,
        "risk_signal_after_guard": 0.49,
        "risk_threshold": 0.5,
        "downgraded_to_diagnostic_watch": True,
        "passed": True,
    }
    assert gate["acceptance_gates"]["near_threshold_false_alarm_fixed"] is True
    assert gate["acceptance_gates"]["runtime_default_allowed"] is False
    assert "R9 validated" in gate["blocked_claims"]
    json.dumps(gate, allow_nan=False)


def test_r9_holdout_guard_can_consume_false_alarm_gate_without_runtime_escalation():
    false_alarm_gate = build_r9_false_alarm_gate_redesign(
        artifact_id="r9-false-alarm-gate-redesign-test",
        run_id="r9-false-alarm-run",
    )
    guard = build_r9_holdout_guard(
        artifact_id="r9-holdout-guard-with-gate-test",
        run_id="r9-false-alarm-run",
        false_alarm_gate_redesign=false_alarm_gate,
    )

    assert guard["status"] == "r9_holdout_guard_passed_guarded"
    assert guard["summary"] == {
        "leave_one_case_pass_rate": 1.0,
        "perturbation_pass_rate": 1.0,
        "near_threshold_false_alarm_passed": True,
        "synthetic_mechanism_recovery_passed": True,
        "overall_holdout_guard_passed": True,
    }
    assert guard["false_alarm_gate_summary"] == {
        "artifact_id": "r9-false-alarm-gate-redesign-test",
        "near_threshold_false_alarm_fixed": True,
        "runtime_default_allowed": False,
    }
    assert guard["research_decision"] == "promote_to_product_ingestion_guarded"
    assert guard["product_decision"] == {
        "display_level": "guarded_diagnostic_candidate",
        "may_show_success_signal": True,
        "may_claim_runtime_method": False,
        "may_claim_field_validation": False,
    }
    assert guard["acceptance_gates"]["holdout_guard_passed"] is True
    assert guard["acceptance_gates"]["runtime_default_allowed"] is False


def test_r9_holdout_guard_cli_can_consume_false_alarm_gate_path(tmp_path):
    false_alarm_gate_output = tmp_path / "r9-false-alarm-gate-redesign.json"
    subprocess.run(
        [
            sys.executable,
            "experiments/r9_false_alarm_gate_redesign.py",
            "--artifact-id",
            "r9-false-alarm-gate-redesign-cli-source",
            "--run-id",
            "r9-false-alarm-run",
            "--output",
            str(false_alarm_gate_output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    holdout_output = tmp_path / "r9-holdout-guard-with-gate.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r9_holdout_guard.py",
            "--artifact-id",
            "r9-holdout-guard-with-gate-cli",
            "--run-id",
            "r9-false-alarm-run",
            "--false-alarm-gate-redesign-path",
            str(false_alarm_gate_output),
            "--output",
            str(holdout_output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(holdout_output.read_text())
    assert artifact["status"] == "r9_holdout_guard_passed_guarded"
    assert artifact["false_alarm_gate_summary"]["artifact_id"] == (
        "r9-false-alarm-gate-redesign-cli-source"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r9-holdout-guard-with-gate-cli",
        "output": str(holdout_output),
        "status": "r9_holdout_guard_passed_guarded",
    }


def test_r9_false_alarm_gate_redesign_cli_writes_artifact(tmp_path):
    output = tmp_path / "r9-false-alarm-gate-redesign.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r9_false_alarm_gate_redesign.py",
            "--artifact-id",
            "r9-false-alarm-gate-redesign-cli",
            "--run-id",
            "r9-false-alarm-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r9-false-alarm-gate-redesign-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r9-false-alarm-gate-redesign-cli",
        "output": str(output),
        "status": "r9_false_alarm_gate_redesign_ready_guarded",
    }
