import json
import subprocess
import sys

from experiments.r6_failure_boundary_report import build_r6_failure_boundary_report
from experiments.r6_proxy_mapping_review import build_r6_proxy_mapping_review


def test_r6_proxy_mapping_review_documents_two_public_proxy_mappings():
    review = build_r6_proxy_mapping_review(
        artifact_id="r6-proxy-mapping-review-test",
        run_id="r6-proxy-mapping-review-run",
    )

    assert review["schema_version"] == "r6-proxy-mapping-review-v1"
    assert review["status"] == "mapping_review_ready"
    assert review["public_proxy_count"] == 2
    assert review["source_count"] == 2
    assert review["overall_mapping_status"] == "proxy_usable_with_boundary"
    assert review["claim_boundary"] == (
        "R6 proxy mapping review only; proxy labels are not direct field outcomes "
        "or direct attitude truth."
    )

    mappings = {mapping["source_key"]: mapping for mapping in review["mappings"]}
    assert mappings["htops_cost_pressure"]["target_response_option"] == "baseline_no_new_support"
    assert mappings["htops_cost_pressure"]["mapped_case_id"] == (
        "generic-public-service-policy-change"
    )
    assert mappings["htops_cost_pressure"]["mapping_direction"] == "reject_proxy"
    assert "not_direct_attitude_truth" in mappings["htops_cost_pressure"]["invalid_claims"]

    assert mappings["anes_health_heldout"]["target_response_option"] == "private_insurance_plan"
    assert mappings["anes_health_heldout"]["mapped_case_id"] == "generic-rights-rule-change"
    assert mappings["anes_health_heldout"]["split_role"] == "heldout"
    assert mappings["anes_health_heldout"]["mapping_direction"] == "reject_proxy"

    assert review["required_report_wording"] == [
        "Use public proxy as bounded outcome signal, not as field validation.",
        "Report mapping rationale before using proxy error as model evidence.",
        "Do not accept global updates from same-case proxy feedback.",
    ]
    json.dumps(review, allow_nan=False)


def test_r6_failure_boundary_report_diagnoses_anes_interaction_regression():
    report = build_r6_failure_boundary_report(
        artifact_id="r6-failure-boundary-report-test",
        run_id="r6-failure-boundary-report-run",
    )

    assert report["schema_version"] == "r6-failure-boundary-report-v1"
    assert report["status"] == "failure_boundary_ready"
    assert report["target_case_id"] == "generic-rights-rule-change"
    assert report["source_proxy_key"] == "anes_health_heldout"
    assert report["failure_boundary"]["failure_type"] == (
        "interaction_over_amplifies_rejection_risk"
    )
    assert report["failure_boundary"]["no_interaction_error"] == 0.02
    assert report["failure_boundary"]["prior_anchored_error"] == 0.05
    assert report["failure_boundary"]["regression_delta"] == 0.03
    assert report["failure_boundary"]["observed_reject_proxy"] == 0.33
    assert report["failure_boundary"]["prior_anchored_prediction"] == 0.38

    assert report["diagnosis"]["primary_hypothesis"] == (
        "rights/rule interaction profile imported too much rejection amplification "
        "for ANES health heldout segments where the static prior is already close."
    )
    assert report["diagnosis"]["suspect_mechanisms"] == [
        "rights_loss_salience",
        "peer_amplification",
        "trust_shock",
    ]
    assert report["recommended_update"]["status"] == "diagnostic_only"
    assert report["recommended_update"]["default_runtime_enabled"] is False
    assert report["recommended_update"]["target_change"] == (
        "shrink rights/rule rejection amplification when static prior error is already low"
    )
    assert "same_case_proxy_not_global_update" in report["risk_flags"]
    json.dumps(report, allow_nan=False)


def test_r6_failure_boundary_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-failure-boundary.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_failure_boundary_report.py",
            "--artifact-id",
            "r6-failure-boundary-cli",
            "--run-id",
            "r6-failure-boundary-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_text().endswith("\n")
    report = json.loads(output.read_text())
    assert report["schema_version"] == "r6-failure-boundary-report-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-failure-boundary-cli",
        "failure_type": "interaction_over_amplifies_rejection_risk",
        "output": str(output),
        "status": "failure_boundary_ready",
    }
