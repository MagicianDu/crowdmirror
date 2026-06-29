import json
import subprocess
import sys

from experiments.r8_learnable_mechanism_simulation import (
    R8_CLAIM_BOUNDARY,
    build_r8_learnable_mechanism_bundle,
)


def test_r8_bundle_contains_l0_artifacts_and_guarded_boundaries():
    bundle = build_r8_learnable_mechanism_bundle(
        artifact_id="r8-learnable-mechanism-bundle-test",
        run_id="r8-l0-run",
        case_id="generic-public-service-policy-change",
    )

    assert bundle["schema_version"] == "r8-learnable-mechanism-bundle-v1"
    assert bundle["status"] == "r8_contract_ready_guarded"
    assert bundle["claim_boundary"] == R8_CLAIM_BOUNDARY
    assert bundle["acceptance_gates"] == {
        "artifact_contracts_present": True,
        "source_refs_present": True,
        "product_guard_consumable": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert set(bundle["artifacts"]) == {
        "r8_mechanism_causal_graph_manifest",
        "r8_operator_parameter_registry",
        "r8_rollout_distribution",
        "r8_risk_interval_calibration_report",
        "r8_risk_ranking_report",
        "r8_outcome_attribution_report",
        "r8_operator_update_candidate",
        "r8_product_support_gate",
    }

    for artifact in bundle["artifacts"].values():
        assert artifact["artifact_id"].startswith("r8-learnable-mechanism-bundle-test")
        assert artifact["run_id"] == "r8-l0-run"
        assert artifact["schema_version"].startswith("r8-")
        assert artifact["source_refs"]
        assert artifact["claim_boundary"] == R8_CLAIM_BOUNDARY

    json.dumps(bundle, allow_nan=False)


def test_r8_mechanism_graph_and_parameter_registry_are_learnable_but_guarded():
    bundle = build_r8_learnable_mechanism_bundle(
        artifact_id="r8-learnable-mechanism-bundle-test",
        run_id="r8-l0-run",
        case_id="generic-public-service-policy-change",
    )

    graph = bundle["artifacts"]["r8_mechanism_causal_graph_manifest"]
    assert graph["mechanism_catalog"]
    assert graph["graph_nodes"]
    assert graph["graph_edges"]
    assert all(edge["evidence_source"] for edge in graph["graph_edges"])
    assert any(edge["learnable"] is True for edge in graph["graph_edges"])

    registry = bundle["artifacts"]["r8_operator_parameter_registry"]
    assert registry["runtime_default_allowed"] is False
    assert registry["parameter_families"] == [
        "mechanism_activation",
        "segment_sensitivity",
        "propagation_edge",
        "uncertainty_calibration",
        "guard_penalty",
    ]
    for parameter in registry["parameters"]:
        assert parameter["parameter_id"]
        assert (
            parameter["allowed_range"][0]
            <= parameter["current_value"]
            <= parameter["allowed_range"][1]
        )
        assert parameter["runtime_default_allowed"] is False


def test_r8_llm_boundary_is_structured_and_non_authoritative():
    bundle = build_r8_learnable_mechanism_bundle(
        artifact_id="r8-learnable-mechanism-bundle-test",
        run_id="r8-l0-run",
        case_id="generic-public-service-policy-change",
    )

    graph = bundle["artifacts"]["r8_mechanism_causal_graph_manifest"]
    assert graph["llm_boundary"] == {
        "llm_may_generate_candidate_mechanisms": True,
        "llm_may_generate_customer_narrative_draft": True,
        "llm_can_set_field_outcome_validated": False,
        "llm_can_set_runtime_default_allowed": False,
        "structured_output_required": True,
    }

    support_gate = bundle["artifacts"]["r8_product_support_gate"]
    assert support_gate["field_outcome_validated"] is False
    assert support_gate["runtime_default_allowed"] is False
    assert "R8 validated" in support_gate["blocked_claims"]
    assert "runtime default ready" in support_gate["blocked_claims"]


def test_r8_bundle_cli_writes_current_artifact(tmp_path):
    output = tmp_path / "r8-learnable-mechanism-bundle.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r8_learnable_mechanism_simulation.py",
            "--artifact-id",
            "r8-learnable-mechanism-bundle-cli",
            "--run-id",
            "r8-l0-run",
            "--case-id",
            "generic-public-service-policy-change",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r8-learnable-mechanism-bundle-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r8-learnable-mechanism-bundle-cli",
        "output": str(output),
        "status": "r8_contract_ready_guarded",
    }


def test_r8_outcome_feedback_generates_mechanism_level_attribution():
    bundle = build_r8_learnable_mechanism_bundle(
        artifact_id="r8-learnable-mechanism-bundle-test",
        run_id="r8-l1-run",
        case_id="generic-public-service-policy-change",
        observed_reject_proxy=0.47,
    )

    attribution = bundle["artifacts"]["r8_outcome_attribution_report"]
    assert attribution["outcome_residual"] is not None
    assert attribution["attribution_by_mechanism"]
    assert attribution["attribution_by_edge"]
    assert attribution["attribution_by_segment"]
    assert attribution["unexplained_error"] <= 0.5
    assert {item["error_type"] for item in attribution["attribution_by_mechanism"]} <= {
        "mechanism_strength_error",
        "mechanism_direction_supported",
        "mechanism_missing",
    }


def test_r8_operator_update_candidate_is_bounded_and_not_runtime_default():
    bundle = build_r8_learnable_mechanism_bundle(
        artifact_id="r8-learnable-mechanism-bundle-test",
        run_id="r8-l1-run",
        case_id="generic-public-service-policy-change",
        observed_reject_proxy=0.47,
    )

    update = bundle["artifacts"]["r8_operator_update_candidate"]
    assert update["updated_parameters"]
    assert update["accepted"] is False
    assert update["rejected_reason"] == "pending_holdout_review"
    assert update["runtime_default_allowed"] is False
    assert update["guard_checks"] == {
        "bounded_update": True,
        "holdout_required": True,
        "robustness_required": True,
        "runtime_default_allowed": False,
    }
    for parameter in update["updated_parameters"]:
        assert abs(parameter["delta"]) <= parameter["max_abs_delta"]
        assert (
            parameter["source_attribution_id"]
            == bundle["artifacts"]["r8_outcome_attribution_report"]["artifact_id"]
        )
