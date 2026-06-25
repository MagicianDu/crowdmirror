import json
from pathlib import Path

from experiments.r6_product_api_manifest import build_r6_product_api_manifest
from experiments.r6_product_customer_value_report import (
    build_r6_product_customer_value_report,
)


def test_r12_product_support_gate_flows_into_customer_report_as_secondary_evidence():
    gate = _load_current_r12_product_support_gate()
    report = build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-r12-integration",
        run_id="r12-product-integration-test",
        r12_product_support_gate=gate,
    )

    assert "r12_transfer_evidence" in report["customer_sections"]
    payload = report["display_payload"]["r12_transfer_evidence"]
    assert payload == {
        "support_status": "guarded_transfer_positive_secondary_evidence",
        "gate_status": "r12_product_support_gate_ready_guarded",
        "claim_level": "product_secondary_evidence_only",
        "metrics": {
            "update_transfer_gain": 0.001287,
            "validation_mean_absolute_error_delta": -0.000431,
            "holdout_mean_absolute_error_delta": -0.000856,
            "interval_coverage_delta": 0.0,
            "false_alarm_rate_delta": 0.0,
        },
        "evidence_summary": gate["transfer_evidence_card"]["evidence_summary"],
        "primary_decision_source": "guarded_baseline_customer_value_report",
        "r12_output_role": "secondary_transfer_evidence_card_only",
        "r12_can_override_primary_decision": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
        "outcome_review_handoff": gate["outcome_review_handoff"],
        "blocked_claims": gate["blocked_claims"],
        "source_artifact_ids": [gate["artifact_id"]],
    }
    r12_contract = next(
        item
        for item in report["section_contracts"]
        if item["section_id"] == "r12_transfer_evidence"
    )
    assert r12_contract == {
        "section_id": "r12_transfer_evidence",
        "claim_status": "secondary_evidence_only",
        "source_artifact_ids": [gate["artifact_id"]],
        "blocked_claims": gate["blocked_claims"],
    }
    registry_ids = {entry["artifact_id"] for entry in report["source_registry"]}
    assert gate["artifact_id"] in registry_ids
    assert "r12-transfer-validation-current-001" in registry_ids
    assert gate["artifact_id"] in report["source_refs"]
    assert "R12 supports Product core method by default" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_product_support_gate_is_exposed_by_product_api_manifest():
    manifest = build_r6_product_api_manifest(
        artifact_id="r6-product-api-manifest-r12-integration",
        run_id="r12-product-integration-test",
    )

    assert manifest["artifact_refs"]["r12_product_support_gate"] == (
        "r12-product-support-gate-current-001"
    )
    endpoint = next(
        item
        for item in manifest["endpoints"]
        if item["endpoint_id"] == "r12_transfer_evidence"
    )
    assert endpoint == {
        "endpoint_id": "r12_transfer_evidence",
        "method": "GET",
        "path": "/r6/product/r12-transfer-evidence",
        "source_artifact_ids": ["r12-product-support-gate-current-001"],
        "response_contract": "source_artifact_json",
    }
    assert "r12_transfer_evidence" in manifest["display_contract"][
        "required_sections"
    ]
    assert "r12-product-support-gate-current-001" in manifest["source_refs"]
    assert manifest["api_contract"]["runtime_default_allowed"] is False
    assert manifest["api_contract"]["field_outcome_validated"] is False
    json.dumps(manifest, allow_nan=False)


def _load_current_r12_product_support_gate():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_product_support_gate/"
            "r12-product-support-gate-current-001.json"
        ).read_text()
    )
