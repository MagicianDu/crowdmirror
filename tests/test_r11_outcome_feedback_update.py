import json
import subprocess
import sys
from pathlib import Path

from experiments.r11_outcome_feedback_update import (
    R11_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION,
    build_r11_outcome_feedback_update,
)


def test_r11_outcome_feedback_update_generates_bounded_candidate_ledger():
    update = build_r11_outcome_feedback_update(
        artifact_id="r11-outcome-feedback-update-test",
        run_id="r11-l3-test",
        r11_product_shadow_trial=_load_current_shadow_trial(),
        r11_external_holdout_validation=_load_current_holdout(),
        observed_feedback=_feedback_packet(),
    )

    assert update["schema_version"] == R11_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION
    assert update["status"] == "r11_outcome_feedback_update_ready_guarded"
    assert update["feedback_contract"] == {
        "source_backed_only": True,
        "feedback_source_level": "field_proxy",
        "updates_are_bounded_candidates": True,
        "prompt_or_persona_manual_patch_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert [item["update_type"] for item in update["update_candidates"]] == [
        "mechanism_weight",
        "segment_sensitivity",
        "propagation_edge",
        "interval_uncertainty",
    ]
    assert {item["status"] for item in update["update_candidates"]} == {
        "accepted",
        "rejected",
        "diagnostic_only",
    }
    for candidate in update["update_candidates"]:
        assert candidate["default_runtime_enabled"] is False
        assert candidate["requires_human_review"] is True
    assert update["update_gate"] == {
        "candidate_update_generated": True,
        "accepted_shadow_only_count": 1,
        "diagnostic_only_count": 2,
        "rejected_count": 1,
        "runtime_default_allowed": False,
        "requires_holdout_before_default": True,
        "prompt_or_persona_manual_patch_allowed": False,
    }
    assert "R11 runtime default update" in update["blocked_claims"]
    json.dumps(update, allow_nan=False)


def test_r11_outcome_feedback_update_computes_case_residuals_and_error_attribution():
    update = build_r11_outcome_feedback_update(
        artifact_id="r11-outcome-feedback-update-test",
        run_id="r11-l3-test",
        r11_product_shadow_trial=_load_current_shadow_trial(),
        r11_external_holdout_validation=_load_current_holdout(),
        observed_feedback=_feedback_packet(),
    )

    assert update["residual_summary"] == {
        "feedback_case_count": 3,
        "mean_signed_residual": 0.017,
        "mean_absolute_residual": 0.03,
        "positive_residual_count": 2,
        "negative_residual_count": 1,
        "interval_miss_count": 0,
    }
    assert update["error_attribution"] == {
        "primary_error_mode": "segment_specific_under_reaction",
        "mechanism_weight_update_needed": True,
        "segment_sensitivity_update_needed": True,
        "propagation_edge_update_supported": False,
        "interval_uncertainty_update_needed": False,
    }
    accepted = [
        item for item in update["update_candidates"] if item["status"] == "accepted"
    ]
    assert accepted == [
        {
            "update_id": "r11-segment-sensitivity-shadow-accepted-001",
            "update_type": "segment_sensitivity",
            "status": "accepted",
            "status_reason": "largest residual segment can be replayed in shadow mode only",
            "target": "hps_METRO_STATUS_2",
            "recommended_delta": 0.04,
            "default_runtime_enabled": False,
            "requires_human_review": True,
        }
    ]


def test_r11_outcome_feedback_update_cli_writes_artifact(tmp_path):
    shadow_path = tmp_path / "shadow.json"
    holdout_path = tmp_path / "holdout.json"
    feedback_path = tmp_path / "feedback.json"
    output = tmp_path / "r11-outcome-feedback-update.json"
    shadow_path.write_text(json.dumps(_load_current_shadow_trial(), allow_nan=False))
    holdout_path.write_text(json.dumps(_load_current_holdout(), allow_nan=False))
    feedback_path.write_text(json.dumps(_feedback_packet(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r11_outcome_feedback_update.py",
            "--artifact-id",
            "r11-outcome-feedback-update-cli",
            "--run-id",
            "r11-l3-test",
            "--r11-product-shadow-trial-path",
            str(shadow_path),
            "--r11-external-holdout-validation-path",
            str(holdout_path),
            "--observed-feedback-path",
            str(feedback_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r11-outcome-feedback-update-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r11-outcome-feedback-update-cli",
        "output": str(output),
        "status": "r11_outcome_feedback_update_ready_guarded",
    }


def _feedback_packet():
    return {
        "feedback_id": "r11-shadow-feedback-field-proxy-test-001",
        "measurement_window": "post_shadow_trial_30d",
        "source_level": "field_proxy",
        "case_measurements": [
            {
                "case_id": "hps_REGION_2",
                "observed_outcome_proxy": 0.523224,
                "evidence_note": "field proxy reports stronger high-risk reaction",
            },
            {
                "case_id": "hps_METRO_STATUS_2",
                "observed_outcome_proxy": 0.538821,
                "evidence_note": "field proxy reports strongest metro risk",
            },
            {
                "case_id": "hps_REGION_1",
                "observed_outcome_proxy": 0.430869,
                "evidence_note": "field proxy reports lower low-risk reaction",
            },
        ],
    }


def _load_current_shadow_trial():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r11_product_shadow_trial/"
            "r11-product-shadow-trial-current-001.json"
        ).read_text()
    )


def _load_current_holdout():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r11_external_holdout_validation/"
            "r11-external-holdout-validation-current-001.json"
        ).read_text()
    )
