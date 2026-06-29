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
from experiments.r6_decision_value_metrics import build_r6_decision_value_metrics


R6_RISK_DISCOVERY_HOLDOUT_VALIDATION_SCHEMA_VERSION = (
    "r6-risk-discovery-holdout-validation-v1"
)


def build_r6_risk_discovery_holdout_validation(
    *,
    artifact_id: str,
    run_id: str,
    decision_value_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    decision_value_metrics = decision_value_metrics or build_r6_decision_value_metrics(
        artifact_id=f"{artifact_id}-decision-value-metrics",
        run_id=run_id,
    )
    cases = {
        case["source_key"]: case
        for case in decision_value_metrics["case_results"]
    }
    trials = [
        _same_family_trial(
            source=cases["anes_health_heldout"],
            holdout=cases["anes_climate_heldout"],
        ),
        _same_family_trial(
            source=cases["anes_climate_heldout"],
            holdout=cases["anes_health_heldout"],
        ),
    ]
    summary = _summary(trials)
    passed = summary["passed_trial_count"] > 0
    report = {
        "schema_version": R6_RISK_DISCOVERY_HOLDOUT_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "risk_discovery_holdout_passed"
            if passed
            else "risk_discovery_holdout_failed_current_public_proxies"
        ),
        "validation_protocol": {
            "source_rule": (
                "Freeze an interaction-delta risk flag from the source case; "
                "evaluate the frozen flag on same-family holdout outcomes."
            ),
            "holdout_outcome_used_for_rule_derivation": False,
            "same_family_axis": "target_case_id",
        },
        "summary": summary,
        "holdout_trials": trials,
        "acceptance_gates": {
            "risk_discovery_holdout_validation_present": True,
            "frozen_rule_has_no_holdout_outcome_leakage": True,
            "same_family_holdout_available": bool(trials),
            "positive_source_signal_available": any(
                trial["source_signal_supported"] for trial in trials
            ),
            "passed_same_family_holdout_count_positive": passed,
            "risk_discovery_holdout_passed": passed,
            "field_outcome_validated": False,
        },
        "source_refs": [decision_value_metrics["artifact_id"]],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            "Risk-discovery holdout validation tests frozen risk flags; it is not field validation.",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "current_same_family_public_holdouts_do_not_validate_risk_discovery",
            "not_field_validation",
        ],
        "blocking_gaps": [] if passed else [
            "needs_positive_same_family_source_signal",
            "needs_lower_false_alarm_rate",
            "needs_field_outcome_validation",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_risk_discovery_holdout_validation(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r6_risk_discovery_holdout_validation(**kwargs),
    )


def _same_family_trial(
    *,
    source: dict[str, Any],
    holdout: dict[str, Any],
) -> dict[str, Any]:
    source_supported = (
        source["interaction_flags_new_risk"] and source["observed_high_risk"]
    )
    holdout_supported = (
        holdout["interaction_flags_new_risk"] and holdout["observed_high_risk"]
    )
    if not source_supported:
        status = "source_signal_not_supported"
    elif holdout_supported:
        status = "passed"
    else:
        status = "failed_holdout_not_supported"
    return {
        "trial_id": f"risk-discovery:{source['source_key']}->{holdout['source_key']}",
        "validation_status": status,
        "same_family": source["target_case_id"] == holdout["target_case_id"],
        "source_case": {
            "source_key": source["source_key"],
            "target_case_id": source["target_case_id"],
            "interaction_flags_new_risk": source["interaction_flags_new_risk"],
            "observed_high_risk": source["observed_high_risk"],
            "source_signal_supported": source_supported,
        },
        "holdout_case": {
            "source_key": holdout["source_key"],
            "target_case_id": holdout["target_case_id"],
            "interaction_flags_new_risk": holdout["interaction_flags_new_risk"],
            "observed_high_risk": holdout["observed_high_risk"],
            "holdout_signal_supported": holdout_supported,
        },
        "source_signal_supported": source_supported,
        "holdout_signal_supported": holdout_supported,
        "holdout_outcome_used_for_rule_derivation": False,
    }


def _summary(trials: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "trial_count": len(trials),
        "same_family_trial_count": sum(1 for trial in trials if trial["same_family"]),
        "passed_trial_count": sum(
            1 for trial in trials if trial["validation_status"] == "passed"
        ),
        "failed_trial_count": sum(
            1
            for trial in trials
            if trial["validation_status"] != "passed"
        ),
        "condition_not_met_count": sum(
            1
            for trial in trials
            if trial["validation_status"] == "source_signal_not_supported"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_risk_discovery_holdout_validation(
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
                "risk_discovery_holdout_passed": report["acceptance_gates"][
                    "risk_discovery_holdout_passed"
                ],
                "status": report["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
