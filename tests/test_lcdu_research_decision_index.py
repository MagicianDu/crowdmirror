import json
import subprocess
import sys

from experiments.lcdu_research_decision_index import (
    build_lcdu_research_decision_index,
)


def test_research_decision_index_reaches_hybrid_conditional_boundary():
    decision = build_lcdu_research_decision_index(
        artifact_id="decision-test",
        paper_gate_index=_paper_gate_index(),
        hybrid_method_validation=_hybrid_method_validation(),
    )

    assert decision["schema_version"] == "lcdu-research-decision-index-v1"
    assert decision["overall_status"] == "decision_boundary_reached_hybrid_conditional"
    assert decision["primary_decision"]["lcdu_soft"] == (
        "reject_as_ccf_a_main_contribution_accuracy_optimizer"
    )
    assert decision["primary_decision"]["lcdu_hybrid"] == (
        "conditionally_promising_as_auditable_constraint_framework"
    )
    assert decision["primary_decision"]["ccf_a_gate"] == (
        "not_passed_under_accuracy_superiority_criterion"
    )
    assert "auditability_metric" in decision["remaining_evidence_for_ccf_a"]
    json.dumps(decision, allow_nan=False)


def test_research_decision_index_marks_incomplete_without_hybrid_gate():
    paper_gate = _paper_gate_index()
    paper_gate["completed_subgates"].remove("hybrid_method_numeric_parity_not_accuracy_win")
    decision = build_lcdu_research_decision_index(
        artifact_id="decision-test",
        paper_gate_index=paper_gate,
        hybrid_method_validation=_hybrid_method_validation(),
    )

    assert decision["overall_status"] == "decision_boundary_incomplete"
    assert decision["primary_decision"]["lcdu_hybrid"] == "insufficient_evidence"


def test_research_decision_index_script_writes_json(tmp_path):
    paper_gate = tmp_path / "paper-gate.json"
    hybrid = tmp_path / "hybrid.json"
    output = tmp_path / "decision.json"
    paper_gate.write_text(json.dumps(_paper_gate_index()))
    hybrid.write_text(json.dumps(_hybrid_method_validation()))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_research_decision_index.py",
            "--paper-gate-index",
            str(paper_gate),
            "--hybrid-method-validation",
            str(hybrid),
            "--output",
            str(output),
            "--artifact-id",
            "decision-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "artifact_id": "decision-test",
        "ccf_a_gate": "not_passed_under_accuracy_superiority_criterion",
        "hybrid_decision": "conditionally_promising_as_auditable_constraint_framework",
        "output": str(output),
        "soft_decision": "reject_as_ccf_a_main_contribution_accuracy_optimizer",
        "status": "decision_boundary_reached_hybrid_conditional",
    }


def _paper_gate_index() -> dict:
    return {
        "schema_version": "lcdu-paper-gate-index-v1",
        "artifact_id": "paper-gate-test",
        "completed_subgates": [
            "strong_baseline_signal_not_positive",
            "hybrid_method_numeric_parity_not_accuracy_win",
            "theoretical_identification_proof_ready",
            "finer_schema_robustness_signal_positive",
        ],
        "required_next_gates": ["run_strong_baseline_matrix"],
    }


def _hybrid_method_validation() -> dict:
    return {
        "schema_version": "lcdu-anes-hybrid-method-validation-v1",
        "artifact_id": "hybrid-test",
        "validation_type": "lcdu_hybrid_method_validation",
        "research_decision": (
            "reframe_as_hybrid_auditable_constraint_framework_not_accuracy_win"
        ),
    }
