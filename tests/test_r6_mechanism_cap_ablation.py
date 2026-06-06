import json
import subprocess
import sys

from experiments.r6_mechanism_cap_ablation import build_r6_mechanism_cap_ablation


def test_r6_mechanism_cap_ablation_fixes_anes_without_breaking_htops():
    report = build_r6_mechanism_cap_ablation(
        artifact_id="r6-mechanism-cap-ablation-test",
        run_id="r6-mechanism-cap-ablation-run",
    )

    assert report["schema_version"] == "r6-mechanism-cap-ablation-v1"
    assert report["status"] == "diagnostic_cap_candidate_ready"
    assert report["cap_rule"] == {
        "condition_static_prior_abs_error_lte": 0.03,
        "max_aggregate_reject_delta": 0.02,
        "scope": "rights_or_rule_change_rejection_amplification",
    }
    assert report["summary"] == {
        "public_proxy_count": 2,
        "cap_applied_count": 1,
        "failure_fixed_count": 1,
        "positive_signal_preserved_count": 1,
        "global_update_status": "blocked_until_follow_up_holdout",
    }

    by_case = {case["target_case_id"]: case for case in report["case_results"]}
    anes = by_case["generic-rights-rule-change"]
    assert anes["source_proxy_key"] == "anes_health_heldout"
    assert anes["cap_applied"] is True
    assert anes["original_prior_anchored_error"] == 0.05
    assert anes["capped_prior_anchored_error"] == 0.0
    assert anes["failure_fixed"] is True
    assert anes["capped_prediction"] == 0.33
    assert anes["capped_reject_delta"] == 0.02

    htops = by_case["generic-public-service-policy-change"]
    assert htops["source_proxy_key"] == "htops_cost_pressure"
    assert htops["cap_applied"] is False
    assert htops["positive_signal_preserved"] is True
    assert htops["original_prior_anchored_error"] == 0.11
    assert htops["capped_prior_anchored_error"] == 0.11

    assert report["recommended_update"] == {
        "status": "diagnostic_only",
        "default_runtime_enabled": False,
        "target_change": "cap rights/rule rejection amplification only when static prior is already close",
        "acceptance_requirement": "requires follow-up or cross-proxy holdout without HTOPS regression",
    }
    assert "same_case_cap_not_global_update" in report["risk_flags"]
    json.dumps(report, allow_nan=False)


def test_r6_mechanism_cap_ablation_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-mechanism-cap-ablation.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_mechanism_cap_ablation.py",
            "--artifact-id",
            "r6-mechanism-cap-ablation-cli",
            "--run-id",
            "r6-mechanism-cap-ablation-run",
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
    assert report["schema_version"] == "r6-mechanism-cap-ablation-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-mechanism-cap-ablation-cli",
        "failure_fixed_count": 1,
        "output": str(output),
        "status": "diagnostic_cap_candidate_ready",
    }
