import json
import subprocess
import sys
from pathlib import Path

from experiments.r11_product_shadow_trial import (
    R11_PRODUCT_SHADOW_TRIAL_SCHEMA_VERSION,
    build_r11_product_shadow_trial,
)


def test_r11_product_shadow_trial_creates_shadow_only_evidence_card():
    shadow = build_r11_product_shadow_trial(
        artifact_id="r11-product-shadow-trial-test",
        run_id="r11-l2-test",
        r11_external_holdout_validation=_load_current_holdout(),
    )

    assert shadow["schema_version"] == R11_PRODUCT_SHADOW_TRIAL_SCHEMA_VERSION
    assert shadow["status"] == "r11_product_shadow_trial_ready_guarded"
    assert shadow["trial_contract"] == {
        "source_backed_only": True,
        "shadow_only": True,
        "customer_visible_evidence_card_allowed": True,
        "customer_visible_primary_claims_use_guarded_baseline": True,
        "r11_can_override_primary_decision": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert shadow["shadow_evidence_card"]["claim_status"] == (
        "shadow_only_guarded_positive"
    )
    assert shadow["shadow_evidence_card"]["display_allowed"] is True
    assert shadow["shadow_evidence_card"]["primary_decision_allowed"] is False
    assert shadow["customer_visible_primary_decision"] == {
        "primary_decision_source": "guarded_baseline_customer_value_report",
        "r11_shadow_output_role": "secondary_evidence_card_only",
        "r11_can_override_primary_decision": False,
        "runtime_default_allowed": False,
    }
    assert shadow["acceptance_gates"]["shadow_only_mode"] is True
    assert shadow["acceptance_gates"]["r11_can_override_primary_decision"] is False
    assert shadow["acceptance_gates"]["product_core_method_ready"] is False
    assert shadow["acceptance_gates"]["field_outcome_validated"] is False
    assert shadow["acceptance_gates"]["runtime_default_allowed"] is False
    assert "R11 supports Product core method by default" in shadow["blocked_claims"]
    json.dumps(shadow, allow_nan=False)


def test_r11_product_shadow_trial_preserves_outcome_review_handoff():
    holdout = _load_current_holdout()
    shadow = build_r11_product_shadow_trial(
        artifact_id="r11-product-shadow-trial-test",
        run_id="r11-l2-test",
        r11_external_holdout_validation=holdout,
    )

    assert shadow["shadow_evidence_card"]["metrics"] == holdout["method_metrics"][
        "r11_external_holdout_transfer"
    ]
    assert shadow["outcome_review_handoff"] == {
        "handoff_id": "r11_shadow_trial_outcome_review",
        "target_artifact_id": "r6-product-outcome-review-current-001",
        "requires_customer_or_field_outcome": True,
        "update_candidate_scope": [
            "mechanism_weight",
            "segment_sensitivity",
            "propagation_edge",
            "interval_uncertainty",
        ],
        "prompt_or_persona_manual_patch_allowed": False,
        "runtime_default_allowed": False,
    }
    assert shadow["source_refs"] == [holdout["artifact_id"]]


def test_r11_product_shadow_trial_cli_writes_artifact(tmp_path):
    holdout_path = tmp_path / "holdout.json"
    output = tmp_path / "r11-product-shadow-trial.json"
    holdout_path.write_text(json.dumps(_load_current_holdout(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r11_product_shadow_trial.py",
            "--artifact-id",
            "r11-product-shadow-trial-cli",
            "--run-id",
            "r11-l2-test",
            "--r11-external-holdout-validation-path",
            str(holdout_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r11-product-shadow-trial-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r11-product-shadow-trial-cli",
        "output": str(output),
        "status": "r11_product_shadow_trial_ready_guarded",
    }


def _load_current_holdout():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r11_external_holdout_validation/"
            "r11-external-holdout-validation-current-001.json"
        ).read_text()
    )
