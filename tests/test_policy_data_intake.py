from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO_ROOT / "data_catalog/policy_reaction_sources.json"
SOURCE_ID = "hps_htops_food_cost_core"


def _intake_module():
    try:
        return importlib.import_module("experiments.policy_data_intake")
    except ModuleNotFoundError as exc:
        if exc.name == "experiments.policy_data_intake":
            pytest.fail("experiments.policy_data_intake module is required")
        raise


def _source_by_id(catalog: dict, source_id: str) -> dict:
    return next(
        source for source in catalog["sources"] if source["source_id"] == source_id
    )


def test_catalog_loads_hps_htops_food_and_cost_fields():
    assert CATALOG_PATH.exists(), "policy reaction source catalog is required"
    intake = _intake_module()

    catalog = intake.load_policy_reaction_catalog(CATALOG_PATH)
    source = _source_by_id(catalog, SOURCE_ID)

    candidate_fields = set(source["candidate_policy_fields"])
    target_fields = set(source["target_fields"])
    all_fields = candidate_fields | target_fields
    assert {
        "FD1_food_sufficiency_last_7_days",
        "FD2_child_recent_food_insufficiency_unaffordable_last_7_days",
        "SPN4_difficulty_paying_usual_household_expenses_last_2_months",
        "INFLATE1_general_price_change_last_2_months",
        "INFLATE2_stress_from_price_increases_last_2_months",
        "EMP1_household_loss_employment_income_last_4_weeks",
    } <= all_fields

    assert source["unit_of_analysis"]
    assert source["claim_boundary"].startswith("Public-data intake readiness")


def test_build_manifest_is_strict_json_and_marks_hps_source_usable(tmp_path):
    intake = _intake_module()
    catalog = intake.load_policy_reaction_catalog(CATALOG_PATH)

    manifest = intake.build_policy_data_intake_manifest(catalog, source_id=SOURCE_ID)

    assert manifest == json.loads(json.dumps(manifest, allow_nan=False))
    assert manifest["schema_version"] == "circe-policy-data-intake-v1"
    assert manifest["source_id"] == SOURCE_ID
    assert manifest["status"] == "usable_for_policy_reaction_benchmark"
    assert manifest["dataset_access_mode"] == "public_use_file_required"
    assert manifest["source_url"].startswith("https://")
    assert manifest["claim_boundary"].startswith("Public-data intake readiness")

    output_path = tmp_path / "intake.json"
    written_path = intake.write_policy_data_intake_manifest(output_path, manifest)
    assert written_path == output_path
    assert json.loads(output_path.read_text()) == manifest


def test_build_manifest_rejects_missing_source_id():
    intake = _intake_module()
    catalog = intake.load_policy_reaction_catalog(CATALOG_PATH)

    with pytest.raises(ValueError, match="source_id"):
        intake.build_policy_data_intake_manifest(
            catalog,
            source_id="missing_policy_source",
        )


def test_load_catalog_rejects_missing_required_source_fields(tmp_path):
    intake = _intake_module()
    invalid_catalog = {
        "schema_version": "circe-policy-reaction-source-catalog-v1",
        "sources": [
            {
                "source_id": SOURCE_ID,
                "name": "Incomplete catalog fixture",
                "url": "https://example.com/public-data",
                "license_or_access": "Public use",
                "unit_of_analysis": "household response",
                "candidate_policy_fields": ["FD1_food_sufficiency_last_7_days"],
                "segment_fields": ["state"],
                "claim_boundary": "Public-data intake readiness only.",
            }
        ],
    }
    invalid_path = tmp_path / "invalid_catalog.json"
    invalid_path.write_text(json.dumps(invalid_catalog))

    with pytest.raises(ValueError, match="target_fields"):
        intake.load_policy_reaction_catalog(invalid_path)


def test_load_catalog_rejects_duplicate_json_keys(tmp_path):
    intake = _intake_module()
    duplicate_key_path = tmp_path / "duplicate_key_catalog.json"
    duplicate_key_path.write_text(
        '{"schema_version": "circe-policy-reaction-source-catalog-v1", '
        '"schema_version": "duplicate", "sources": []}'
    )

    with pytest.raises(ValueError, match="duplicate JSON object key"):
        intake.load_policy_reaction_catalog(duplicate_key_path)


def test_load_catalog_rejects_unsupported_schema_version(tmp_path):
    intake = _intake_module()
    invalid_catalog = {
        "schema_version": "unsupported-policy-catalog-v0",
        "sources": [_valid_source_fixture()],
    }
    invalid_path = tmp_path / "invalid_schema_catalog.json"
    invalid_path.write_text(json.dumps(invalid_catalog))

    with pytest.raises(ValueError, match="schema_version"):
        intake.load_policy_reaction_catalog(invalid_path)


def test_build_manifest_requires_explicit_status_and_access_mode():
    intake = _intake_module()
    source = _valid_source_fixture()
    source.pop("intake_status")

    with pytest.raises(ValueError, match="intake_status"):
        intake.build_policy_data_intake_manifest(
            {
                "schema_version": "circe-policy-reaction-source-catalog-v1",
                "sources": [source],
            },
            source_id=SOURCE_ID,
        )


def test_build_manifest_requires_explicit_dataset_access_mode():
    intake = _intake_module()
    source = _valid_source_fixture()
    source.pop("dataset_access_mode")

    with pytest.raises(ValueError, match="dataset_access_mode"):
        intake.build_policy_data_intake_manifest(
            {
                "schema_version": "circe-policy-reaction-source-catalog-v1",
                "sources": [source],
            },
            source_id=SOURCE_ID,
        )


def _valid_source_fixture() -> dict:
    return {
        "source_id": SOURCE_ID,
        "name": "Valid catalog fixture",
        "url": "https://example.com/public-data",
        "license_or_access": "Public use",
        "unit_of_analysis": "household response",
        "dataset_access_mode": "public_use_file_required",
        "intake_status": "usable_for_policy_reaction_benchmark",
        "candidate_policy_fields": ["FD1_food_sufficiency_last_7_days"],
        "segment_fields": ["state"],
        "target_fields": ["FD1_food_sufficiency_last_7_days"],
        "claim_boundary": "Public-data intake readiness only.",
    }
