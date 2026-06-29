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
from experiments.r12_customer_feedback_loop_operator_rehearsal import (
    R12_CUSTOMER_FEEDBACK_LOOP_OPERATOR_REHEARSAL_SCHEMA_VERSION,
)
from experiments.r12_customer_field_slice_operator_rehearsal import (
    R12_CUSTOMER_FIELD_SLICE_OPERATOR_REHEARSAL_SCHEMA_VERSION,
)
from experiments.r12_customer_trial_launch_bundle_verification import (
    R12_CUSTOMER_TRIAL_LAUNCH_BUNDLE_VERIFICATION_SCHEMA_VERSION,
)


R12_CUSTOMER_TRIAL_EVIDENCE_LEDGER_SCHEMA_VERSION = (
    "r12-customer-trial-evidence-ledger-v1"
)


def build_r12_customer_trial_evidence_ledger(
    *,
    artifact_id: str,
    run_id: str,
    ledger_created_at: str,
    r12_customer_trial_launch_bundle_verification: dict[str, Any],
    r12_customer_trial_launch_bundle_verification_path: str | Path,
    r12_customer_field_slice_operator_rehearsal: dict[str, Any],
    r12_customer_field_slice_operator_rehearsal_path: str | Path,
    r12_customer_feedback_loop_operator_rehearsal: dict[str, Any],
    r12_customer_feedback_loop_operator_rehearsal_path: str | Path,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    ledger_created_at = non_empty_string(
        ledger_created_at,
        field="ledger_created_at",
    )
    l32_path = non_empty_string(
        str(r12_customer_trial_launch_bundle_verification_path),
        field="r12_customer_trial_launch_bundle_verification_path",
    )
    l34_path = non_empty_string(
        str(r12_customer_field_slice_operator_rehearsal_path),
        field="r12_customer_field_slice_operator_rehearsal_path",
    )
    l35_path = non_empty_string(
        str(r12_customer_feedback_loop_operator_rehearsal_path),
        field="r12_customer_feedback_loop_operator_rehearsal_path",
    )
    _validate_launch_bundle(r12_customer_trial_launch_bundle_verification)
    _validate_operator_rehearsal(r12_customer_field_slice_operator_rehearsal)
    _validate_feedback_loop_rehearsal(
        r12_customer_feedback_loop_operator_rehearsal
    )

    l32 = r12_customer_trial_launch_bundle_verification
    l34 = r12_customer_field_slice_operator_rehearsal
    l35 = r12_customer_feedback_loop_operator_rehearsal
    l32_gates = l32["acceptance_gates"]
    l34_gates = l34["acceptance_gates"]
    l35_gates = l35["acceptance_gates"]

    launch_bundle_verified = bool(l32_gates["launch_bundle_verified"])
    operator_rehearsal_executed = bool(
        l34_gates["operator_command_rehearsed"]
    )
    feedback_loop_rehearsed = bool(
        l35_gates["l22_intake_validator_executed"]
        and l35_gates["l23_field_revalidation_executed"]
        and l35_gates["l24_feedback_candidates_generated"]
        and l35_gates["l25_shadow_replay_executed"]
        and l35_gates["l26_synthetic_holdout_review_executed"]
    )
    ledger_ready = (
        launch_bundle_verified
        and operator_rehearsal_executed
        and feedback_loop_rehearsed
    )
    blocking_gaps = _blocking_gaps()
    evidence_rows = _evidence_rows(
        launch_bundle=l32,
        operator_rehearsal=l34,
        feedback_loop_rehearsal=l35,
    )
    status = (
        "r12_customer_trial_evidence_ledger_ready_source_pending"
        if ledger_ready
        else "r12_customer_trial_evidence_ledger_blocked_incomplete_chain"
    )

    report = {
        "schema_version": R12_CUSTOMER_TRIAL_EVIDENCE_LEDGER_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "claim_level": (
            "customer_trial_readiness_and_rehearsal_ledger_no_validation_claim"
        ),
        "ledger_summary": {
            "ledger_created_at": ledger_created_at,
            "launch_bundle_verified": launch_bundle_verified,
            "operator_rehearsal_executed": operator_rehearsal_executed,
            "feedback_loop_rehearsed_l22_to_l26": feedback_loop_rehearsed,
            "customer_visible_readiness_evidence_count": sum(
                1 for row in evidence_rows if row["customer_visible"]
            ),
            "operator_only_rehearsal_evidence_count": sum(
                1
                for row in evidence_rows
                if row["evidence_scope"] == "operator_only_synthetic_rehearsal"
            ),
            "blocking_gap_count": len(blocking_gaps),
            "next_required_artifact": l35["next_required_artifact"],
        },
        "evidence_rows": evidence_rows,
        "blocking_gaps": blocking_gaps,
        "acceptance_gates": {
            "customer_trial_evidence_ledger_ready": ledger_ready,
            "launch_bundle_verified": launch_bundle_verified,
            "operator_rehearsal_executed": operator_rehearsal_executed,
            "feedback_loop_rehearsed_l22_to_l26": feedback_loop_rehearsed,
            "real_customer_field_slice_submitted": False,
            "metrics_computed_on_real_customer_slice": False,
            "field_outcome_validated": False,
            "claim_boundary_machine_checkable": True,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "acceptance_decision": (
            "accept_customer_trial_evidence_ledger_keep_validation_blocked"
            if ledger_ready
            else "reject_customer_trial_evidence_ledger_complete_chain_first"
        ),
        "next_required_artifact": l35["next_required_artifact"],
        "source_refs": _source_refs(l32, l34, l35),
        "source_registry": _source_registry(
            launch_bundle=l32,
            launch_bundle_path=l32_path,
            operator_rehearsal=l34,
            operator_rehearsal_path=l34_path,
            feedback_loop_rehearsal=l35,
            feedback_loop_rehearsal_path=l35_path,
        ),
        "allowed_claims": [
            (
                "Product can show customer trial readiness evidence with "
                "source-backed launch bundle verification."
            ),
            (
                "Operators have rehearsed the field-slice intake command and "
                "the L22-L26 feedback loop on synthetic fixtures."
            ),
            (
                "The ledger is an audit trail for customer trial readiness, "
                "not evidence of real field validation."
            ),
        ],
        "blocked_claims": [
            "real_customer_field_slice_validated=true",
            "metrics_computed_on_real_customer_slice=true",
            "pre_outcome_field_validation_passed=true",
            "customer trial produced accepted feedback update",
            "Product default can use customer trial output",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_customer_trial_evidence_ledger(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_customer_trial_evidence_ledger(**kwargs),
    )


def _validate_launch_bundle(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_TRIAL_LAUNCH_BUNDLE_VERIFICATION_SCHEMA_VERSION
    ):
        raise ValueError("r12 L32 launch bundle schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L32 launch bundle acceptance_gates required")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L32 must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L32 must block runtime default")


def _validate_operator_rehearsal(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FIELD_SLICE_OPERATOR_REHEARSAL_SCHEMA_VERSION
    ):
        raise ValueError("r12 L34 operator rehearsal schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L34 operator rehearsal acceptance_gates required")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L34 must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L34 must block runtime default")


def _validate_feedback_loop_rehearsal(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FEEDBACK_LOOP_OPERATOR_REHEARSAL_SCHEMA_VERSION
    ):
        raise ValueError("r12 L35 feedback loop rehearsal schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L35 feedback loop acceptance_gates required")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L35 must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L35 must block runtime default")


def _evidence_rows(
    *,
    launch_bundle: dict[str, Any],
    operator_rehearsal: dict[str, Any],
    feedback_loop_rehearsal: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": "customer_launch_bundle_verified",
            "source_artifact_id": launch_bundle["artifact_id"],
            "evidence_scope": "customer_visible_trial_readiness",
            "evidence_status": "ready_source_pending",
            "customer_visible": True,
            "validation_claim_allowed": False,
            "product_default_allowed": False,
        },
        {
            "evidence_id": "customer_field_slice_operator_rehearsed",
            "source_artifact_id": operator_rehearsal["artifact_id"],
            "evidence_scope": "operator_only_synthetic_rehearsal",
            "evidence_status": "rehearsed_no_field_claim",
            "customer_visible": False,
            "validation_claim_allowed": False,
            "product_default_allowed": False,
        },
        {
            "evidence_id": "customer_feedback_loop_rehearsed_l22_to_l26",
            "source_artifact_id": feedback_loop_rehearsal["artifact_id"],
            "evidence_scope": "operator_only_synthetic_rehearsal",
            "evidence_status": "rehearsed_no_field_claim",
            "customer_visible": False,
            "validation_claim_allowed": False,
            "product_default_allowed": False,
        },
    ]


def _blocking_gaps() -> list[dict[str, str]]:
    return [
        {
            "gap_id": "real_customer_field_slice_missing",
            "required_artifact": "real_customer_field_slice",
            "blocks_claim": "metrics_computed_on_real_customer_slice=true",
        },
        {
            "gap_id": "public_target_outcome_missing",
            "required_artifact": "may_2026_dot_target_outcome_or_equivalent",
            "blocks_claim": "pre_outcome_field_validation_passed=true",
        },
        {
            "gap_id": "field_outcome_validation_missing",
            "required_artifact": "field_outcome_validation_report",
            "blocks_claim": "runtime_default_allowed=true",
        },
    ]


def _source_refs(
    launch_bundle: dict[str, Any],
    operator_rehearsal: dict[str, Any],
    feedback_loop_rehearsal: dict[str, Any],
) -> list[str]:
    return _unique_strings(
        [
            launch_bundle["artifact_id"],
            operator_rehearsal["artifact_id"],
            feedback_loop_rehearsal["artifact_id"],
            *launch_bundle.get("source_refs", []),
            *operator_rehearsal.get("source_refs", []),
            *feedback_loop_rehearsal.get("source_refs", []),
        ]
    )


def _source_registry(
    *,
    launch_bundle: dict[str, Any],
    launch_bundle_path: str,
    operator_rehearsal: dict[str, Any],
    operator_rehearsal_path: str,
    feedback_loop_rehearsal: dict[str, Any],
    feedback_loop_rehearsal_path: str,
) -> list[dict[str, str]]:
    registry = [
        {"artifact_id": launch_bundle["artifact_id"], "path": launch_bundle_path},
        {
            "artifact_id": operator_rehearsal["artifact_id"],
            "path": operator_rehearsal_path,
        },
        {
            "artifact_id": feedback_loop_rehearsal["artifact_id"],
            "path": feedback_loop_rehearsal_path,
        },
    ]
    for artifact in [
        launch_bundle,
        operator_rehearsal,
        feedback_loop_rehearsal,
    ]:
        for entry in artifact.get("source_registry", []):
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
    parser.add_argument("--ledger-created-at", required=True)
    parser.add_argument(
        "--r12-customer-trial-launch-bundle-verification-path",
        required=True,
    )
    parser.add_argument(
        "--r12-customer-field-slice-operator-rehearsal-path",
        required=True,
    )
    parser.add_argument(
        "--r12-customer-feedback-loop-operator-rehearsal-path",
        required=True,
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_customer_trial_evidence_ledger(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        ledger_created_at=args.ledger_created_at,
        r12_customer_trial_launch_bundle_verification=load_json_artifact(
            args.r12_customer_trial_launch_bundle_verification_path
        ),
        r12_customer_trial_launch_bundle_verification_path=(
            args.r12_customer_trial_launch_bundle_verification_path
        ),
        r12_customer_field_slice_operator_rehearsal=load_json_artifact(
            args.r12_customer_field_slice_operator_rehearsal_path
        ),
        r12_customer_field_slice_operator_rehearsal_path=(
            args.r12_customer_field_slice_operator_rehearsal_path
        ),
        r12_customer_feedback_loop_operator_rehearsal=load_json_artifact(
            args.r12_customer_feedback_loop_operator_rehearsal_path
        ),
        r12_customer_feedback_loop_operator_rehearsal_path=(
            args.r12_customer_feedback_loop_operator_rehearsal_path
        ),
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "customer_trial_evidence_ledger_ready": (
                    artifact["acceptance_gates"][
                        "customer_trial_evidence_ledger_ready"
                    ]
                ),
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
