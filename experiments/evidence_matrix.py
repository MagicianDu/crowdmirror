from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import quote
import uuid

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.evidence_manifest import build_run_manifest, write_manifest


VALID_MATRIX_MODES = {"dry-run", "local"}


def build_matrix_commands(
    mode: str,
    manifest_dir: str,
    matrix_run_id: str | None = None,
) -> list[dict]:
    if mode not in VALID_MATRIX_MODES:
        raise ValueError(f"mode must be one of {sorted(VALID_MATRIX_MODES)}")

    resolved_matrix_run_id = matrix_run_id or generate_matrix_run_id(mode)
    dry = mode == "dry-run"
    dry_flag = ["--dry-run"] if dry else []
    local_flag = [] if dry else ["--local"]
    suffix = "dry-run" if dry else "local"
    child_run_ids = {
        "w3w4": f"{resolved_matrix_run_id}--w3w4-soft-{suffix}",
        "w5w6_async": f"{resolved_matrix_run_id}--w5w6-async-{suffix}",
        "w5w6_sync": f"{resolved_matrix_run_id}--w5w6-sync-{suffix}",
    }

    return [
        {
            "run_id": child_run_ids["w3w4"],
            "command": [
                sys.executable,
                "experiments/w3w4_causal_calibration.py",
                *dry_flag,
                *local_flag,
                "--max-iter",
                "3",
                "--eval-size",
                "5",
                "--run-id",
                child_run_ids["w3w4"],
                "--manifest-dir",
                manifest_dir,
            ],
        },
        {
            "run_id": child_run_ids["w5w6_async"],
            "command": [
                sys.executable,
                "experiments/w5w6_emergence_calibration.py",
                *dry_flag,
                *local_flag,
                "--agents",
                "5",
                "--steps",
                "3",
                "--max-iter",
                "2",
                "--update-mode",
                "asynchronous",
                "--run-id",
                child_run_ids["w5w6_async"],
                "--manifest-dir",
                manifest_dir,
            ],
        },
        {
            "run_id": child_run_ids["w5w6_sync"],
            "command": [
                sys.executable,
                "experiments/w5w6_emergence_calibration.py",
                *dry_flag,
                *local_flag,
                "--agents",
                "5",
                "--steps",
                "3",
                "--max-iter",
                "2",
                "--update-mode",
                "synchronous",
                "--run-id",
                child_run_ids["w5w6_sync"],
                "--manifest-dir",
                manifest_dir,
            ],
        },
    ]


def run_matrix(
    mode: str,
    manifest_dir: str,
    matrix_run_id: str | None = None,
) -> dict:
    resolved_matrix_run_id = matrix_run_id or generate_matrix_run_id(mode)
    commands = build_matrix_commands(
        mode=mode,
        manifest_dir=manifest_dir,
        matrix_run_id=resolved_matrix_run_id,
    )
    child_env = _child_process_env()
    results = []
    started_at = datetime.now(timezone.utc).isoformat()
    for item in commands:
        completed = subprocess.run(
            item["command"],
            check=False,
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            env=child_env,
        )
        results.append(
            {
                "run_id": item["run_id"],
                "command": item["command"],
                "returncode": completed.returncode,
                "stdout_tail": (completed.stdout or "")[-2000:],
                "stderr_tail": (completed.stderr or "")[-2000:],
            }
        )

    completed_at = datetime.now(timezone.utc).isoformat()
    failed_results = [result for result in results if result["returncode"] != 0]
    status = "failed" if failed_results else "completed"
    unique_output_path = _matrix_output_path(
        manifest_dir=manifest_dir,
        mode=mode,
        matrix_run_id=resolved_matrix_run_id,
    )
    latest_alias_path = Path(manifest_dir) / f"matrix-{mode}.json"
    index = _build_matrix_index(
        mode=mode,
        manifest_dir=manifest_dir,
        matrix_run_id=resolved_matrix_run_id,
        commands=commands,
        results=results,
        status=status,
        unique_output_path=unique_output_path,
        latest_alias_path=latest_alias_path,
        started_at=started_at,
        completed_at=completed_at,
    )
    write_manifest(unique_output_path, index)
    write_manifest(latest_alias_path, index)

    if failed_results:
        raise SystemExit(1)
    return index


def generate_matrix_run_id(mode: str) -> str:
    if mode not in VALID_MATRIX_MODES:
        raise ValueError(f"mode must be one of {sorted(VALID_MATRIX_MODES)}")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"matrix-{mode}-{timestamp}-{uuid.uuid4().hex[:8]}"


def _child_process_env() -> dict[str, str]:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    pythonpath_parts = ["src", "."]
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    return env


def _build_matrix_index(
    *,
    mode: str,
    manifest_dir: str,
    matrix_run_id: str,
    commands: list[dict],
    results: list[dict],
    status: str,
    unique_output_path: Path,
    latest_alias_path: Path,
    started_at: str,
    completed_at: str,
) -> dict:
    failed_child_count = sum(1 for result in results if result["returncode"] != 0)
    index = build_run_manifest(
        run_id=matrix_run_id,
        lane="matrix",
        mode=mode,
        command=_matrix_command(mode, manifest_dir, matrix_run_id),
        config={
            "matrix_run_id": matrix_run_id,
            "manifest_dir": manifest_dir,
            "child_run_ids": [item["run_id"] for item in commands],
        },
        metrics={
            "child_count": len(results),
            "failed_child_count": failed_child_count,
        },
        artifacts={
            "matrix_index_json": str(unique_output_path),
            "matrix_latest_alias_json": str(latest_alias_path),
        },
        notes=[
            "Matrix index records child command return codes and output tails.",
            "Latest alias is convenience-only; matrix_index_json is the unique evidence artifact.",
        ],
        status=status,
        started_at=started_at,
        completed_at=completed_at,
    )
    index["matrix_run_id"] = matrix_run_id
    index["manifest_dir"] = manifest_dir
    index["results"] = results
    return index


def _matrix_command(mode: str, manifest_dir: str, matrix_run_id: str) -> list[str]:
    return [
        sys.executable,
        "experiments/evidence_matrix.py",
        "--mode",
        mode,
        "--manifest-dir",
        manifest_dir,
        "--matrix-run-id",
        matrix_run_id,
    ]


def _matrix_output_path(
    *,
    manifest_dir: str,
    mode: str,
    matrix_run_id: str,
) -> Path:
    safe_matrix_run_id = quote(matrix_run_id, safe="._-")
    return Path(manifest_dir) / f"matrix-{mode}-{safe_matrix_run_id}.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CIRCE evidence matrix")
    parser.add_argument("--mode", choices=sorted(VALID_MATRIX_MODES), default="dry-run")
    parser.add_argument("--manifest-dir", default="experiments/results/manifests")
    parser.add_argument("--matrix-run-id", default=None)
    args = parser.parse_args()
    print(
        json.dumps(
            run_matrix(args.mode, args.manifest_dir, matrix_run_id=args.matrix_run_id),
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
    )
