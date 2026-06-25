import json
import subprocess
import sys

from experiments.r7_mechanism_generative_simulation import (
    R7_CLAIM_BOUNDARY,
    build_r7_mechanism_generative_bundle,
)


def test_r7_bundle_contains_all_contract_first_artifacts():
    bundle = build_r7_mechanism_generative_bundle(
        artifact_id="r7-mechanism-generative-bundle-test",
        run_id="r7-contract-first-run",
        case_id="generic-price-change",
    )

    assert bundle["schema_version"] == "r7-mechanism-generative-bundle-v1"
    assert bundle["status"] == "r7_contract_first_mvp_ready_guarded"
    assert bundle["claim_boundary"] == R7_CLAIM_BOUNDARY
    assert bundle["acceptance_gates"] == {
        "artifact_contracts_present": True,
        "product_six_outputs_source_backed": True,
        "interaction_trace_present": True,
        "rollout_distribution_present": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }

    expected_artifacts = {
        "r7_mechanism_state_manifest",
        "r7_interaction_graph_manifest",
        "r7_rollout_distribution",
        "r7_risk_interval_report",
        "r7_segment_anomaly_report",
        "r7_counterfactual_policy_sandbox",
        "r7_outcome_feedback_update_candidate",
        "r7_product_support_report",
    }
    assert set(bundle["artifacts"]) == expected_artifacts

    for artifact_name, artifact in bundle["artifacts"].items():
        assert artifact["artifact_id"].startswith("r7-mechanism-generative-bundle-test")
        assert artifact["run_id"] == "r7-contract-first-run"
        assert artifact["schema_version"].startswith(artifact_name.replace("_", "-"))
        assert artifact["source_refs"]
        assert artifact["claim_boundary"] == R7_CLAIM_BOUNDARY

    json.dumps(bundle, allow_nan=False)


def test_r7_bundle_builds_mechanism_states_and_interaction_rollouts():
    bundle = build_r7_mechanism_generative_bundle(
        artifact_id="r7-mechanism-generative-bundle-test",
        run_id="r7-contract-first-run",
        case_id="generic-price-change",
    )

    mechanism = bundle["artifacts"]["r7_mechanism_state_manifest"]
    assert mechanism["mechanism_dimensions"] == [
        "price_sensitivity",
        "trust_loss",
        "fairness_perception",
        "substitution_option",
        "identity_alignment",
        "social_diffusion_sensitivity",
    ]
    assert len(mechanism["segment_mechanism_states"]) == 3
    for segment_state in mechanism["segment_mechanism_states"]:
        assert segment_state["mechanism_state"]
        assert segment_state["ablation_ready"] is True
        for value in segment_state["mechanism_state"].values():
            assert 0.0 <= value <= 1.0

    graph = bundle["artifacts"]["r7_interaction_graph_manifest"]
    assert graph["controls"]["no_interaction_control_present"] is True
    assert graph["controls"]["interaction_on_present"] is True
    assert len(graph["nodes"]) == 3
    assert graph["edges"]
    assert graph["propagation_steps"]

    rollout = bundle["artifacts"]["r7_rollout_distribution"]
    assert rollout["rollout_count"] == 50
    assert rollout["seeded_reproducible"] is True
    assert rollout["no_interaction_control"]["median"] < rollout["interaction_on"]["median"]
    assert len(rollout["rollouts"]) == 50
    first_rollout = rollout["rollouts"][0]
    assert first_rollout["seed"] == 0
    assert first_rollout["segment_results"]
    assert first_rollout["aggregate"]["interaction_on"] >= first_rollout["aggregate"]["no_interaction"]


def test_r7_bundle_supports_product_outputs_and_guarded_claims():
    bundle = build_r7_mechanism_generative_bundle(
        artifact_id="r7-mechanism-generative-bundle-test",
        run_id="r7-contract-first-run",
        case_id="generic-price-change",
    )

    interval = bundle["artifacts"]["r7_risk_interval_report"]
    assert interval["risk_interval"]["p10"] <= interval["risk_interval"]["median"]
    assert interval["risk_interval"]["median"] <= interval["risk_interval"]["p90"]
    assert interval["risk_interval"]["interval_width"] > 0
    assert interval["risk_interval"]["over_wide_penalty"] >= 0

    anomaly = bundle["artifacts"]["r7_segment_anomaly_report"]
    assert anomaly["static_hidden_risks"]
    assert anomaly["interaction_amplified_risks"]
    assert anomaly["false_alarm_diagnosis"]

    sandbox = bundle["artifacts"]["r7_counterfactual_policy_sandbox"]
    assert len(sandbox["policy_options"]) >= 3
    assert sandbox["policy_ranking"][0]["dominance_status"] in {
        "dominant_on_risk_reduction",
        "trade_off",
    }

    update = bundle["artifacts"]["r7_outcome_feedback_update_candidate"]
    assert update["update_status"] == "blocked_until_holdout_and_runtime_guard"
    assert update["rollback_conditions"]
    assert update["runtime_default_allowed"] is False

    support = bundle["artifacts"]["r7_product_support_report"]
    assert support["product_positioning"] == "人群反应趋势与风险区间模拟器"
    assert support["product_outputs"] == [
        "trend_direction",
        "risk_interval",
        "risk_distribution",
        "abnormal_segments",
        "mechanism_explanation",
        "counterfactual_policy_sandbox",
    ]
    for output in support["output_support"]:
        assert output["source_artifact_ids"]
        assert output["claim_status"] in {"guarded", "diagnostic"}
    assert "精准预测系统" in support["blocked_claims"]
    assert "runtime_default_allowed=true" in support["blocked_claims"]


def test_r7_bundle_cli_writes_current_artifact(tmp_path):
    output = tmp_path / "r7-mechanism-generative-bundle.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r7_mechanism_generative_simulation.py",
            "--artifact-id",
            "r7-mechanism-generative-bundle-cli",
            "--run-id",
            "r7-contract-first-run",
            "--case-id",
            "generic-price-change",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r7-mechanism-generative-bundle-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r7-mechanism-generative-bundle-cli",
        "output": str(output),
        "status": "r7_contract_first_mvp_ready_guarded",
    }
