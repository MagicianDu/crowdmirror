import json
import subprocess
import sys

from experiments.r8_product_failure_diagnosis_package import (
    build_r8_product_failure_diagnosis_package,
)


def test_r8_product_failure_diagnosis_package_turns_stop_loss_into_cards():
    package = build_r8_product_failure_diagnosis_package(
        artifact_id="r8-product-failure-diagnosis-package-test",
        run_id="r8-product-failure-run",
    )

    assert package["schema_version"] == "r8-product-failure-diagnosis-package-v1"
    assert package["status"] == "r8_product_failure_diagnosis_package_ready_guarded"
    assert package["product_positioning"] == "人群反应趋势与风险区间模拟器"
    assert package["package_contract"] == {
        "source_backed_only": True,
        "customer_visible": True,
        "diagnostic_only": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert package["executive_summary"]["research_decision"] == (
        "keep_r8_as_diagnostic_asset"
    )
    assert package["failure_cards"]
    card_ids = {card["card_id"] for card in package["failure_cards"]}
    assert "not_beating_fixed_rule_baseline" in card_ids
    assert "field_customer_outcome_missing" in card_ids
    for card in package["failure_cards"]:
        assert card["customer_question"]
        assert card["evidence"]
        assert card["product_response"]
        assert card["source_artifact_ids"]
        assert card["display_level"] == "diagnostic_only"
    assert "R8 validated" in package["blocked_claims"]
    json.dumps(package, allow_nan=False)


def test_r8_product_failure_diagnosis_package_contains_replay_and_evidence_requests():
    package = build_r8_product_failure_diagnosis_package(
        artifact_id="r8-product-failure-diagnosis-package-test",
        run_id="r8-product-failure-run",
    )

    assert package["outcome_replay_workflow"]["workflow_id"] == (
        "r8_failure_diagnosis_outcome_replay"
    )
    assert [step["step_id"] for step in package["outcome_replay_workflow"]["steps"]] == [
        "replay_current_blocked_result",
        "compare_against_baselines",
        "collect_customer_or_field_outcome",
        "rerun_r8_gate",
    ]
    assert package["evidence_requests"] == [
        {
            "request_id": "field_or_customer_outcome",
            "why_needed": "R8 cannot move beyond diagnostic-only without real outcome validation.",
            "minimum_required_fields": [
                "scenario_id",
                "release_date",
                "segment_id",
                "observed_response_metric",
                "measurement_window",
            ],
        },
        {
            "request_id": "segment_outcome_labels",
            "why_needed": "Risk ranking and abnormal segment claims require segment-level outcome support.",
            "minimum_required_fields": [
                "segment_id",
                "risk_label",
                "label_source",
                "label_confidence",
            ],
        },
    ]
    assert package["acceptance_gates"]["field_outcome_validated"] is False
    assert package["acceptance_gates"]["runtime_default_allowed"] is False


def test_r8_product_failure_diagnosis_package_cli_writes_artifact(tmp_path):
    output = tmp_path / "r8-product-failure-diagnosis-package.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r8_product_failure_diagnosis_package.py",
            "--artifact-id",
            "r8-product-failure-diagnosis-package-cli",
            "--run-id",
            "r8-product-failure-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r8-product-failure-diagnosis-package-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r8-product-failure-diagnosis-package-cli",
        "output": str(output),
        "status": "r8_product_failure_diagnosis_package_ready_guarded",
    }
