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
    load_json_artifact,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_product_customer_value_report import (
    build_r6_product_customer_value_report,
)
from experiments.r6_product_outcome_review import build_r6_product_outcome_review
from experiments.r6_product_scenario_intake import build_r6_product_scenario_intake
from experiments.r9_combination_comparison import build_r9_combination_comparison
from experiments.r9_false_alarm_gate_redesign import build_r9_false_alarm_gate_redesign
from experiments.r9_holdout_guard import build_r9_holdout_guard
from experiments.r9_synthetic_mechanism_lab import build_r9_synthetic_mechanism_lab


R6_PRODUCT_R9_DIAGNOSTIC_WORKFLOW_SCHEMA_VERSION = (
    "r6-product-r9-diagnostic-workflow-v1"
)


def build_r6_product_r9_diagnostic_workflow(
    *,
    artifact_id: str,
    run_id: str,
    scenario_intake: dict[str, Any] | None = None,
    customer_value_report: dict[str, Any] | None = None,
    outcome_review: dict[str, Any] | None = None,
    r9_combination_comparison: dict[str, Any] | None = None,
    r9_synthetic_mechanism_lab: dict[str, Any] | None = None,
    r9_false_alarm_gate_redesign: dict[str, Any] | None = None,
    r9_holdout_guard: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    scenario = scenario_intake or build_r6_product_scenario_intake(
        artifact_id="r6-product-scenario-intake-current-001",
        run_id=run_id,
    )
    comparison = r9_combination_comparison or build_r9_combination_comparison(
        artifact_id="r9-combination-comparison-current-001",
        run_id=run_id,
    )
    synthetic_lab = r9_synthetic_mechanism_lab or build_r9_synthetic_mechanism_lab(
        artifact_id="r9-synthetic-mechanism-lab-current-001",
        run_id=run_id,
    )
    false_alarm_gate = (
        r9_false_alarm_gate_redesign
        or build_r9_false_alarm_gate_redesign(
            artifact_id="r9-false-alarm-gate-redesign-current-001",
            run_id=run_id,
        )
    )
    holdout_guard = r9_holdout_guard or build_r9_holdout_guard(
        artifact_id="r9-holdout-guard-current-001",
        run_id=run_id,
        combination_comparison=comparison,
        synthetic_mechanism_lab=synthetic_lab,
        false_alarm_gate_redesign=false_alarm_gate,
    )
    customer_report = customer_value_report or build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-current-001",
        run_id=run_id,
        r9_combination_comparison=comparison,
        r9_synthetic_mechanism_lab=synthetic_lab,
        r9_false_alarm_gate_redesign=false_alarm_gate,
        r9_holdout_guard=holdout_guard,
    )
    review = outcome_review or build_r6_product_outcome_review(
        artifact_id="r6-product-outcome-review-current-001",
        run_id=run_id,
    )
    r9_support = customer_report["display_payload"]["r9_method_support"]
    source_refs = [
        scenario["artifact_id"],
        customer_report["artifact_id"],
        review["artifact_id"],
        comparison["artifact_id"],
        synthetic_lab["artifact_id"],
        false_alarm_gate["artifact_id"],
        holdout_guard["artifact_id"],
    ]
    report = {
        "schema_version": R6_PRODUCT_R9_DIAGNOSTIC_WORKFLOW_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "product_r9_diagnostic_workflow_ready_guarded",
        "workflow_contract": {
            "source_backed_only": True,
            "scenario_to_diagnostic_to_outcome_review": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
            "customer_visible": True,
        },
        "workflow_stages": [
            {
                "stage_id": "scenario_intake",
                "artifact_id": scenario["artifact_id"],
                "status": scenario["status"],
                "customer_action": "provide scenario assumptions and decision question",
            },
            {
                "stage_id": "r9_guarded_diagnostic_report",
                "artifact_id": customer_report["artifact_id"],
                "status": customer_report["status"],
                "customer_action": "review guarded R9 trend, risk, mechanism, and blocked claims",
            },
            {
                "stage_id": "outcome_review",
                "artifact_id": review["artifact_id"],
                "status": review["status"],
                "customer_action": "attach post-release field or proxy outcome for replay",
            },
        ],
        "r9_diagnostic_summary": {
            "support_status": r9_support["support_status"],
            "best_combination_id": r9_support["best_combination_id"],
            "holdout_guard_status": r9_support["holdout_guard_status"],
            "false_alarm_gate_status": r9_support["false_alarm_gate_status"],
            "field_outcome_validated": r9_support["field_outcome_validated"],
            "runtime_default_allowed": r9_support["runtime_default_allowed"],
        },
        "outcome_review_handoff": {
            "requires_customer_or_field_outcome": True,
            "minimum_required_fields": [
                "outcome_id",
                "measurement_window",
                "observed_signal",
                "source_level",
            ],
            "target_artifact_id": review["artifact_id"],
            "runtime_default_allowed": False,
        },
        "source_refs": source_refs,
        "source_registry": [
            {
                "artifact_id": scenario["artifact_id"],
                "path": (
                    "experiments/results/r6_product_scenario_intake/"
                    "r6-product-scenario-intake-current-001.json"
                ),
            },
            {
                "artifact_id": customer_report["artifact_id"],
                "path": (
                    "experiments/results/r6_product_customer_value_report/"
                    "r6-product-customer-value-report-current-001.json"
                ),
            },
            {
                "artifact_id": review["artifact_id"],
                "path": (
                    "experiments/results/r6_product_outcome_review/"
                    "r6-product-outcome-review-current-001.json"
                ),
            },
            {
                "artifact_id": comparison["artifact_id"],
                "path": (
                    "experiments/results/r9_combination_comparison/"
                    "r9-combination-comparison-current-001.json"
                ),
            },
            {
                "artifact_id": synthetic_lab["artifact_id"],
                "path": (
                    "experiments/results/r9_synthetic_mechanism_lab/"
                    "r9-synthetic-mechanism-lab-current-001.json"
                ),
            },
            {
                "artifact_id": false_alarm_gate["artifact_id"],
                "path": (
                    "experiments/results/r9_false_alarm_gate_redesign/"
                    "r9-false-alarm-gate-redesign-current-001.json"
                ),
            },
            {
                "artifact_id": holdout_guard["artifact_id"],
                "path": (
                    "experiments/results/r9_holdout_guard/"
                    "r9-holdout-guard-current-001.json"
                ),
            },
        ],
        "allowed_claims": [
            (
                "Product can route a customer scenario through guarded R9 "
                "diagnostic support and outcome review handoff."
            )
        ],
        "blocked_claims": _unique_strings(
            [
            *customer_report.get("blocked_claims", []),
            "R9 validated",
            "runtime default ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "精准预测系统",
            ]
        ),
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_product_r9_diagnostic_workflow(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r6_product_r9_diagnostic_workflow(**kwargs),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scenario-intake-path", default=None)
    parser.add_argument("--customer-value-report-path", default=None)
    parser.add_argument("--outcome-review-path", default=None)
    parser.add_argument("--r9-combination-comparison-path", default=None)
    parser.add_argument("--r9-synthetic-mechanism-lab-path", default=None)
    parser.add_argument("--r9-false-alarm-gate-redesign-path", default=None)
    parser.add_argument("--r9-holdout-guard-path", default=None)
    args = parser.parse_args()
    output_path = write_r6_product_r9_diagnostic_workflow(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        scenario_intake=_load_optional(args.scenario_intake_path),
        customer_value_report=_load_optional(args.customer_value_report_path),
        outcome_review=_load_optional(args.outcome_review_path),
        r9_combination_comparison=_load_optional(args.r9_combination_comparison_path),
        r9_synthetic_mechanism_lab=_load_optional(args.r9_synthetic_mechanism_lab_path),
        r9_false_alarm_gate_redesign=_load_optional(
            args.r9_false_alarm_gate_redesign_path
        ),
        r9_holdout_guard=_load_optional(args.r9_holdout_guard_path),
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _load_optional(path: str | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return load_json_artifact(path)


def _unique_strings(values: list[Any]) -> list[str]:
    seen = set()
    result = []
    for index, value in enumerate(values):
        normalized = non_empty_string(value, field=f"blocked_claims[{index}]")
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
