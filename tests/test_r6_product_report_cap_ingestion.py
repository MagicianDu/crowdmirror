import json
import subprocess
import sys

from experiments.r6_mechanism_cap_ablation import build_r6_mechanism_cap_ablation
from experiments.r6_product_report import build_r6_product_report


def test_r6_product_report_ingests_mechanism_cap_as_diagnostic_chain():
    cap = build_r6_mechanism_cap_ablation(
        artifact_id="r6-mechanism-cap-ablation-product-test",
        run_id="r6-product-cap-ingestion-run",
    )
    report = build_r6_product_report(
        artifact_id="r6-product-report-cap-test",
        run_id="r6-product-cap-ingestion-run",
        mechanism_cap_ablation=cap,
    )

    assert report["schema_version"] == "r6-product-report-v1"
    assert report["mechanism_cap_review"] == {
        "source_artifact_id": "r6-mechanism-cap-ablation-product-test",
        "claim_status": "diagnostic_candidate_not_runtime_default",
        "global_update_status": "blocked_until_follow_up_holdout",
        "default_runtime_enabled": False,
        "cap_rule": {
            "condition_static_prior_abs_error_lte": 0.03,
            "max_aggregate_reject_delta": 0.02,
            "scope": "rights_or_rule_change_rejection_amplification",
        },
        "summary": {
            "public_proxy_count": 2,
            "cap_applied_count": 1,
            "failure_fixed_count": 1,
            "positive_signal_preserved_count": 1,
        },
        "case_reviews": [
            {
                "target_case_id": "generic-public-service-policy-change",
                "source_proxy_key": "htops_cost_pressure",
                "cap_applied": False,
                "original_prior_anchored_error": 0.11,
                "capped_prior_anchored_error": 0.11,
                "failure_fixed": False,
                "positive_signal_preserved": True,
            },
            {
                "target_case_id": "generic-rights-rule-change",
                "source_proxy_key": "anes_health_heldout",
                "cap_applied": True,
                "original_prior_anchored_error": 0.05,
                "capped_prior_anchored_error": 0.0,
                "failure_fixed": True,
                "positive_signal_preserved": False,
            },
        ],
    }
    assert report["product_evidence_chain"] == [
        {
            "stage": "pre_release_risk_shift",
            "status": "risk_hypothesis_ready",
            "claim_status": "not_accuracy_claim",
        },
        {
            "stage": "public_proxy_failure_boundary",
            "status": "mixed_evidence_diagnosed",
            "claim_status": "public_proxy_not_field_validation",
        },
        {
            "stage": "mechanism_cap_candidate",
            "status": "blocked_until_follow_up_holdout",
            "claim_status": "diagnostic_candidate_not_runtime_default",
        },
    ]
    assert "mechanism_cap_not_runtime_default" in report["risk_flags"]
    assert "validate_mechanism_cap_on_follow_up_or_holdout_case" in report["next_actions"]
    assert "r6-mechanism-cap-ablation-product-test" in report["source_refs"]
    json.dumps(report, allow_nan=False)


def test_r6_product_report_cli_can_include_mechanism_cap_ablation(tmp_path):
    output = tmp_path / "r6-product-report-cap.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_product_report.py",
            "--artifact-id",
            "r6-product-report-cap-cli",
            "--run-id",
            "r6-product-cap-ingestion-run",
            "--include-mechanism-cap-ablation",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    report = json.loads(output.read_text())
    assert report["mechanism_cap_review"]["source_artifact_id"] == (
        "r6-product-report-cap-cli-mechanism-cap-ablation"
    )
    assert report["mechanism_cap_review"]["default_runtime_enabled"] is False
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-product-report-cap-cli",
        "case_count": 3,
        "mechanism_cap_status": "diagnostic_candidate_not_runtime_default",
        "output": str(output),
        "status": "report_ready",
    }
