from __future__ import annotations

import argparse
import csv
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
from experiments.r12_target_outcome_or_customer_field_slice_arrival import (
    MINIMUM_CUSTOMER_FIELD_CASE_COUNT,
    REQUIRED_CUSTOMER_FIELD_SLICE_FIELDS,
    R12_TARGET_OUTCOME_OR_CUSTOMER_FIELD_SLICE_ARRIVAL_SCHEMA_VERSION,
)


R12_CUSTOMER_FIELD_SLICE_HANDOFF_PACKAGE_SCHEMA_VERSION = (
    "r12-customer-field-slice-handoff-package-v1"
)


def build_r12_customer_field_slice_handoff_package(
    *,
    artifact_id: str,
    run_id: str,
    r12_target_outcome_or_customer_field_slice_arrival: dict[str, Any],
    generated_at: str,
    template_output_path: str | Path,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    generated_at = non_empty_string(generated_at, field="generated_at")
    template_output_path = non_empty_string(
        str(template_output_path),
        field="template_output_path",
    )
    _validate_l20_arrival(r12_target_outcome_or_customer_field_slice_arrival)

    arrival = r12_target_outcome_or_customer_field_slice_arrival
    arrival_summary = arrival["arrival_summary"]
    report = {
        "schema_version": R12_CUSTOMER_FIELD_SLICE_HANDOFF_PACKAGE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r12_customer_field_slice_handoff_package_ready_guarded",
        "claim_level": "customer_field_slice_handoff_ready_no_validation_claim",
        "handoff_summary": {
            "source_arrival_artifact_id": arrival["artifact_id"],
            "target_outcome_period": arrival_summary["target_outcome_period"],
            "prediction_case_count": arrival_summary["prediction_case_count"],
            "minimum_case_count": MINIMUM_CUSTOMER_FIELD_CASE_COUNT,
            "generated_at": generated_at,
            "template_output_path": template_output_path,
        },
        "field_slice_contract": _field_slice_contract(),
        "privacy_and_approval_contract": {
            "customer_approval_reference_required": True,
            "direct_personal_identifiers_allowed": False,
            "aggregation_or_pseudonymous_case_id_required": True,
            "manual_prompt_or_persona_patch_allowed": False,
        },
        "template_preview": {
            "template_output_path": template_output_path,
            "header_only_template": True,
            "columns": REQUIRED_CUSTOMER_FIELD_SLICE_FIELDS,
            "example_row": {
                "case_id": "customer_case_001",
                "segment_id": "segment_or_cohort_id",
                "scenario_id": "customer_scenario_001",
                "prediction_share_or_score": "0.125",
                "observed_outcome": "0.140",
                "outcome_timestamp": "2026-07-15T00:00:00Z",
                "customer_approval_reference": "customer_approval_id",
            },
        },
        "acceptance_gates": {
            "source_arrival_gate_ready": True,
            "customer_field_slice_template_generated": True,
            "customer_field_slice_contract_machine_checkable": True,
            "customer_data_request_ready": True,
            "outcome_source_arrived": arrival["acceptance_gates"][
                "outcome_source_arrived"
            ],
            "metrics_computed": False,
            "field_outcome_validated": False,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
            "direct_personal_identifiers_allowed": False,
            "manual_prompt_or_persona_patch_allowed": False,
        },
        "acceptance_decision": (
            "accept_customer_field_slice_handoff_ready_keep_validation_blocked"
        ),
        "next_required_artifact": (
            "r12_target_outcome_or_customer_field_slice_arrival_with_customer_slice"
        ),
        "source_refs": [
            arrival["artifact_id"],
            f"customer_field_slice_template:{template_output_path}",
        ],
        "source_registry": [
            {
                "artifact_id": arrival["artifact_id"],
                "path": (
                    "experiments/results/"
                    "r12_target_outcome_or_customer_field_slice_arrival/"
                    "r12-target-outcome-or-customer-field-slice-arrival-current-001.json"
                ),
            },
            {
                "artifact_id": (
                    f"customer_field_slice_template:{template_output_path}"
                ),
                "path": template_output_path,
            },
        ],
        "allowed_claims": [
            (
                "Product can provide a machine-checkable customer field slice "
                "template for outcome revalidation."
            ),
            (
                "Customer field slices must be approved and pseudonymous before "
                "they can trigger revalidation."
            ),
        ],
        "blocked_claims": [
            "metrics_computed=true",
            "field_or_pre_outcome_revalidation_passed=true",
            "field_outcome_validated=true",
            "direct personal identifiers in customer slice",
            "manual prompt/persona patch from customer slice",
            "Product default can use customer field slice by default",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_customer_field_slice_handoff_package(
    *,
    output: str | Path,
    template_output_path: str | Path,
    **kwargs: Any,
) -> Path:
    _write_csv_template(Path(template_output_path))
    return write_json_artifact(
        output,
        build_r12_customer_field_slice_handoff_package(
            template_output_path=template_output_path,
            **kwargs,
        ),
    )


def _validate_l20_arrival(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_TARGET_OUTCOME_OR_CUSTOMER_FIELD_SLICE_ARRIVAL_SCHEMA_VERSION
    ):
        raise ValueError("r12 L20 source arrival schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L20 source arrival acceptance_gates required")
    if gates.get("metrics_computed") is not False:
        raise ValueError("r12 L20 must not compute metrics")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 L20 must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L20 must block runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L20 must block Product default")


def _field_slice_contract() -> dict[str, Any]:
    return {
        "accepted_formats": ["csv", "jsonl"],
        "minimum_case_count": MINIMUM_CUSTOMER_FIELD_CASE_COUNT,
        "required_fields": REQUIRED_CUSTOMER_FIELD_SLICE_FIELDS,
        "field_definitions": [
            {
                "field": "case_id",
                "type": "string",
                "required": True,
                "validation_rule": (
                    "Use a pseudonymous stable id; do not include direct PII."
                ),
            },
            {
                "field": "segment_id",
                "type": "string",
                "required": True,
                "validation_rule": "Segment, cohort, route, policy group, or account cohort id.",
            },
            {
                "field": "scenario_id",
                "type": "string",
                "required": True,
                "validation_rule": "Must match the scenario being revalidated.",
            },
            {
                "field": "prediction_share_or_score",
                "type": "number",
                "required": True,
                "validation_rule": "Locked prediction score used before outcome arrival.",
            },
            {
                "field": "observed_outcome",
                "type": "number",
                "required": True,
                "validation_rule": "Observed post-event response or risk outcome.",
            },
            {
                "field": "outcome_timestamp",
                "type": "datetime",
                "required": True,
                "validation_rule": "Timestamp must be after the pre-outcome prediction lock.",
            },
            {
                "field": "customer_approval_reference",
                "type": "string",
                "required": True,
                "validation_rule": "Reference to customer approval or data-use record.",
            },
        ],
        "validation_rules": [
            "case_count >= 10",
            "all required fields present",
            "customer_approval_reference non-empty for every row",
            "direct personal identifiers are not allowed",
            "manual prompt/persona patch is not allowed",
        ],
    }


def _write_csv_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(REQUIRED_CUSTOMER_FIELD_SLICE_FIELDS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--r12-target-outcome-or-customer-field-slice-arrival-path",
        required=True,
    )
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--template-output", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_customer_field_slice_handoff_package(
        output=args.output,
        template_output_path=args.template_output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_target_outcome_or_customer_field_slice_arrival=load_json_artifact(
            args.r12_target_outcome_or_customer_field_slice_arrival_path
        ),
        generated_at=args.generated_at,
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["status"],
                "template_output": str(args.template_output),
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
