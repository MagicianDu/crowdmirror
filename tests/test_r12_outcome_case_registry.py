import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_outcome_case_registry import (
    R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION,
    build_r12_outcome_case_registry,
)


def test_r12_outcome_case_registry_builds_fixed_split_without_runtime_escalation():
    registry = build_r12_outcome_case_registry(
        artifact_id="r12-outcome-case-registry-test",
        run_id="r12-l0-test",
        r11_external_holdout_validation=_load_current_r11_external_holdout(),
    )

    assert registry["schema_version"] == R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION
    assert registry["status"] == "r12_outcome_case_registry_ready_guarded"
    assert registry["claim_level"] == "outcome_supervised_learning_material_only"
    assert registry["case_registry_contract"] == {
        "source_backed_public_proxy": True,
        "split_strategy": "fixed_hps_segment_split_v1",
        "train_outcome_read_allowed": True,
        "validation_outcome_read_allowed_for_training": False,
        "holdout_outcome_read_allowed_for_training": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert registry["split_summary"] == {
        "case_count": 6,
        "train_count": 2,
        "validation_count": 2,
        "holdout_count": 2,
        "observed_high_risk_train_count": 2,
        "observed_high_risk_validation_count": 0,
        "observed_high_risk_holdout_count": 0,
    }
    assert {case["case_id"] for case in registry["cases"] if case["split"] == "train"} == {
        "hps_REGION_2",
        "hps_METRO_STATUS_2",
    }
    assert registry["leakage_guard"] == {
        "train_case_ids_with_observed_outcome_available": [
            "hps_METRO_STATUS_2",
            "hps_REGION_2",
        ],
        "validation_case_ids_blocked_for_training": [
            "hps_METRO_STATUS_1",
            "hps_REGION_1",
        ],
        "holdout_case_ids_blocked_for_training": [
            "hps_REGION_3",
            "hps_REGION_4",
        ],
        "outcome_leakage_blocked": True,
    }
    assert registry["acceptance_gates"] == {
        "case_registry_ready": True,
        "minimum_case_count_present": True,
        "train_validation_holdout_split_present": True,
        "outcome_leakage_blocked": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert "runtime_default_allowed=true" in registry["blocked_claims"]
    json.dumps(registry, allow_nan=False)


def test_r12_outcome_case_registry_cases_have_learning_fields():
    registry = build_r12_outcome_case_registry(
        artifact_id="r12-outcome-case-registry-test",
        run_id="r12-l0-test",
        r11_external_holdout_validation=_load_current_r11_external_holdout(),
    )

    by_id = {case["case_id"]: case for case in registry["cases"]}
    train = by_id["hps_METRO_STATUS_2"]
    assert train["learning_role"] == "train_outcome_supervision"
    assert train["scenario_shock"] == "hps_price_pressure_proxy"
    assert train["mechanism_labels"] == ["price_pressure"]
    assert train["outcome_proxy"]["name"] == "PRICESTRESS"
    assert train["outcome_proxy"]["observed_value"] == 0.55329
    assert train["prediction_state"] == {
        "static_prior_prediction": 0.454619,
        "interaction_prediction": 0.498821,
        "residual_vs_interaction": 0.054469,
        "residual_vs_static_prior": 0.098671,
    }
    assert train["guard_flags"] == {
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
        "eligible_for_runtime_update": False,
    }


def test_r12_outcome_case_registry_cli_writes_artifact(tmp_path):
    r11_path = tmp_path / "r11-external-holdout.json"
    output = tmp_path / "r12-outcome-case-registry.json"
    r11_path.write_text(json.dumps(_load_current_r11_external_holdout(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_outcome_case_registry.py",
            "--artifact-id",
            "r12-outcome-case-registry-cli",
            "--run-id",
            "r12-l0-test",
            "--r11-external-holdout-validation-path",
            str(r11_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r12-outcome-case-registry-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-outcome-case-registry-cli",
        "output": str(output),
        "status": "r12_outcome_case_registry_ready_guarded",
    }


def _load_current_r11_external_holdout():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r11_external_holdout_validation/"
            "r11-external-holdout-validation-current-001.json"
        ).read_text()
    )
