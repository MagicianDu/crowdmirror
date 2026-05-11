from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


VALID_LANES = {"causal", "emergence", "trust-chain", "matrix"}
VALID_MODES = {"dry-run", "local", "live"}
VALID_STATUSES = {"completed", "failed", "running"}
JSON_PAYLOAD_FIELDS = ("config", "metrics", "artifacts", "notes")


def _claim_boundary(mode: str) -> str:
    if mode == "dry-run":
        return "dry-run plumbing evidence only"
    if mode == "local":
        return "local-model calibration evidence; not cross-provider evidence"
    return "live-model calibration evidence; not cross-domain generalization"


def _parse_timestamp(field: str, value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"{field} must be a valid ISO 8601 timezone-aware datetime string"
        )
    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            f"{field} must be a valid ISO 8601 timezone-aware datetime string"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(
            f"{field} must be a valid ISO 8601 timezone-aware datetime string"
        )
    return parsed.astimezone(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _resolve_timestamps(
    started_at: str | None,
    completed_at: str | None,
) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    if started_at is None and completed_at is None:
        started = now
        completed = now
    elif started_at is None:
        completed = _parse_timestamp("completed_at", completed_at)
        started = completed
    elif completed_at is None:
        started = _parse_timestamp("started_at", started_at)
        completed = now if now >= started else started
    else:
        started = _parse_timestamp("started_at", started_at)
        completed = _parse_timestamp("completed_at", completed_at)

    if completed < started:
        raise ValueError("completed_at must be greater than or equal to started_at")
    return _format_timestamp(started), _format_timestamp(completed)


def _ensure_json_serializable(field: str, value: Any) -> None:
    try:
        json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{field} must be JSON serializable") from exc


def _validate_payload_fields(manifest: dict[str, Any]) -> None:
    for field in JSON_PAYLOAD_FIELDS:
        if field in manifest:
            _ensure_json_serializable(field, manifest[field])


def _manifest_json(manifest: dict[str, Any]) -> str:
    _validate_payload_fields(manifest)
    try:
        return json.dumps(manifest, indent=2, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise TypeError("manifest must be JSON serializable") from exc


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
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
    resolved_started_at, resolved_completed_at = _resolve_timestamps(
        started_at,
        completed_at,
    )
    manifest = {
        "schema_version": "circe-evidence-v1",
        "run_id": run_id,
        "lane": lane,
        "mode": mode,
        "status": status,
        "started_at": resolved_started_at,
        "completed_at": resolved_completed_at,
        "command": command,
        "config": config,
        "metrics": metrics,
        "artifacts": artifacts,
        "notes": notes,
        "claim_boundary": _claim_boundary(mode),
    }
    _manifest_json(manifest)
    return manifest


def write_manifest(path: str | Path, manifest: dict[str, Any]) -> Path:
    output_path = Path(path)
    manifest_json = _manifest_json(manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(manifest_json)
    return output_path
