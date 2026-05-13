import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import experiments.w3w4_causal_calibration as causal
import experiments.w5w6_emergence_calibration as emergence
from experiments.w3w4_causal_calibration import build_causal_manifest
from experiments.w5w6_emergence_calibration import build_emergence_manifest
from circe.dgp.counterfactual import CounterfactualPair


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
            "textgrad_call_count": 2,
            "prompt_update_count": 2,
        },
        result_path="experiments/results/w3w4_calibration_result.json",
    )
    assert manifest["lane"] == "causal"
    assert manifest["metrics"]["improvement_ratio"] == (0.30 - 0.20) / 0.30
    assert (
        manifest["artifacts"]["result_json"]
        == "experiments/results/w3w4_calibration_result.json"
    )


def test_build_causal_manifest_records_textgrad_evidence_artifact():
    manifest = build_causal_manifest(
        run_id="causal-textgrad-test",
        mode="local",
        command=["python", "experiments/w3w4_causal_calibration.py", "--local"],
        config={"max_iterations": 3, "eval_size": 5},
        result_summary={
            "initial_loss": 0.30,
            "best_loss": 0.20,
            "final_loss": 0.22,
            "n_iterations": 3,
            "total_llm_calls": 63,
            "textgrad_call_count": 2,
            "prompt_update_count": 1,
        },
        result_path="experiments/results/w3w4_calibration_result.json",
        textgrad_steps_path="experiments/results/w3w4_calibration_textgrad_steps.json",
    )

    assert manifest["metrics"]["textgrad_call_count"] == 2
    assert manifest["metrics"]["prompt_update_count"] == 1
    assert (
        manifest["artifacts"]["textgrad_steps_json"]
        == "experiments/results/w3w4_calibration_textgrad_steps.json"
    )
    assert any("TextGrad" in note for note in manifest["notes"])


def test_build_causal_manifest_records_textgrad_effect_status():
    manifest = build_causal_manifest(
        run_id="textgrad-effect-status",
        mode="local",
        command=["python", "experiments/w3w4_causal_calibration.py", "--local"],
        config={"max_iterations": 2, "eval_size": 1},
        result_summary={
            "initial_loss": 0.036,
            "best_loss": 0.036,
            "final_loss": 0.036,
            "n_iterations": 2,
            "total_llm_calls": 6,
            "textgrad_call_count": 2,
            "prompt_update_count": 2,
            "textgrad_effect_status": "updated_no_improvement",
        },
        result_path="experiments/results/w3w4_local.json",
        textgrad_steps_path="experiments/results/w3w4_local_textgrad_steps.json",
    )

    assert manifest["metrics"]["textgrad_effect_status"] == "updated_no_improvement"


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
                "textgrad_call_count": 2,
                "prompt_update_count": 1,
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


def test_non_dry_run_writes_textgrad_steps_artifact(tmp_path, monkeypatch):
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
        run_id="textgrad/local run 01",
        manifest_dir=str(manifest_dir),
    )

    result_path = tmp_path / "experiments/results/w3w4_textgrad%2Flocal%20run%2001.json"
    steps_path = (
        tmp_path
        / "experiments/results/w3w4_textgrad%2Flocal%20run%2001_textgrad_steps.json"
    )
    manifest = _read_json(manifest_dir / "textgrad%2Flocal%20run%2001.json")
    result_summary = _read_json(result_path)
    steps = _read_json(steps_path)

    assert result_summary["textgrad_call_count"] == 2
    assert result_summary["prompt_update_count"] == 1
    assert steps == [
        {
            "iteration": 0,
            "loss_before": 0.30,
            "feedback": "Need more cost sensitivity",
            "edited_prompt": "choose with more cost sensitivity",
            "edited_prompt_changed": True,
        },
        {
            "iteration": 1,
            "loss_before": 0.22,
            "feedback": "No further prompt change needed",
            "edited_prompt": "choose with more cost sensitivity",
            "edited_prompt_changed": False,
        },
    ]
    assert manifest["metrics"]["textgrad_call_count"] == 2
    assert manifest["metrics"]["prompt_update_count"] == 1
    assert manifest["artifacts"]["textgrad_steps_json"] == str(
        Path("experiments/results/w3w4_textgrad%2Flocal%20run%2001_textgrad_steps.json")
    )


