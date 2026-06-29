import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from experiments.openrouter_textgrad_matrix import (
    build_openrouter_textgrad_plan,
    run_openrouter_textgrad_matrix,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_build_openrouter_textgrad_plan_records_model_axis():
    plan = build_openrouter_textgrad_plan(
        models=("openai/gpt-oss-120b:free", "qwen/qwen3-coder:free"),
        eval_sizes=(2,),
        dataset_seeds=(42,),
        prompt_baselines=("structured",),
    )

    assert len(plan) == 2
    assert {item["model"] for item in plan} == {
        "openai/gpt-oss-120b:free",
        "qwen/qwen3-coder:free",
    }
    assert all(item["base_url"] == "https://openrouter.ai/api/v1" for item in plan)
    assert all(item["mode"] == "local-openrouter" for item in plan)
    assert all("--base-url" in item["command"] for item in plan)
    assert all("OPENROUTER_API_KEY" not in " ".join(item["command"]) for item in plan)
    assert all("structured" in item["command"] for item in plan)


def test_run_openrouter_matrix_requires_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        run_openrouter_textgrad_matrix(
            matrix_id="openrouter-missing-key-test",
            output_dir=str(tmp_path),
            models=("openai/gpt-oss-120b:free",),
        )


def test_run_openrouter_matrix_writes_index_without_leaking_key(
    tmp_path,
    monkeypatch,
):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="{}", stderr="")

    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-key")
    monkeypatch.setattr("experiments.openrouter_textgrad_matrix.subprocess.run", fake_run)

    index = run_openrouter_textgrad_matrix(
        matrix_id="openrouter-smoke-test",
        output_dir=str(tmp_path),
        models=("openai/gpt-oss-120b:free",),
        eval_sizes=(2,),
        dataset_seeds=(42,),
        prompt_baselines=("structured",),
    )

    output = tmp_path / "openrouter-smoke-test.json"
    assert output.exists()
    assert json.loads(output.read_text()) == index
    assert index["schema_version"] == "circe-openrouter-textgrad-matrix-v1"
    assert index["status"] == "completed"
    assert index["run_count"] == 1
    assert index["results"][0]["returncode"] == 0
    assert "secret-key" not in json.dumps(index)
    assert "secret-key" not in " ".join(calls[0][0])
    assert calls[0][1]["cwd"] == REPO_ROOT
    assert calls[0][1]["env"]["PYTHONPATH"].split(os.pathsep)[:2] == ["src", "."]


def test_run_openrouter_matrix_records_partial_rate_limited_runs(
    tmp_path,
    monkeypatch,
):
    responses = iter(
        [
            SimpleNamespace(returncode=0, stdout="completed", stderr=""),
            SimpleNamespace(
                returncode=1,
                stdout="started",
                stderr=(
                    "openai.RateLimitError: Error code: 429 - temporarily "
                    "rate-limited upstream {'user_id': 'user_sensitive'} "
                    "sk-or-v1-sensitive"
                ),
            ),
            SimpleNamespace(returncode=1, stdout="", stderr="plain failure"),
        ]
    )

    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-key")
    monkeypatch.setattr(
        "experiments.openrouter_textgrad_matrix.subprocess.run",
        lambda *args, **kwargs: next(responses),
    )

    index = run_openrouter_textgrad_matrix(
        matrix_id="openrouter-partial-test",
        output_dir=str(tmp_path),
        models=(
            "openai/gpt-oss-120b:free",
            "qwen/qwen3-coder:free",
            "meta-llama/llama-3.3-70b-instruct:free",
        ),
        eval_sizes=(2,),
        dataset_seeds=(42,),
        prompt_baselines=("structured",),
    )

    assert index["status"] == "partial"
    assert index["completed_count"] == 1
    assert index["rate_limited_count"] == 1
    assert index["failed_count"] == 1
    assert [item["status"] for item in index["results"]] == [
        "completed",
        "rate_limited",
        "failed",
    ]
    assert "user_sensitive" not in json.dumps(index)
    assert "sk-or-v1-sensitive" not in json.dumps(index)
    assert "[REDACTED_USER_ID]" in json.dumps(index)
    assert "[REDACTED_OPENROUTER_KEY]" in json.dumps(index)
    assert "secret-key" not in json.dumps(index)


def test_openrouter_matrix_script_writes_plan(tmp_path):
    output = tmp_path / "openrouter-plan.json"
    completed = __import__("subprocess").run(
        [
            sys.executable,
            "experiments/openrouter_textgrad_matrix.py",
            "--plan-only",
            "--output",
            str(output),
            "--model",
            "openai/gpt-oss-120b:free",
        ],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    assert summary == {"output": str(output), "run_count": 1, "status": "planned"}
    payload = json.loads(output.read_text())
    assert payload["schema_version"] == "circe-openrouter-textgrad-matrix-v1"
    assert payload["status"] == "planned"
    assert payload["run_count"] == 1
