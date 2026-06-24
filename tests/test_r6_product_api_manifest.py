import json
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.r6_product_api_manifest import build_r6_product_api_manifest


def test_r6_product_api_manifest_exposes_guarded_artifact_contract():
    manifest = build_r6_product_api_manifest(
        artifact_id="r6-product-api-manifest-test",
        run_id="r6-product-api-run",
    )

    assert manifest["schema_version"] == "r6-product-api-manifest-v1"
    assert manifest["status"] == "product_api_manifest_ready_guarded"
    assert manifest["api_contract"] == {
        "source_backed_only": True,
        "static_narrative_fallback_allowed": False,
        "customer_visible_claims_require_source_artifact": True,
        "customer_facing_ui_demo_ready": True,
        "runtime_default_allowed": False,
        "field_outcome_validated": False,
    }
    assert manifest["readiness_gates"]["product_api_manifest_ready"] is True
    assert manifest["readiness_gates"]["customer_facing_ui_demo_ready"] is True
    assert manifest["readiness_gates"]["field_outcome_validated"] is False
    assert manifest["readiness_gates"]["runtime_default_allowed"] is False
    assert "needs_field_outcome_validation" in manifest["blocking_gaps"]
    assert "needs_runtime_default_holdout_review" in manifest["blocking_gaps"]
    assert "needs_customer_facing_ui_integration" not in manifest["blocking_gaps"]
    assert manifest["display_contract"]["static_frontend_path"] == "/demo/"

    endpoint_ids = {endpoint["endpoint_id"] for endpoint in manifest["endpoints"]}
    assert endpoint_ids == {
        "product_readiness",
        "frontend_demo",
        "scenario_intake",
        "story_package",
        "decision_report",
        "customer_value_report",
        "outcome_review",
        "source_registry",
    }
    assert manifest["artifact_refs"] == {
        "readiness_index": "r6-product-readiness-index-current-001",
        "scenario_intake": "r6-product-scenario-intake-current-001",
        "story_package": "r6-product-story-package-current-001",
        "decision_report": "r6-product-decision-report-current-001",
        "customer_value_report": "r6-product-customer-value-report-current-001",
        "outcome_review": "r6-product-outcome-review-current-001",
    }
    assert "r6-product-customer-value-report-current-001" in manifest["source_refs"]
    _assert_manifest_sources_resolvable(manifest)
    json.dumps(manifest, allow_nan=False)


def test_r6_product_api_manifest_rejects_unresolved_story_source(tmp_path):
    fixtures = _copy_current_product_artifacts(tmp_path)
    story_path = fixtures["story_package"]
    story = json.loads(story_path.read_text())
    story["source_refs"] = [*story["source_refs"], "missing-source-artifact"]
    story_path.write_text(json.dumps(story, allow_nan=False))

    with pytest.raises(ValueError, match="story_package.source_refs"):
        build_r6_product_api_manifest(
            artifact_id="r6-product-api-manifest-bad-source",
            run_id="r6-product-api-run",
            artifact_paths=fixtures,
        )


def test_r6_product_api_manifest_rejects_static_story_fallback(tmp_path):
    fixtures = _copy_current_product_artifacts(tmp_path)
    story_path = fixtures["story_package"]
    story = json.loads(story_path.read_text())
    story["ui_contract"]["static_narrative_fallback_allowed"] = True
    story_path.write_text(json.dumps(story, allow_nan=False))

    with pytest.raises(ValueError, match="story_package.ui_contract"):
        build_r6_product_api_manifest(
            artifact_id="r6-product-api-manifest-static-fallback",
            run_id="r6-product-api-run",
            artifact_paths=fixtures,
        )


def test_r6_product_api_manifest_rejects_bad_registry_path(tmp_path):
    fixtures = _copy_current_product_artifacts(tmp_path)
    story_path = fixtures["story_package"]
    story = json.loads(story_path.read_text())
    story["source_registry"] = [
        (
            {
                **entry,
                "path": (
                    "experiments/results/r6_product_scenario_intake/"
                    "r6-product-scenario-intake-current-001.json"
                ),
            }
            if entry["artifact_id"] == "r6-product-report-current-003"
            else entry
        )
        for entry in story["source_registry"]
    ]
    story_path.write_text(json.dumps(story, allow_nan=False))

    with pytest.raises(ValueError, match="source_registry"):
        build_r6_product_api_manifest(
            artifact_id="r6-product-api-manifest-bad-registry-path",
            run_id="r6-product-api-run",
            artifact_paths=fixtures,
        )


def test_r6_product_api_manifest_cli_writes_artifact_and_stdout_json(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    output = tmp_path / "api-manifest.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_product_api_manifest.py",
            "--artifact-id",
            "r6-product-api-manifest-cli-test",
            "--run-id",
            "r6-product-api-run",
            "--output",
            str(output),
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout = json.loads(completed.stdout)
    artifact = json.loads(output.read_text())
    assert stdout == {
        "artifact_id": "r6-product-api-manifest-cli-test",
        "output": str(output),
        "status": "product_api_manifest_ready_guarded",
    }
    assert artifact["api_contract"]["source_backed_only"] is True
    _assert_manifest_sources_resolvable(artifact)


def _copy_current_product_artifacts(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    mapping = {
        "readiness_index": (
            "experiments/results/r6_product_readiness_index/"
            "r6-product-readiness-index-current-001.json"
        ),
        "scenario_intake": (
            "experiments/results/r6_product_scenario_intake/"
            "r6-product-scenario-intake-current-001.json"
        ),
        "story_package": (
            "experiments/results/r6_product_story_package/"
            "r6-product-story-package-current-001.json"
        ),
        "decision_report": (
            "experiments/results/r6_product_decision_report/"
            "r6-product-decision-report-current-001.json"
        ),
        "customer_value_report": (
            "experiments/results/r6_product_customer_value_report/"
            "r6-product-customer-value-report-current-001.json"
        ),
        "outcome_review": (
            "experiments/results/r6_product_outcome_review/"
            "r6-product-outcome-review-current-001.json"
        ),
    }
    copied = {}
    for key, relative_path in mapping.items():
        source = repo_root / relative_path
        target = tmp_path / source.name
        target.write_text(source.read_text())
        copied[key] = target
    return copied


def _assert_manifest_sources_resolvable(manifest):
    registry_ids = {entry["artifact_id"] for entry in manifest["source_registry"]}
    direct_ids = {manifest["artifact_id"], *manifest["artifact_refs"].values()}
    repo_root = Path(__file__).resolve().parents[1]
    for entry in manifest["source_registry"]:
        path = entry["path"]
        if path.startswith("direct_input:"):
            continue
        source_artifact = json.loads((repo_root / path).read_text())
        assert source_artifact["artifact_id"] == entry["artifact_id"]
    unresolved = set()
    for endpoint in manifest["endpoints"]:
        for source_ref in endpoint["source_artifact_ids"]:
            if source_ref not in registry_ids and source_ref not in direct_ids:
                unresolved.add(source_ref)
    for source_ref in manifest["source_refs"]:
        if source_ref not in registry_ids and source_ref not in direct_ids:
            unresolved.add(source_ref)
    assert unresolved == set()
