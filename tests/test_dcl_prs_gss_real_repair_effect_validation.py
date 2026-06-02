import json
import subprocess
import sys

from experiments.dcl_prs_gss_real_repair_effect_validation import (
    build_gss_real_repair_effect_validation,
)


def test_gss_real_repair_effect_validation_promotes_only_accepted_improvements():
    repair_repeat = _repair_repeat_fixture()
    gss_smoke = _gss_smoke_fixture()
    prediction_scenarios = [
        {
            "repair_id": "repair-accepted",
            "initial_prediction": {
                "probabilities": {
                    "a great deal": 0.10,
                    "only some": 0.60,
                    "hardly any": 0.30,
                }
            },
            "repaired_prediction": {
                "probabilities": {
                    "a great deal": 0.22,
                    "only some": 0.56,
                    "hardly any": 0.22,
                }
            },
        },
        {
            "repair_id": "repair-rejected",
            "initial_prediction": {
                "probabilities": {
                    "a great deal": 0.10,
                    "only some": 0.60,
                    "hardly any": 0.30,
                }
            },
            "repaired_prediction": {
                "probabilities": {
                    "a great deal": 0.24,
                    "only some": 0.54,
                    "hardly any": 0.22,
                }
            },
        },
    ]

    artifact = build_gss_real_repair_effect_validation(
        artifact_id="dcl-prs-gss-real-repair-effect-test",
        gss_policy_task_ingestion_smoke=gss_smoke,
        repair_repeat_acceptance_matrix=repair_repeat,
        prediction_scenarios=prediction_scenarios,
    )

    assert artifact["schema_version"] == "dcl-prs-gss-real-repair-effect-v1"
    assert artifact["overall_status"] == "gss_real_repair_effect_validation_ready"
    assert artifact["source_artifact_id"] == "dcl-prs-gss-policy-task-smoke-test"
    assert artifact["loss_metric"] == "weighted_choice_distribution_jsd"
    assert artifact["real_target"]["valid_policy_response_count"] == 100
    assert artifact["accepted_candidate_count"] == 1
    assert artifact["real_effect_promoted_count"] == 1
    assert artifact["rejected_real_improvement_count"] == 1
    accepted = artifact["candidate_results"][0]
    rejected = artifact["candidate_results"][1]
    assert accepted["repair_id"] == "repair-accepted"
    assert accepted["decision"] == "accepted"
    assert accepted["repaired_loss"] < accepted["initial_loss"]
    assert accepted["promoted_to_real_effect"] is True
    assert rejected["decision"] == "rejected"
    assert rejected["repaired_loss"] < rejected["initial_loss"]
    assert rejected["promoted_to_real_effect"] is False
    assert "single_gss_policy_task_only" in artifact["risk_flags"]
    json.dumps(artifact, allow_nan=False)


def test_gss_real_repair_effect_validation_script_writes_artifact(tmp_path):
    gss_smoke_path = tmp_path / "gss_smoke.json"
    gss_smoke_path.write_text(json.dumps(_gss_smoke_fixture()))
    repair_repeat_path = tmp_path / "repair_repeat.json"
    repair_repeat_path.write_text(json.dumps(_repair_repeat_fixture()))
    prediction_scenarios_path = tmp_path / "prediction_scenarios.json"
    prediction_scenarios_path.write_text(
        json.dumps(
            [
                {
                    "repair_id": "repair-accepted",
                    "initial_prediction": {
                        "probabilities": {
                            "a great deal": 0.10,
                            "only some": 0.60,
                            "hardly any": 0.30,
                        }
                    },
                    "repaired_prediction": {
                        "probabilities": {
                            "a great deal": 0.22,
                            "only some": 0.56,
                            "hardly any": 0.22,
                        }
                    },
                }
            ]
        )
    )
    output_dir = tmp_path / "real_effect"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_gss_real_repair_effect_validation.py",
            "--gss-policy-task-ingestion-smoke-path",
            str(gss_smoke_path),
            "--repair-repeat-acceptance-matrix-path",
            str(repair_repeat_path),
            "--prediction-scenarios-path",
            str(prediction_scenarios_path),
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-gss-real-repair-effect-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-gss-real-repair-effect-test.json"),
        "overall_status": "gss_real_repair_effect_validation_ready",
        "real_effect_promoted_count": 1,
    }


def _gss_smoke_fixture():
    return {
        "schema_version": "dcl-prs-gss-policy-task-ingestion-smoke-v1",
        "artifact_id": "dcl-prs-gss-policy-task-smoke-test",
        "overall_status": "gss_policy_task_ingestion_smoke_ready",
        "valid_policy_response_count": 100,
        "response_distribution": {
            "counts": {
                "a great deal": 25,
                "only some": 55,
                "hardly any": 20,
            },
            "probabilities": {
                "a great deal": 0.25,
                "only some": 0.55,
                "hardly any": 0.20,
            },
        },
    }


def _repair_repeat_fixture():
    return {
        "schema_version": "dcl-prs-repair-repeat-acceptance-matrix-v1",
        "artifact_id": "dcl-prs-repair-repeat-test",
        "overall_status": "repair_repeat_acceptance_matrix_ready",
        "repair_candidate_count": 2,
        "candidate_results": [
            {
                "repair_id": "repair-accepted",
                "action": "fallback_anchor",
                "decision": "accepted",
                "accepted_repeat_count": 3,
                "repeat_count": 3,
            },
            {
                "repair_id": "repair-rejected",
                "action": "switch_candidate_family",
                "decision": "rejected",
                "accepted_repeat_count": 0,
                "repeat_count": 3,
            },
        ],
    }
