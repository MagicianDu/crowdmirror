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
from experiments.r11_external_holdout_validation import (
    R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION,
)


R11_PRODUCT_SHADOW_TRIAL_SCHEMA_VERSION = "r11-product-shadow-trial-v1"
R11_PRODUCT_SHADOW_TRIAL_CLAIM_BOUNDARY = (
    "R11 Product shadow trial artifact. It allows Product to display a "
    "source-backed R11 shadow-only evidence card and record an outcome-review "
    "handoff, while preserving guarded baseline primary decisions. It is not "
    "Product core method validation, not field validation, and not runtime "
    "default authorization."
)


def build_r11_product_shadow_trial(
    *,
    artifact_id: str,
    run_id: str,
    r11_external_holdout_validation: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_holdout(r11_external_holdout_validation)
    holdout_passed = (
        r11_external_holdout_validation["acceptance_gates"][
            "external_holdout_passed_guarded"
        ]
        is True
    )
    report = {
        "schema_version": R11_PRODUCT_SHADOW_TRIAL_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r11_product_shadow_trial_ready_guarded",
        "claim_level": "product_shadow_trial_only",
        "claim_boundary": R11_PRODUCT_SHADOW_TRIAL_CLAIM_BOUNDARY,
        "trial_contract": {
            "source_backed_only": True,
            "shadow_only": True,
            "customer_visible_evidence_card_allowed": True,
            "customer_visible_primary_claims_use_guarded_baseline": True,
            "r11_can_override_primary_decision": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "shadow_evidence_card": _shadow_evidence_card(
            r11_external_holdout_validation,
            holdout_passed=holdout_passed,
        ),
        "customer_visible_primary_decision": {
            "primary_decision_source": "guarded_baseline_customer_value_report",
            "r11_shadow_output_role": "secondary_evidence_card_only",
            "r11_can_override_primary_decision": False,
            "runtime_default_allowed": False,
        },
        "outcome_review_handoff": {
            "handoff_id": "r11_shadow_trial_outcome_review",
            "target_artifact_id": "r6-product-outcome-review-current-001",
            "requires_customer_or_field_outcome": True,
            "update_candidate_scope": [
                "mechanism_weight",
                "segment_sensitivity",
                "propagation_edge",
                "interval_uncertainty",
            ],
            "prompt_or_persona_manual_patch_allowed": False,
            "runtime_default_allowed": False,
        },
        "acceptance_gates": {
            "r11_external_holdout_passed_guarded": holdout_passed,
            "shadow_only_mode": True,
            "customer_visible_evidence_card_allowed": True,
            "primary_claims_guarded_baseline_only": True,
            "r11_can_override_primary_decision": False,
            "outcome_review_handoff_present": True,
            "product_core_method_ready": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_registry": [
            {
                "artifact_id": r11_external_holdout_validation["artifact_id"],
                "path": (
                    "experiments/results/r11_external_holdout_validation/"
                    "r11-external-holdout-validation-current-001.json"
                ),
            }
        ],
        "source_refs": [r11_external_holdout_validation["artifact_id"]],
        "allowed_claims": [
            "Product can display R11 as a source-backed shadow-only evidence card.",
            "R11 shadow output can be reviewed after customer or field outcome arrives.",
        ],
        "blocked_claims": [
            "R11 validated",
            "R11 supports Product core method by default",
            "R11 can override guarded baseline primary decision",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "runtime default ready",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r11_product_shadow_trial(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r11_product_shadow_trial(**kwargs))


def _validate_holdout(holdout: dict[str, Any]) -> None:
    if holdout.get("schema_version") != R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION:
        raise ValueError(
            "r11_external_holdout_validation.schema_version must be "
            f"{R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION}"
        )
    gates = holdout.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r11_external_holdout_validation.acceptance_gates must be an object")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r11 external holdout must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r11 external holdout must not allow runtime default")
    if gates.get("product_core_method_ready") is not False:
        raise ValueError("r11 external holdout must not mark product core ready")


def _shadow_evidence_card(
    holdout: dict[str, Any],
    *,
    holdout_passed: bool,
) -> dict[str, Any]:
    metrics = holdout["method_metrics"]["r11_external_holdout_transfer"]
    return {
        "card_id": "r11_shadow_trial_evidence_card",
        "title": "R11 shadow-only interaction risk evidence",
        "claim_status": (
            "shadow_only_guarded_positive"
            if holdout_passed
            else "shadow_only_blocked_or_diagnostic"
        ),
        "display_allowed": True,
        "primary_decision_allowed": False,
        "metrics": metrics,
        "evidence_summary": {
            "source_signal": holdout["external_holdout_summary"]["source_signal"],
            "holdout_outcome_proxy": holdout["external_holdout_summary"][
                "holdout_outcome_proxy"
            ],
            "case_count": holdout["external_holdout_summary"]["case_count"],
            "failure_reasons": holdout["failure_reasons"],
            "stop_loss_or_next_step": holdout["stop_loss_or_next_step"],
        },
        "allowed_display_claims": [
            (
                "R11 is running in shadow mode with source-backed public-use "
                "proxy holdout evidence."
            ),
            (
                "R11 evidence is secondary and requires outcome review before "
                "any runtime-default update."
            ),
        ],
        "blocked_display_claims": [
            "R11 primary decision",
            "R11 field validated",
            "R11 runtime default",
            "R11 precise point prediction",
        ],
        "source_artifact_ids": [holdout["artifact_id"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--r11-external-holdout-validation-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r11_product_shadow_trial(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r11_external_holdout_validation=load_json_artifact(
            args.r11_external_holdout_validation_path
        ),
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


if __name__ == "__main__":
    raise SystemExit(main())
