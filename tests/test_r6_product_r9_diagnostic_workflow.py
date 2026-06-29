import json
import subprocess
import sys

from experiments.r6_product_customer_value_report import (
    build_r6_product_customer_value_report,
)
from experiments.r6_product_outcome_review import build_r6_product_outcome_review
from experiments.r6_product_r9_diagnostic_workflow import (
    build_r6_product_r9_diagnostic_workflow,
)
from experiments.r6_product_scenario_intake import build_r6_product_scenario_intake
from experiments.r9_combination_comparison import build_r9_combination_comparison
from experiments.r9_false_alarm_gate_redesign import (
    build_r9_false_alarm_gate_redesign,
)
from experiments.r9_holdout_guard import build_r9_holdout_guard
from experiments.r9_synthetic_mechanism_lab import build_r9_synthetic_mechanism_lab


def test_r6_product_r9_diagnostic_workflow_links_scenario_r9_and_outcome_review():
    scenario = build_r6_product_scenario_intake(
        artifact_id="r6-product-scenario-intake-test",
        run_id="r9-workflow-run",
    )
    comparison = build_r9_combination_comparison(
        artifact_id="r9-combination-comparison-test",
        run_id="r9-workflow-run",
    )
    synthetic_lab = build_r9_synthetic_mechanism_lab(
        artifact_id="r9-synthetic-mechanism-lab-test",
        run_id="r9-workflow-run",
    )
    false_alarm_gate = build_r9_false_alarm_gate_redesign(
        artifact_id="r9-false-alarm-gate-redesign-test",
        run_id="r9-workflow-run",
    )
    holdout_guard = build_r9_holdout_guard(
        artifact_id="r9-holdout-guard-test",
        run_id="r9-workflow-run",
        combination_comparison=comparison,
        synthetic_mechanism_lab=synthetic_lab,
        false_alarm_gate_redesign=false_alarm_gate,
    )
    customer_report = build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-r9-workflow-test",
        run_id="r9-workflow-run",
        r9_combination_comparison=comparison,
        r9_synthetic_mechanism_lab=synthetic_lab,
        r9_false_alarm_gate_redesign=false_alarm_gate,
        r9_holdout_guard=holdout_guard,
    )
    outcome_review = build_r6_product_outcome_review(
        artifact_id="r6-product-outcome-review-test",
        run_id="r9-workflow-run",
    )

    workflow = build_r6_product_r9_diagnostic_workflow(
        artifact_id="r6-product-r9-diagnostic-workflow-test",
        run_id="r9-workflow-run",
        scenario_intake=scenario,
        customer_value_report=customer_report,
        outcome_review=outcome_review,
        r9_combination_comparison=comparison,
        r9_synthetic_mechanism_lab=synthetic_lab,
        r9_false_alarm_gate_redesign=false_alarm_gate,
        r9_holdout_guard=holdout_guard,
    )

    assert workflow["schema_version"] == "r6-product-r9-diagnostic-workflow-v1"
    assert workflow["status"] == "product_r9_diagnostic_workflow_ready_guarded"
    assert workflow["workflow_contract"] == {
        "source_backed_only": True,
        "scenario_to_diagnostic_to_outcome_review": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
        "customer_visible": True,
    }
    assert [stage["stage_id"] for stage in workflow["workflow_stages"]] == [
        "scenario_intake",
        "r9_guarded_diagnostic_report",
        "outcome_review",
    ]
    assert workflow["r9_diagnostic_summary"] == {
        "support_status": "guarded_diagnostic_candidate",
        "best_combination_id": "A+B+C",
        "holdout_guard_status": "r9_holdout_guard_passed_guarded",
        "false_alarm_gate_status": "r9_false_alarm_gate_redesign_ready_guarded",
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert workflow["outcome_review_handoff"]["requires_customer_or_field_outcome"] is True
    assert workflow["outcome_review_handoff"]["runtime_default_allowed"] is False
    assert scenario["artifact_id"] in workflow["source_refs"]
    assert customer_report["artifact_id"] in workflow["source_refs"]
    assert outcome_review["artifact_id"] in workflow["source_refs"]
    assert holdout_guard["artifact_id"] in workflow["source_refs"]
    assert len(workflow["blocked_claims"]) == len(set(workflow["blocked_claims"]))
    assert "R9 validated" in workflow["blocked_claims"]
    json.dumps(workflow, allow_nan=False)


def test_r6_product_r9_diagnostic_workflow_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-product-r9-diagnostic-workflow.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_product_r9_diagnostic_workflow.py",
            "--artifact-id",
            "r6-product-r9-diagnostic-workflow-cli",
            "--run-id",
            "r9-workflow-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r6-product-r9-diagnostic-workflow-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-product-r9-diagnostic-workflow-cli",
        "output": str(output),
        "status": "product_r9_diagnostic_workflow_ready_guarded",
    }
