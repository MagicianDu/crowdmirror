import json
from types import SimpleNamespace

from experiments.evidence_matrix import build_matrix_commands, run_matrix


def test_build_matrix_commands_for_dry_run():
    manifest_dir = "experiments/results/manifests"
    commands = build_matrix_commands(mode="dry-run", manifest_dir=manifest_dir)

    run_ids = [item["run_id"] for item in commands]
    assert run_ids == [
        "w3w4-soft-dry-run",
        "w5w6-async-dry-run",
        "w5w6-sync-dry-run",
    ]
    assert all("--dry-run" in item["command"] for item in commands)
    assert all("--manifest-dir" in item["command"] for item in commands)
    assert all(manifest_dir in item["command"] for item in commands)

    w3w4_command = commands[0]["command"]
    assert "experiments/w3w4_causal_calibration.py" in w3w4_command
    assert "--max-iter" in w3w4_command
    assert "--eval-size" in w3w4_command
    assert "--run-id" in w3w4_command
    assert "w3w4-soft-dry-run" in w3w4_command

    async_command = commands[1]["command"]
    sync_command = commands[2]["command"]
    assert "experiments/w5w6_emergence_calibration.py" in async_command
    assert "experiments/w5w6_emergence_calibration.py" in sync_command
    assert "asynchronous" in async_command
    assert "synchronous" in sync_command


def test_run_matrix_writes_child_return_codes(tmp_path, monkeypatch):
    manifest_dir = tmp_path / "manifests"

    def fake_run(command, check, text, capture_output):
        assert check is False
        assert text is True
        assert capture_output is True
        return SimpleNamespace(
            returncode=0,
            stdout=f"ran {' '.join(command)}",
            stderr="",
        )

    monkeypatch.setattr("experiments.evidence_matrix.subprocess.run", fake_run)

    index = run_matrix(mode="dry-run", manifest_dir=str(manifest_dir))

    output_path = manifest_dir / "matrix-dry-run.json"
    assert output_path.exists()
    payload = json.loads(output_path.read_text())
    assert index == payload
    assert [item["returncode"] for item in payload["results"]] == [0, 0, 0]
    assert [item["run_id"] for item in payload["results"]] == [
        "w3w4-soft-dry-run",
        "w5w6-async-dry-run",
        "w5w6-sync-dry-run",
    ]
