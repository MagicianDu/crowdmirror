import json

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
