import json
import subprocess
import sys

from circe.llm_client import LLMResponse
from experiments.lcdu_anes_anchor_fidelity_repair import (
    anchor_json_from_prompt,
    build_lcdu_anes_anchor_fidelity_repair_artifact,
)


def test_anchor_fidelity_repair_reports_hybrid_gap_closure():
    artifact = build_lcdu_anes_anchor_fidelity_repair_artifact(
        microdata_artifact=_microdata_artifact(),
        strong_baseline_matrix=_strong_baseline_matrix(),
        artifact_id="anchor-repair-test",
        provider="openai",
        model="test-model",
        base_url="http://localhost",
    )

    assert artifact["schema_version"] == "lcdu-anes-anchor-fidelity-repair-v1"
    assert artifact["overall_status"] == "hybrid_anchor_fidelity_repair_available"
    task = artifact["task_results"]["task_a"]
    assert task["deterministic_anchor_copy"]["closes_lcdu_gap"] is True
    assert task["deterministic_anchor_copy"]["test_loss"] < task["current_lcdu"][
        "test_loss"
    ]
    assert "llm_anchor_copy_not_executed" in artifact["risk_flags"]
    json.dumps(artifact, allow_nan=False)


def test_anchor_fidelity_repair_can_execute_exact_llm_copy_with_fake_completion():
    artifact = build_lcdu_anes_anchor_fidelity_repair_artifact(
        microdata_artifact=_microdata_artifact(),
        strong_baseline_matrix=_strong_baseline_matrix(),
        artifact_id="anchor-repair-test",
        provider="openai",
        model="test-model",
        base_url="http://localhost",
        completion_fn=_copy_anchor_completion,
        execute_llm_copy=True,
    )

    assert artifact["overall_status"] == "llm_anchor_copy_repair_positive"
    assert artifact["llm_accounting"]["total_call_count"] == 2
    task = artifact["task_results"]["task_a"]
    assert task["llm_anchor_copy"]["closes_lcdu_gap"] is True
    assert task["llm_anchor_copy"]["mean_anchor_l1_deviation"] == 0.0


def test_anchor_fidelity_repair_script_writes_json(tmp_path):
    microdata = tmp_path / "microdata.json"
    strong = tmp_path / "strong.json"
    output = tmp_path / "repair.json"
    microdata.write_text(json.dumps(_microdata_artifact()))
    strong.write_text(json.dumps(_strong_baseline_matrix()))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_anes_anchor_fidelity_repair.py",
            "--microdata-artifact",
            str(microdata),
            "--strong-baseline-matrix",
            str(strong),
            "--output",
            str(output),
            "--artifact-id",
            "anchor-repair-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "artifact_id": "anchor-repair-test",
        "deterministic_closes_count": 1,
        "llm_copy_closes_count": 0,
        "output": str(output),
        "status": "hybrid_anchor_fidelity_repair_available",
        "task_count": 1,
        "total_call_count": 0,
    }
    assert json.loads(output.read_text())["overall_status"] == (
        "hybrid_anchor_fidelity_repair_available"
    )


def _copy_anchor_completion(_system: str, user: str) -> LLMResponse:
    return LLMResponse(
        content=json.dumps(anchor_json_from_prompt(user), sort_keys=True),
        input_tokens=100,
        output_tokens=30,
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


def _strong_baseline_matrix() -> dict:
    return {
        "schema_version": "lcdu-anes-strong-baseline-matrix-v1",
        "artifact_id": "strong-baseline-test",
        "overall_status": "strong_baseline_lcdu_not_leading",
        "task_results": {
            "task_a": {
                "lcdU_test_loss": 0.02,
                "lcdU_selected_source_artifact_id": "llm-test",
                "lcdU_selected_heldout_loss": 0.015,
                "best_covered_baseline_family": "deterministic_anchor_search",
                "best_covered_baseline_method_id": "calibration_segment_anchor",
                "best_covered_baseline_test_loss": 0.001,
            }
        },
    }
