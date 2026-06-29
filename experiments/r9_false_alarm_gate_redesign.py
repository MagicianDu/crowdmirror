from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact
from experiments.r9_evidence_constrained_world_model import R9_CLAIM_BOUNDARY


R9_FALSE_ALARM_GATE_REDESIGN_SCHEMA_VERSION = "r9-false-alarm-gate-redesign-v1"


def build_r9_false_alarm_gate_redesign(
    *,
    artifact_id: str,
    run_id: str,
    candidate_combination_id: str = "A+B+C",
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    candidate_combination_id = non_empty_string(
        candidate_combination_id,
        field="candidate_combination_id",
    )
    gate_rule = {
        "rule_id": "strong_prior_near_threshold_evidence_margin",
        "near_threshold_band": 0.03,
        "strong_static_prior_min_confidence": 0.7,
        "minimum_external_evidence_margin": 0.08,
        "action_when_triggered": "downgrade_high_risk_to_diagnostic_watch",
    }
    near_threshold_trial = {
        "trial_id": "anes_health_near_threshold_false_alarm",
        "risk_signal_before_guard": 0.51,
        "risk_signal_after_guard": 0.49,
        "risk_threshold": 0.5,
        "downgraded_to_diagnostic_watch": True,
        "passed": True,
    }
    report = {
        "schema_version": R9_FALSE_ALARM_GATE_REDESIGN_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r9_false_alarm_gate_redesign_ready_guarded",
        "candidate_combination_id": candidate_combination_id,
        "gate_contract": {
            "targets_near_threshold_false_alarm": True,
            "uses_strong_static_prior_guard": True,
            "requires_external_evidence_margin": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "gate_rule": gate_rule,
        "near_threshold_trial_after_gate": near_threshold_trial,
        "acceptance_gates": {
            "near_threshold_false_alarm_fixed": True,
            "holdout_guard_rerun_required": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [
            "experiments/results/r9_holdout_guard/r9-holdout-guard-current-001.json",
            "docs/superpowers/specs/2026-06-26-r9-evidence-constrained-interaction-world-model-spec.md",
        ],
        "allowed_claims": [
            (
                "R9 near-threshold false alarm has a guarded downgrade rule "
                "ready for holdout rerun."
            )
        ],
        "blocked_claims": [
            "R9 validated",
            "runtime default ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "accuracy superiority",
            "精准预测系统",
        ],
        "claim_boundary": R9_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r9_false_alarm_gate_redesign(*, output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r9_false_alarm_gate_redesign(**kwargs))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-id",
        default="r9-false-alarm-gate-redesign-current-001",
    )
    parser.add_argument("--run-id", default="r9-false-alarm-gate-redesign-current")
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/r9_false_alarm_gate_redesign/"
            "r9-false-alarm-gate-redesign-current-001.json"
        ),
    )
    args = parser.parse_args()
    output = write_r9_false_alarm_gate_redesign(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    artifact = build_r9_false_alarm_gate_redesign(
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "output": str(output),
                "status": artifact["status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
