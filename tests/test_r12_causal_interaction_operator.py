import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_causal_interaction_operator import (
    R12_CAUSAL_INTERACTION_OPERATOR_SCHEMA_VERSION,
    build_r12_causal_interaction_operator,
)


def test_r12_causal_interaction_operator_defines_bounded_parameters():
    operator = build_r12_causal_interaction_operator(
        artifact_id="r12-causal-interaction-operator-test",
        run_id="r12-l1-test",
        r12_outcome_case_registry=_load_current_case_registry(),
        r11_outcome_feedback_update=_load_current_r11_feedback_update(),
    )

    assert operator["schema_version"] == R12_CAUSAL_INTERACTION_OPERATOR_SCHEMA_VERSION
    assert operator["status"] == "r12_causal_interaction_operator_ready_guarded"
    assert operator["operator_contract"] == {
        "operator_id": "r12_oscio_l1",
        "updates_are_structured_parameters_only": True,
        "prompt_or_persona_manual_patch_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert set(operator["parameter_state"]) == {
        "mechanism_weights",
        "segment_sensitivities",
        "interaction_edge_weights",
        "uncertainty_parameters",
    }
    assert operator["parameter_state"]["mechanism_weights"]["price_pressure"] == {
        "value": 0.52,
        "prior": 0.5,
        "lower_bound": 0.35,
        "upper_bound": 0.75,
        "source": "r11_feedback_diagnostic_price_pressure",
    }
    assert operator["parameter_state"]["segment_sensitivities"]["hps_METRO_STATUS_2"] == {
        "value": 1.09,
        "prior": 1.0,
        "lower_bound": 0.8,
        "upper_bound": 1.25,
        "source": "r11_segment_sensitivity_shadow_accepted",
    }
    assert operator["update_bounds"]["segment_sensitivity"] == {
        "max_abs_delta": 0.12,
        "requires_holdout_before_default": True,
    }
    assert operator["acceptance_gates"] == {
        "operator_contract_ready": True,
        "structured_parameter_state_present": True,
        "train_cases_only_used_for_parameter_initialization": True,
        "prompt_or_persona_manual_patch_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert "prompt/persona manual patch as automatic calibration" in operator["blocked_claims"]
    json.dumps(operator, allow_nan=False)


def test_r12_causal_interaction_operator_records_prior_shrinkage_and_edge_guard():
    operator = build_r12_causal_interaction_operator(
        artifact_id="r12-causal-interaction-operator-test",
        run_id="r12-l1-test",
        r12_outcome_case_registry=_load_current_case_registry(),
        r11_outcome_feedback_update=_load_current_r11_feedback_update(),
    )

    assert operator["prior_shrinkage_rules"] == {
        "static_prior_is_base_distribution": True,
        "interaction_layer_updates_are_bounded": True,
        "small_sample_updates_shrink_toward_prior": True,
        "posterior_shrinkage_strength": 0.65,
        "validation_or_holdout_outcome_not_used_for_initialization": True,
    }
    assert operator["interaction_edge_update_guard"] == {
        "direct_propagation_evidence_present": False,
        "edge_update_status": "rejected",
        "rejection_reason": "r11 feedback packet lacks direct interaction propagation evidence",
    }
    assert operator["next_required_artifact"] == "r12_outcome_supervised_update"


def test_r12_causal_interaction_operator_cli_writes_artifact(tmp_path):
    registry_path = tmp_path / "r12-case-registry.json"
    feedback_path = tmp_path / "r11-feedback-update.json"
    output = tmp_path / "r12-causal-interaction-operator.json"
    registry_path.write_text(json.dumps(_load_current_case_registry(), allow_nan=False))
    feedback_path.write_text(json.dumps(_load_current_r11_feedback_update(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_causal_interaction_operator.py",
            "--artifact-id",
            "r12-causal-interaction-operator-cli",
            "--run-id",
            "r12-l1-test",
            "--r12-outcome-case-registry-path",
            str(registry_path),
            "--r11-outcome-feedback-update-path",
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
    assert artifact["schema_version"] == "r12-causal-interaction-operator-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-causal-interaction-operator-cli",
        "output": str(output),
        "status": "r12_causal_interaction_operator_ready_guarded",
    }


def _load_current_case_registry():
    repo_root = Path(__file__).resolve().parents[1]
    path = (
        repo_root
        / "experiments/results/r12_outcome_case_registry/"
        "r12-outcome-case-registry-current-001.json"
    )
    if path.exists():
        return json.loads(path.read_text())
    from experiments.r12_outcome_case_registry import build_r12_outcome_case_registry

    return build_r12_outcome_case_registry(
        artifact_id="r12-outcome-case-registry-fixture",
        run_id="r12-l1-test",
        r11_external_holdout_validation=json.loads(
            (
                repo_root
                / "experiments/results/r11_external_holdout_validation/"
                "r11-external-holdout-validation-current-001.json"
            ).read_text()
        ),
    )


def _load_current_r11_feedback_update():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r11_outcome_feedback_update/"
            "r11-outcome-feedback-update-current-001.json"
        ).read_text()
    )
