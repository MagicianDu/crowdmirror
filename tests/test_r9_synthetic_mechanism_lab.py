import json
import subprocess
import sys

from experiments.r9_synthetic_mechanism_lab import build_r9_synthetic_mechanism_lab


def test_r9_synthetic_mechanism_lab_recovers_known_mechanisms_guarded():
    lab = build_r9_synthetic_mechanism_lab(
        artifact_id="r9-synthetic-mechanism-lab-test",
        run_id="r9-task4-run",
    )

    assert lab["schema_version"] == "r9-synthetic-mechanism-lab-v1"
    assert lab["status"] == "r9_synthetic_mechanism_lab_passed_guarded"
    assert lab["candidate_combination_id"] == "A+B+C"
    assert lab["lab_contract"] == {
        "synthetic_only": True,
        "known_mechanism_truth_available": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert lab["summary"] == {
        "trial_count": 4,
        "mechanism_direction_recovery_rate": 1.0,
        "propagation_trace_consistency": 0.75,
        "abnormal_segment_recall": 1.0,
        "synthetic_mechanism_recovery_passed": True,
    }
    assert len(lab["trials"]) == 4
    assert all(trial["known_mechanism_truth"] for trial in lab["trials"])
    assert all(trial["recovered_mechanism_direction"] is True for trial in lab["trials"])
    assert "field validation completed" in lab["blocked_claims"]
    json.dumps(lab, allow_nan=False)


def test_r9_synthetic_mechanism_lab_cli_writes_artifact(tmp_path):
    output = tmp_path / "r9-synthetic-mechanism-lab.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r9_synthetic_mechanism_lab.py",
            "--artifact-id",
            "r9-synthetic-mechanism-lab-cli",
            "--run-id",
            "r9-task4-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r9-synthetic-mechanism-lab-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r9-synthetic-mechanism-lab-cli",
        "output": str(output),
        "status": "r9_synthetic_mechanism_lab_passed_guarded",
    }
