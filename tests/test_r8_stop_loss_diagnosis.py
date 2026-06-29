import json
import subprocess
import sys

from experiments.r8_stop_loss_diagnosis import build_r8_stop_loss_diagnosis


def test_r8_stop_loss_diagnosis_explains_diagnostic_asset_decision():
    report = build_r8_stop_loss_diagnosis(
        artifact_id="r8-stop-loss-diagnosis-test",
        run_id="r8-stop-loss-run",
    )

    assert report["schema_version"] == "r8-stop-loss-diagnosis-v1"
    assert report["status"] == "r8_stop_loss_diagnosis_ready"
    assert report["research_decision"] == "keep_r8_as_diagnostic_asset"
    assert report["evidence_summary"]["r8_metric_win_count"] == 1
    assert report["evidence_summary"]["r8_winning_metrics"] == ["risk_ranking_quality"]
    assert report["evidence_summary"]["l1_status"] == "diagnostic_blocked"
    assert report["evidence_summary"]["l2_status"] == "diagnostic_blocked"
    assert report["acceptance_gates"] == {
        "stop_loss_diagnosis_present": True,
        "product_diagnostic_ingestion_allowed": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert "not_beating_fixed_rule_baseline" in report["root_causes"]
    assert "l1_l2_gate_blocked" in report["root_causes"]
    assert "field_customer_outcome_missing" in report["root_causes"]
    assert "R8 validated" in report["blocked_claims"]
    assert "runtime default ready" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r8_stop_loss_diagnosis_maps_research_and_product_next_tracks():
    report = build_r8_stop_loss_diagnosis(
        artifact_id="r8-stop-loss-diagnosis-test",
        run_id="r8-stop-loss-run",
    )

    assert report["product_decision"] == {
        "display_level": "diagnostic_only",
        "customer_visible_use": "failure_diagnosis_and_outcome_replay",
        "product_core_method_claim_allowed": False,
    }
    assert report["recommended_next_tracks"] == [
        {
            "track_id": "research_stronger_learnable_operator",
            "goal": "replace fixed current-proxy heuristics with a stronger transferable mechanism learner",
            "entry_condition": "new operator must beat R7 v2 on more than one metric and pass L1 gate",
        },
        {
            "track_id": "field_or_customer_outcome",
            "goal": "collect or ingest real outcome evidence that can validate trend, interval, ranking, and false-alarm control",
            "entry_condition": "at least one field/customer outcome has aligned scenario, segment, and mechanism trace",
        },
        {
            "track_id": "product_failure_diagnosis_hardening",
            "goal": "turn blocked R8 evidence into customer-facing risk boundary, replay, and learning workflow",
            "entry_condition": "all blocked claims remain source-backed and runtime-default false",
        },
    ]
    assert report["source_refs"]


def test_r8_stop_loss_diagnosis_cli_writes_artifact(tmp_path):
    output = tmp_path / "r8-stop-loss-diagnosis.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r8_stop_loss_diagnosis.py",
            "--artifact-id",
            "r8-stop-loss-diagnosis-cli",
            "--run-id",
            "r8-stop-loss-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r8-stop-loss-diagnosis-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r8-stop-loss-diagnosis-cli",
        "output": str(output),
        "research_decision": "keep_r8_as_diagnostic_asset",
        "status": "r8_stop_loss_diagnosis_ready",
    }
