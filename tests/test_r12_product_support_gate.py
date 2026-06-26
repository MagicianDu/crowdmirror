import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_product_support_gate import (
    R12_PRODUCT_SUPPORT_GATE_SCHEMA_VERSION,
    build_r12_product_support_gate,
)


def test_r12_product_support_gate_creates_guarded_transfer_evidence_card():
    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l4-test",
        r12_transfer_validation=_load_current_transfer_validation(),
    )

    assert gate["schema_version"] == R12_PRODUCT_SUPPORT_GATE_SCHEMA_VERSION
    assert gate["status"] == "r12_product_support_gate_ready_guarded"
    assert gate["claim_level"] == "product_secondary_evidence_only"
    assert gate["product_support_contract"] == {
        "source_backed_only": True,
        "customer_visible_evidence_card_allowed": True,
        "secondary_evidence_card_only": True,
        "customer_visible_primary_claims_use_guarded_baseline": True,
        "r12_can_override_primary_decision": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    card = gate["transfer_evidence_card"]
    assert card["card_id"] == "r12_transfer_validation_evidence_card"
    assert card["claim_status"] == "guarded_transfer_positive_secondary_evidence"
    assert card["display_allowed"] is True
    assert card["primary_decision_allowed"] is False
    assert card["metrics"] == {
        "update_transfer_gain": 0.001287,
        "validation_mean_absolute_error_delta": -0.000431,
        "holdout_mean_absolute_error_delta": -0.000856,
        "interval_coverage_delta": 0.0,
        "false_alarm_rate_delta": 0.0,
    }
    assert card["source_artifact_ids"] == [
        "r12-transfer-validation-current-001",
    ]
    assert card["evidence_summary"]["extended_metric_gates"] == {
        "risk_ranking_non_regression": True,
        "decision_value_non_regression": True,
        "static_prior_miss_recovery_holdout_covered": False,
        "abnormal_segment_recall_holdout_covered": False,
        "extended_product_metric_support_level": (
            "guarded_mae_positive_extended_metric_coverage_gap"
        ),
    }
    assert gate["customer_visible_primary_decision"] == {
        "primary_decision_source": "guarded_baseline_customer_value_report",
        "r12_output_role": "secondary_transfer_evidence_card_only",
        "r12_can_override_primary_decision": False,
        "runtime_default_allowed": False,
    }
    assert gate["acceptance_gates"] == {
        "r12_transfer_positive_guarded": True,
        "customer_visible_evidence_card_allowed": True,
        "secondary_evidence_card_only": True,
        "primary_claims_guarded_baseline_only": True,
        "r12_can_override_primary_decision": False,
        "product_core_method_ready": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert "R12 supports Product core method by default" in gate["blocked_claims"]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_preserves_outcome_review_boundary():
    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l4-test",
        r12_transfer_validation=_load_current_transfer_validation(),
    )

    assert gate["outcome_review_handoff"] == {
        "handoff_id": "r12_transfer_evidence_outcome_review",
        "target_artifact_id": "r6-product-outcome-review-current-001",
        "requires_customer_or_field_outcome": True,
        "update_candidate_scope": [
            "mechanism_weight",
            "segment_sensitivity",
            "interaction_edge_weight",
            "uncertainty_parameter",
        ],
        "prompt_or_persona_manual_patch_allowed": False,
        "runtime_default_allowed": False,
    }
    assert gate["source_refs"] == [
        "r12-transfer-validation-current-001",
    ]
    assert gate["source_registry"] == [
        {
            "artifact_id": "r12-transfer-validation-current-001",
            "path": (
                "experiments/results/r12_transfer_validation/"
                "r12-transfer-validation-current-001.json"
            ),
        }
    ]


def test_r12_product_support_gate_cli_writes_artifact(tmp_path):
    transfer_path = tmp_path / "r12-transfer-validation.json"
    output = tmp_path / "r12-product-support-gate.json"
    transfer_path.write_text(
        json.dumps(_load_current_transfer_validation(), allow_nan=False)
    )

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_product_support_gate.py",
            "--artifact-id",
            "r12-product-support-gate-cli",
            "--run-id",
            "r12-l4-test",
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
    assert artifact["schema_version"] == "r12-product-support-gate-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-product-support-gate-cli",
        "output": str(output),
        "status": "r12_product_support_gate_ready_guarded",
    }


def _load_current_transfer_validation():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_transfer_validation/"
            "r12-transfer-validation-current-001.json"
        ).read_text()
    )
