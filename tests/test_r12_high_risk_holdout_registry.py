import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_high_risk_holdout_registry import (
    R12_HIGH_RISK_HOLDOUT_REGISTRY_SCHEMA_VERSION,
    build_r12_high_risk_holdout_registry,
)


def test_r12_high_risk_holdout_registry_finds_source_backed_research_candidates():
    registry = build_r12_high_risk_holdout_registry(
        artifact_id="r12-high-risk-holdout-registry-test",
        run_id="r12-l5-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=_load_current_transfer_validation(),
    )

    assert registry["schema_version"] == R12_HIGH_RISK_HOLDOUT_REGISTRY_SCHEMA_VERSION
    assert registry["status"] == "r12_high_risk_holdout_registry_ready_research_only"
    assert registry["claim_level"] == "source_backed_public_proxy_high_risk_holdout_candidates"
    assert registry["selection_policy"] == {
        "outcome_proxy": "PRICESTRESS",
        "source_signal": "PRICECONCERN",
        "minimum_valid_response_count": 100,
        "high_risk_rule": "outcome_proxy_share >= global_outcome_risk_share + 0.03",
        "static_prior_miss_required": True,
        "exclude_existing_r12_train_cases": True,
        "product_default_allowed_segment_sensitivity": "low_only",
    }
    assert registry["candidate_summary"] == {
        "scanned_segment_column_count": 6,
        "scanned_case_count": 84,
        "research_eligible_case_count": 29,
        "research_recoverable_static_prior_miss_count": 12,
        "product_default_eligible_case_count": 0,
        "rejected_existing_train_case_count": 2,
        "current_r12_holdout_high_risk_case_count": 0,
        "current_r12_holdout_static_prior_miss_case_count": 0,
    }
    assert registry["metric_support_projection"] == {
        "research_static_prior_miss_recovery_holdout_coverable": True,
        "research_abnormal_segment_recall_holdout_coverable": True,
        "product_default_static_prior_miss_recovery_holdout_coverable": False,
        "product_default_abnormal_segment_recall_holdout_coverable": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert registry["acceptance_gates"] == {
        "source_backed_public_proxy_present": True,
        "current_r12_gap_confirmed": True,
        "high_risk_research_holdout_candidates_present": True,
        "existing_train_cases_excluded": True,
        "product_default_low_sensitive_high_risk_holdout_present": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }

    income_candidate = next(
        case
        for case in registry["holdout_candidate_cases"]
        if case["case_id"] == "hps_RHHINCOME_7"
    )
    assert income_candidate == {
        "case_id": "hps_RHHINCOME_7",
        "segment_labels": {
            "segment_column": "RHHINCOME",
            "segment_value": "7",
            "sensitivity_level": "socioeconomic_sensitive",
        },
        "valid_response_count": 3050,
        "static_prior_prediction": 0.454619,
        "observed_outcome_proxy": 0.601441,
        "source_signal_risk_share": 0.310482,
        "source_signal_delta": 0.066559,
        "r12_after_prediction": 0.491226,
        "observed_high_risk": True,
        "static_prior_missed_observed_high_risk": True,
        "r12_update_recovers_static_prior_miss": True,
        "research_holdout_eligible": True,
        "product_default_eligible": False,
        "product_default_block_reason": "sensitive_or_high_governance_segment_axis",
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert {
        case["case_id"] for case in registry["rejected_high_risk_cases"]
    } == {"hps_METRO_STATUS_2", "hps_REGION_2"}
    assert "R12 Product default high-risk recovery validated" in registry["blocked_claims"]
    json.dumps(registry, allow_nan=False)


def test_r12_high_risk_holdout_registry_cli_writes_artifact(tmp_path):
    hps_path = tmp_path / "hps-ingestion.json"
    transfer_path = tmp_path / "r12-transfer-validation.json"
    output = tmp_path / "r12-high-risk-holdout-registry.json"
    hps_path.write_text(json.dumps(_load_current_hps_ingestion(), allow_nan=False))
    transfer_path.write_text(
        json.dumps(_load_current_transfer_validation(), allow_nan=False)
    )

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_high_risk_holdout_registry.py",
            "--artifact-id",
            "r12-high-risk-holdout-registry-cli",
            "--run-id",
            "r12-l5-test",
            "--hps-ingestion-path",
            str(hps_path),
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
    assert artifact["schema_version"] == "r12-high-risk-holdout-registry-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-high-risk-holdout-registry-cli",
        "output": str(output),
        "status": "r12_high_risk_holdout_registry_ready_research_only",
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
