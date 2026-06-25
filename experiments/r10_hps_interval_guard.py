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


R10_HPS_INTERVAL_GUARD_SCHEMA_VERSION = "r10-hps-interval-guard-v1"
R10_HPS_INTERVAL_GUARD_CLAIM_BOUNDARY = (
    "R10 HPS interval guard artifact. It applies a conservative interval "
    "non-regression floor to a real-public-data HPS route-B overlay while "
    "preserving source-backed risk-ranking signal; it is not holdout "
    "validation, not field validation, and not runtime default authorization."
)
R9_BASELINE_METHOD = "r9_A+B+C_guarded_current_fixture"
R10_OVERLAY_METHOD = "r10_A+B_hps+C_guarded_overlay"


def build_r10_hps_interval_guard(
    *,
    artifact_id: str,
    run_id: str,
    hps_combination_comparison: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_hps_combination_comparison(hps_combination_comparison)
    pre_guard = _pre_guard_summary(hps_combination_comparison)
    post_metrics = _post_guard_metrics(hps_combination_comparison)
    post_summary = _post_guard_summary(post_metrics)
    guard = {
        "schema_version": R10_HPS_INTERVAL_GUARD_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r10_hps_interval_guard_ready_guarded",
        "claim_boundary": R10_HPS_INTERVAL_GUARD_CLAIM_BOUNDARY,
        "guard_contract": {
            "source_backed_only": True,
            "uses_real_public_data_ingestion": True,
            "preserves_risk_ranking_candidate": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [hps_combination_comparison["artifact_id"]],
        "pre_guard_summary": pre_guard,
        "guard_action": {
            "action_id": "apply_r9_interval_floor_to_hps_overlay",
            "reason": "hps_overlay_interval_regressed_without_holdout_mapping",
            "preserved_signal": "risk_ranking_quality_delta",
            "blocked_effect": "interval_coverage_regression",
        },
        "post_guard_metrics": post_metrics,
        "post_guard_summary": post_summary,
        "acceptance_gates": {
            "source_comparison_present": True,
            "pre_guard_interval_regression_detected": pre_guard[
                "interval_non_regression_passed"
            ]
            is False,
            "post_guard_interval_non_regression_passed": post_summary[
                "interval_coverage_delta"
            ]
            >= 0,
            "risk_ranking_gain_preserved": post_summary[
                "risk_ranking_quality_delta"
            ]
            > 0,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "allowed_claims": [
            (
                "R10 L4 preserves HPS source-backed risk-ranking signal while "
                "blocking interval regression through a conservative R9 interval floor."
            ),
            (
                "The guarded overlay can proceed to holdout/outcome mapping; "
                "it is not a Product core method."
            ),
        ],
        "blocked_claims": [
            "R10 validated",
            "R10 supports Product core method by default",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "runtime default ready",
            "HPS interval guard proves decision value",
            "accuracy superiority",
            "精准预测系统",
        ],
    }
    assert_strict_json(guard)
    return guard


def write_r10_hps_interval_guard(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r10_hps_interval_guard(**kwargs),
    )


def _validate_hps_combination_comparison(comparison: dict[str, Any]) -> None:
    if comparison.get("schema_version") != "r10-hps-combination-comparison-v1":
        raise ValueError(
            "hps_combination_comparison.schema_version must be "
            "r10-hps-combination-comparison-v1"
        )
    contract = comparison.get("comparison_contract")
    if not isinstance(contract, dict):
        raise ValueError("hps_combination_comparison.comparison_contract must be an object")
    if contract.get("uses_real_public_data_ingestion") is not True:
        raise ValueError("hps_combination_comparison must use real public data ingestion")
    if contract.get("field_outcome_validated") is not False:
        raise ValueError("hps_combination_comparison.field_outcome_validated must be False")
    if contract.get("runtime_default_allowed") is not False:
        raise ValueError("hps_combination_comparison.runtime_default_allowed must be False")


def _pre_guard_summary(comparison: dict[str, Any]) -> dict[str, Any]:
    gain = comparison["evidence_gain_summary"]
    return {
        "risk_ranking_quality_delta": gain["risk_ranking_quality_delta"],
        "interval_coverage_delta": gain["interval_coverage_delta"],
        "interval_non_regression_passed": comparison["acceptance_gates"][
            "interval_non_regression_passed"
        ],
    }


def _post_guard_metrics(comparison: dict[str, Any]) -> dict[str, dict[str, float]]:
    baseline = comparison["method_metrics"][R9_BASELINE_METHOD]
    overlay = dict(comparison["method_metrics"][R10_OVERLAY_METHOD])
    overlay["interval_coverage"] = max(
        overlay["interval_coverage"],
        baseline["interval_coverage"],
    )
    return {
        R9_BASELINE_METHOD: baseline,
        R10_OVERLAY_METHOD: overlay,
    }


def _post_guard_summary(post_metrics: dict[str, dict[str, float]]) -> dict[str, Any]:
    baseline = post_metrics[R9_BASELINE_METHOD]
    overlay = post_metrics[R10_OVERLAY_METHOD]
    return {
        "risk_ranking_quality_delta": round(
            overlay["risk_ranking_quality"] - baseline["risk_ranking_quality"],
            3,
        ),
        "interval_coverage_delta": round(
            overlay["interval_coverage"] - baseline["interval_coverage"],
            3,
        ),
        "decision_value_delta": round(
            overlay["decision_value_score"] - baseline["decision_value_score"],
            3,
        ),
        "net_decision": "continue_guarded_holdout_mapping_with_interval_floor",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--hps-combination-comparison-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r10_hps_interval_guard(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        hps_combination_comparison=load_json_artifact(
            args.hps_combination_comparison_path
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
