from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


INDEX_SCHEMA_VERSION = "circe-local-evidence-index-v1"
SUPPORTED_MANIFEST_SCHEMA = "circe-evidence-v1"


def build_local_evidence_index(manifest_dir: str | Path) -> dict[str, Any]:
    manifest_path = Path(manifest_dir)
    entries = [
        entry for entry in (
            _entry_from_manifest(path)
            for path in sorted(manifest_path.glob("*.json"))
        )
        if entry is not None
    ]
    index = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "manifest_dir": str(manifest_path),
        "completed_evidence_count": len(entries),
        "claimable_improvement_count": sum(
            1 for entry in entries
            if "research_manifest_has_no_measured_improvement"
            not in entry["unsupported_warnings"]
        ),
        "entries": entries,
    }
    _assert_strict_json(index)
    return index


def write_local_evidence_index(
    manifest_dir: str | Path,
    output: str | Path,
) -> dict[str, Any]:
    index = build_local_evidence_index(manifest_dir)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return index


def _entry_from_manifest(path: Path) -> dict[str, Any] | None:
    try:
        manifest = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    if not isinstance(manifest, dict):
        return None
    if manifest.get("schema_version") != SUPPORTED_MANIFEST_SCHEMA:
        return None
    if manifest.get("mode") not in {"local", "live"}:
        return None
    if manifest.get("status") != "completed":
        return None

    metrics = manifest.get("metrics", {})
    artifacts = manifest.get("artifacts", {})
    entry = {
        "manifest_path": str(path),
        "run_id": manifest["run_id"],
        "lane": manifest["lane"],
        "mode": manifest["mode"],
        "status": manifest["status"],
        "claim_boundary": manifest["claim_boundary"],
        "metrics": metrics,
        "artifact_refs": [
            value for value in artifacts.values()
            if isinstance(value, str) and value
        ],
        "unsupported_warnings": _unsupported_warnings(metrics),
    }
    _assert_strict_json(entry)
    return entry


def _unsupported_warnings(metrics: dict[str, Any]) -> list[str]:
    warnings = [
        "research_manifest_scope_not_product_scenario",
    ]
    improvement = metrics.get("improvement_ratio")
    if isinstance(improvement, (int, float)) and float(improvement) <= 0.0:
        warnings.append("research_manifest_has_no_measured_improvement")
    return warnings


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build CIRCE local evidence index")
    parser.add_argument("--manifest-dir", default="experiments/results/manifests")
    parser.add_argument("--output", default="experiments/results/local-evidence-index.json")
    args = parser.parse_args()
    index = write_local_evidence_index(args.manifest_dir, args.output)
    print(json.dumps({
        "output": args.output,
        "completed_evidence_count": index["completed_evidence_count"],
    }, sort_keys=True))
