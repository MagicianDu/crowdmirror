import json
import subprocess
import sys

from experiments.lcdu_theoretical_identification_proof import (
    build_lcdu_theoretical_identification_proof,
)


def test_theoretical_identification_proof_ready_for_full_hybrid_parity():
    proof = build_lcdu_theoretical_identification_proof(
        artifact_id="theory-proof-test",
        theory_contract=_theory_contract(),
        hybrid_method_validation=_hybrid_method_validation(),
    )

    assert proof["schema_version"] == "lcdu-theoretical-identification-proof-v1"
    assert proof["overall_status"] == "bounded_hybrid_identification_proof_ready"
    assert proof["closed_gate_ids"] == ["theoretical_identification_proof_ready"]
    assert proof["identification_result"] == (
        "hybrid_numeric_distribution_identified_with_segment_anchor"
    )
    claim_ids = {claim["claim_id"] for claim in proof["formal_claims"]}
    assert claim_ids == {
        "split_isolation",
        "anchor_copy_identification",
        "non_superiority_boundary",
    }
    assert "narrative_utility_metric_missing" in proof["remaining_theory_risks"]
    json.dumps(proof, allow_nan=False)


def test_theoretical_identification_proof_marks_partial_parity_incomplete():
    hybrid = _hybrid_method_validation()
    hybrid["numeric_parity_count"] = 0
    proof = build_lcdu_theoretical_identification_proof(
        artifact_id="theory-proof-test",
        theory_contract=_theory_contract(),
        hybrid_method_validation=hybrid,
    )

    assert proof["overall_status"] == "bounded_hybrid_identification_proof_incomplete"
    assert proof["identification_result"] == (
        "hybrid_numeric_distribution_not_fully_identified"
    )


def test_theoretical_identification_proof_script_writes_json(tmp_path):
    theory = tmp_path / "theory.json"
    hybrid = tmp_path / "hybrid.json"
    output = tmp_path / "proof.json"
    theory.write_text(json.dumps(_theory_contract()))
    hybrid.write_text(json.dumps(_hybrid_method_validation()))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_theoretical_identification_proof.py",
            "--theory-contract",
            str(theory),
            "--hybrid-method-validation",
            str(hybrid),
            "--output",
            str(output),
            "--artifact-id",
            "theory-proof-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "artifact_id": "theory-proof-test",
        "closed_gate_ids": ["theoretical_identification_proof_ready"],
        "identification_result": (
            "hybrid_numeric_distribution_identified_with_segment_anchor"
        ),
        "output": str(output),
        "status": "bounded_hybrid_identification_proof_ready",
    }


def _theory_contract() -> dict:
    return {
        "schema_version": "lcdu-theory-contract-v1",
        "artifact_id": "theory-contract-test",
        "overall_status": "formal_objects_mapped",
        "closed_gate_ids": ["complete_lcdu_theory_contract"],
    }


def _hybrid_method_validation() -> dict:
    return {
        "schema_version": "lcdu-anes-hybrid-method-validation-v1",
        "artifact_id": "hybrid-method-test",
        "overall_status": "hybrid_candidate_numeric_parity_soft_not_leading",
        "validation_type": "lcdu_hybrid_method_validation",
        "task_count": 2,
        "numeric_parity_count": 2,
        "strict_copy_positive_count": 2,
        "research_decision": (
            "reframe_as_hybrid_auditable_constraint_framework_not_accuracy_win"
        ),
    }
