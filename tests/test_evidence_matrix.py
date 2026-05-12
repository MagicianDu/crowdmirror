import json
import os
from pathlib import Path
import subprocess as stdlib_subprocess
import sys
from types import SimpleNamespace

import pytest

from experiments.evidence_matrix import build_matrix_commands, run_matrix


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_build_matrix_commands_for_dry_run_child_ids_include_matrix_run_id():
    manifest_dir = "experiments/results/manifests"
    commands = build_matrix_commands(
        mode="dry-run",
        manifest_dir=manifest_dir,
        matrix_run_id="matrix-dry-run-abc123",
    )

    run_ids = [item["run_id"] for item in commands]
    assert run_ids == [
        "matrix-dry-run-abc123--w3w4-soft-dry-run",
        "matrix-dry-run-abc123--w5w6-async-dry-run",
        "matrix-dry-run-abc123--w5w6-sync-dry-run",
    ]
    assert all("--dry-run" in item["command"] for item in commands)
    assert all("--manifest-dir" in item["command"] for item in commands)
    assert all(manifest_dir in item["command"] for item in commands)

    w3w4_command = commands[0]["command"]
    assert "experiments/w3w4_causal_calibration.py" in w3w4_command
    assert "--max-iter" in w3w4_command
    assert "--eval-size" in w3w4_command
    assert "--run-id" in w3w4_command
    assert "matrix-dry-run-abc123--w3w4-soft-dry-run" in w3w4_command

    async_command = commands[1]["command"]
    sync_command = commands[2]["command"]
    assert "experiments/w5w6_emergence_calibration.py" in async_command
    assert "experiments/w5w6_emergence_calibration.py" in sync_command
    assert "asynchronous" in async_command
    assert "synchronous" in sync_command


def test_child_run_ids_are_unique_per_matrix_run_id():
    first = build_matrix_commands(
        mode="dry-run",
        manifest_dir="manifests",
        matrix_run_id="matrix-first",
    )
    second = build_matrix_commands(
        mode="dry-run",
        manifest_dir="manifests",
        matrix_run_id="matrix-second",
    )

    first_ids = {item["run_id"] for item in first}
    second_ids = {item["run_id"] for item in second}
    assert all(run_id.startswith("matrix-first--") for run_id in first_ids)
    assert all(run_id.startswith("matrix-second--") for run_id in second_ids)
    assert first_ids.isdisjoint(second_ids)


def test_run_matrix_writes_child_return_codes(tmp_path, monkeypatch):
    manifest_dir = tmp_path / "manifests"

    def fake_run(command, **kwargs):
        assert kwargs["check"] is False
        assert kwargs["text"] is True
        assert kwargs["capture_output"] is True
        assert kwargs["cwd"] == REPO_ROOT
        assert kwargs["env"]["PYTHONPATH"].split(os.pathsep)[:2] == ["src", "."]
        return SimpleNamespace(
            returncode=0,
            stdout=f"ran {' '.join(command)}",
            stderr="",
        )

    monkeypatch.setattr("experiments.evidence_matrix.subprocess.run", fake_run)

    index = run_matrix(
        mode="dry-run",
        manifest_dir=str(manifest_dir),
        matrix_run_id="matrix-dry-run-test",
    )

    unique_path = manifest_dir / "matrix-dry-run-matrix-dry-run-test.json"
    alias_path = manifest_dir / "matrix-dry-run.json"
    assert unique_path.exists()
    assert alias_path.exists()
    payload = json.loads(unique_path.read_text())
    assert json.loads(alias_path.read_text()) == payload
    assert index == payload
    assert payload["schema_version"] == "circe-evidence-v1"
    assert payload["run_id"] == "matrix-dry-run-test"
    assert payload["matrix_run_id"] == "matrix-dry-run-test"
    assert payload["lane"] == "matrix"
    assert payload["status"] == "completed"
    assert payload["started_at"]
    assert payload["completed_at"]
    assert payload["claim_boundary"] == "dry-run plumbing evidence only"
    assert [item["returncode"] for item in payload["results"]] == [0, 0, 0]
    assert [item["run_id"] for item in payload["results"]] == [
        "matrix-dry-run-test--w3w4-soft-dry-run",
        "matrix-dry-run-test--w5w6-async-dry-run",
        "matrix-dry-run-test--w5w6-sync-dry-run",
    ]


def test_run_matrix_generates_unique_matrix_run_ids_and_outputs(tmp_path, monkeypatch):
    manifest_dir = tmp_path / "manifests"

    def fake_run(command, **kwargs):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("experiments.evidence_matrix.subprocess.run", fake_run)

    first = run_matrix(mode="dry-run", manifest_dir=str(manifest_dir))
    second = run_matrix(mode="dry-run", manifest_dir=str(manifest_dir))

    assert first["matrix_run_id"] != second["matrix_run_id"]
    assert first["artifacts"]["matrix_index_json"] != second["artifacts"]["matrix_index_json"]
    assert Path(first["artifacts"]["matrix_index_json"]).exists()
    assert Path(second["artifacts"]["matrix_index_json"]).exists()


def test_run_matrix_passes_repo_cwd_and_pythonpath_env(tmp_path, monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setenv("PYTHONPATH", "existing")
    monkeypatch.setattr("experiments.evidence_matrix.subprocess.run", fake_run)

    run_matrix(
        mode="dry-run",
        manifest_dir=str(tmp_path / "manifests"),
        matrix_run_id="matrix-env-test",
    )

    assert len(calls) == 3
    for command, kwargs in calls:
        assert Path(kwargs["cwd"]) == REPO_ROOT
        assert command[1].startswith("experiments/")
        pythonpath = kwargs["env"]["PYTHONPATH"].split(os.pathsep)
        assert pythonpath[:2] == ["src", "."]
        assert "existing" in pythonpath


def test_run_matrix_rejects_non_finite_index_values(tmp_path, monkeypatch):
    def fake_run(command, **kwargs):
        return SimpleNamespace(returncode=float("nan"), stdout="", stderr="")

    monkeypatch.setattr("experiments.evidence_matrix.subprocess.run", fake_run)

    with pytest.raises(TypeError, match="JSON serializable"):
        run_matrix(
            mode="dry-run",
            manifest_dir=str(tmp_path / "manifests"),
            matrix_run_id="matrix-non-finite",
        )


def test_evidence_matrix_script_help_runs_from_repo_root():
    completed = stdlib_subprocess.run(
        [sys.executable, "experiments/evidence_matrix.py", "--help"],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "--matrix-run-id" in completed.stdout
