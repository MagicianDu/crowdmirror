import json
import subprocess
import sys

from experiments.r6_theory_framework import build_r6_theory_framework


def test_r6_theory_framework_defines_problem_value_and_guards():
    report = build_r6_theory_framework(
        artifact_id="r6-theory-framework-test",
        run_id="r6-gap-closure-run",
    )

    assert report["schema_version"] == "r6-theory-framework-v1"
    assert report["status"] == "theory_framework_ready"
    assert report["formal_problem"]["static_prior_role"] == "simulation_foundation"
    assert report["formal_problem"]["interaction_role"] == "risk_discovery_layer"
    assert report["risk_discovery_value_function"] == {
        "formula": (
            "recovered_static_prior_miss - false_alarm_penalty "
            "- guard_violation_penalty - overfit_penalty"
        ),
        "optimization_target": "auditable_risk_discovery_not_raw_accuracy_superiority",
    }
    assert report["acceptance_gates"] == {
        "formal_problem_definition_present": True,
        "risk_discovery_value_defined": True,
        "error_attribution_defined": True,
        "runtime_default_allowed": False,
        "field_outcome_validated": False,
    }
    assert "accuracy superiority" in " ".join(report["blocked_claims"])
    assert "field validated" in " ".join(report["blocked_claims"])
    json.dumps(report, allow_nan=False)


def test_r6_theory_framework_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-theory-framework.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_theory_framework.py",
            "--artifact-id",
            "r6-theory-framework-cli",
            "--run-id",
            "r6-gap-closure-run",
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
    assert report["schema_version"] == "r6-theory-framework-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-theory-framework-cli",
        "output": str(output),
        "status": "theory_framework_ready",
    }
