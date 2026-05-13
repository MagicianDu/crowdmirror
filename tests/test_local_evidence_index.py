import json
import subprocess
import sys

from experiments.local_evidence_index import build_local_evidence_index


def _manifest(**overrides):
    payload = {
        "schema_version": "circe-evidence-v1",
        "run_id": "local-gemma-w3w4-canary-001",
        "lane": "causal",
        "mode": "local",
        "status": "completed",
        "metrics": {"improvement_ratio": 0.0, "total_llm_calls": 4},
        "artifacts": {"result_json": "experiments/results/w3w4_local-gemma-w3w4-canary-001.json"},
        "claim_boundary": "local-model calibration evidence; not cross-provider evidence",
    }
    payload.update(overrides)
    return payload


def test_build_local_evidence_index_filters_completed_local_or_live_manifests(tmp_path):
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()
    (manifest_dir / "local.json").write_text(json.dumps(_manifest()))
    (manifest_dir / "dry.json").write_text(json.dumps(_manifest(run_id="dry", mode="dry-run")))
    (manifest_dir / "failed.json").write_text(json.dumps(_manifest(run_id="failed", status="failed")))

    index = build_local_evidence_index(manifest_dir)

    assert index["schema_version"] == "circe-local-evidence-index-v1"
    assert index["manifest_dir"] == str(manifest_dir)
    assert index["completed_evidence_count"] == 1
    assert index["claimable_improvement_count"] == 0
    assert index["entries"][0]["run_id"] == "local-gemma-w3w4-canary-001"
    assert index["entries"][0]["artifact_refs"] == [
        "experiments/results/w3w4_local-gemma-w3w4-canary-001.json"
    ]
    assert "research_manifest_has_no_measured_improvement" in index["entries"][0]["unsupported_warnings"]


def test_local_evidence_index_script_writes_json(tmp_path):
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()
    output = tmp_path / "local-index.json"
    (manifest_dir / "local.json").write_text(json.dumps(_manifest()))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/local_evidence_index.py",
            "--manifest-dir",
            str(manifest_dir),
            "--output",
            str(output),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "completed_evidence_count": 1,
        "output": str(output),
    }
    assert json.loads(output.read_text())["entries"][0]["mode"] == "local"
