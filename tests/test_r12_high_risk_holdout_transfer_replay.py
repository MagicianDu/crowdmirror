import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_high_risk_holdout_transfer_replay import (
    R12_HIGH_RISK_HOLDOUT_TRANSFER_REPLAY_SCHEMA_VERSION,
    build_r12_high_risk_holdout_transfer_replay,
)


def test_r12_high_risk_holdout_transfer_replay_reports_research_only_partial_signal():
    replay = build_r12_high_risk_holdout_transfer_replay(
        artifact_id="r12-high-risk-holdout-transfer-replay-test",
        run_id="r12-l6-test",
        r12_high_risk_holdout_registry=_load_current_high_risk_registry(),
        r12_transfer_validation=_load_current_transfer_validation(),
    )

    assert replay["schema_version"] == R12_HIGH_RISK_HOLDOUT_TRANSFER_REPLAY_SCHEMA_VERSION
    assert replay["status"] == (
        "r12_high_risk_holdout_transfer_replay_partial_research_positive"
    )
    assert replay["claim_level"] == "research_only_sensitive_public_proxy_replay"
    assert replay["replay_contract"] == {
        "source_backed_public_proxy": True,
        "uses_research_only_high_risk_candidates": True,
        "sensitive_or_high_governance_axes_present": True,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert replay["replay_summary"] == {
        "candidate_case_count": 29,
        "recoverable_static_prior_miss_case_count": 12,
        "product_default_eligible_case_count": 0,
        "sensitive_or_high_governance_case_count": 29,
        "false_alarm_evaluable_case_count": 0,
    }
    assert replay["metric_comparison"] == {
        "mean_absolute_error": {
            "before": 0.087818,
            "after": 0.084134,
            "delta": -0.003684,
        },
        "static_prior_miss_recovery": {
            "eligible_case_count": 29,
            "before": 0.413793,
            "after": 0.413793,
            "delta": 0.0,
        },
        "abnormal_segment_recall": {
            "eligible_case_count": 29,
            "before": 0.413793,
            "after": 0.413793,
            "delta": 0.0,
        },
        "interval_coverage": {
            "before": 0.62069,
            "after": 0.62069,
            "delta": 0.0,
        },
        "risk_ranking_quality": {
            "before": 0.662562,
            "after": 0.662562,
            "delta": 0.0,
        },
        "false_alarm_rate": {
            "evaluable_case_count": 0,
            "before": None,
            "after": None,
            "delta": None,
        },
    }
    assert replay["acceptance_gates"] == {
        "source_backed_public_proxy_present": True,
        "high_risk_replay_executed": True,
        "mae_improved": True,
        "static_prior_miss_recovery_improved": False,
        "abnormal_segment_recall_improved": False,
        "interval_coverage_non_regression": True,
        "risk_ranking_non_regression": True,
        "false_alarm_rate_evaluable": False,
        "product_default_eligible_high_risk_holdout_present": False,
        "product_core_method_ready": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert replay["transfer_decision"] == (
        "r12_high_risk_replay_mae_positive_recall_flat_research_only"
    )
    assert replay["product_support_level"] == (
        "research_only_mae_positive_recall_and_product_default_gap"
    )
    assert "R12 Product default high-risk recovery validated" in replay["blocked_claims"]
    json.dumps(replay, allow_nan=False)


def test_r12_high_risk_holdout_transfer_replay_keeps_case_level_audit_rows():
    replay = build_r12_high_risk_holdout_transfer_replay(
        artifact_id="r12-high-risk-holdout-transfer-replay-test",
        run_id="r12-l6-test",
        r12_high_risk_holdout_registry=_load_current_high_risk_registry(),
        r12_transfer_validation=_load_current_transfer_validation(),
    )

    first = replay["case_replays"][0]
    assert first == {
        "case_id": "hps_TAGE_81",
        "segment_labels": {
            "segment_column": "TAGE",
            "segment_value": "81",
            "sensitivity_level": "protected_sensitive",
        },
        "observed_value": 0.763693,
        "before_prediction": 0.579212,
        "after_prediction": 0.597381,
        "static_prior_prediction": 0.454619,
        "absolute_error_before": 0.184481,
        "absolute_error_after": 0.166312,
        "before_predicted_high_risk": True,
        "after_predicted_high_risk": True,
        "observed_high_risk": True,
        "static_prior_missed_observed_high_risk": True,
        "before_static_prior_miss_recovered": True,
        "after_static_prior_miss_recovered": True,
        "before_interval_hit": False,
        "after_interval_hit": False,
        "product_default_eligible": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert len(replay["case_replays"]) == 29


def test_r12_high_risk_holdout_transfer_replay_cli_writes_artifact(tmp_path):
    registry_path = tmp_path / "r12-high-risk-registry.json"
    transfer_path = tmp_path / "r12-transfer-validation.json"
    output = tmp_path / "r12-high-risk-transfer-replay.json"
    registry_path.write_text(
        json.dumps(_load_current_high_risk_registry(), allow_nan=False)
    )
    transfer_path.write_text(
        json.dumps(_load_current_transfer_validation(), allow_nan=False)
    )

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_high_risk_holdout_transfer_replay.py",
            "--artifact-id",
            "r12-high-risk-holdout-transfer-replay-cli",
            "--run-id",
            "r12-l6-test",
            "--r12-high-risk-holdout-registry-path",
            str(registry_path),
            "--r12-transfer-validation-path",
            str(transfer_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r12-high-risk-holdout-transfer-replay-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-high-risk-holdout-transfer-replay-cli",
        "output": str(output),
        "status": (
            "r12_high_risk_holdout_transfer_replay_partial_research_positive"
        ),
    }


def _load_current_high_risk_registry():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_high_risk_holdout_registry/"
            "r12-high-risk-holdout-registry-current-001.json"
        ).read_text()
    )


def _load_current_transfer_validation():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_transfer_validation/"
            "r12-transfer-validation-current-001.json"
        ).read_text()
    )
