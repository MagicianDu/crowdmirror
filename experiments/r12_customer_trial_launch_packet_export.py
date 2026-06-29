from __future__ import annotations

import argparse
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
from experiments.r12_customer_trial_launch_handoff_package import (
    R12_CUSTOMER_TRIAL_LAUNCH_HANDOFF_PACKAGE_SCHEMA_VERSION,
)


R12_CUSTOMER_TRIAL_LAUNCH_PACKET_EXPORT_SCHEMA_VERSION = (
    "r12-customer-trial-launch-packet-export-v1"
)


def build_r12_customer_trial_launch_packet_export(
    *,
    artifact_id: str,
    run_id: str,
    exported_at: str,
    r12_customer_trial_launch_handoff_package: dict[str, Any],
    markdown_output_path: str | Path,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    exported_at = non_empty_string(exported_at, field="exported_at")
    markdown_path = Path(markdown_output_path)
    _validate_launch_handoff(r12_customer_trial_launch_handoff_package)

    handoff = r12_customer_trial_launch_handoff_package
    launch_summary = handoff["launch_summary"]
    gates = handoff["acceptance_gates"]
    markdown = _render_markdown(handoff)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown)
    markdown_written = markdown_path.exists()

    report = {
        "schema_version": R12_CUSTOMER_TRIAL_LAUNCH_PACKET_EXPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r12_customer_trial_launch_packet_export_ready_source_pending",
        "claim_level": "customer_trial_packet_export_no_validation_claim",
        "export_summary": {
            "exported_at": exported_at,
            "launch_handoff_artifact_id": handoff["artifact_id"],
            "current_stage": launch_summary["current_stage"],
            "launch_handoff_ready": gates["launch_handoff_package_ready"],
            "markdown_output_path": str(markdown_path),
            "markdown_export_written": markdown_written,
            "customer_field_slice_present": gates["customer_field_slice_present"],
            "field_outcome_validated": gates["field_outcome_validated"],
        },
        "packet_sections": [
            "客户试运行数据回流请求",
            "字段模板",
            "审批与隐私边界",
            "提交后操作步骤",
            "阻断声明",
        ],
        "acceptance_gates": {
            "launch_packet_export_ready": markdown_written,
            "launch_handoff_package_ready": gates["launch_handoff_package_ready"],
            "markdown_export_written": markdown_written,
            "customer_field_slice_present": gates["customer_field_slice_present"],
            "field_outcome_validated": False,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "next_required_artifact": handoff["next_required_artifact"],
        "source_refs": _source_refs(handoff, markdown_path),
        "source_registry": _source_registry(handoff, markdown_path),
        "allowed_claims": [
            (
                "Product can export a customer-readable launch packet for "
                "field-slice submission."
            ),
            (
                "The packet is ready to request customer data, but does not "
                "claim field validation or runtime default readiness."
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


def write_r12_customer_trial_launch_packet_export(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_customer_trial_launch_packet_export(**kwargs),
    )


def _validate_launch_handoff(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_TRIAL_LAUNCH_HANDOFF_PACKAGE_SCHEMA_VERSION
    ):
        raise ValueError("r12 L30 launch handoff package schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L30 launch handoff package acceptance_gates required")
    if gates.get("launch_handoff_package_ready") is not True:
        raise ValueError("r12 L30 launch handoff package must be ready")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L30 must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L30 must block runtime default")


def _render_markdown(handoff: dict[str, Any]) -> str:
    request = handoff["customer_data_request"]
    instructions = handoff["submission_instructions"]
    governance = handoff["approval_and_governance"]
    fields = ", ".join(request["required_fields"])
    steps = "\n".join(
        f"- {step_id}" for step_id in instructions["operator_step_ids"]
    )
    approvals = "\n".join(
        f"- {item}" for item in governance["manual_approval_points"]
    )
    return "\n".join(
        [
            "# 客户试运行数据回流请求",
            "",
            f"- request_id: {request['request_id']}",
            f"- minimum_case_count: {request['minimum_case_count']}",
            f"- required_fields: {fields}",
            "",
            "## 字段模板",
            "",
            f"- template_path: {request['template_path']}",
            "",
            "## 审批与隐私边界",
            "",
            f"- approval_reference_required: {request['approval_reference_required']}",
            (
                "- direct_personal_identifiers_allowed: "
                f"{request['direct_personal_identifiers_allowed']}"
            ),
            "- manual_approval_points:",
            approvals,
            "",
            "## 提交后操作步骤",
            "",
            f"- first_operator_step: {instructions['first_operator_step']}",
            f"- first_operator_command: {instructions['first_operator_command']}",
            "- operator_step_ids:",
            steps,
            "",
            "## 阻断声明",
            "",
            "- field validation 尚未完成",
            "- customer field validation passed 不能声明",
            "- Product default 和 runtime default 仍保持关闭",
            "",
        ]
    )


def _source_refs(handoff: dict[str, Any], markdown_path: Path) -> list[str]:
    return _unique_strings(
        [
            handoff["artifact_id"],
            f"customer_trial_launch_packet_markdown:{markdown_path}",
            *handoff.get("source_refs", []),
        ]
    )


def _source_registry(
    handoff: dict[str, Any],
    markdown_path: Path,
) -> list[dict[str, str]]:
    registry = [
        {
            "artifact_id": handoff["artifact_id"],
            "path": (
                "experiments/results/r12_customer_trial_launch_handoff_package/"
                "r12-customer-trial-launch-handoff-package-current-001.json"
            ),
        },
        {
            "artifact_id": f"customer_trial_launch_packet_markdown:{markdown_path}",
            "path": str(markdown_path),
        },
    ]
    for entry in handoff.get("source_registry", []):
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
    parser.add_argument("--exported-at", required=True)
    parser.add_argument(
        "--r12-customer-trial-launch-handoff-package-path",
        required=True,
    )
    parser.add_argument("--markdown-output-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_customer_trial_launch_packet_export(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        exported_at=args.exported_at,
        r12_customer_trial_launch_handoff_package=load_json_artifact(
            args.r12_customer_trial_launch_handoff_package_path
        ),
        markdown_output_path=args.markdown_output_path,
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "markdown_export_written": artifact["acceptance_gates"][
                    "markdown_export_written"
                ],
                "output": str(output_path),
                "status": artifact["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
