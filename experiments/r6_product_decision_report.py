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
from experiments.r6_product_story_package import (
    R6_PRODUCT_STORY_PACKAGE_SCHEMA_VERSION,
    build_r6_product_story_package,
)


R6_PRODUCT_DECISION_REPORT_SCHEMA_VERSION = "r6-product-decision-report-v1"
R6_PRODUCT_DECISION_REPORT_CUSTOMER_SECTIONS = [
    "what_changed",
    "who_is_at_risk",
    "why_risk_moved",
    "what_is_supported_by_evidence",
    "what_is_blocked",
    "what_to_measure_next",
]
R6_PRODUCT_DECISION_DEFAULT_STORY_ARTIFACT_ID = "r6-product-story-package-current-001"
R6_PRODUCT_DECISION_DEFAULT_STORY_ARTIFACT_PATH = (
    "experiments/results/r6_product_story_package/"
    "r6-product-story-package-current-001.json"
)


def build_r6_product_decision_report(
    *,
    artifact_id: str,
    run_id: str,
    story_package: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    story_artifact_id = (
        R6_PRODUCT_DECISION_DEFAULT_STORY_ARTIFACT_ID
        if story_package is None
        else f"{artifact_id}-story-package"
    )
    if story_package is None:
        story_package = build_r6_product_story_package(
            artifact_id=story_artifact_id,
            run_id=run_id,
        )
    story_package = _validate_story_package(
        story_package,
        expected_artifact_id=story_artifact_id,
    )
    report = {
        "schema_version": R6_PRODUCT_DECISION_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "decision_report_ready_guarded",
        "customer_sections": R6_PRODUCT_DECISION_REPORT_CUSTOMER_SECTIONS,
        "report_contract": {
            "source_backed_only": True,
            "static_narrative_fallback_allowed": False,
            "customer_visible_claims_require_source_artifact": True,
        },
        "display_sources": {
            "scenario": "story_package.section_contracts[scenario]",
            "evidence_cards": "story_package.evidence_card_ids",
            "blocked_claims": "story_package.blocked_claims",
            "next_measurement_plan": "story_package.next_measurement_plan",
        },
        "blocked_claims": story_package["blocked_claims"],
        "next_measurement_plan": story_package["next_measurement_plan"],
        "source_refs": _unique_strings(
            [story_package["artifact_id"], *story_package["source_refs"]]
        ),
        "source_registry": _source_registry_with_story_package(story_package),
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def _validate_story_package(
    story_package: dict[str, Any],
    *,
    expected_artifact_id: str,
) -> dict[str, Any]:
    if not isinstance(story_package, dict):
        raise ValueError("story_package must be an object")
    _require_exact(
        story_package,
        field="story_package.schema_version",
        expected=R6_PRODUCT_STORY_PACKAGE_SCHEMA_VERSION,
    )
    _require_exact(
        story_package,
        field="story_package.status",
        expected="product_story_package_ready_guarded",
    )
    artifact_id = non_empty_string(
        story_package.get("artifact_id"),
        field="story_package.artifact_id",
    )
    expected_artifact_id = non_empty_string(
        expected_artifact_id,
        field="expected_artifact_id",
    )
    if artifact_id != expected_artifact_id:
        raise ValueError(
            "story_package.artifact_id must match expected story artifact id"
        )
    ui_contract = _require_object(
        story_package.get("ui_contract"),
        field="story_package.ui_contract",
    )
    if ui_contract.get("static_narrative_fallback_allowed") is not False:
        raise ValueError(
            "story_package.ui_contract.static_narrative_fallback_allowed "
            "must be False"
        )
    if ui_contract.get("all_customer_visible_claims_require_source_artifact") is not True:
        raise ValueError(
            "story_package.ui_contract."
            "all_customer_visible_claims_require_source_artifact must be True"
        )
    next_measurement_plan = _require_object(
        story_package.get("next_measurement_plan"),
        field="story_package.next_measurement_plan",
    )
    normalized_next_measurement_plan = {
        "source_artifact_ids": _require_non_empty_string_list(
            next_measurement_plan.get("source_artifact_ids"),
            field="story_package.next_measurement_plan.source_artifact_ids",
        ),
        "required_gate_paths": _require_non_empty_string_list(
            next_measurement_plan.get("required_gate_paths"),
            field="story_package.next_measurement_plan.required_gate_paths",
        ),
    }
    return {
        **story_package,
        "artifact_id": artifact_id,
        "blocked_claims": _require_non_empty_string_list(
            story_package.get("blocked_claims"),
            field="story_package.blocked_claims",
        ),
        "next_measurement_plan": normalized_next_measurement_plan,
        "source_refs": _require_non_empty_string_list(
            story_package.get("source_refs"),
            field="story_package.source_refs",
        ),
        "source_registry": _validate_source_registry(
            story_package.get("source_registry"),
        ),
    }


def _validate_source_registry(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ValueError("story_package.source_registry must be a non-empty list")
    registry = []
    for index, entry in enumerate(value):
        if not isinstance(entry, dict):
            raise ValueError(f"story_package.source_registry[{index}] must be an object")
        registry.append(
            {
                "artifact_id": non_empty_string(
                    entry.get("artifact_id"),
                    field=f"story_package.source_registry[{index}].artifact_id",
                ),
                "path": non_empty_string(
                    entry.get("path"),
                    field=f"story_package.source_registry[{index}].path",
                ),
            }
        )
    if not registry:
        raise ValueError("story_package.source_registry must be a non-empty list")
    return registry


def _source_registry_with_story_package(
    story_package: dict[str, Any],
) -> list[dict[str, str]]:
    registry = [dict(entry) for entry in story_package["source_registry"]]
    story_artifact_id = story_package["artifact_id"]
    registry_ids = {entry["artifact_id"] for entry in registry}
    if story_artifact_id not in registry_ids:
        registry.append(
            {
                "artifact_id": story_artifact_id,
                "path": (
                    R6_PRODUCT_DECISION_DEFAULT_STORY_ARTIFACT_PATH
                    if story_artifact_id == R6_PRODUCT_DECISION_DEFAULT_STORY_ARTIFACT_ID
                    else "direct_input:story_package"
                ),
            }
        )
    return registry


def _require_exact(report: dict[str, Any], *, field: str, expected: str) -> None:
    key = field.rsplit(".", 1)[-1]
    if report.get(key) != expected:
        raise ValueError(f"{field} must be {expected!r}")


def _require_object(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _require_non_empty_string_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a non-empty list")
    items = [
        non_empty_string(item, field=f"{field}[{index}]")
        for index, item in enumerate(value)
    ]
    if not items:
        raise ValueError(f"{field} must be a non-empty list")
    return items


def _unique_strings(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        normalized = non_empty_string(value, field="source_refs[]")
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def write_r6_product_decision_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_decision_report(**kwargs))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r6_product_decision_report(
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
