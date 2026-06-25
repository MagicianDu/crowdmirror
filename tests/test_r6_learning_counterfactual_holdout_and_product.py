from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from experiments.r6_learning_counterfactual_holdout_validation import (
    build_r6_learning_counterfactual_holdout_validation,
)
from experiments.r6_learning_counterfactual_simulator import (
    build_r6_learning_counterfactual_simulator,
)
from experiments.r6_product_claim_evidence_registry import (
    build_r6_product_claim_evidence_registry,
    build_r6_research_product_value_support_v2,
)
from experiments.r6_product_customer_value_report import (
    build_r6_product_customer_value_report,
)


def test_learning_counterfactual_holdout_reports_leave_one_case_evidence():
    report = build_r6_learning_counterfactual_holdout_validation(
        artifact_id="r6-learning-counterfactual-holdout-test",
        run_id="r6-learning-counterfactual-run",
    )

    assert report["schema_version"] == "r6-learning-counterfactual-holdout-validation-v1"
    assert report["status"] == "learning_counterfactual_holdout_mixed_blocked"
    assert report["summary"]["holdout_trial_count"] == 3
    assert report["summary"]["non_regression_rate"] >= 0.667
    assert report["summary"]["false_alarm_reduction_rate"] >= 0.5
    assert report["summary"]["static_prior_miss_recovery_rate"] == 1.0
    assert report["summary"]["supported_holdout_count"] >= 1
    assert report["acceptance_gates"]["leave_one_case_holdout_present"] is True
    assert report["acceptance_gates"]["independent_holdout_passed"] is False
    assert report["acceptance_gates"]["runtime_default_allowed"] is False
    assert "needs_more_independent_holdout_support" in report["blocking_gaps"]

    for trial in report["holdout_trials"]:
        assert trial["train_source_keys"]
        assert trial["heldout_source_key"]
        assert trial["heldout_source_key"] not in trial["train_source_keys"]
        assert trial["learned_mechanism_weights"]
        assert trial["transfer_diagnostics"]["unseen_mechanism_count"] >= 0
        assert trial["claim_status"] in {"guarded_supported", "diagnostic_blocked"}


def test_learning_counterfactual_holdout_applies_unseen_mechanism_floor_without_restoring_false_alarms():
    report = build_r6_learning_counterfactual_holdout_validation(
        artifact_id="r6-learning-counterfactual-holdout-test",
        run_id="r6-learning-counterfactual-run",
    )

    trials = {
        trial["heldout_source_key"]: trial
        for trial in report["holdout_trials"]
    }
    htops = trials["htops_cost_pressure"]
    assert htops["static_prior_missed_high_risk"] is True
    assert htops["static_prior_miss_recovered"] is True
    assert htops["learned_operator_flags_new_risk"] is True
    assert htops["transfer_diagnostics"]["unseen_mechanism_floor_applied"] is True
    assert htops["transfer_diagnostics"]["unseen_mechanism_count"] >= 3
    assert "unseen_high_risk_mechanism_transfer_floor" in htops["transfer_diagnostics"][
        "diagnostic_reasons"
    ]

    for source_key in ["anes_health_heldout", "anes_climate_heldout"]:
        assert trials[source_key]["raw_interaction_false_alarm"] is True
        assert trials[source_key]["learned_operator_false_alarm"] is False
        assert trials[source_key]["false_alarm_reduced"] is True


def test_learning_counterfactual_holdout_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-learning-counterfactual-holdout-validation.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_learning_counterfactual_holdout_validation.py",
            "--artifact-id",
            "r6-learning-counterfactual-holdout-cli",
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
    assert stdout["status"] == "learning_counterfactual_holdout_mixed_blocked"
    assert stdout["output"] == str(output)
    assert artifact["schema_version"] == "r6-learning-counterfactual-holdout-validation-v1"


def test_product_evidence_registry_ingests_learning_counterfactual_policy_comparison():
    simulator = build_r6_learning_counterfactual_simulator(
        artifact_id="r6-learning-counterfactual-simulator-test",
        run_id="r6-learning-counterfactual-run",
    )
    holdout = build_r6_learning_counterfactual_holdout_validation(
        artifact_id="r6-learning-counterfactual-holdout-test",
        run_id="r6-learning-counterfactual-run",
        learning_counterfactual_simulator=simulator,
    )
    registry = build_r6_product_claim_evidence_registry(
        artifact_id="r6-product-claim-evidence-registry-test",
        run_id="r6-learning-counterfactual-run",
        learning_counterfactual_simulator=simulator,
        learning_counterfactual_holdout_validation=holdout,
    )

    claims = {
        claim["product_section"]: claim
        for claim in registry["claim_results"]
    }
    assert "counterfactual_policy_comparison" in claims
    counterfactual = claims["counterfactual_policy_comparison"]
    assert counterfactual["claim_status"] == "diagnostic"
    assert counterfactual["support_status"] == "guarded_current_proxy_positive_signal"
    assert simulator["artifact_id"] in counterfactual["source_artifact_ids"]
    assert holdout["artifact_id"] in counterfactual["source_artifact_ids"]
    assert registry["acceptance_gates"]["all_product_visible_claims_source_backed"] is True
    assert registry["acceptance_gates"]["counterfactual_policy_comparison_source_backed"] is True


def test_customer_value_report_exposes_counterfactual_policy_comparison_from_source():
    simulator = build_r6_learning_counterfactual_simulator(
        artifact_id="r6-learning-counterfactual-simulator-test",
        run_id="r6-learning-counterfactual-run",
    )
    holdout = build_r6_learning_counterfactual_holdout_validation(
        artifact_id="r6-learning-counterfactual-holdout-test",
        run_id="r6-learning-counterfactual-run",
        learning_counterfactual_simulator=simulator,
    )
    registry = build_r6_product_claim_evidence_registry(
        artifact_id="r6-product-claim-evidence-registry-test",
        run_id="r6-learning-counterfactual-run",
        learning_counterfactual_simulator=simulator,
        learning_counterfactual_holdout_validation=holdout,
    )
    support = build_r6_research_product_value_support_v2(
        artifact_id="r6-research-product-value-support-v2-test",
        run_id="r6-learning-counterfactual-run",
        claim_evidence_registry=registry,
    )
    report = build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-test",
        run_id="r6-learning-counterfactual-run",
        value_support=support,
        learning_counterfactual_simulator=simulator,
        learning_counterfactual_holdout_validation=holdout,
    )

    payload = report["display_payload"]["counterfactual_policy_comparison"]
    assert payload["support_status"] == "guarded_current_proxy_positive_signal"
    assert payload["claim_status"] == "diagnostic"
    assert payload["summary"]["learned_operator_false_alarm_rate"] == 0.0
    assert payload["holdout_summary"]["independent_holdout_passed"] is False
    assert payload["top_policy_by_case"]
    assert {
        simulator["artifact_id"],
        holdout["artifact_id"],
    }.issubset(set(report["source_refs"]))
