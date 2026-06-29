from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_SOURCE_ID = "hps_htops_food_cost_core"
POLICY_REACTION_CATALOG_SCHEMA_VERSION = "circe-policy-reaction-source-catalog-v1"
POLICY_DATA_INTAKE_SCHEMA_VERSION = "circe-policy-data-intake-v1"
REQUIRED_SOURCE_FIELDS = {
    "source_id",
    "name",
    "url",
    "license_or_access",
    "unit_of_analysis",
    "candidate_policy_fields",
    "segment_fields",
    "target_fields",
    "claim_boundary",
    "dataset_access_mode",
    "intake_status",
}
LIST_SOURCE_FIELDS = {
    "candidate_policy_fields",
    "segment_fields",
    "target_fields",
}
MANIFEST_FIELDS = {
    "schema_version",
    "source_id",
    "status",
    "unit_of_analysis",
    "candidate_policy_fields",
    "segment_fields",
    "target_fields",
    "source_url",
    "license_or_access",
    "claim_boundary",
    "dataset_access_mode",
}


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-strict JSON constant is not allowed: {value}")


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON object key: {key}")
        obj[key] = value
    return obj


def _load_strict_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(),
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise ValueError(f"catalog must be valid strict JSON: {path}") from exc


def _manifest_json(manifest: dict[str, Any]) -> str:
    try:
        return json.dumps(manifest, allow_nan=False, indent=2, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise TypeError("manifest must be strict JSON serializable") from exc


def _validate_non_empty_string(source_id: str, field: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"source {source_id!r} field {field} must be a non-empty string")


def _validate_string_list(source_id: str, field: str, value: Any) -> None:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise ValueError(
            f"source {source_id!r} field {field} must be a non-empty list of strings"
        )


def _validate_source(source: Any) -> dict[str, Any]:
    if not isinstance(source, dict):
        raise ValueError("each catalog source must be an object")
    source_id = source.get("source_id")
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a non-empty string")

    missing = sorted(REQUIRED_SOURCE_FIELDS - set(source))
    if missing:
        raise ValueError(f"source {source_id!r} missing required fields: {missing}")

    for field in REQUIRED_SOURCE_FIELDS - LIST_SOURCE_FIELDS:
        _validate_non_empty_string(source_id, field, source[field])
    for field in LIST_SOURCE_FIELDS:
        _validate_string_list(source_id, field, source[field])

    return source


def _validate_catalog(catalog: Any) -> dict[str, Any]:
    if not isinstance(catalog, dict):
        raise ValueError("catalog must be a JSON object")
    schema_version = catalog.get("schema_version")
    if schema_version != POLICY_REACTION_CATALOG_SCHEMA_VERSION:
        raise ValueError(
            "catalog schema_version must be "
            f"{POLICY_REACTION_CATALOG_SCHEMA_VERSION!r}"
        )
    sources = catalog.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("catalog must contain a non-empty sources list")

    seen_source_ids: set[str] = set()
    for source in sources:
        validated_source = _validate_source(source)
        source_id = validated_source["source_id"]
        if source_id in seen_source_ids:
            raise ValueError(f"duplicate source_id in catalog: {source_id}")
        seen_source_ids.add(source_id)
    return catalog


def _source_for_id(catalog: dict[str, Any], source_id: str) -> dict[str, Any]:
    for source in catalog["sources"]:
        if source["source_id"] == source_id:
            return source
    raise ValueError(f"source_id not found in policy reaction catalog: {source_id}")


def load_policy_reaction_catalog(path: str | Path) -> dict[str, Any]:
    """Load and validate the offline policy-reaction public-data source catalog."""

    catalog_path = Path(path)
    return _validate_catalog(_load_strict_json(catalog_path))


def build_policy_data_intake_manifest(
    catalog: dict[str, Any],
    *,
    source_id: str = DEFAULT_SOURCE_ID,
) -> dict[str, Any]:
    """Build a strict-JSON-ready intake manifest for a cataloged public data source."""

    validated_catalog = _validate_catalog(catalog)
    source = _source_for_id(validated_catalog, source_id)
    manifest = {
        "schema_version": POLICY_DATA_INTAKE_SCHEMA_VERSION,
        "source_id": source["source_id"],
        "status": source["intake_status"],
        "unit_of_analysis": source["unit_of_analysis"],
        "candidate_policy_fields": list(source["candidate_policy_fields"]),
        "segment_fields": list(source["segment_fields"]),
        "target_fields": list(source["target_fields"]),
        "source_url": source["url"],
        "license_or_access": source["license_or_access"],
        "claim_boundary": source["claim_boundary"],
        "dataset_access_mode": source["dataset_access_mode"],
    }
    missing = sorted(MANIFEST_FIELDS - set(manifest))
    if missing:
        raise ValueError(f"policy data intake manifest missing fields: {missing}")
    _manifest_json(manifest)
    return manifest


def write_policy_data_intake_manifest(
    path: str | Path,
    manifest: dict[str, Any],
) -> Path:
    """Write a policy-data intake manifest as strict JSON and return its path."""

    output_path = Path(path)
    missing = sorted(MANIFEST_FIELDS - set(manifest))
    if missing:
        raise ValueError(f"policy data intake manifest missing fields: {missing}")
    manifest_json = _manifest_json(manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(manifest_json)
    return output_path
