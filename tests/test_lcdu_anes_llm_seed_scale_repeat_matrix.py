import json
import re
import subprocess
import sys

from circe.llm_client import LLMResponse
from experiments.lcdu_anes_llm_seed_scale_repeat_matrix import (
    build_lcdu_anes_llm_seed_scale_repeat_matrix,
)


def test_build_seed_scale_repeat_matrix_reports_stable_positive_signal():
    matrix = build_lcdu_anes_llm_seed_scale_repeat_matrix(
        microdata_artifact=_microdata_artifact(),
        artifact_id="lcdu-anes-llm-seed-scale-repeat-test",
        provider="openai",
        model="fake-model",
        base_url="http://127.0.0.1:1234/v1",
        completion_fn=_fake_completion,
        segment_scales=[1, 2],
        segment_offsets=[0, 1],
        prompt_variants=["standard", "compact"],
    )

    assert matrix["schema_version"] == "lcdu-anes-llm-seed-scale-repeat-matrix-v1"
    assert matrix["overall_status"] == "seed_scale_repeat_signal_positive"
    assert matrix["run_count"] == 8
    assert matrix["positive_run_count"] == 8
    assert matrix["llm_accounting"]["total_call_count"] == 72
    for stability in matrix["task_stability"].values():
        assert stability["accepted_rate"] == 1.0
        assert stability["test_improved_rate"] == 1.0
    json.dumps(matrix, allow_nan=False)


def test_seed_scale_repeat_matrix_script_writes_planned_artifact(tmp_path):
    microdata = tmp_path / "microdata.json"
    output = tmp_path / "matrix.json"
    microdata.write_text(json.dumps(_microdata_artifact()))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_anes_llm_seed_scale_repeat_matrix.py",
            "--microdata-artifact",
            str(microdata),
            "--output",
            str(output),
            "--artifact-id",
            "lcdu-anes-llm-seed-scale-repeat-test",
            "--segment-scales",
            "1",
            "2",
            "--segment-offsets",
            "0",
            "1",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "artifact_id": "lcdu-anes-llm-seed-scale-repeat-test",
        "output": str(output),
        "positive_run_count": 0,
        "run_count": 0,
        "status": "planned_not_executed",
        "total_call_count": 0,
    }


def _fake_completion(system: str, user: str) -> LLMResponse:
    del system
    if "LCDU segment anchor" in user:
        match = user.split("LCDU segment anchor from calibration public microdata:")[1]
        json_text = match.split("Treat this as")[0].strip()
    else:
        options = json.loads(re.findall(r"\[[^\]]+\]", user)[-1])
        json_text = json.dumps({option: 1.0 / len(options) for option in options})
    return LLMResponse(content=json_text, input_tokens=10, output_tokens=5)


def _microdata_artifact() -> dict:
    task_ids = [
        "public_health_medical_insurance_attitude_v1",
        "climate_energy_regulation_attitude_v1",
    ]
    return {
        "schema_version": "lcdu-anes-public-microdata-ingestion-v1",
        "artifact_id": "lcdu-anes-2024-sda-public-microdata-test",
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
                "policy_counts": {
                    options[0]: int(left * 50),
                    options[1]: int((1 - left) * 50),
                },
                "policy_probabilities": {options[0]: left, options[1]: 1.0 - left},
            },
            "party_or_ideology=conservative|income=upper": {
                "row_count": 50,
                "policy_counts": {
                    options[0]: int(right * 50),
                    options[1]: int((1 - right) * 50),
                },
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
