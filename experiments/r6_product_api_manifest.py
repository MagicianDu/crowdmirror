from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)


R6_PRODUCT_API_MANIFEST_SCHEMA_VERSION = "r6-product-api-manifest-v1"
R6_PRODUCT_API_MANIFEST_DEFAULT_PATHS = {
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
    "r9_diagnostic_workflow": (
        "experiments/results/r6_product_r9_diagnostic_workflow/"
        "r6-product-r9-diagnostic-workflow-current-001.json"
    ),
    "outcome_review": (
        "experiments/results/r6_product_outcome_review/"
        "r6-product-outcome-review-current-001.json"
    ),
}
R6_PRODUCT_API_REQUIRED_ARTIFACTS = {
    "readiness_index": (
        "r6-product-readiness-index-v1",
        "product_first_readiness_partial",
    ),
    "scenario_intake": ("r6-product-scenario-intake-v1", "scenario_intake_ready"),
    "story_package": (
        "r6-product-story-package-v1",
        "product_story_package_ready_guarded",
    ),
    "decision_report": (
        "r6-product-decision-report-v1",
        "decision_report_ready_guarded",
    ),
    "customer_value_report": (
        "r6-product-customer-value-report-v1",
        "customer_value_report_ready_guarded",
    ),
    "r9_diagnostic_workflow": (
        "r6-product-r9-diagnostic-workflow-v1",
        "product_r9_diagnostic_workflow_ready_guarded",
    ),
    "outcome_review": (
        "r6-product-outcome-review-v1",
        "outcome_review_ready_update_blocked",
    ),
}


