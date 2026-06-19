import json
import subprocess
import sys
from pathlib import Path

from experiments.r6_evidence_report import build_r6_evidence_report
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
    assert report["readiness_gates"]["scenario_intake_ready"] is True
    assert report["readiness_gates"]["story_package_ready"] is True
    assert report["readiness_gates"]["evidence_cards_ready"] is True
    assert report["readiness_gates"]["decision_report_ready"] is True
    assert report["readiness_gates"]["outcome_review_ready"] is True
    assert report["readiness_gates"]["product_api_manifest_ready"] is True
    assert report["readiness_gates"]["trend_interval_risk_metrics_ready"] is True
    assert report["readiness_gates"]["research_product_value_support_ready"] is True
    assert report["readiness_gates"]["customer_value_report_ready"] is True
    assert report["readiness_gates"]["static_narrative_fallback_allowed"] is False
    assert report["readiness_gates"]["field_outcome_validated"] is False
    assert report["readiness_gates"]["runtime_default_allowed"] is False
    assert report["contract_readiness"] == {
        "scenario_intake_contract_ready": True,
        "story_package_contract_ready": True,
        "decision_report_contract_ready": True,
        "customer_value_report_contract_ready": True,
        "outcome_review_contract_ready": True,
        "product_api_manifest_contract_ready": True,
        "contract_ready_is_not_field_validation": True,
    }
    assert "needs_product_scenario_intake" not in report["blocking_gaps"]
    assert "needs_customer_decision_report" not in report["blocking_gaps"]
    assert "needs_outcome_review_contract" not in report["blocking_gaps"]
    assert "needs_product_ui_or_api_contract" not in report["blocking_gaps"]
    assert "needs_customer_facing_ui_integration" in report["blocking_gaps"]
    assert "needs_field_outcome_validation" in report["blocking_gaps"]
    assert "needs_runtime_default_holdout_review" in report["blocking_gaps"]
    assert "精准预测系统" in report["blocked_claims"]
    assert "field validation 已完成" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r6_product_readiness_index_fails_closed_when_product_guard_is_not_preserved():
    evidence_report = _valid_evidence_report()
    evidence_report["acceptance_gates"]["product_guard_preserved"] = False

    assert _evidence_cards_ready(evidence_report) is False


def test_r6_product_readiness_index_fails_closed_when_static_fallback_is_allowed():
    evidence_report = _valid_evidence_report()
    evidence_report["product_evidence_cards_summary"][
        "static_narrative_fallback_allowed"
    ] = True

    assert _evidence_cards_ready(evidence_report) is False


def test_r6_product_readiness_index_fails_closed_when_card_count_is_too_low():
    evidence_report = _valid_evidence_report()
    evidence_report["product_evidence_cards_summary"]["card_count"] = 7

    assert _evidence_cards_ready(evidence_report) is False


def test_r6_product_readiness_index_fails_closed_when_evidence_summary_is_missing():
    evidence_report = _valid_evidence_report()
    del evidence_report["product_evidence_cards_summary"]

    assert _evidence_cards_ready(evidence_report) is False


def test_r6_product_readiness_index_cli_writes_parseable_artifact(tmp_path):
    output = tmp_path / "r6-product-readiness-index.json"
    script = (
        Path(__file__).resolve().parents[1]
        / "experiments"
        / "r6_product_readiness_index.py"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--artifact-id",
            "r6-product-readiness-index-cli-test",
            "--run-id",
            "r6-product-readiness-index-cli-run",
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_payload = json.loads(result.stdout)
    artifact = json.loads(output.read_text())
    assert stdout_payload["artifact_id"] == "r6-product-readiness-index-cli-test"
    assert stdout_payload["status"] == "product_first_readiness_partial"
    assert stdout_payload["output"] == str(output)
    assert artifact["status"] == "product_first_readiness_partial"
    assert artifact["artifact_id"] == "r6-product-readiness-index-cli-test"


def _valid_evidence_report():
    return build_r6_evidence_report(
        artifact_id="r6-product-readiness-index-test-evidence-report",
        run_id="r6-product-first-run",
    )


def _evidence_cards_ready(evidence_report):
    report = build_r6_product_readiness_index(
        artifact_id="r6-product-readiness-index-test",
        run_id="r6-product-first-run",
        evidence_report=evidence_report,
    )
    return report["readiness_gates"]["evidence_cards_ready"]