def test_non_dry_run_manifest_records_local_generation_limits(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(causal, "generate_counterfactual_dataset", _fake_pairs)
    monkeypatch.setattr(causal, "CalibrationLoop", _FakeCalibrationLoop)

    manifest_dir = tmp_path / "manifests"
    causal.run_experiment(
        max_iterations=2,
        dry_run=False,
        local=True,
        base_url="http://127.0.0.1:1234/v1",
        model="local-model",
        eval_size=3,
        run_id="limited-local",
        manifest_dir=str(manifest_dir),
        simulator_max_tokens=128,
        textgrad_max_tokens=512,
        request_timeout=45.0,
    )

    manifest = _read_json(manifest_dir / "limited-local.json")
    assert manifest["config"]["simulator_max_tokens"] == 128
    assert manifest["config"]["textgrad_max_tokens"] == 512
    assert manifest["config"]["request_timeout"] == 45.0
    assert "--sim-max-tokens" in manifest["command"]
    assert "--textgrad-max-tokens" in manifest["command"]
    assert "--request-timeout" in manifest["command"]


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
            "textgrad_call_count": 2,
            "prompt_update_count": 2,
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


def test_dry_run_summary_includes_textgrad_audit_fields(monkeypatch):
    pairs = _fake_counterfactual_pairs()
    config = causal.CalibrationConfig(max_iterations=2, eval_sample_size=2, patience=5)

    summary = causal._run_dry(config, pairs[:400], pairs[400:])

    assert summary["textgrad_call_count"] == 2
    assert summary["prompt_update_count"] >= 1
    assert summary["textgrad_steps"]
    assert summary["textgrad_steps"][0]["feedback"] == (
        "The prompt needs more cost sensitivity."
    )


def test_build_emergence_manifest_records_edm_metrics():
    manifest = build_emergence_manifest(
        run_id="emergence-test",
        mode="dry-run",
        command=["python", "experiments/w5w6_emergence_calibration.py", "--dry-run"],
        config={"n_agents": 5, "n_steps": 3, "update_mode": "asynchronous"},
        result_summary={
            "initial_edm": 0.12,
            "best_edm": 0.08,
            "final_edm": 0.09,
            "n_iterations": 2,
        },
        result_path="experiments/results/w5w6_emergence_result.json",
    )
    assert manifest["lane"] == "emergence"
    assert manifest["metrics"]["improvement_ratio"] == (0.12 - 0.08) / 0.12
    assert manifest["config"]["update_mode"] == "asynchronous"


def test_build_emergence_manifest_rejects_missing_required_metrics():
    with pytest.raises(ValueError, match="result_summary missing required metrics"):
        build_emergence_manifest(
            run_id="emergence-test",
            mode="dry-run",
            command=["python", "experiments/w5w6_emergence_calibration.py", "--dry-run"],
            config={"n_agents": 5, "n_steps": 3, "update_mode": "asynchronous"},
            result_summary={
                "initial_edm": 0.12,
                "best_edm": 0.08,
                "n_iterations": 2,
            },
            result_path="experiments/results/w5w6_emergence_test.json",
        )


def test_emergence_non_dry_run_writes_unique_result_artifact_and_truthful_command(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(emergence, "EmergenceCalibrationLoop", _FakeEmergenceLoop)

    manifest_dir = tmp_path / "manifests"
    emergence.run_experiment(
        n_agents=6,
        n_steps=4,
        max_iterations=3,
        dry_run=False,
        local=True,
        bad_init=True,
        update_mode="synchronous",
        run_id="matrix/local run 02",
        manifest_dir=str(manifest_dir),
    )

    result_path = tmp_path / "experiments/results/w5w6_matrix%2Flocal%20run%2002.json"
    manifest_path = manifest_dir / "matrix%2Flocal%20run%2002.json"
    assert result_path.exists()
    manifest = _read_json(manifest_path)
    assert manifest["artifacts"]["result_json"] == str(
        Path("experiments/results/w5w6_matrix%2Flocal%20run%2002.json")
    )
    assert manifest["config"]["update_mode"] == "synchronous"
    assert manifest["command"] == [
        "python",
        "experiments/w5w6_emergence_calibration.py",
        "--agents",
        "6",
        "--steps",
        "4",
        "--max-iter",
        "3",
        "--local",
        "--bad-init",
        "--run-id",
        "matrix/local run 02",
        "--manifest-dir",
        str(manifest_dir),
        "--update-mode",
        "synchronous",
    ]


def test_emergence_dry_run_writes_result_artifact_and_truthful_command(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        emergence,
        "_run_dry",
        lambda n_agents, n_steps, max_iterations, update_mode: {
            "initial_edm": 0.12,
            "best_edm": 0.08,
            "final_edm": 0.09,
            "n_iterations": 2,
        },
    )

    manifest_dir = tmp_path / "manifests"
    emergence.run_experiment(
        n_agents=5,
        n_steps=3,
        max_iterations=2,
        dry_run=True,
        local=False,
        bad_init=False,
        update_mode="asynchronous",
        run_id="w5w6-plan-check",
        manifest_dir=str(manifest_dir),
    )

    result_path = tmp_path / "experiments/results/w5w6_w5w6-plan-check.json"
    assert result_path.exists()
    assert _read_json(result_path)["best_edm"] == 0.08
    manifest = _read_json(manifest_dir / "w5w6-plan-check.json")
    assert manifest["artifacts"]["result_json"] == str(
        Path("experiments/results/w5w6_w5w6-plan-check.json")
    )
    assert manifest["command"] == [
        "python",
        "experiments/w5w6_emergence_calibration.py",
        "--agents",
        "5",
        "--steps",
        "3",
        "--max-iter",
        "2",
        "--dry-run",
        "--run-id",
        "w5w6-plan-check",
        "--manifest-dir",
        str(manifest_dir),
        "--update-mode",
        "asynchronous",
    ]


def test_emergence_default_run_ids_are_unique_within_same_second(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(emergence.time, "time", lambda: 1_700_000_000)
    monkeypatch.setattr(
        emergence,
        "_run_dry",
        lambda n_agents, n_steps, max_iterations, update_mode: {
            "initial_edm": 0.12,
            "best_edm": 0.08,
            "final_edm": 0.09,
            "n_iterations": 2,
            "mock_llm_call_count": 11,
            "effective_config": {
                "n_agents": min(n_agents, 5),
                "n_steps": min(n_steps, 3),
                "max_iterations": min(max_iterations, 2),
                "update_mode": update_mode,
            },
            "history": [{"iteration": 0, "edm_score": 0.12, "d_macro": 0.05}],
        },
    )

    manifest_dir = tmp_path / "manifests"
    for _ in range(2):
        emergence.run_experiment(
            n_agents=5,
            n_steps=3,
            max_iterations=2,
            dry_run=True,
            local=False,
            bad_init=False,
            update_mode="asynchronous",
            run_id=None,
            manifest_dir=str(manifest_dir),
        )

    manifests = sorted(manifest_dir.glob("*.json"))
    assert len(manifests) == 2
    run_ids = [_read_json(path)["run_id"] for path in manifests]
    assert len(set(run_ids)) == 2


def test_emergence_manifest_command_includes_generated_run_id_when_omitted(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        emergence,
        "_run_dry",
        lambda n_agents, n_steps, max_iterations, update_mode: {
            "initial_edm": 0.12,
            "best_edm": 0.08,
            "final_edm": 0.09,
            "n_iterations": 2,
            "mock_llm_call_count": 11,
            "effective_config": {
                "n_agents": 5,
                "n_steps": 3,
                "max_iterations": 2,
                "update_mode": update_mode,
            },
            "history": [{"iteration": 0, "edm_score": 0.12, "d_macro": 0.05}],
        },
    )

    manifest_dir = tmp_path / "manifests"
    emergence.run_experiment(
        n_agents=5,
        n_steps=3,
        max_iterations=2,
        dry_run=True,
        local=False,
        bad_init=False,
        update_mode="asynchronous",
        run_id=None,
        manifest_dir=str(manifest_dir),
        command=[
            "python",
            "experiments/w5w6_emergence_calibration.py",
            "--dry-run",
        ],
    )

    manifest = _read_json(next(manifest_dir.glob("*.json")))
    assert "--run-id" in manifest["command"]
    run_id_index = manifest["command"].index("--run-id")
    assert manifest["command"][run_id_index + 1] == manifest["run_id"]


def test_emergence_result_summary_rejects_non_finite_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError):
        emergence._write_result_summary(
            "bad-json",
            {
                "initial_edm": float("nan"),
                "best_edm": 0.08,
                "final_edm": 0.09,
                "n_iterations": 2,
            },
        )

    assert not (tmp_path / "experiments/results/w5w6_bad-json.json").exists()


def test_emergence_dry_run_summary_includes_audit_fields():
    summary = emergence._run_dry(
        n_agents=9,
        n_steps=7,
        max_iterations=4,
        update_mode="synchronous",
    )

    assert summary["mock_llm_call_count"] > 0
    assert summary["effective_config"] == {
        "n_agents": 5,
        "n_steps": 3,
        "max_iterations": 2,
        "update_mode": "synchronous",
    }
    assert summary["requested_config"] == {
        "n_agents": 9,
        "n_steps": 7,
        "max_iterations": 4,
        "update_mode": "synchronous",
    }
    assert summary["history"]
    assert summary["audit"] == {
        "mode": "dry-run",
        "mocked_llm": True,
        "cap_reason": "dry-run caps agent, step, and iteration counts for fast plumbing verification",
    }


def test_w5w6_script_help_runs_from_repo_root():
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "experiments/w5w6_emergence_calibration.py", "--help"],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "--run-id" in result.stdout
    assert "--update-mode" in result.stdout


def _fake_pairs(**kwargs):
    return [SimpleNamespace(ate=i / 1000) for i in range(500)]


def _fake_counterfactual_pairs():
    return [
        CounterfactualPair(
            scenario_id=f"s{i}",
            factual_attrs={
                "sm_cost": 0.6,
                "sm_tt": 0.8,
                "train_tt": 1.0,
                "train_cost": 0.5,
                "train_he": 10,
                "sm_he": 5,
                "car_tt": 1.2,
                "car_cost": 0.3,
            },
            counterfactual_attrs={
                "sm_cost": 1.2,
                "sm_tt": 0.8,
                "train_tt": 1.0,
                "train_cost": 0.5,
                "train_he": 10,
                "sm_he": 5,
                "car_tt": 1.2,
                "car_cost": 0.3,
            },
            intervention={"sm_cost_increase": 2.0},
            factual_probs={"train": 0.3, "swissmetro": 0.5, "car": 0.2},
            counterfactual_probs={"train": 0.4, "swissmetro": 0.35, "car": 0.25},
            ate=-0.1,
        )
        for i in range(20)
    ]


class _FakeCalibrationLoop:
    def __init__(self, config, dataset):
        self.config = config
        self.dataset = dataset

    def run(self):
        from circe.calibration.textgrad import GradientStep

        return SimpleNamespace(
            best_prompt="choose with calibrated cost sensitivity",
            best_loss=0.20,
            initial_loss=0.30,
            final_loss=0.22,
            n_iterations=4,
            total_llm_calls=84,
            simulator_llm_call_count=82,
            textgrad_call_count=2,
            textgrad_input_tokens=900,
            textgrad_output_tokens=300,
            history=[
                SimpleNamespace(
                    iteration=0,
                    loss=SimpleNamespace(total_loss=0.30, ece=0.10, ate_mae=0.20),
                    prompt="choose with default sensitivity",
                    gradient_step=GradientStep(
                        iteration=0,
                        feedback="Need more cost sensitivity",
                        edited_prompt="choose with more cost sensitivity",
                        loss_before=0.30,
                    ),
                ),
                SimpleNamespace(
                    iteration=1,
                    loss=SimpleNamespace(total_loss=0.22, ece=0.08, ate_mae=0.14),
                    prompt="choose with more cost sensitivity",
                    gradient_step=GradientStep(
                        iteration=1,
                        feedback="No further prompt change needed",
                        edited_prompt="choose with more cost sensitivity",
                        loss_before=0.22,
                    ),
                ),
                SimpleNamespace(
                    iteration=2,
                    loss=SimpleNamespace(total_loss=0.20, ece=0.07, ate_mae=0.13),
                    prompt="choose with more cost sensitivity",
                    gradient_step=None,
                ),
            ],
        )


class _FakeEmergenceLoop:
    def __init__(self, config):
        self.config = config

    def run(self):
        return SimpleNamespace(
            best_prompt="follow calibrated neighbor pressure",
            best_edm=0.08,
            initial_edm=0.12,
            final_edm=0.09,
            n_iterations=3,
            history=[
                {"iteration": 0, "edm_score": 0.12, "d_macro": 0.05},
                {"iteration": 2, "edm_score": 0.08, "d_macro": 0.03},
            ],
        )


def _read_json(path):
    import json

    return json.loads(Path(path).read_text())
