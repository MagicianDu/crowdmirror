from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    assert_strict_json,
    load_json_artifact,
    non_empty_string,
    write_json_artifact,
)
from experiments.r12_customer_trial_launch_packet_export import (
    R12_CUSTOMER_TRIAL_LAUNCH_PACKET_EXPORT_SCHEMA_VERSION,
)


R12_CUSTOMER_TRIAL_LAUNCH_BUNDLE_VERIFICATION_SCHEMA_VERSION = (
    "r12-customer-trial-launch-bundle-verification-v1"
)

REQUIRED_BUNDLE_ITEM_IDS = {
    "packet_export_json",
    "customer_launch_packet_markdown",
    "launch_handoff_json",
    "field_slice_template_csv",
}


def build_r12_customer_trial_launch_bundle_verification(
    *,
    artifact_id: str,
    run_id: str,
    verified_at: str,
    r12_customer_trial_launch_packet_export: dict[str, Any],
    r12_customer_trial_launch_packet_export_path: str | Path,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    verified_at = non_empty_string(verified_at, field="verified_at")
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    packet_path = Path(r12_customer_trial_launch_packet_export_path)
    _validate_launch_packet_export(r12_customer_trial_launch_packet_export)

    packet = r12_customer_trial_launch_packet_export
    bundle_items = _bundle_items(packet, packet_path, root)
    required_items = [
        item for item in bundle_items if item["required_for_customer_launch"]
    ]
    missing_required_item_ids = [
        item["bundle_item_id"] for item in required_items if not item["path_resolvable"]
    ]
    all_required_resolvable = not missing_required_item_ids
    status = (
        "r12_customer_trial_launch_bundle_verification_ready_source_pending"
        if all_required_resolvable
        else "r12_customer_trial_launch_bundle_verification_blocked_missing_bundle_item"
    )

    report = {
        "schema_version": R12_CUSTOMER_TRIAL_LAUNCH_BUNDLE_VERIFICATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "claim_level": "customer_trial_launch_bundle_verified_no_validation_claim",
        "bundle_summary": {
            "verified_at": verified_at,
            "packet_export_artifact_id": packet["artifact_id"],
            "current_stage": packet["export_summary"]["current_stage"],
            "required_item_count": len(required_items),
            "resolved_required_item_count": sum(
                1 for item in required_items if item["path_resolvable"]
            ),
            "missing_required_item_ids": missing_required_item_ids,
            "field_outcome_validated": False,
        },
        "bundle_items": bundle_items,
        "acceptance_gates": {
            "launch_bundle_verified": all_required_resolvable,
            "packet_export_json_resolvable": _item_resolvable(
                bundle_items, "packet_export_json"
            ),
            "markdown_packet_resolvable": _item_resolvable(
                bundle_items, "customer_launch_packet_markdown"
            ),
            "launch_handoff_json_resolvable": _item_resolvable(
                bundle_items, "launch_handoff_json"
            ),
            "field_slice_template_resolvable": _item_resolvable(
                bundle_items, "field_slice_template_csv"
            ),
            "all_required_bundle_items_resolvable": all_required_resolvable,
            "field_outcome_validated": False,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "next_required_artifact": packet["next_required_artifact"],
        "source_refs": _source_refs(packet, bundle_items),
        "source_registry": _source_registry(packet, bundle_items),
        "allowed_claims": [
            (
                "Product can verify that the customer trial launch bundle "
                "contains resolvable packet, handoff, and template files."
            ),
            (
                "The launch bundle is deliverable for customer field-slice "
                "submission, but does not claim field validation."
            ),
        ],
        "blocked_claims": [
            "field validation 已完成",
            "customer field validation passed",
            "customer trial produced accepted feedback update",
            "Product default can use customer trial output",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_customer_trial_launch_bundle_verification(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_customer_trial_launch_bundle_verification(**kwargs),
    )


def _validate_launch_packet_export(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_TRIAL_LAUNCH_PACKET_EXPORT_SCHEMA_VERSION
    ):
        raise ValueError("r12 L31 launch packet export schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L31 launch packet export acceptance_gates required")
    if gates.get("launch_packet_export_ready") is not True:
        raise ValueError("r12 L31 launch packet export must be ready")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L31 must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L31 must block runtime default")


def _bundle_items(
    packet: dict[str, Any],
    packet_path: Path,
    root: Path,
) -> list[dict[str, Any]]:
    entries = [
        {
            "artifact_id": packet["artifact_id"],
            "path": str(packet_path),
        },
        *packet.get("source_registry", []),
    ]
    result = []
    seen_item_ids = set()
    for entry in entries:
        item_id = _bundle_item_id(entry["artifact_id"])
        if item_id in seen_item_ids:
            continue
        seen_item_ids.add(item_id)
        result.append(_bundle_item(entry, item_id, root))
    return result


def _bundle_item(
    entry: dict[str, str],
    item_id: str,
    root: Path,
) -> dict[str, Any]:
    raw_path = non_empty_string(entry["path"], field=f"{item_id}.path")
    resolved = _resolve_path(raw_path, root)
    path_resolvable = resolved.exists() and resolved.is_file()
    size_bytes = resolved.stat().st_size if path_resolvable else 0
    digest = _sha256(resolved) if path_resolvable else ""
    return {
        "bundle_item_id": item_id,
        "artifact_id": entry["artifact_id"],
        "path": raw_path,
        "path_resolvable": path_resolvable,
        "size_bytes": size_bytes,
        "sha256": digest,
        "required_for_customer_launch": item_id in REQUIRED_BUNDLE_ITEM_IDS,
    }


def _bundle_item_id(artifact_id: str) -> str:
    if artifact_id.startswith("customer_trial_launch_packet_markdown:"):
        return "customer_launch_packet_markdown"
    if artifact_id.startswith("customer_field_slice_template:"):
        return "field_slice_template_csv"
    if artifact_id.startswith("r12-customer-trial-launch-handoff-package"):
        return "launch_handoff_json"
    if artifact_id.startswith("r12-customer-trial-launch-packet-export"):
        return "packet_export_json"
    return artifact_id.replace("-", "_").replace(":", "_")


def _resolve_path(path: str, root: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _item_resolvable(items: list[dict[str, Any]], item_id: str) -> bool:
    return any(
        item["bundle_item_id"] == item_id and item["path_resolvable"]
        for item in items
    )


def _source_refs(
    packet: dict[str, Any],
    bundle_items: list[dict[str, Any]],
) -> list[str]:
    return _unique_strings(
        [
            packet["artifact_id"],
            *packet.get("source_refs", []),
            *[item["artifact_id"] for item in bundle_items],
        ]
    )


def _source_registry(
    packet: dict[str, Any],
    bundle_items: list[dict[str, Any]],
) -> list[dict[str, str]]:
    registry = [
        {
            "artifact_id": item["artifact_id"],
            "path": item["path"],
        }
        for item in bundle_items
    ]
    for entry in packet.get("source_registry", []):
        if entry not in registry:
            registry.append(entry)
    return registry


def _unique_strings(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--verified-at", required=True)
    parser.add_argument(
        "--r12-customer-trial-launch-packet-export-path",
        required=True,
    )
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    packet_path = Path(args.r12_customer_trial_launch_packet_export_path)
    output_path = write_r12_customer_trial_launch_bundle_verification(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        verified_at=args.verified_at,
        r12_customer_trial_launch_packet_export=load_json_artifact(packet_path),
        r12_customer_trial_launch_packet_export_path=packet_path,
        repo_root=args.repo_root,
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "launch_bundle_verified": artifact["acceptance_gates"][
                    "launch_bundle_verified"
                ],
                "output": str(output_path),
                "status": artifact["status"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
