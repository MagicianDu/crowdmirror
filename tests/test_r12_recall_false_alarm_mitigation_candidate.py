import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_recall_false_alarm_mitigation_candidate import (
    R12_RECALL_FALSE_ALARM_MITIGATION_SCHEMA_VERSION,
    build_r12_recall_false_alarm_mitigation_candidate,
)


def test_r12_recall_false_alarm_mitigation_selects_guarded_band_candidate():
    report = build_r12_recall_false_alarm_mitigation_candidate(
        artifact_id="r12-recall-false-alarm-mitigation-candidate-test",
        run_id="r12-l9-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_recall_oriented_update=_load_current_recall_update(),
        r12_recall_update_false_alarm_stress_test=_load_current_stress_test(),
    )

    assert report["schema_version"] == (
        R12_RECALL_FALSE_ALARM_MITIGATION_SCHEMA_VERSION
    )
    assert (
        report["status"]
        == "r12_recall_false_alarm_mitigation_ready_research_guarded"
    )
    assert report["claim_level"] == (
        "research_only_false_alarm_mitigated_overfit_risk"
    )
    assert report["selected_candidate"] == {
        "candidate_id": "r12-tage-58-62-activation-guard-001",
        "candidate_type": "segment_value_band_activation_margin_guard",
        "target_segment_column": "TAGE",
        "target_segment_value_min": 58,
        "target_segment_value_max": 62,
        "default_activation_margin": 0.01,
        "guarded_activation_margin": 0.03,
        "status": "accepted_for_research_mitigation_replay",
        "overfit_risk": "high_current_false_alarm_band_derived",
        "product_default_allowed": False,
    }
    assert report["selection_policy"] == {
        "selection_rule": (
            "maximize recall retention subject to false-alarm and precision non-regression"
        ),
        "requires_false_alarm_non_regression": True,
        "requires_precision_non_regression": True,
        "allows_current_false_alarm_band_guard_for_research_only": True,
        "product_default_requires_independent_holdout": True,
    }
    assert report["metric_comparison"] == {
        "static_prior_miss_recovery": {
            "before": 0.413793,
            "l7_after": 0.62069,
            "mitigated_after": 0.586207,
            "mitigated_delta": 0.172414,
            "l7_recall_gain_retained": 0.833333,
        },
        "abnormal_segment_recall": {
            "before": 0.413793,
            "l7_after": 0.62069,
            "mitigated_after": 0.586207,
            "mitigated_delta": 0.172414,
            "l7_recall_gain_retained": 0.833333,
        },
        "false_alarm_rate": {
            "before": 0.097561,
            "l7_after": 0.170732,
            "mitigated_after": 0.097561,
            "mitigated_delta": 0.0,
            "l7_false_alarm_delta_removed": 0.073171,
        },
        "precision": {
            "before": 0.75,
            "l7_after": 0.72,
            "mitigated_after": 0.809524,
            "mitigated_delta": 0.059524,
        },
        "interval_coverage": {
            "before": 0.8,
            "l7_after": 0.8,
            "mitigated_after": 0.8,
            "mitigated_delta": 0.0,
        },
    }
    assert report["mitigation_effect_summary"] == {
        "newly_recovered_case_ids": [
            "hps_ESEX_1",
            "hps_RRACETH_1",
            "hps_TAGE_46",
            "hps_TAGE_64",
            "hps_TAGE_73",
        ],
        "removed_l7_false_alarm_case_ids": [
            "hps_TAGE_58",
            "hps_TAGE_59",
            "hps_TAGE_62",
        ],
        "lost_l7_recovered_case_ids": ["hps_TAGE_60"],
        "new_false_alarm_case_ids": [],
    }
    assert report["acceptance_gates"] == {
        "source_backed_public_proxy_present": True,
        "l7_recall_gain_partially_preserved": True,
        "false_alarm_non_regression": True,
        "precision_non_regression": True,
        "protected_sensitive_false_alarm_non_regression": True,
        "l7_new_false_alarms_removed": True,
        "low_sensitive_recall_evaluable": False,
        "overfit_risk_present": True,
        "mitigation_candidate_selected": True,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "accept_research_guarded_mitigation_reject_product_default"
    )
    assert report["next_required_artifact"] == (
        "r12_recall_mitigation_holdout_validation"
    )
    assert (
        "mitigation generalizes beyond current false-alarm band"
        in report["blocked_claims"]
    )
    json.dumps(report, allow_nan=False)


