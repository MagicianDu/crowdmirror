import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_outcome_supervised_update import (
    R12_OUTCOME_SUPERVISED_UPDATE_SCHEMA_VERSION,
    build_r12_outcome_supervised_update,
)


def test_r12_outcome_supervised_update_uses_train_outcomes_only():
    update = build_r12_outcome_supervised_update(
        artifact_id="r12-outcome-supervised-update-test",
        run_id="r12-l2-test",
        r12_outcome_case_registry=_load_current_case_registry(),
        r12_causal_interaction_operator=_load_current_operator(),
    )

    assert update["schema_version"] == R12_OUTCOME_SUPERVISED_UPDATE_SCHEMA_VERSION
    assert update["status"] == "r12_outcome_supervised_update_ready_guarded"
    assert update["claim_level"] == "train_only_outcome_update_candidate"
    assert update["training_residual_summary"] == {
        "train_case_count": 2,
        "mean_train_residual_vs_interaction": 0.041323,
        "mean_abs_train_residual_vs_interaction": 0.041323,
        "positive_train_residual_count": 2,
        "negative_train_residual_count": 0,
    }
    assert [item["case_id"] for item in update["training_residuals"]] == [
        "hps_METRO_STATUS_2",
        "hps_REGION_2",
    ]
    assert update["training_data_guard"] == {
        "train_outcomes_used_for_update": [
            "hps_METRO_STATUS_2",
            "hps_REGION_2",
        ],
        "validation_outcomes_used_for_update": [],
        "holdout_outcomes_used_for_update": [],
        "outcome_leakage_blocked": True,
    }


def test_r12_outcome_supervised_update_records_structured_candidates():
    update = build_r12_outcome_supervised_update(
        artifact_id="r12-outcome-supervised-update-test",
        run_id="r12-l2-test",
        r12_outcome_case_registry=_load_current_case_registry(),
        r12_causal_interaction_operator=_load_current_operator(),
    )

    by_type = {candidate["update_type"]: candidate for candidate in update["update_candidates"]}
    assert set(by_type) == {
        "mechanism_weight",
        "segment_sensitivity",
        "interaction_edge_weight",
        "uncertainty_parameter",
    }
    assert by_type["mechanism_weight"] == {
        "update_id": "r12-mechanism-weight-price-pressure-accepted-001",
        "update_type": "mechanism_weight",
        "status": "accepted",
        "status_reason": (
            "positive train residual supports bounded price-pressure update "
            "for holdout replay"
        ),
        "target": "price_pressure",
        "current_value": 0.52,
        "recommended_value": 0.55,
        "recommended_delta": 0.03,
        "transfer_scope": "same_family_holdout_required",
        "default_runtime_enabled": False,
        "requires_human_review": True,
    }
    assert by_type["segment_sensitivity"]["status"] == "diagnostic_only"
    assert by_type["segment_sensitivity"]["target"] == [
        "hps_METRO_STATUS_2",
        "hps_REGION_2",
    ]
    assert by_type["interaction_edge_weight"]["status"] == "rejected"
    assert by_type["uncertainty_parameter"]["status"] == "diagnostic_only"
    assert all(
        candidate["default_runtime_enabled"] is False
        for candidate in update["update_candidates"]
    )
    assert update["update_gate"] == {
        "candidate_update_generated": True,
        "accepted_shadow_only_count": 1,
        "diagnostic_only_count": 2,
        "rejected_count": 1,
        "train_only_update": True,
        "outcome_leakage_blocked": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
        "requires_transfer_validation_before_product_support": True,
    }
    assert "runtime_default_allowed=true" in update["blocked_claims"]
    json.dumps(update, allow_nan=False)


def test_r12_outcome_supervised_update_cli_writes_artifact(tmp_path):
    registry_path = tmp_path / "r12-case-registry.json"
    operator_path = tmp_path / "r12-causal-operator.json"
    output = tmp_path / "r12-outcome-supervised-update.json"
    registry_path.write_text(json.dumps(_load_current_case_registry(), allow_nan=False))
    operator_path.write_text(json.dumps(_load_current_operator(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_outcome_supervised_update.py",
            "--artifact-id",
            "r12-outcome-supervised-update-cli",
            "--run-id",
            "r12-l2-test",
            "--r12-outcome-case-registry-path",
            str(registry_path),
            "--r12-causal-interaction-operator-path",
            str(operator_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r12-outcome-supervised-update-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-outcome-supervised-update-cli",
        "output": str(output),
        "status": "r12_outcome_supervised_update_ready_guarded",
    }


def _load_current_case_registry():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_outcome_case_registry/"
            "r12-outcome-case-registry-current-001.json"
        ).read_text()
    )


def _load_current_operator():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_causal_interaction_operator/"
            "r12-causal-interaction-operator-current-001.json"
        ).read_text()
    )
