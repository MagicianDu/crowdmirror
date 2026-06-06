from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_ablation_report import build_r6_ablation_report
from experiments.r6_contracts import R6_CLAIM_BOUNDARY, assert_strict_json, non_empty_string, write_json_artifact
from experiments.r6_public_outcome_proxy import build_r6_public_outcome_proxy


R6_FAILURE_BOUNDARY_REPORT_SCHEMA_VERSION = "r6-failure-boundary-report-v1"


def build_r6_failure_boundary_report(
    *,
    artifact_id: str,
    run_id: str,
    public_outcome_proxy: dict[str, Any] | None = None,
    ablation_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    proxy = public_outcome_proxy or build_r6_public_outcome_proxy(
        artifact_id=f"{artifact_id}-anes-health-proxy",
        run_id=run_id,
        source_key="anes_health_heldout",
    )
    ablation = ablation_report or build_r6_ablation_report(
        artifact_id=f"{artifact_id}-anes-health-ablation",
        run_id=run_id,
        public_outcome_proxy=proxy,
    )
    by_method = {result["method"]: result for result in ablation["baseline_results"]}
    no_interaction = by_method["no_interaction_prior"]
    prior_anchored = by_method["prior_anchored_interaction"]
    failure_boundary = {
        "failure_type": "interaction_over_amplifies_rejection_risk",
        "observed_reject_proxy": proxy["metrics"]["observed_reject_proxy"],
        "no_interaction_prediction": no_interaction["mean_prediction"],
        "prior_anchored_prediction": prior_anchored["mean_prediction"],
        "no_interaction_error": no_interaction["mean_absolute_error"],
        "prior_anchored_error": prior_anchored["mean_absolute_error"],
        "regression_delta": round(
            prior_anchored["mean_absolute_error"] - no_interaction["mean_absolute_error"],
            2,
        ),
    }
    report = {
        "schema_version": R6_FAILURE_BOUNDARY_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "failure_boundary_ready",
        "target_case_id": proxy["target_case_id"],
        "source_proxy_key": proxy["source_key"],
        "source_public_outcome_proxy_id": proxy["artifact_id"],
        "source_ablation_report_id": ablation["artifact_id"],
        "failure_boundary": failure_boundary,
        "diagnosis": {
            "primary_hypothesis": (
                "rights/rule interaction profile imported too much rejection amplification "
                "for ANES health heldout segments where the static prior is already close."
            ),
            "suspect_mechanisms": [
                "rights_loss_salience",
                "peer_amplification",
                "trust_shock",
            ],
            "evidence": [
                "no_interaction_prior is closer to the ANES heldout reject proxy",
                "prior_anchored_interaction increases rejection from 0.31 to 0.38",
                "observed reject proxy is 0.33, so the interaction shift overshoots",
            ],
        },
        "recommended_update": {
            "status": "diagnostic_only",
            "default_runtime_enabled": False,
            "target_change": (
                "shrink rights/rule rejection amplification when static prior error is already low"
            ),
            "candidate_rule": {
                "condition": "static_prior_absolute_error <= 0.03 on public proxy",
                "action": "cap aggregate reject delta at 0.02 before holdout validation",
            },
            "acceptance_requirement": (
                "requires follow-up or cross-proxy holdout case without regression"
            ),
        },
        "source_refs": [
            proxy["artifact_id"],
            ablation["artifact_id"],
            proxy["public_source"]["source_artifact_id"],
        ],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            "Failure boundary is diagnostic only and not a global method update.",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "same_case_proxy_not_global_update",
            "public_proxy_not_field_validation",
            "interaction_mechanism_regression_boundary",
        ],
        "blocking_gaps": [
            "needs_follow_up_case_for_update_acceptance",
            "needs_mechanism_cap_ablation_before_runtime_default",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_failure_boundary_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_failure_boundary_report(**kwargs))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_failure_boundary_report(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "failure_type": report["failure_boundary"]["failure_type"],
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
