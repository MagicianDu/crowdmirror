import json
import subprocess
import sys

from experiments.lcdu_anes_hybrid_method_validation import (
    build_lcdu_anes_hybrid_method_validation,
)


def test_hybrid_method_validation_marks_numeric_parity_not_accuracy_win():
    artifact = build_lcdu_anes_hybrid_method_validation(
        artifact_id="hybrid-method-test",
        strong_baseline_matrix=_strong_baseline_matrix(),
        anchor_fidelity_repair=_repair_artifact(),
    )

    assert artifact["schema_version"] == "lcdu-anes-hybrid-method-validation-v1"
    assert artifact["overall_status"] == (
        "hybrid_candidate_numeric_parity_soft_not_leading"
    )
    assert artifact["numeric_parity_count"] == 1
    assert artifact["strict_copy_positive_count"] == 1
    assert artifact["soft_loses_count"] == 1
    assert artifact["research_decision"] == (
        "reframe_as_hybrid_auditable_constraint_framework_not_accuracy_win"
    )
    assert artifact["product_decision"] == "adopt_hybrid_for_auditable_product_reports"
    task = artifact["task_results"]["task_a"]
    assert task["hybrid_numeric_parity"] is True
    assert task["hybrid_candidate"]["loss_delta_vs_soft_lcdu"] < 0
    assert "not_accuracy_win_over_deterministic_anchor" in artifact["risk_flags"]
    json.dumps(artifact, allow_nan=False)


def test_hybrid_method_validation_rejects_non_parity_candidate():
    repair = _repair_artifact()
    repair["task_results"]["task_a"]["llm_anchor_copy"]["test_loss"] = 0.02
    artifact = build_lcdu_anes_hybrid_method_validation(
        artifact_id="hybrid-method-test",
        strong_baseline_matrix=_strong_baseline_matrix(),
        anchor_fidelity_repair=repair,
    )

    assert artifact["overall_status"] == "hybrid_candidate_not_validated"
    assert artifact["numeric_parity_count"] == 0
    assert "hybrid_numeric_parity_incomplete" in artifact["risk_flags"]


def test_hybrid_method_validation_script_writes_json(tmp_path):
    strong = tmp_path / "strong.json"
    repair = tmp_path / "repair.json"
    output = tmp_path / "hybrid.json"
    strong.write_text(json.dumps(_strong_baseline_matrix()))
    repair.write_text(json.dumps(_repair_artifact()))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_anes_hybrid_method_validation.py",
            "--strong-baseline-matrix",
            str(strong),
            "--anchor-fidelity-repair",
            str(repair),
            "--output",
            str(output),
            "--artifact-id",
            "hybrid-method-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "artifact_id": "hybrid-method-test",
        "numeric_parity_count": 1,
        "output": str(output),
        "research_decision": (
            "reframe_as_hybrid_auditable_constraint_framework_not_accuracy_win"
        ),
        "status": "hybrid_candidate_numeric_parity_soft_not_leading",
        "strict_copy_positive_count": 1,
        "task_count": 1,
    }


def _strong_baseline_matrix() -> dict:
    return {
        "schema_version": "lcdu-anes-strong-baseline-matrix-v1",
        "artifact_id": "strong-test",
        "overall_status": "strong_baseline_lcdu_not_leading",
        "validation_type": "lcdu_strong_baseline_matrix",
        "task_results": {
            "task_a": {
                "lcdU_test_loss": 0.03,
                "lcdU_selected_source_artifact_id": "soft-source",
                "best_covered_baseline_family": "deterministic_anchor_search",
                "best_covered_baseline_method_id": "calibration_segment_anchor",
                "best_covered_baseline_test_loss": 0.01,
            }
        },
    }


def _repair_artifact() -> dict:
    return {
        "schema_version": "lcdu-anes-anchor-fidelity-repair-v1",
        "artifact_id": "repair-test",
        "overall_status": "llm_anchor_copy_repair_positive",
        "validation_type": "lcdu_anchor_fidelity_repair_diagnostic",
        "task_results": {
            "task_a": {
                "llm_anchor_copy": {
                    "closes_lcdu_gap": True,
                    "test_loss": 0.01,
                },
                "deterministic_anchor_copy": {
                    "closes_lcdu_gap": True,
                    "test_loss": 0.01,
                },
            }
        },
    }
