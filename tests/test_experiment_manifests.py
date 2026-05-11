import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import experiments.w3w4_causal_calibration as causal
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


def test_build_causal_manifest_rejects_missing_required_metrics():
    with pytest.raises(ValueError, match="result_summary missing required metrics"):
        build_causal_manifest(
            run_id="causal-test",
            mode="dry-run",
            command=["python", "experiments/w3w4_causal_calibration.py", "--dry-run"],
            config={"max_iterations": 3, "eval_size": 5},
            result_summary={
                "initial_loss": 0.30,
                "best_loss": 0.20,
                "n_iterations": 3,
                "total_llm_calls": 63,
            },
            result_path="experiments/results/w3w4_causal_test.json",
        )


def test_non_dry_run_writes_unique_result_artifact_and_truthful_command(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(causal, "generate_counterfactual_dataset", _fake_pairs)
    monkeypatch.setattr(causal, "CalibrationLoop", _FakeCalibrationLoop)

    manifest_dir = tmp_path / "manifests"
    causal.run_experiment(
        max_iterations=4,
        dry_run=False,
        local=True,
        base_url="http://127.0.0.1:1234/v1",
        model="local-model",
        eval_size=7,
        run_id="matrix/local run 01",
        manifest_dir=str(manifest_dir),
    )

    result_path = tmp_path / "experiments/results/w3w4_matrix%2Flocal%20run%2001.json"
    manifest_path = manifest_dir / "matrix%2Flocal%20run%2001.json"
    assert result_path.exists()
    manifest = _read_json(manifest_path)
    assert manifest["artifacts"]["result_json"] == str(
        Path("experiments/results/w3w4_matrix%2Flocal%20run%2001.json")
    )
    assert manifest["command"] == [
        "python",
        "experiments/w3w4_causal_calibration.py",
        "--max-iter",
        "4",
        "--eval-size",
        "7",
        "--local",
        "--base-url",
        "http://127.0.0.1:1234/v1",
        "--model",
        "local-model",
        "--run-id",
        "matrix/local run 01",
        "--manifest-dir",
        str(manifest_dir),
    ]


def test_dry_run_writes_result_artifact_and_truthful_command(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(causal, "generate_counterfactual_dataset", _fake_pairs)
    monkeypatch.setattr(
        causal,
        "_run_dry",
        lambda config, train_pairs, test_pairs: {
            "initial_loss": 0.30,
            "best_loss": 0.20,
            "final_loss": 0.22,
            "n_iterations": 3,
            "total_llm_calls": 63,
        },
    )

    manifest_dir = tmp_path / "manifests"
    causal.run_experiment(
        max_iterations=3,
        dry_run=True,
        local=False,
        base_url="http://localhost:1234/v1",
        model="google/gemma-4-31b",
        eval_size=5,
        run_id="w3w4-plan-check",
        manifest_dir=str(manifest_dir),
    )

    result_path = tmp_path / "experiments/results/w3w4_w3w4-plan-check.json"
    assert result_path.exists()
    assert _read_json(result_path)["best_loss"] == 0.20
    manifest = _read_json(manifest_dir / "w3w4-plan-check.json")
    assert manifest["artifacts"]["result_json"] == str(
        Path("experiments/results/w3w4_w3w4-plan-check.json")
    )
    assert manifest["command"] == [
        "python",
        "experiments/w3w4_causal_calibration.py",
        "--max-iter",
        "3",
        "--eval-size",
        "5",
        "--dry-run",
        "--base-url",
        "http://localhost:1234/v1",
        "--model",
        "google/gemma-4-31b",
        "--run-id",
        "w3w4-plan-check",
        "--manifest-dir",
        str(manifest_dir),
    ]


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


def _fake_pairs(**kwargs):
    return [SimpleNamespace(ate=i / 1000) for i in range(500)]


class _FakeCalibrationLoop:
    def __init__(self, config, dataset):
        self.config = config
        self.dataset = dataset

    def run(self):
        return SimpleNamespace(
            best_prompt="choose with calibrated cost sensitivity",
            best_loss=0.20,
            initial_loss=0.30,
            final_loss=0.22,
            n_iterations=4,
            total_llm_calls=84,
            history=[
                SimpleNamespace(
                    iteration=1,
                    loss=SimpleNamespace(total_loss=0.30, ece=0.10, ate_mae=0.20),
                ),
                SimpleNamespace(
                    iteration=4,
                    loss=SimpleNamespace(total_loss=0.20, ece=0.07, ate_mae=0.13),
                ),
            ],
        )


def _read_json(path):
    import json

    return json.loads(Path(path).read_text())
