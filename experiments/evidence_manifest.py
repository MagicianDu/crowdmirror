from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


VALID_LANES = {"causal", "emergence", "trust-chain", "matrix"}
VALID_MODES = {"dry-run", "local", "live"}


def _claim_boundary(mode: str) -> str:
    if mode == "dry-run":
        return "dry-run plumbing evidence only"
    if mode == "local":
        return "local-model calibration evidence; not cross-provider evidence"
    return "live-model calibration evidence; not cross-domain generalization"


def build_run_manifest(
    *,
    run_id: str,
    lane: str,
    mode: str,
    command: list[str],
    config: dict[str, Any],
    metrics: dict[str, Any],
    artifacts: dict[str, str],
    notes: list[str],
    status: str = "completed",
    started_at: str | None = None,
    completed_at: str | None = None,
) -> dict[str, Any]:
    if not run_id:
        raise ValueError("run_id must be non-empty")
    if lane not in VALID_LANES:
        raise ValueError(f"lane must be one of {sorted(VALID_LANES)}")
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {sorted(VALID_MODES)}")
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": "circe-evidence-v1",
        "run_id": run_id,
        "lane": lane,
        "mode": mode,
        "status": status,
        "started_at": started_at or now,
        "completed_at": completed_at or now,
        "command": command,
        "config": config,
        "metrics": metrics,
        "artifacts": artifacts,
        "notes": notes,
        "claim_boundary": _claim_boundary(mode),
    }


def write_manifest(path: str | Path, manifest: dict[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return output_path
