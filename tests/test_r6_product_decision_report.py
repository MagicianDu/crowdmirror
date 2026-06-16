import json

from experiments.r6_product_decision_report import build_r6_product_decision_report


def test_r6_product_decision_report_exports_customer_readable_guarded_report():
    report = build_r6_product_decision_report(
        artifact_id="r6-product-decision-report-test",
        run_id="r6-product-first-run",
    )

    assert report["schema_version"] == "r6-product-decision-report-v1"
    assert report["status"] == "decision_report_ready_guarded"
    assert report["customer_sections"] == [
        "what_changed",
        "who_is_at_risk",
        "why_risk_moved",
        "what_is_supported_by_evidence",
        "what_is_blocked",
        "what_to_measure_next",
    ]
    assert report["report_contract"]["source_backed_only"] is True
    assert report["report_contract"]["static_narrative_fallback_allowed"] is False
    assert "field validation 已完成" in report["blocked_claims"]
    assert "runtime default 可以开启" in report["blocked_claims"]
    assert report["next_measurement_plan"]
    json.dumps(report, allow_nan=False)
