import json

from experiments.r6_product_claim_evidence_registry import (
    build_r6_product_claim_evidence_registry,
    build_r6_research_product_value_support_v2,
)
from experiments.r6_product_customer_value_report import (
    build_r6_product_customer_value_report,
)
from experiments.r6_product_readiness_index import build_r6_product_readiness_index


def test_full_product_support_v2_flows_into_customer_report_with_guarded_claims():
    value_support = build_r6_research_product_value_support_v2(
        artifact_id="r6-research-product-value-support-v2-integration",
        run_id="r6-full-product-support-run",
    )
    report = build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-v2-integration",
        run_id="r6-full-product-support-run",
        value_support=value_support,
    )

    assert report["status"] == "customer_value_report_ready_guarded"
    assert report["report_contract"]["source_backed_only"] is True
    assert report["report_contract"]["static_narrative_fallback_allowed"] is False
    assert report["report_contract"]["precise_point_prediction_allowed"] is False
    assert report["report_contract"]["field_outcome_validated"] is False
    assert report["report_contract"]["runtime_default_allowed"] is False
    assert report["display_payload"]["risk_distribution"]["support_status"] == (
        "supported_current_proxy_guarded"
    )
    assert report["display_payload"]["abnormal_segments"][0]["support_status"] == (
        "guarded_proxy_supported"
    )
    assert report["display_payload"]["research_support"]["support_coverage"][
        "supported_value_count"
    ] >= 1
    json.dumps(report, allow_nan=False)


def test_full_product_support_registry_and_readiness_remain_fail_closed():
    registry = build_r6_product_claim_evidence_registry(
        artifact_id="r6-product-claim-evidence-registry-integration",
        run_id="r6-full-product-support-run",
    )
    readiness = build_r6_product_readiness_index(
        artifact_id="r6-product-readiness-index-integration",
        run_id="r6-full-product-support-run",
    )

    assert registry["acceptance_gates"]["all_product_visible_claims_source_backed"] is True
    assert registry["acceptance_gates"]["no_source_claim_rejected"] is True
    assert registry["acceptance_gates"]["runtime_default_allowed"] is False
    assert readiness["readiness_gates"]["customer_value_report_ready"] is True
    assert readiness["readiness_gates"]["field_outcome_validated"] is False
    assert readiness["readiness_gates"]["runtime_default_allowed"] is False
    assert "精准预测系统" in readiness["blocked_claims"]
    json.dumps(registry, allow_nan=False)
    json.dumps(readiness, allow_nan=False)