def test_r12_recall_false_alarm_mitigation_reports_candidate_leaderboard():
    report = build_r12_recall_false_alarm_mitigation_candidate(
        artifact_id="r12-recall-false-alarm-mitigation-candidate-test",
        run_id="r12-l9-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_recall_oriented_update=_load_current_recall_update(),
        r12_recall_update_false_alarm_stress_test=_load_current_stress_test(),
    )

    assert report["candidate_leaderboard"] == [
        {
            "candidate_id": "r12-tage-58-62-activation-guard-001",
            "candidate_type": "segment_value_band_activation_margin_guard",
            "recall_delta": 0.172414,
            "false_alarm_rate_delta": 0.0,
            "precision_delta": 0.059524,
            "newly_recovered_count": 5,
            "new_false_alarm_count": 0,
            "passes_mitigation_gate": True,
        },
        {
            "candidate_id": "r12-tage-family-conservative-cap-001",
            "candidate_type": "segment_family_activation_margin_guard",
            "recall_delta": 0.068966,
            "false_alarm_rate_delta": 0.0,
            "precision_delta": 0.027778,
            "newly_recovered_count": 2,
            "new_false_alarm_count": 0,
            "passes_mitigation_gate": True,
        },
        {
            "candidate_id": "r12-global-margin-0015-001",
            "candidate_type": "global_activation_margin",
            "recall_delta": 0.137931,
            "false_alarm_rate_delta": 0.073171,
            "precision_delta": -0.054348,
            "newly_recovered_count": 4,
            "new_false_alarm_count": 3,
            "passes_mitigation_gate": False,
        },
        {
            "candidate_id": "r12-global-margin-002-001",
            "candidate_type": "global_activation_margin",
            "recall_delta": 0.034483,
            "false_alarm_rate_delta": 0.04878,
            "precision_delta": -0.065789,
            "newly_recovered_count": 1,
            "new_false_alarm_count": 2,
            "passes_mitigation_gate": False,
        },
        {
            "candidate_id": "r12-protected-sensitive-conservative-cap-001",
            "candidate_type": "sensitivity_level_activation_margin_guard",
            "recall_delta": 0.0,
            "false_alarm_rate_delta": 0.0,
            "precision_delta": 0.0,
            "newly_recovered_count": 0,
            "new_false_alarm_count": 0,
            "passes_mitigation_gate": False,
        },
    ]


def test_r12_recall_false_alarm_mitigation_cli_writes_artifact(tmp_path):
    hps_path = tmp_path / "hps-ingestion.json"
    transfer_path = tmp_path / "r12-transfer-validation.json"
    recall_update_path = tmp_path / "r12-recall-update.json"
    stress_path = tmp_path / "r12-recall-stress.json"
    output = tmp_path / "r12-recall-false-alarm-mitigation.json"
    hps_path.write_text(json.dumps(_load_current_hps_ingestion(), allow_nan=False))
    transfer_path.write_text(
        json.dumps(_load_current_transfer_validation(), allow_nan=False)
    )
    recall_update_path.write_text(
        json.dumps(_load_current_recall_update(), allow_nan=False)
    )
    stress_path.write_text(json.dumps(_load_current_stress_test(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_recall_false_alarm_mitigation_candidate.py",
            "--artifact-id",
            "r12-recall-false-alarm-mitigation-candidate-cli",
            "--run-id",
            "r12-l9-test",
            "--hps-ingestion-path",
            str(hps_path),
            "--r12-transfer-validation-path",
            str(transfer_path),
            "--r12-recall-oriented-update-path",
            str(recall_update_path),
            "--r12-recall-update-false-alarm-stress-test-path",
            str(stress_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == (
        "r12-recall-false-alarm-mitigation-candidate-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-recall-false-alarm-mitigation-candidate-cli",
        "output": str(output),
        "status": "r12_recall_false_alarm_mitigation_ready_research_guarded",
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


def _load_current_recall_update():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_recall_oriented_update/"
            "r12-recall-oriented-update-current-001.json"
        ).read_text()
    )


def _load_current_stress_test():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_recall_update_false_alarm_stress_test/"
            "r12-recall-update-false-alarm-stress-test-current-001.json"
        ).read_text()
    )
