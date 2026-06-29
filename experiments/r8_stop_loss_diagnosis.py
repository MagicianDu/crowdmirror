from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact
from experiments.r8_baseline_comparison import build_r8_baseline_comparison
from experiments.r8_learnable_mechanism_simulation import R8_CLAIM_BOUNDARY
from experiments.r8_robustness_holdout_gate import build_r8_robustness_holdout_gate


R8_STOP_LOSS_DIAGNOSIS_SCHEMA_VERSION = "r8-stop-loss-diagnosis-v1"


def build_r8_stop_loss_diagnosis(
    *,
    artifact_id: str,
    run_id: str,
    baseline_comparison: dict[str, Any] | None = None,
    robustness_holdout_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    baseline = baseline_comparison or build_r8_baseline_comparison(
        artifact_id=f"{artifact_id}-baseline-comparison",
        run_id=run_id,
    )
    robustness = robustness_holdout_gate or build_r8_robustness_holdout_gate(
        artifact_id=f"{artifact_id}-robustness-holdout-gate",
        run_id=run_id,
    )
    r8_winning_metrics = [
        metric
        for metric, winner in baseline["winner_by_metric"].items()
        if winner["method"] == "r8_main_learnable_mechanism"
    ]
    research_decision = robustness["stop_loss_recommendation"]
    root_causes = _root_causes(
        baseline=baseline,
        robustness=robustness,
        r8_winning_metrics=r8_winning_metrics,
    )
    report = {
        "schema_version": R8_STOP_LOSS_DIAGNOSIS_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r8_stop_loss_diagnosis_ready",
        "research_decision": research_decision,
        "product_decision": {
            "display_level": "diagnostic_only",
            "customer_visible_use": "failure_diagnosis_and_outcome_replay",
            "product_core_method_claim_allowed": False,
        },
        "evidence_summary": {
            "baseline_status": baseline["status"],
            "robustness_status": robustness["status"],
            "baseline_stop_loss_recommendation": baseline[
                "stop_loss_recommendation"
            ],
            "robustness_stop_loss_recommendation": robustness[
                "stop_loss_recommendation"
            ],
            "r8_metric_win_count": len(r8_winning_metrics),
            "r8_winning_metrics": r8_winning_metrics,
            "total_compared_metrics": len(baseline["winner_by_metric"]),
            "l1_status": robustness["l1_status"],
            "l2_status": robustness["l2_status"],
            "perturbation_pass_rate": robustness["summary"][
                "perturbation_pass_rate"
            ],
            "leave_one_non_regression_rate": robustness["summary"][
                "leave_one_non_regression_rate"
            ],
        },
        "root_causes": root_causes,
        "diagnosis": [
            {
                "cause_id": "not_beating_fixed_rule_baseline",
                "evidence": (
                    "R8 wins only risk_ranking_quality; R7 v2 or R6/static "
                    "baselines still win trend, interval, false alarm, and "
                    "static-miss recovery metrics."
                ),
                "implication": (
                    "R8 cannot be claimed as a stronger Product core method."
                ),
            },
            {
                "cause_id": "l1_l2_gate_blocked",
                "evidence": (
                    f"L1={robustness['l1_status']}, L2={robustness['l2_status']}."
                ),
                "implication": (
                    "Robustness evidence can be shown as diagnostic guard output, "
                    "not as runtime authorization."
                ),
            },
            {
                "cause_id": "field_customer_outcome_missing",
                "evidence": "field_outcome_validated=false in all R8 gates.",
                "implication": (
                    "Product can use R8 for failure diagnosis and outcome replay, "
                    "but not field-validated claims."
                ),
            },
        ],
        "recommended_next_tracks": [
            {
                "track_id": "research_stronger_learnable_operator",
                "goal": (
                    "replace fixed current-proxy heuristics with a stronger "
                    "transferable mechanism learner"
                ),
                "entry_condition": (
                    "new operator must beat R7 v2 on more than one metric and "
                    "pass L1 gate"
                ),
            },
            {
                "track_id": "field_or_customer_outcome",
                "goal": (
                    "collect or ingest real outcome evidence that can validate "
                    "trend, interval, ranking, and false-alarm control"
                ),
                "entry_condition": (
                    "at least one field/customer outcome has aligned scenario, "
                    "segment, and mechanism trace"
                ),
            },
            {
                "track_id": "product_failure_diagnosis_hardening",
                "goal": (
                    "turn blocked R8 evidence into customer-facing risk boundary, "
                    "replay, and learning workflow"
                ),
                "entry_condition": (
                    "all blocked claims remain source-backed and runtime-default false"
                ),
            },
        ],
        "acceptance_gates": {
            "stop_loss_diagnosis_present": True,
            "product_diagnostic_ingestion_allowed": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [baseline["artifact_id"], robustness["artifact_id"]],
        "allowed_claims": [
            "R8 stop-loss diagnosis can explain why R8 is diagnostic-only.",
            "Product may display R8 as failure diagnosis and outcome replay evidence.",
        ],
        "blocked_claims": [
            "R8 validated",
            "runtime default ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "accuracy superiority",
        ],
        "claim_boundary": R8_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def _root_causes(
    *,
    baseline: dict[str, Any],
    robustness: dict[str, Any],
    r8_winning_metrics: list[str],
) -> list[str]:
    causes = []
    if baseline["stop_loss_recommendation"] != "continue_to_holdout_validation":
        causes.append("not_beating_fixed_rule_baseline")
    if len(r8_winning_metrics) <= 1:
        causes.append("insufficient_metric_dominance")
    if (
        robustness["l1_status"] != "passed_guarded"
        or robustness["l2_status"] != "passed_guarded"
    ):
        causes.append("l1_l2_gate_blocked")
    if robustness["acceptance_gates"]["field_outcome_validated"] is False:
        causes.append("field_customer_outcome_missing")
    if robustness["acceptance_gates"]["runtime_default_allowed"] is False:
        causes.append("runtime_default_guard_blocked")
    return causes


def write_r8_stop_loss_diagnosis(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r8_stop_loss_diagnosis(**kwargs))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-id", default="r8-stop-loss-diagnosis-current-001")
    parser.add_argument("--run-id", default="r8-stop-loss-diagnosis-current")
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/r8_stop_loss_diagnosis/"
            "r8-stop-loss-diagnosis-current-001.json"
        ),
    )
    args = parser.parse_args()
    output = write_r8_stop_loss_diagnosis(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    artifact = build_r8_stop_loss_diagnosis(
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "output": str(output),
                "research_decision": artifact["research_decision"],
                "status": artifact["status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
