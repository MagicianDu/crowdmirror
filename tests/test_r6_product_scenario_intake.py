import json
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.r6_product_scenario_intake import build_r6_product_scenario_intake


def test_r6_product_scenario_intake_accepts_airline_fee_case_without_vertical_overfit():
    report = build_r6_product_scenario_intake(
        artifact_id="r6-product-scenario-intake-test",
        run_id="r6-product-first-run",
        scenario={
            "scenario_id": "airline-fuel-fee-001",
            "change_type": "price",
            "target_population": "existing_route_customers",
            "impact_dimensions": ["price_sensitivity", "fairness_concern", "churn_risk"],
            "communication_plan": "announce_fee_with_service_reason",
            "alternative_scenarios": ["no_fee", "smaller_fee", "loyalty_credit"],
            "decision_question": "Will the fee create unacceptable churn risk?",
            "assumptions": ["route has alternatives", "customers observe total price"],
        },
    )

    assert report["schema_version"] == "r6-product-scenario-intake-v1"
    assert report["status"] == "scenario_intake_ready"
    assert report["scenario"]["scenario_id"] == "airline-fuel-fee-001"
    assert report["scenario"]["domain_binding"] == "case_input_not_method_definition"
    assert report["scenario"]["method_family"] == "price_or_rule_change_reaction"
    assert report["product_contract"]["can_drive_product_story_package"] is True
    assert report["product_contract"]["vertical_overfit_allowed"] is False
    assert "case_specific_input_not_research_method" in report["risk_flags"]
    json.dumps(report, allow_nan=False)


def test_r6_product_scenario_intake_rejects_missing_decision_question():
    with pytest.raises(ValueError, match="decision_question"):
        build_r6_product_scenario_intake(
            artifact_id="r6-product-scenario-intake-test",
            run_id="r6-product-first-run",
            scenario={
                "scenario_id": "bad-scenario",
                "change_type": "price",
                "target_population": "customers",
                "impact_dimensions": ["price_sensitivity"],
                "communication_plan": "announce",
                "alternative_scenarios": ["no_change"],
                "assumptions": ["customers see the total price before purchase"],
            },
        )


def test_r6_product_scenario_intake_rejects_empty_scenario_object():
    with pytest.raises(ValueError, match="scenario.scenario_id"):
        build_r6_product_scenario_intake(
            artifact_id="r6-product-scenario-intake-test",
            run_id="r6-product-first-run",
            scenario={},
        )


def test_r6_product_scenario_intake_rejects_non_object_scenario():
    with pytest.raises(ValueError, match="scenario must be an object"):
        build_r6_product_scenario_intake(
            artifact_id="r6-product-scenario-intake-test",
            run_id="r6-product-first-run",
            scenario=[],
        )


def test_r6_product_scenario_intake_rejects_empty_impact_dimensions():
    scenario = _valid_scenario()
    scenario["impact_dimensions"] = []

    with pytest.raises(ValueError, match="scenario.impact_dimensions"):
        build_r6_product_scenario_intake(
            artifact_id="r6-product-scenario-intake-test",
            run_id="r6-product-first-run",
            scenario=scenario,
        )


def test_r6_product_scenario_intake_rejects_blank_impact_dimension_item():
    scenario = _valid_scenario()
    scenario["impact_dimensions"] = ["price_sensitivity", " "]

    with pytest.raises(ValueError, match=r"scenario\.impact_dimensions\[1\]"):
        build_r6_product_scenario_intake(
            artifact_id="r6-product-scenario-intake-test",
            run_id="r6-product-first-run",
            scenario=scenario,
        )


@pytest.mark.parametrize(
    ("artifact_id", "run_id", "error_field"),
    [
        (" ", "r6-product-first-run", "artifact_id"),
        ("r6-product-scenario-intake-test", " ", "run_id"),
    ],
)
def test_r6_product_scenario_intake_rejects_blank_required_ids(
    artifact_id,
    run_id,
    error_field,
):
    with pytest.raises(ValueError, match=error_field):
        build_r6_product_scenario_intake(
            artifact_id=artifact_id,
            run_id=run_id,
            scenario=_valid_scenario(),
        )


def test_r6_product_scenario_intake_cli_writes_artifact_and_stdout_json(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    output = tmp_path / "scenario-intake.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_product_scenario_intake.py",
            "--artifact-id",
            "r6-product-scenario-intake-cli-test",
            "--run-id",
            "r6-product-cli-run",
            "--output",
            str(output),
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout = json.loads(completed.stdout)
    artifact = json.loads(output.read_text())
    assert stdout == {
        "artifact_id": "r6-product-scenario-intake-cli-test",
        "output": str(output),
        "status": "scenario_intake_ready",
    }
    assert artifact["artifact_id"] == "r6-product-scenario-intake-cli-test"
    assert artifact["run_id"] == "r6-product-cli-run"
    assert artifact["scenario"]["domain_binding"] == "case_input_not_method_definition"
    json.dumps(artifact, allow_nan=False)


def _valid_scenario():
    return {
        "scenario_id": "valid-scenario",
        "change_type": "price",
        "target_population": "customers",
        "impact_dimensions": ["price_sensitivity"],
        "communication_plan": "announce",
        "alternative_scenarios": ["no_change"],
        "decision_question": "Will this change create unacceptable customer risk?",
        "assumptions": ["customers see the total price before purchase"],
    }
