import json
import subprocess
import sys

from experiments.lcdu_anes_baseline_family_matrix import (
    build_lcdu_anes_baseline_family_matrix,
)


def test_baseline_family_matrix_covers_population_and_prompt_optimizer():
    matrix = build_lcdu_anes_baseline_family_matrix(
        microdata_artifact=_microdata_artifact(),
        llm_validation_artifacts=[_llm_validation_artifact()],
        artifact_id="lcdu-baseline-family-test",
    )

    assert matrix["schema_version"] == "lcdu-anes-baseline-family-matrix-v1"
    assert matrix["overall_status"] == "baseline_family_matrix_ready"
    assert matrix["baseline_families"] == [
        "population_search",
        "textgrad_or_prompt_optimizer",
    ]
    task = matrix["task_results"]["task_a"]
    assert task["covered_baseline_families"] == [
        "population_search",
        "textgrad_or_prompt_optimizer",
    ]
    population = task["baseline_results"][0]
    prompt_optimizer = task["baseline_results"][1]
    assert population["baseline_family"] == "population_search"
    assert population["method_id"] == "population_search_alpha_1"
    assert population["test_loss"] < 0.001
    assert prompt_optimizer["baseline_family"] == "textgrad_or_prompt_optimizer"
    assert prompt_optimizer["selected_prompt_method_id"] == "aggregate_anchor_prompt"
    assert prompt_optimizer["test_loss"] == 0.04
    assert "prompt_optimizer_not_textgrad_gradient_update" in matrix["risk_flags"]
    json.dumps(matrix, allow_nan=False)


def test_baseline_family_matrix_marks_prompt_optimizer_missing_without_llm_artifacts():
    matrix = build_lcdu_anes_baseline_family_matrix(
        microdata_artifact=_microdata_artifact(),
        llm_validation_artifacts=[],
        artifact_id="lcdu-baseline-family-test",
    )

    assert matrix["overall_status"] == "baseline_family_matrix_partial"
    assert matrix["baseline_families"] == ["population_search"]
    assert "prompt_optimizer_family_missing" in matrix["risk_flags"]


def test_baseline_family_matrix_script_writes_json(tmp_path):
    microdata = tmp_path / "microdata.json"
    llm = tmp_path / "llm.json"
    output = tmp_path / "baseline-family.json"
    microdata.write_text(json.dumps(_microdata_artifact()))
    llm.write_text(json.dumps(_llm_validation_artifact()))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_anes_baseline_family_matrix.py",
            "--microdata-artifact",
            str(microdata),
            "--llm-validation-artifacts",
            str(llm),
            "--output",
            str(output),
            "--artifact-id",
            "lcdu-baseline-family-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "artifact_id": "lcdu-baseline-family-test",
        "baseline_families": [
            "population_search",
            "textgrad_or_prompt_optimizer",
        ],
        "output": str(output),
        "status": "baseline_family_matrix_ready",
        "task_count": 1,
    }
    assert json.loads(output.read_text())["overall_status"] == (
        "baseline_family_matrix_ready"
    )


def _microdata_artifact() -> dict:
    return {
        "schema_version": "lcdu-anes-public-microdata-ingestion-v1",
        "artifact_id": "microdata-test",
        "target_distributions": {"task_a": {}},
        "splits": {
            "calibration": {
                "target_distributions": {
                    "task_a": _split_distribution(
                        s1={"yes": 0.8, "no": 0.2},
                        s2={"yes": 0.2, "no": 0.8},
                    )
                }
            },
            "heldout": {
                "target_distributions": {
                    "task_a": _split_distribution(
                        s1={"yes": 0.78, "no": 0.22},
                        s2={"yes": 0.22, "no": 0.78},
                    )
                }
            },
            "test": {
                "target_distributions": {
                    "task_a": _split_distribution(
                        s1={"yes": 0.79, "no": 0.21},
                        s2={"yes": 0.21, "no": 0.79},
                    )
                }
            },
        },
    }


def _split_distribution(*, s1: dict[str, float], s2: dict[str, float]) -> dict:
    return {
        "target_variable_id": "target",
        "segment_schema_coverage": {"axis_count": 1},
        "overall": {
            "policy_probabilities": {
                "yes": (s1["yes"] + s2["yes"]) / 2.0,
                "no": (s1["no"] + s2["no"]) / 2.0,
            }
        },
        "by_segment": {
            "segment=s1": {
                "row_count": 50,
                "policy_probabilities": s1,
            },
            "segment=s2": {
                "row_count": 50,
                "policy_probabilities": s2,
            },
        },
    }


def _llm_validation_artifact() -> dict:
    return {
        "schema_version": "lcdu-anes-llm-simulator-validation-v1",
        "artifact_id": "llm-validation-test",
        "overall_status": "cross_task_llm_signal_positive",
        "validation_type": "split_gated_llm_segment_simulator_smoke",
        "provider": "openai",
        "model": "test-model",
        "base_url": "http://localhost",
        "max_segments_per_task": 2,
        "segment_offset": 0,
        "prompt_variant": "deliberative",
        "task_results": {
            "task_a": {
                "heldout": {
                    "loss_by_method": {
                        "raw_prompt": 0.08,
                        "aggregate_anchor_prompt": 0.03,
                        "lcdu_segment_anchor_prompt": 0.02,
                    }
                },
                "test": {
                    "loss_by_method": {
                        "raw_prompt": 0.09,
                        "aggregate_anchor_prompt": 0.04,
                        "lcdu_segment_anchor_prompt": 0.01,
                    }
                },
            }
        },
    }