def build_r6_product_api_manifest(
    *,
    artifact_id: str,
    run_id: str,
    artifact_paths: dict[str, str | Path] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    paths = _artifact_paths(artifact_paths)
    artifacts = {
        key: _load_required_artifact(key, path)
        for key, path in paths.items()
    }
    _validate_story_package(artifacts["story_package"])
    _validate_decision_report(artifacts["decision_report"])
    _validate_customer_value_report(artifacts["customer_value_report"])
    _validate_r9_diagnostic_workflow(artifacts["r9_diagnostic_workflow"])
    _validate_runtime_boundaries(
        readiness_index=artifacts["readiness_index"],
        outcome_review=artifacts["outcome_review"],
    )
    _validate_frontend_demo_contract(
        readiness_index=artifacts["readiness_index"],
        customer_value_report=artifacts["customer_value_report"],
    )

    artifact_refs = {
        key: non_empty_string(value.get("artifact_id"), field=f"{key}.artifact_id")
        for key, value in artifacts.items()
    }
    source_registry = _source_registry(
        direct_artifact_paths=paths,
        artifact_refs=artifact_refs,
        story_package=artifacts["story_package"],
        decision_report=artifacts["decision_report"],
        customer_value_report=artifacts["customer_value_report"],
        r9_diagnostic_workflow=artifacts["r9_diagnostic_workflow"],
    )
    _assert_registry_paths_match_artifacts(source_registry)
    endpoints = _endpoints(artifact_refs)
    report = {
        "schema_version": R6_PRODUCT_API_MANIFEST_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "product_api_manifest_ready_guarded",
        "artifact_refs": artifact_refs,
        "artifact_paths": {
            key: _string_path(path)
            for key, path in paths.items()
        },
        "api_contract": {
            "source_backed_only": True,
            "static_narrative_fallback_allowed": False,
            "customer_visible_claims_require_source_artifact": True,
            "customer_facing_ui_demo_ready": True,
            "runtime_default_allowed": False,
            "field_outcome_validated": False,
        },
        "readiness_gates": {
            "product_api_manifest_ready": True,
            "customer_facing_ui_demo_ready": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "endpoints": endpoints,
        "source_registry": source_registry,
        "source_refs": _unique_strings(
            [
                *artifact_refs.values(),
                *artifacts["story_package"].get("source_refs", []),
                *artifacts["decision_report"].get("source_refs", []),
                *artifacts["customer_value_report"].get("source_refs", []),
                *artifacts["r9_diagnostic_workflow"].get("source_refs", []),
            ]
        ),
        "display_contract": {
            "entry_endpoint": "/r6/product/customer-value-report",
            "required_sections": artifacts["customer_value_report"][
                "customer_sections"
            ],
            "claim_boundary_required": True,
            "blocked_claims_required": True,
            "source_registry_required": True,
            "precise_point_prediction_allowed": False,
            "static_frontend_path": "/demo/",
        },
        "blocking_gaps": [
            "needs_field_outcome_validation",
            "needs_runtime_default_holdout_review",
            "needs_customer_workflow_runtime_integration",
        ],
        "allowed_claims": [
            "Product API manifest exposes the source-backed R6 artifact chain.",
            "Customer-facing reports can consume guarded artifacts without static narrative fallback.",
            "The static /demo/ frontend can render the guarded customer value report.",
        ],
        "blocked_claims": _unique_strings(
            [
                *artifacts["readiness_index"].get("blocked_claims", []),
                *artifacts["story_package"].get("blocked_claims", []),
                *artifacts["decision_report"].get("blocked_claims", []),
                *artifacts["customer_value_report"].get("blocked_claims", []),
                *artifacts["r9_diagnostic_workflow"].get("blocked_claims", []),
                "field validation 已完成",
                "runtime default 可以开启",
            ]
        ),
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    _assert_manifest_sources_resolvable(report)
    assert_strict_json(report)
    return report


def write_r6_product_api_manifest(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_api_manifest(**kwargs))


def _artifact_paths(
    artifact_paths: dict[str, str | Path] | None,
) -> dict[str, Path]:
    provided = artifact_paths or R6_PRODUCT_API_MANIFEST_DEFAULT_PATHS
    paths: dict[str, Path] = {}
    for key in R6_PRODUCT_API_REQUIRED_ARTIFACTS:
        if key not in provided:
            raise ValueError(f"artifact_paths missing required artifact: {key}")
        paths[key] = Path(provided[key])
    return paths


def _load_required_artifact(key: str, path: Path) -> dict[str, Any]:
    resolved = _resolve_path(path)
    payload = json.loads(resolved.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{key} artifact must be a JSON object")
    schema_version, status = R6_PRODUCT_API_REQUIRED_ARTIFACTS[key]
    if payload.get("schema_version") != schema_version:
        raise ValueError(f"{key}.schema_version must be {schema_version!r}")
    if payload.get("status") != status:
        raise ValueError(f"{key}.status must be {status!r}")
    return payload


def _validate_story_package(story_package: dict[str, Any]) -> None:
    ui_contract = _require_object(
        story_package.get("ui_contract"),
        field="story_package.ui_contract",
    )
    if ui_contract.get("static_narrative_fallback_allowed") is not False:
        raise ValueError(
            "story_package.ui_contract.static_narrative_fallback_allowed must be False"
        )
    if ui_contract.get("all_customer_visible_claims_require_source_artifact") is not True:
        raise ValueError(
            "story_package.ui_contract."
            "all_customer_visible_claims_require_source_artifact must be True"
        )
    _assert_artifact_sources_resolvable(
        artifact=story_package,
        artifact_label="story_package",
        direct_refs=set(story_package["artifact_refs"].values())
        | {story_package["artifact_id"]},
        source_fields=[
            ("source_refs", story_package.get("source_refs")),
            (
                "next_measurement_plan.source_artifact_ids",
                story_package["next_measurement_plan"].get("source_artifact_ids"),
            ),
            *[
                (
                    f"section_contracts[{index}].source_artifact_ids",
                    section.get("source_artifact_ids"),
                )
                for index, section in enumerate(story_package["section_contracts"])
            ],
            *[
                (
                    f"customer_visible_claim_cards[{index}].source_artifact_ids",
                    card.get("source_artifact_ids"),
                )
                for index, card in enumerate(story_package["customer_visible_claim_cards"])
            ],
        ],
    )


def _validate_decision_report(decision_report: dict[str, Any]) -> None:
    contract = _require_object(
        decision_report.get("report_contract"),
        field="decision_report.report_contract",
    )
    if contract.get("source_backed_only") is not True:
        raise ValueError("decision_report.report_contract.source_backed_only must be True")
    if contract.get("static_narrative_fallback_allowed") is not False:
        raise ValueError(
            "decision_report.report_contract.static_narrative_fallback_allowed must be False"
        )
    _assert_artifact_sources_resolvable(
        artifact=decision_report,
        artifact_label="decision_report",
        direct_refs={decision_report["artifact_id"]},
        source_fields=[("source_refs", decision_report.get("source_refs"))],
    )


def _validate_customer_value_report(customer_value_report: dict[str, Any]) -> None:
    contract = _require_object(
        customer_value_report.get("report_contract"),
        field="customer_value_report.report_contract",
    )
    if contract.get("source_backed_only") is not True:
        raise ValueError(
            "customer_value_report.report_contract.source_backed_only must be True"
        )
    if contract.get("static_narrative_fallback_allowed") is not False:
        raise ValueError(
            "customer_value_report.report_contract.static_narrative_fallback_allowed "
            "must be False"
        )
    if contract.get("precise_point_prediction_allowed") is not False:
        raise ValueError(
            "customer_value_report.report_contract.precise_point_prediction_allowed "
            "must be False"
        )
    _assert_artifact_sources_resolvable(
        artifact=customer_value_report,
        artifact_label="customer_value_report",
        direct_refs={customer_value_report["artifact_id"]},
        source_fields=[
            ("source_refs", customer_value_report.get("source_refs")),
            *[
                (
                    f"section_contracts[{index}].source_artifact_ids",
                    section.get("source_artifact_ids"),
                )
                for index, section in enumerate(
                    customer_value_report["section_contracts"]
                )
            ],
        ],
    )


def _validate_r9_diagnostic_workflow(
    r9_diagnostic_workflow: dict[str, Any],
) -> None:
    contract = _require_object(
        r9_diagnostic_workflow.get("workflow_contract"),
        field="r9_diagnostic_workflow.workflow_contract",
    )
    if contract.get("source_backed_only") is not True:
        raise ValueError(
            "r9_diagnostic_workflow.workflow_contract.source_backed_only must be True"
        )
    if contract.get("scenario_to_diagnostic_to_outcome_review") is not True:
        raise ValueError(
            "r9_diagnostic_workflow.workflow_contract."
            "scenario_to_diagnostic_to_outcome_review must be True"
        )
    if contract.get("field_outcome_validated") is not False:
        raise ValueError(
            "r9_diagnostic_workflow.workflow_contract.field_outcome_validated must be False"
        )
    if contract.get("runtime_default_allowed") is not False:
        raise ValueError(
            "r9_diagnostic_workflow.workflow_contract.runtime_default_allowed must be False"
        )
    if contract.get("customer_visible") is not True:
        raise ValueError(
            "r9_diagnostic_workflow.workflow_contract.customer_visible must be True"
        )
    stages = _require_list(
        r9_diagnostic_workflow.get("workflow_stages"),
        field="r9_diagnostic_workflow.workflow_stages",
    )
    handoff = _require_object(
        r9_diagnostic_workflow.get("outcome_review_handoff"),
        field="r9_diagnostic_workflow.outcome_review_handoff",
    )
    if handoff.get("runtime_default_allowed") is not False:
        raise ValueError(
            "r9_diagnostic_workflow.outcome_review_handoff."
            "runtime_default_allowed must be False"
        )
    if handoff.get("requires_customer_or_field_outcome") is not True:
        raise ValueError(
            "r9_diagnostic_workflow.outcome_review_handoff."
            "requires_customer_or_field_outcome must be True"
        )
    _assert_artifact_sources_resolvable(
        artifact=r9_diagnostic_workflow,
        artifact_label="r9_diagnostic_workflow",
        direct_refs={r9_diagnostic_workflow["artifact_id"]},
        source_fields=[
            ("source_refs", r9_diagnostic_workflow.get("source_refs")),
            (
                "workflow_stages.artifact_id",
                [stage.get("artifact_id") for stage in stages],
            ),
            (
                "outcome_review_handoff.target_artifact_id",
                [handoff.get("target_artifact_id")],
            ),
        ],
    )


def _validate_runtime_boundaries(
    *,
    readiness_index: dict[str, Any],
    outcome_review: dict[str, Any],
) -> None:
    readiness_gates = _require_object(
        readiness_index.get("readiness_gates"),
        field="readiness_index.readiness_gates",
    )
    if readiness_gates.get("field_outcome_validated") is not False:
        raise ValueError("readiness_index.field_outcome_validated must be False")
    if readiness_gates.get("runtime_default_allowed") is not False:
        raise ValueError("readiness_index.runtime_default_allowed must be False")
    update_gate = _require_object(
        outcome_review.get("update_gate"),
        field="outcome_review.update_gate",
    )
    if update_gate.get("runtime_default_allowed") is not False:
        raise ValueError("outcome_review.update_gate.runtime_default_allowed must be False")
    if update_gate.get("requires_holdout_before_default") is not True:
        raise ValueError(
            "outcome_review.update_gate.requires_holdout_before_default must be True"
        )


def _validate_frontend_demo_contract(
    *,
    readiness_index: dict[str, Any],
    customer_value_report: dict[str, Any],
) -> None:
    readiness_gates = _require_object(
        readiness_index.get("readiness_gates"),
        field="readiness_index.readiness_gates",
    )
    if readiness_gates.get("customer_facing_ui_demo_ready") is not True:
        raise ValueError("readiness_index.customer_facing_ui_demo_ready must be True")
    customer_contract = _require_object(
        customer_value_report.get("report_contract"),
        field="customer_value_report.report_contract",
    )
    if customer_contract.get("customer_facing_ui_demo_ready") is not True:
        raise ValueError(
            "customer_value_report.report_contract.customer_facing_ui_demo_ready "
            "must be True"
        )


def _assert_artifact_sources_resolvable(
    *,
    artifact: dict[str, Any],
    artifact_label: str,
    direct_refs: set[str],
    source_fields: list[tuple[str, Any]],
) -> None:
    registry_ids = {
        non_empty_string(entry.get("artifact_id"), field=f"{artifact_label}.source_registry")
        for entry in _require_list(
            artifact.get("source_registry"),
            field=f"{artifact_label}.source_registry",
        )
        if isinstance(entry, dict)
    }
    for field, refs in source_fields:
        if not isinstance(refs, list):
            raise ValueError(f"{artifact_label}.{field} must be a list")
        for index, ref in enumerate(refs):
            normalized = non_empty_string(ref, field=f"{artifact_label}.{field}[{index}]")
            if normalized not in registry_ids and normalized not in direct_refs:
                raise ValueError(
                    f"{artifact_label}.{field}[{index}] contains unregistered "
                    f"source artifact: {normalized}"
                )


def _source_registry(
    *,
    direct_artifact_paths: dict[str, Path],
    artifact_refs: dict[str, str],
    story_package: dict[str, Any],
    decision_report: dict[str, Any],
    customer_value_report: dict[str, Any],
    r9_diagnostic_workflow: dict[str, Any],
) -> list[dict[str, str]]:
    entries = [
        {
            "artifact_id": artifact_refs[key],
            "path": _string_path(direct_artifact_paths[key]),
        }
        for key in R6_PRODUCT_API_REQUIRED_ARTIFACTS
    ]
    entries.extend(story_package["source_registry"])
    entries.extend(decision_report["source_registry"])
    entries.extend(customer_value_report["source_registry"])
    entries.extend(r9_diagnostic_workflow["source_registry"])
    return _dedupe_registry(entries)


def _endpoints(artifact_refs: dict[str, str]) -> list[dict[str, Any]]:
    return [
        _endpoint("product_readiness", "/r6/product/readiness", artifact_refs["readiness_index"]),
        {
            "endpoint_id": "frontend_demo",
            "method": "GET",
            "path": "/demo/",
            "source_artifact_ids": [
                artifact_refs["customer_value_report"],
                artifact_refs["readiness_index"],
            ],
            "response_contract": "static_source_backed_ui",
        },
        _endpoint("scenario_intake", "/r6/product/scenario-intake", artifact_refs["scenario_intake"]),
        _endpoint("story_package", "/r6/product/story-package", artifact_refs["story_package"]),
        _endpoint("decision_report", "/r6/product/decision-report", artifact_refs["decision_report"]),
        _endpoint(
            "customer_value_report",
            "/r6/product/customer-value-report",
            artifact_refs["customer_value_report"],
        ),
        _endpoint(
            "r9_diagnostic_workflow",
            "/r6/product/r9-diagnostic-workflow",
            artifact_refs["r9_diagnostic_workflow"],
        ),
        _endpoint("outcome_review", "/r6/product/outcome-review", artifact_refs["outcome_review"]),
        {
            "endpoint_id": "source_registry",
            "method": "GET",
            "path": "/r6/product/source-registry",
            "source_artifact_ids": list(artifact_refs.values()),
            "response_contract": "r6_product_api_manifest.source_registry",
        },
    ]


def _endpoint(endpoint_id: str, path: str, source_artifact_id: str) -> dict[str, Any]:
    return {
        "endpoint_id": endpoint_id,
        "method": "GET",
        "path": path,
        "source_artifact_ids": [source_artifact_id],
        "response_contract": "source_artifact_json",
    }


def _assert_manifest_sources_resolvable(report: dict[str, Any]) -> None:
    registry_ids = {entry["artifact_id"] for entry in report["source_registry"]}
    direct_ids = {report["artifact_id"], *report["artifact_refs"].values()}
    for index, source_ref in enumerate(report["source_refs"]):
        normalized = non_empty_string(source_ref, field=f"source_refs[{index}]")
        if normalized not in registry_ids and normalized not in direct_ids:
            raise ValueError(
                f"source_refs[{index}] contains unregistered source artifact: {normalized}"
            )
    for endpoint_index, endpoint in enumerate(report["endpoints"]):
        for source_index, source_ref in enumerate(endpoint["source_artifact_ids"]):
            normalized = non_empty_string(
                source_ref,
                field=f"endpoints[{endpoint_index}].source_artifact_ids[{source_index}]",
            )
            if normalized not in registry_ids and normalized not in direct_ids:
                raise ValueError(
                    "endpoints"
                    f"[{endpoint_index}].source_artifact_ids[{source_index}] "
                    f"contains unregistered source artifact: {normalized}"
                )


def _dedupe_registry(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    result = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"source_registry[{index}] must be an object")
        artifact_id = non_empty_string(
            entry.get("artifact_id"),
            field=f"source_registry[{index}].artifact_id",
        )
        path = non_empty_string(entry.get("path"), field=f"source_registry[{index}].path")
        if artifact_id not in seen:
            seen.add(artifact_id)
            result.append({"artifact_id": artifact_id, "path": path})
    return result


def _assert_registry_paths_match_artifacts(registry: list[dict[str, str]]) -> None:
    for index, entry in enumerate(registry):
        path = entry["path"]
        if path.startswith("direct_input:"):
            continue
        resolved = _resolve_path(Path(path))
        try:
            payload = json.loads(resolved.read_text())
        except FileNotFoundError as exc:
            raise ValueError(
                f"source_registry[{index}].path does not exist: {path}"
            ) from exc
        if not isinstance(payload, dict):
            raise ValueError(f"source_registry[{index}].path must contain a JSON object")
        if payload.get("artifact_id") != entry["artifact_id"]:
            raise ValueError(
                "source_registry"
                f"[{index}] artifact_id does not match path artifact: {path}"
            )


def _unique_strings(values: list[Any]) -> list[str]:
    seen = set()
    result = []
    for index, value in enumerate(values):
        normalized = non_empty_string(value, field=f"source_refs[{index}]")
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _require_object(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _require_list(value: Any, *, field: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    return value


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return Path(__file__).resolve().parents[1] / path


def _string_path(path: Path) -> str:
    return str(path) if path.is_absolute() else path.as_posix()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r6_product_api_manifest(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "output": str(output_path),
                "status": report["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
