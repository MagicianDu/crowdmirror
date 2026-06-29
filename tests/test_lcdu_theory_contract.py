import json
import subprocess
import sys

from experiments.lcdu_theory_contract import build_lcdu_theory_contract


def test_build_lcdu_theory_contract_maps_formal_objects_to_artifact_fields():
    contract = build_lcdu_theory_contract(
        artifact_id="lcdu-theory-contract-test",
        method_summary=_method_summary(),
        theory_ref="paper/LCDU_THEORY.md",
        algorithm_ref="paper/LCDU_ALGORITHM.md",
    )

    assert contract["schema_version"] == "lcdu-theory-contract-v1"
    assert contract["overall_status"] == "formal_objects_mapped"
    assert contract["method_summary_artifact_id"] == (
        "policy-reaction-lcdu-l3-method-summary-current-001"
    )
    assert contract["formal_object_count"] == 8
    assert [item["object_id"] for item in contract["formal_objects"]] == [
        "simulator_state_theta",
        "segment_space_s",
        "policy_option_space_p",
        "target_distribution_p_star",
        "simulator_distribution_q_theta",
        "residual_signature_r",
        "lcdu_update_candidate_u",
        "split_gated_acceptance",
    ]
    acceptance = contract["formal_objects"][-1]
    assert acceptance["required_artifact_fields"] == [
        "source_split_contract",
        "initial_loss",
        "best_loss",
        "final_loss",
        "candidate_accepted_count",
        "candidate_rejected_count",
    ]
    assert "complete_lcdu_theory_contract" in contract["closed_gate_ids"]
    json.dumps(contract, allow_nan=False)


def test_lcdu_theory_contract_script_writes_json(tmp_path):
    method_summary = tmp_path / "method-summary.json"
    output = tmp_path / "theory-contract.json"
    method_summary.write_text(json.dumps(_method_summary()))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_theory_contract.py",
            "--method-summary",
            str(method_summary),
            "--output",
            str(output),
            "--artifact-id",
            "lcdu-theory-contract-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "artifact_id": "lcdu-theory-contract-test",
        "formal_object_count": 8,
        "output": str(output),
        "overall_status": "formal_objects_mapped",
    }
    assert json.loads(output.read_text())["closed_gate_ids"] == [
        "complete_lcdu_theory_contract"
    ]


def _method_summary() -> dict:
    return {
        "schema_version": "policy-reaction-lcdu-l3-method-summary-v1",
        "artifact_id": "policy-reaction-lcdu-l3-method-summary-current-001",
        "method_id": "LCDU-L3",
        "overall_status": "active_mainline_bounded",
        "product_transfer_status": "bounded_transfer_ready",
        "accepted_candidate_ids": [
            "policy-reaction-lcdu-l3-current-001-h02",
            "policy-reaction-lcdu-l3-interaction-current-001-i01",
        ],
        "evidence": {
            "stability": {"stable_repeat_count": 2},
            "mechanism": {"best_runtime_loss": 0.000092334757},
            "route_coverage": {"challenger_count": 6},
            "residual_weakness": {"status": "open"},
        },
        "ccf_a_gaps": ["theoretical_identification_needs_formalization"],
        "risk_flags": ["not_customer_field_validated"],
        "claim_boundaries": [
            "LCDU L3 method summary supports bounded product transfer only; not field validation."
        ],
    }
