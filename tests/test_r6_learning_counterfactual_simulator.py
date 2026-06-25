from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from experiments.r6_learning_counterfactual_simulator import (
    build_r6_learning_counterfactual_simulator,
)


def test_learning_counterfactual_simulator_reduces_false_alarm_without_losing_risk_recovery():
    report = build_r6_learning_counterfactual_simulator(
        artifact_id="r6-learning-counterfactual-simulator-test",
        run_id="r6-learning-counterfactual-run",
    )

    assert report["schema_version"] == "r6-learning-counterfactual-simulator-v1"
    assert report["status"] == "learning_counterfactual_simulator_guarded_positive_signal"
    assert report["claim_status"] == "guarded_diagnostic"

    summary = report["summary"]
    assert summary["raw_interaction_false_alarm_rate"] == 0.667
    assert summary["learned_operator_false_alarm_rate"] <= 0.333
    assert summary["static_prior_miss_recovery_rate"] == 1.0
    assert summary["counterfactual_policy_count"] >= 3

    gates = report["acceptance_gates"]
    assert gates["learned_operator_reduces_false_alarm_vs_raw_interaction"] is True
    assert gates["static_prior_miss_recovery_preserved"] is True
    assert gates["counterfactual_policy_rankings_present"] is True
    assert gates["field_outcome_validated"] is False
    assert gates["runtime_default_allowed"] is False


def test_learning_counterfactual_simulator_outputs_learned_mechanism_weights_and_ranked_policies():
    report = build_r6_learning_counterfactual_simulator(
        artifact_id="r6-learning-counterfactual-simulator-test",
        run_id="r6-learning-counterfactual-run",
    )

    weights = {
        weight["mechanism_id"]: weight
        for weight in report["learned_mechanism_weights"]
    }
    assert weights["access_anxiety"]["learned_weight"] > 1.0
    assert weights["rights_loss_salience"]["learned_weight"] < 1.0
    assert weights["official_trust_buffer"]["learned_weight"] == 0.0
    assert weights["access_anxiety"]["evidence_case_count"] >= 1
    assert weights["rights_loss_salience"]["evidence_case_count"] >= 2

    for case in report["case_results"]:
        policies = case["counterfactual_policy_results"]
        assert len(policies) >= 3
        assert [policy["rank"] for policy in policies] == list(range(1, len(policies) + 1))
        assert policies[0]["decision_value_score"] >= policies[-1]["decision_value_score"]
        assert case["source_artifact_ids"]

    htops = {
        case["source_key"]: case for case in report["case_results"]
    }["htops_cost_pressure"]
    assert htops["learned_operator_flags_new_risk"] is True
    assert htops["raw_interaction_flags_new_risk"] is True

    health = {
        case["source_key"]: case for case in report["case_results"]
    }["anes_health_heldout"]
    assert health["raw_interaction_false_alarm"] is True
    assert health["learned_operator_false_alarm"] is False


def test_learning_counterfactual_simulator_keeps_product_claims_fail_closed():
    report = build_r6_learning_counterfactual_simulator(
        artifact_id="r6-learning-counterfactual-simulator-test",
        run_id="r6-learning-counterfactual-run",
    )

    assert "field_outcome_validated=true" in report["blocked_claims"]
    assert "runtime_default_allowed=true" in report["blocked_claims"]
    assert "精准预测系统" in report["blocked_claims"]
    assert report["product_support_delta"]["supports_product_values"] == [
        "risk_distribution",
        "abnormal_segments",
        "mechanism_explanation",
        "counterfactual_policy_comparison",
        "false_alarm_control",
    ]
    assert report["product_support_delta"]["unsupported_product_values"] == [
        "field_validated_trend_direction",
        "runtime_default_update",
    ]


def test_learning_counterfactual_simulator_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-learning-counterfactual-simulator.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_learning_counterfactual_simulator.py",
            "--artifact-id",
            "r6-learning-counterfactual-simulator-cli",
            "--run-id",
            "r6-learning-counterfactual-run",
            "--output",
            str(output),
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    stdout = json.loads(completed.stdout)
    artifact = json.loads(Path(output).read_text())
    assert stdout["status"] == "learning_counterfactual_simulator_guarded_positive_signal"
    assert stdout["output"] == str(output)
    assert artifact["schema_version"] == "r6-learning-counterfactual-simulator-v1"
