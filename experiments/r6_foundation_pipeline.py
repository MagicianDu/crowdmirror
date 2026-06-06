from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import R6_CLAIM_BOUNDARY, assert_strict_json, non_empty_string, write_json_artifact
from experiments.r6_interaction_trace import build_r6_interaction_trace
from experiments.r6_learning_report import build_r6_learning_report
from experiments.r6_outcome_manifest import build_r6_outcome_manifest
from experiments.r6_prior_manifest import build_r6_prior_manifest
from experiments.r6_risk_shift_report import build_r6_risk_shift_report
from experiments.r6_scenario_manifest import build_r6_scenario_manifest
from experiments.r6_update_registry import build_r6_update_registry


R6_FOUNDATION_PACKAGE_SCHEMA_VERSION = "r6-foundation-package-v1"


def build_r6_foundation_pipeline(
    *,
    artifact_id: str,
    run_id: str,
    case_template: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    template = case_template or {}
    prior = build_r6_prior_manifest(
        artifact_id=f"{artifact_id}-prior",
        run_id=run_id,
        segments=template.get("prior_segments"),
    )
    scenario = build_r6_scenario_manifest(
        artifact_id=f"{artifact_id}-scenario",
        run_id=run_id,
        scenario=template.get("scenario"),
    )
    trace = build_r6_interaction_trace(
        artifact_id=f"{artifact_id}-interaction",
        run_id=run_id,
        prior_manifest=prior,
        scenario_manifest=scenario,
        interaction_profile=template.get("interaction_profile"),
    )
    risk = build_r6_risk_shift_report(
        artifact_id=f"{artifact_id}-risk-shift",
        run_id=run_id,
        prior_manifest=prior,
        interaction_trace=trace,
    )
    outcome = build_r6_outcome_manifest(
        artifact_id=f"{artifact_id}-outcome",
        run_id=run_id,
        outcome=template.get("outcome"),
    )
    learning = build_r6_learning_report(
        artifact_id=f"{artifact_id}-learning",
        run_id=run_id,
        risk_shift_report=risk,
        outcome_manifest=outcome,
    )
    registry = build_r6_update_registry(
        artifact_id=f"{artifact_id}-update-registry",
        run_id=run_id,
        learning_report=learning,
    )
    package = {
        "schema_version": R6_FOUNDATION_PACKAGE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "diagnostic_ready",
        "case_id": template.get("case_id", "generic-price-change"),
        "case_type": template.get("case_type", "price_change"),
        "industry_binding": template.get("industry_binding", "generic"),
        "public_outcome_proxy_artifact_id": template.get("public_outcome_proxy_artifact_id"),
        "prior_manifest": prior,
        "scenario_manifest": scenario,
        "interaction_trace": trace,
        "risk_shift_report": risk,
        "outcome_manifest": outcome,
        "learning_report": learning,
        "update_registry": registry,
        "claim_boundaries": [R6_CLAIM_BOUNDARY],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "not_accuracy_superiority_evidence",
            "unvalidated_update_not_enabled",
        ],
    }
    assert_strict_json(package)
    return package


def write_r6_foundation_pipeline(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_foundation_pipeline(**kwargs))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_foundation_pipeline(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    package = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": package["artifact_id"],
                "output": str(output_path),
                "status": package["status"],
                "update_status": package["update_registry"]["overall_status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
