from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


VALID_MATRIX_MODES = {"dry-run", "local"}


def build_matrix_commands(mode: str, manifest_dir: str) -> list[dict]:
    if mode not in VALID_MATRIX_MODES:
        raise ValueError(f"mode must be one of {sorted(VALID_MATRIX_MODES)}")

    dry = mode == "dry-run"
    dry_flag = ["--dry-run"] if dry else []
    local_flag = [] if dry else ["--local"]
    suffix = "dry-run" if dry else "local"

    return [
        {
            "run_id": f"w3w4-soft-{suffix}",
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
                f"w3w4-soft-{suffix}",
                "--manifest-dir",
                manifest_dir,
            ],
        },
        {
            "run_id": f"w5w6-async-{suffix}",
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
                f"w5w6-async-{suffix}",
                "--manifest-dir",
                manifest_dir,
            ],
        },
        {
            "run_id": f"w5w6-sync-{suffix}",
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
                f"w5w6-sync-{suffix}",
                "--manifest-dir",
                manifest_dir,
            ],
        },
    ]


def run_matrix(mode: str, manifest_dir: str) -> dict:
    commands = build_matrix_commands(mode=mode, manifest_dir=manifest_dir)
    results = []
    for item in commands:
        completed = subprocess.run(
            item["command"],
            check=False,
            text=True,
            capture_output=True,
        )
        results.append(
            {
                "run_id": item["run_id"],
                "command": item["command"],
                "returncode": completed.returncode,
                "stdout_tail": completed.stdout[-2000:],
                "stderr_tail": completed.stderr[-2000:],
            }
        )

    index = {"mode": mode, "manifest_dir": manifest_dir, "results": results}
    output_path = Path(manifest_dir) / f"matrix-{mode}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2, sort_keys=True))

    if any(result["returncode"] != 0 for result in results):
        raise SystemExit(1)
    return index


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CIRCE evidence matrix")
    parser.add_argument("--mode", choices=sorted(VALID_MATRIX_MODES), default="dry-run")
    parser.add_argument("--manifest-dir", default="experiments/results/manifests")
    args = parser.parse_args()
    print(json.dumps(run_matrix(args.mode, args.manifest_dir), indent=2, sort_keys=True))
