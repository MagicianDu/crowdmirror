import json

from experiments.r6_product_readiness_index import build_r6_product_readiness_index


def test_r6_product_readiness_index_prioritizes_product_without_overclaiming():
    report = build_r6_product_readiness_index(
        artifact_id="r6-product-readiness-index-test",
        run_id="r6-product-first-run",
    )

    assert report["schema_version"] == "r6-product-readiness-index-v1"
    assert report["status"] == "product_first_readiness_partial"
    assert report["product_goal"] == {
        "primary": "usable_pre_release_risk_assessment_product",
        "research_role": "theory_and_evidence_boundary_support",
        "not_default_goal": "ccf_a_main_contribution",
    }
    assert report["readiness_gates"]["scenario_intake_ready"] is False
    assert report["readiness_gates"]["evidence_cards_ready"] is True
    assert report["readiness_gates"]["decision_report_ready"] is False
    assert report["readiness_gates"]["static_narrative_fallback_allowed"] is False
    assert report["readiness_gates"]["field_outcome_validated"] is False
    assert report["readiness_gates"]["runtime_default_allowed"] is False
    assert "needs_product_scenario_intake" in report["blocking_gaps"]
    assert "needs_customer_decision_report" in report["blocking_gaps"]
    assert "field validation 已完成" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)
