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


R6_PRODUCT_OUTCOME_REVIEW_SCHEMA_VERSION = "r6-product-outcome-review-v1"
R6_PRODUCT_OUTCOME_REVIEW_OUTPUTS = [
    "static_prior_error",
    "interaction_error",
    "risk_signal_classification",
    "error_attribution",
    "candidate_update",
    "update_gate",
]
_DEFAULT_OBSERVED_OUTCOME = {
    "outcome_id": "generic-outcome-review-001",
    "measurement_window": "post_release_30d",
    "observed_signal": "risk_signal_requires_review",
    "source_level": "field_proxy",
}


def build_r6_product_outcome_review(
    *,
    artifact_id: str,
    run_id: str,
    observed_outcome: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    observed_outcome = _normalize_observed_outcome(observed_outcome)
    review = {
        "schema_version": R6_PRODUCT_OUTCOME_REVIEW_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "outcome_review_ready_update_blocked",
        "observed_outcome": observed_outcome,
        "review_outputs": R6_PRODUCT_OUTCOME_REVIEW_OUTPUTS,
        "error_attribution": {
            "static_prior_error": (
                "requires later metric and source review before changing priors"
            ),
            "interaction_error": (
                "requires later metric and source review before changing "
                "interaction assumptions"
            ),
            "risk_signal_classification": (
                "candidate classification only until source audit and holdout"
            ),
        },
        "candidate_update": {
            "scope": "same_outcome_review_only",
            "allowed_use": "review_artifact_and_followup_measurement_plan",
            "blocked_use": "runtime_default_or_global_validation",
        },
        "update_gate": {
            "candidate_update_generated": True,
            "runtime_default_allowed": False,
            "requires_holdout_before_default": True,
        },
        "risk_flags": [
            "same_outcome_review_not_global_validation",
            "field_or_proxy_source_requires_audit",
        ],
        "source_refs": [observed_outcome["outcome_id"]],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(review)
    return review


def _normalize_observed_outcome(
    observed_outcome: dict[str, Any] | None,
) -> dict[str, str]:
    if observed_outcome is None:
        observed_outcome = _DEFAULT_OBSERVED_OUTCOME
    if not isinstance(observed_outcome, dict):
        raise ValueError("observed_outcome must be an object")
    return {
        "outcome_id": non_empty_string(
            observed_outcome.get("outcome_id"),
            field="observed_outcome.outcome_id",
        ),
        "measurement_window": non_empty_string(
            observed_outcome.get("measurement_window"),
            field="observed_outcome.measurement_window",
        ),
        "observed_signal": non_empty_string(
            observed_outcome.get("observed_signal"),
            field="observed_outcome.observed_signal",
        ),
        "source_level": non_empty_string(
            observed_outcome.get("source_level"),
            field="observed_outcome.source_level",
        ),
    }


def write_r6_product_outcome_review(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_outcome_review(**kwargs))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r6_product_outcome_review(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    review = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": review["artifact_id"],
                "output": str(output_path),
                "status": review["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
