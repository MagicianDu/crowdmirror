import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_recall_oriented_update import (
    R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION,
    build_r12_recall_oriented_update,
)


def test_r12_recall_oriented_update_selects_guarded_activation_margin_candidate():
    report = build_r12_recall_oriented_update(
        artifact_id="r12-recall-oriented-update-test",
        run_id="r12-l7-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_high_risk_holdout_transfer_replay=_load_current_high_risk_replay(),
    )

    assert report["schema_version"] == R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION
    assert report["status"] == "r12_recall_oriented_update_ready_research_guarded"
    assert report["claim_level"] == "research_only_recall_positive_false_alarm_tradeoff"
    assert report["update_candidate"] == {
        "update_id": "r12-high-risk-activation-margin-recall-001",
        "update_type": "high_risk_activation_margin",
        "target": "high_risk_activation_margin",
        "current_value": 0.03,
        "recommended_value": 0.01,
        "status": "accepted_for_research_replay",
        "default_runtime_enabled": False,
        "product_default_allowed": False,
    }
    assert report["evaluation_summary"] == {
        "evaluated_case_count": 70,
        "observed_high_risk_case_count": 29,
        "observed_low_risk_case_count": 41,
        "excluded_train_case_count": 2,
        "minimum_valid_response_count": 100,
    }
    assert report["metric_comparison"] == {
        "static_prior_miss_recovery": {
            "eligible_case_count": 29,
            "before": 0.413793,
            "after": 0.62069,
            "delta": 0.206897,
        },
        "abnormal_segment_recall": {
            "eligible_case_count": 29,
            "before": 0.413793,
            "after": 0.62069,
            "delta": 0.206897,
        },
        "false_alarm_rate": {
            "evaluable_case_count": 41,
            "before": 0.097561,
            "after": 0.170732,
            "delta": 0.073171,
        },
        "precision": {
            "before": 0.75,
            "after": 0.72,
            "delta": -0.03,
        },
        "interval_coverage": {
            "before": 0.8,
            "after": 0.8,
            "delta": 0.0,
        },
    }
    assert report["acceptance_gates"] == {
        "source_backed_public_proxy_present": True,
        "recall_improved": True,
        "false_alarm_delta_within_research_ceiling": True,
        "false_alarm_non_regression": False,
        "precision_non_regression": False,
        "interval_coverage_non_regression": True,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "research_guarded_recall_candidate_accept_false_alarm_tradeoff"
    )
    assert report["next_required_artifact"] == (
        "r12_recall_update_holdout_false_alarm_stress_test"
    )
    assert "false_alarm_non_regression=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_recall_oriented_update_reports_recovered_and_false_alarm_cases():
    report = build_r12_recall_oriented_update(
        artifact_id="r12-recall-oriented-update-test",
        run_id="r12-l7-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_high_risk_holdout_transfer_replay=_load_current_high_risk_replay(),
    )

    assert report["newly_recovered_static_prior_miss_case_ids"] == [
        "hps_ESEX_1",
        "hps_RRACETH_1",
        "hps_TAGE_46",
        "hps_TAGE_60",
        "hps_TAGE_64",
        "hps_TAGE_73",
    ]
    assert report["new_false_alarm_case_ids"] == [
        "hps_TAGE_58",
        "hps_TAGE_59",
        "hps_TAGE_62",
    ]
    assert report["threshold_sweep"][:4] == [
        {
            "activation_margin": 0.03,
            "recall": 0.413793,
            "false_alarm_rate": 0.097561,
            "precision": 0.75,
            "recall_delta": 0.0,
            "false_alarm_delta": 0.0,
            "passes_research_ceiling": True,
        },
        {
            "activation_margin": 0.02,
            "recall": 0.448276,
            "false_alarm_rate": 0.146341,
            "precision": 0.684211,
            "recall_delta": 0.034483,
            "false_alarm_delta": 0.04878,
            "passes_research_ceiling": True,
        },
        {
            "activation_margin": 0.015,
            "recall": 0.551724,
            "false_alarm_rate": 0.170732,
            "precision": 0.695652,
            "recall_delta": 0.137931,
            "false_alarm_delta": 0.073171,
            "passes_research_ceiling": True,
        },
        {
            "activation_margin": 0.01,
            "recall": 0.62069,
            "false_alarm_rate": 0.170732,
            "precision": 0.72,
            "recall_delta": 0.206897,
            "false_alarm_delta": 0.073171,
            "passes_research_ceiling": True,
        },
    ]


def test_r12_recall_oriented_update_cli_writes_artifact(tmp_path):
    hps_path = tmp_path / "hps-ingestion.json"
    transfer_path = tmp_path / "r12-transfer-validation.json"
    replay_path = tmp_path / "r12-high-risk-replay.json"
    output = tmp_path / "r12-recall-oriented-update.json"
    hps_path.write_text(json.dumps(_load_current_hps_ingestion(), allow_nan=False))
    transfer_path.write_text(
        json.dumps(_load_current_transfer_validation(), allow_nan=False)
    )
    replay_path.write_text(
        json.dumps(_load_current_high_risk_replay(), allow_nan=False)
    )

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_recall_oriented_update.py",
            "--artifact-id",
            "r12-recall-oriented-update-cli",
            "--run-id",
            "r12-l7-test",
            "--hps-ingestion-path",
            str(hps_path),
            "--r12-transfer-validation-path",
            str(transfer_path),
            "--r12-high-risk-holdout-transfer-replay-path",
            str(replay_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r12-recall-oriented-update-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-recall-oriented-update-cli",
        "output": str(output),
        "status": "r12_recall_oriented_update_ready_research_guarded",
    }


def _load_current_hps_ingestion():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r10_hps_policy_reaction_ingestion/"
            "r10-hps-policy-reaction-ingestion-current-001.json"
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


def _load_current_high_risk_replay():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_high_risk_holdout_transfer_replay/"
            "r12-high-risk-holdout-transfer-replay-current-001.json"
        ).read_text()
    )
