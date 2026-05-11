import os
import subprocess
import sys
from pathlib import Path

from experiments.w3w4_causal_calibration import build_causal_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_build_causal_manifest_records_loss_metrics():
    manifest = build_causal_manifest(
        run_id="causal-test",
        mode="dry-run",
        command=["python", "experiments/w3w4_causal_calibration.py", "--dry-run"],
        config={"max_iterations": 3, "eval_size": 5},
        result_summary={
            "initial_loss": 0.30,
            "best_loss": 0.20,
            "final_loss": 0.22,
            "n_iterations": 3,
            "total_llm_calls": 63,
        },
        result_path="experiments/results/w3w4_calibration_result.json",
    )
    assert manifest["lane"] == "causal"
    assert manifest["metrics"]["improvement_ratio"] == (0.30 - 0.20) / 0.30
    assert (
        manifest["artifacts"]["result_json"]
        == "experiments/results/w3w4_calibration_result.json"
    )


def test_w3w4_script_help_runs_from_repo_root():
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "experiments/w3w4_causal_calibration.py", "--help"],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "--run-id" in result.stdout
