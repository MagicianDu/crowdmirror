import json
import subprocess
import sys

from experiments.r11_interaction_risk_discoverer import (
    R11_INTERACTION_RISK_DISCOVERER_SCHEMA_VERSION,
    build_r11_interaction_risk_discoverer,
)


def test_r11_interaction_risk_discoverer_defines_learnable_method_without_escalating_claims():
    report = build_r11_interaction_risk_discoverer(
        artifact_id="r11-interaction-risk-discoverer-test",
        run_id="r11-l0-run",
    )

    assert report["schema_version"] == R11_INTERACTION_RISK_DISCOVERER_SCHEMA_VERSION
    assert report["status"] == (
        "r11_interaction_risk_discoverer_controlled_lab_positive"
    )
    assert report["claim_level"] == "controlled_proxy_lab_only"
    assert report["method_contract"] == {
        "static_prior_is_foundation": True,
        "learns_interaction_update_operator": True,
        "learns_from_outcome_residual": True,
        "uses_mechanism_and_segment_state": True,
        "separates_product_guard_from_method": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert [unit["unit_id"] for unit in report["learning_units"]] == [
        "mechanism_weight_learning",
        "segment_sensitivity_learning",
        "interaction_propagation_learning",
        "uncertainty_interval_learning",
    ]
    assert report["acceptance_gates"]["controlled_lab_positive_signal"] is True
    assert report["acceptance_gates"]["external_holdout_required_before_product_core"] is True
    assert report["acceptance_gates"]["product_core_method_ready"] is False
    assert report["acceptance_gates"]["field_outcome_validated"] is False
    assert report["acceptance_gates"]["runtime_default_allowed"] is False
    assert "R11 supports Product core method by default" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r11_interaction_risk_discoverer_beats_guarded_overlay_only_inside_controlled_lab():
    report = build_r11_interaction_risk_discoverer(
        artifact_id="r11-interaction-risk-discoverer-test",
        run_id="r11-l0-run",
    )

    metrics = report["method_metrics"]
    r10 = metrics["r10_hps_interval_guarded_overlay"]
    r11 = metrics["r11_learnable_interaction_risk_discoverer"]

    assert r11["risk_ranking_quality"] > r10["risk_ranking_quality"]
    assert r11["decision_value_score"] > r10["decision_value_score"]
    assert r11["interval_coverage"] >= r10["interval_coverage"]
    assert r11["false_alarm_rate"] <= r10["false_alarm_rate"]
    assert report["method_gain_summary"] == {
        "comparison_baseline": "r10_hps_interval_guarded_overlay",
        "risk_ranking_quality_delta": 0.25,
        "decision_value_delta": 0.08,
        "interval_coverage_delta": 0.0,
        "false_alarm_rate_delta": 0.0,
        "net_decision": "continue_to_external_holdout_and_runtime_trial_guarded",
    }
    assert report["research_decision"] == (
        "continue_r11_method_development_but_do_not_enable_product_core"
    )


def test_r11_interaction_risk_discoverer_keeps_holdout_and_failure_boundary_visible():
    report = build_r11_interaction_risk_discoverer(
        artifact_id="r11-interaction-risk-discoverer-test",
        run_id="r11-l0-run",
    )

    holdout = report["controlled_lab_holdout"]
    assert holdout["protocol"] == "leave_one_scenario_family_out"
    assert holdout["case_count"] == 4
    assert holdout["pass_rate"] == 1.0
    assert holdout["field_outcome_validated"] is False
    assert holdout["runtime_default_allowed"] is False
    assert report["failure_boundary"] == [
        "controlled_proxy_lab_not_external_holdout",
        "mechanism_taxonomy_is_still_hand_defined",
        "needs_real_customer_or_field_outcome_feedback",
        "needs_product_runtime_shadow_trial",
    ]


def test_r11_interaction_risk_discoverer_cli_writes_artifact(tmp_path):
    output = tmp_path / "r11-interaction-risk-discoverer.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r11_interaction_risk_discoverer.py",
            "--artifact-id",
            "r11-interaction-risk-discoverer-cli",
            "--run-id",
            "r11-l0-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r11-interaction-risk-discoverer-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r11-interaction-risk-discoverer-cli",
        "output": str(output),
        "status": "r11_interaction_risk_discoverer_controlled_lab_positive",
    }
