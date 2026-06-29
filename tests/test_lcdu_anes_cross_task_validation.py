import json
import subprocess
import sys

from experiments.lcdu_anes_cross_task_validation import (
    build_lcdu_anes_cross_task_validation_artifact,
)


def test_build_cross_task_validation_accepts_split_gated_anchor_candidates():
    artifact = build_lcdu_anes_cross_task_validation_artifact(
        microdata_artifact=_microdata_artifact(),
        artifact_id="lcdu-anes-cross-task-validation-test",
    )

    assert artifact["schema_version"] == "lcdu-anes-cross-task-validation-v1"
    assert artifact["overall_status"] == "cross_task_anchor_signal_positive"
    assert artifact["task_count"] == 2
    assert artifact["accepted_task_count"] == 2
    assert artifact["test_improvement_task_count"] == 2
    assert artifact["candidate_generation_split"] == "calibration"
    assert artifact["candidate_acceptance_split"] == "heldout"
    assert artifact["final_claim_check_split"] == "test"
    assert artifact["validation_type"] == "split_gated_segment_anchor_transfer_smoke"

    for result in artifact["task_results"].values():
        assert result["candidate_accepted"] is True
        assert result["heldout"]["best_loss"] < result["heldout"]["initial_loss"]
        assert result["test"]["final_loss"] < result["test"]["initial_loss"]
    assert "not_llm_simulator_validation" in artifact["risk_flags"]
    json.dumps(artifact, allow_nan=False)


def test_cross_task_validation_script_writes_artifact(tmp_path):
    microdata = tmp_path / "microdata.json"
    output = tmp_path / "cross-task.json"
    microdata.write_text(json.dumps(_microdata_artifact()))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_anes_cross_task_validation.py",
            "--microdata-artifact",
            str(microdata),
            "--output",
            str(output),
            "--artifact-id",
            "lcdu-anes-cross-task-validation-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "accepted_task_count": 2,
        "artifact_id": "lcdu-anes-cross-task-validation-test",
        "output": str(output),
        "status": "cross_task_anchor_signal_positive",
        "task_count": 2,
        "test_improvement_task_count": 2,
    }
    assert json.loads(output.read_text())["source_artifact_id"] == (
        "lcdu-anes-2024-sda-public-microdata-test"
    )


def _microdata_artifact() -> dict:
    task_ids = [
        "public_health_medical_insurance_attitude_v1",
        "climate_energy_regulation_attitude_v1",
    ]
    return {
        "schema_version": "lcdu-anes-public-microdata-ingestion-v1",
        "artifact_id": "lcdu-anes-2024-sda-public-microdata-test",
        "overall_status": "segment_target_distributions_materialized_with_partial_schema",
        "target_distributions": {
            task_id: _task_distribution(task_id, left=0.9, right=0.1)
            for task_id in task_ids
        },
        "splits": {
            "calibration": {
                "target_distributions": {
                    task_id: _task_distribution(task_id, left=0.9, right=0.1)
                    for task_id in task_ids
                }
            },
            "heldout": {
                "target_distributions": {
                    task_id: _task_distribution(task_id, left=0.85, right=0.15)
                    for task_id in task_ids
                }
            },
            "test": {
                "target_distributions": {
                    task_id: _task_distribution(task_id, left=0.8, right=0.2)
                    for task_id in task_ids
                }
            },
        },
    }


def _task_distribution(task_id: str, *, left: float, right: float) -> dict:
    options = _options(task_id)
    return {
        "task_id": task_id,
        "target_variable_id": "V241245" if "health" in task_id else "V241258",
        "segment_schema_coverage": {
            "coverage_status": "partial",
            "missing_required_axes": [],
        },
        "overall": {
            "row_count": 100,
            "policy_counts": {options[0]: 50, options[1]: 50},
            "policy_probabilities": {options[0]: 0.5, options[1]: 0.5},
        },
        "by_segment": {
            "party_or_ideology=liberal|income=lower": {
                "row_count": 50,
                "policy_counts": {options[0]: int(left * 50), options[1]: int((1-left) * 50)},
                "policy_probabilities": {options[0]: left, options[1]: 1.0 - left},
            },
            "party_or_ideology=conservative|income=upper": {
                "row_count": 50,
                "policy_counts": {options[0]: int(right * 50), options[1]: int((1-right) * 50)},
                "policy_probabilities": {options[0]: right, options[1]: 1.0 - right},
            },
        },
    }


def _options(task_id: str) -> list[str]:
    if "health" in task_id:
        return ["government_insurance_plan", "private_insurance_plan"]
    return [
        "support_more_regulation_or_spending",
        "oppose_more_regulation_or_spending",
    ]
