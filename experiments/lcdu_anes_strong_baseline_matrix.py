from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STRONG_BASELINE_SCHEMA_VERSION = "lcdu-anes-strong-baseline-matrix-v1"
BASELINE_FAMILY_SCHEMA_VERSION = "lcdu-anes-baseline-family-matrix-v1"
LLM_VALIDATION_SCHEMA_VERSION = "lcdu-anes-llm-simulator-validation-v1"
CROSS_TASK_VALIDATION_SCHEMA_VERSION = "lcdu-anes-cross-task-validation-v1"

DEFAULT_REQUIRED_BASELINE_FAMILIES = [
    "llm_raw_prompt",
    "llm_aggregate_anchor",
    "deterministic_anchor_search",
    "textgrad_or_prompt_optimizer",
    "population_search",
]


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_lcdu_anes_strong_baseline_matrix(
    *,
    artifact_id: str,
    llm_validation_artifacts: list[dict[str, Any]],
    anchor_validation_artifacts: list[dict[str, Any]],
    baseline_family_artifacts: list[dict[str, Any]] | None = None,
    required_baseline_families: list[str] | None = None,
    lcdU_method_id: str = "lcdu_segment_anchor_prompt",
) -> dict[str, Any]:
    required = required_baseline_families or DEFAULT_REQUIRED_BASELINE_FAMILIES
    baseline_family_artifacts = baseline_family_artifacts or []
    for artifact in llm_validation_artifacts:
        _validate_llm_validation_artifact(artifact)
    for artifact in anchor_validation_artifacts:
        _validate_anchor_validation_artifact(artifact)
    for artifact in baseline_family_artifacts:
        _validate_baseline_family_artifact(artifact)

    task_results = _task_results(
        llm_validation_artifacts=llm_validation_artifacts,
        anchor_validation_artifacts=anchor_validation_artifacts,
        baseline_family_artifacts=baseline_family_artifacts,
        lcdU_method_id=lcdU_method_id,
    )
    covered_families = sorted(
        {
            candidate["baseline_family"]
            for task in task_results.values()
            for candidate in task["covered_baselines"]
        }
    )
    missing_families = sorted(set(required) - set(covered_families))
    lcdU_leads = bool(task_results) and all(
        result["lcdU_leads_covered_baselines"] for result in task_results.values()
    )
    artifact = {
        "schema_version": STRONG_BASELINE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            lcdU_leads=lcdU_leads,
            missing_families=missing_families,
        ),
        "validation_type": "lcdu_strong_baseline_matrix",
        "lcdU_method_id": lcdU_method_id,
        "required_baseline_families": required,
        "covered_baseline_families": covered_families,
        "missing_baseline_families": missing_families,
        "lcdU_leads_covered_baselines": lcdU_leads,
        "task_results": task_results,
        "source_artifact_ids": [
            artifact["artifact_id"]
            for artifact in [
                *llm_validation_artifacts,
                *anchor_validation_artifacts,
                *baseline_family_artifacts,
            ]
        ],
        "llm_accounting": _llm_accounting(llm_validation_artifacts),
        "risk_flags": _risk_flags(
            lcdU_leads=lcdU_leads,
            missing_families=missing_families,
        ),
        "claim_boundary": (
            "This artifact compares LCDU against the baseline families covered by "
            "the provided ANES artifacts under the same split-gated test-loss "
            "contract. Missing baseline families remain explicit blockers and "
            "must not be silently treated as passed."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_lcdu_anes_strong_baseline_matrix(
    output: str | Path,
    *,
    artifact_id: str,
    llm_validation_artifact_paths: list[str | Path],
    anchor_validation_artifact_paths: list[str | Path],
    baseline_family_artifact_paths: list[str | Path] | None = None,
    required_baseline_families: list[str] | None = None,
    lcdU_method_id: str,
) -> dict[str, Any]:
    baseline_family_artifact_paths = baseline_family_artifact_paths or []
    artifact = build_lcdu_anes_strong_baseline_matrix(
        artifact_id=artifact_id,
        llm_validation_artifacts=[
            load_json_artifact(path) for path in llm_validation_artifact_paths
        ],
        anchor_validation_artifacts=[
            load_json_artifact(path) for path in anchor_validation_artifact_paths
        ],
        baseline_family_artifacts=[
            load_json_artifact(path) for path in baseline_family_artifact_paths
        ],
        required_baseline_families=required_baseline_families,
        lcdU_method_id=lcdU_method_id,
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"output_path": str(output_path), "artifact": artifact}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm-validation-artifacts", nargs="+", required=True)
    parser.add_argument("--anchor-validation-artifacts", nargs="+", required=True)
    parser.add_argument("--baseline-family-artifacts", nargs="*", default=[])
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/lcdu_strong_baseline/"
            "lcdu-anes-strong-baseline-matrix-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-anes-strong-baseline-matrix-current-001",
    )
    parser.add_argument(
        "--required-baseline-families",
        nargs="+",
        default=DEFAULT_REQUIRED_BASELINE_FAMILIES,
    )
    parser.add_argument("--lcdu-method-id", default="lcdu_segment_anchor_prompt")
    args = parser.parse_args()
    written = write_lcdu_anes_strong_baseline_matrix(
        args.output,
        artifact_id=args.artifact_id,
        llm_validation_artifact_paths=args.llm_validation_artifacts,
        anchor_validation_artifact_paths=args.anchor_validation_artifacts,
        baseline_family_artifact_paths=args.baseline_family_artifacts,
        required_baseline_families=args.required_baseline_families,
        lcdU_method_id=args.lcdu_method_id,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "lcdU_leads_covered_baselines": artifact[
                    "lcdU_leads_covered_baselines"
                ],
                "missing_baseline_family_count": len(
                    artifact["missing_baseline_families"]
                ),
                "output": written["output_path"],
                "status": artifact["overall_status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_llm_validation_artifact(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != LLM_VALIDATION_SCHEMA_VERSION:
        raise ValueError("llm validation artifact has unsupported schema")
    if artifact.get("validation_type") != "split_gated_llm_segment_simulator_smoke":
        raise ValueError("llm validation artifact has unsupported validation_type")
    if not isinstance(artifact.get("task_results"), dict):
        raise ValueError("llm validation artifact missing task_results")


def _validate_anchor_validation_artifact(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != CROSS_TASK_VALIDATION_SCHEMA_VERSION:
        raise ValueError("anchor validation artifact has unsupported schema")
    if artifact.get("validation_type") != "split_gated_segment_anchor_transfer_smoke":
        raise ValueError("anchor validation artifact has unsupported validation_type")
    if not isinstance(artifact.get("task_results"), dict):
        raise ValueError("anchor validation artifact missing task_results")


def _validate_baseline_family_artifact(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != BASELINE_FAMILY_SCHEMA_VERSION:
        raise ValueError("baseline family artifact has unsupported schema")
    if artifact.get("validation_type") != "lcdu_baseline_family_matrix":
        raise ValueError("baseline family artifact has unsupported validation_type")
    if not isinstance(artifact.get("task_results"), dict):
        raise ValueError("baseline family artifact missing task_results")


def _task_results(
    *,
    llm_validation_artifacts: list[dict[str, Any]],
    anchor_validation_artifacts: list[dict[str, Any]],
    baseline_family_artifacts: list[dict[str, Any]],
    lcdU_method_id: str,
) -> dict[str, Any]:
    task_ids = sorted(
        {
            task_id
            for artifact in llm_validation_artifacts
            for task_id in artifact.get("task_results", {})
        }
    )
    results = {}
    for task_id in task_ids:
        lcdU_candidates = [
            {
                "source_artifact_id": artifact["artifact_id"],
                "heldout_loss": float(heldout_loss),
                "test_loss": float(test_loss),
            }
            for artifact in llm_validation_artifacts
            if task_id in artifact.get("task_results", {})
            for heldout_loss, test_loss in [
                (
                    artifact["task_results"][task_id]
                    .get("heldout", {})
                    .get("loss_by_method", {})
                    .get(lcdU_method_id),
                    artifact["task_results"][task_id]
                    .get("test", {})
                    .get("loss_by_method", {})
                    .get(lcdU_method_id),
                )
            ]
            if isinstance(heldout_loss, (int, float))
            and isinstance(test_loss, (int, float))
        ]
        if not lcdU_candidates:
            continue
        selected_lcdU = min(
            lcdU_candidates,
            key=lambda candidate: candidate["heldout_loss"],
        )
        lcdU_test_loss = selected_lcdU["test_loss"]
        covered_baselines = []
        for artifact in llm_validation_artifacts:
            task = artifact.get("task_results", {}).get(task_id)
            if task is None:
                continue
            losses = task.get("test", {}).get("loss_by_method", {})
            _append_loss(
                covered_baselines,
                baseline_family="llm_raw_prompt",
                method_id="raw_prompt",
                source_artifact_id=artifact["artifact_id"],
                loss=losses.get("raw_prompt"),
            )
            _append_loss(
                covered_baselines,
                baseline_family="llm_aggregate_anchor",
                method_id="aggregate_anchor_prompt",
                source_artifact_id=artifact["artifact_id"],
                loss=losses.get("aggregate_anchor_prompt"),
            )
        for artifact in anchor_validation_artifacts:
            task = artifact.get("task_results", {}).get(task_id)
            if task is None:
                continue
            losses = task.get("test", {}).get("loss_by_method", {})
            for method_id, loss in losses.items():
                _append_loss(
                    covered_baselines,
                    baseline_family="deterministic_anchor_search",
                    method_id=method_id,
                    source_artifact_id=artifact["artifact_id"],
                    loss=loss,
                )
        for artifact in baseline_family_artifacts:
            task = artifact.get("task_results", {}).get(task_id)
            if task is None:
                continue
            for baseline in task.get("baseline_results", []):
                if not isinstance(baseline, dict):
                    continue
                _append_loss(
                    covered_baselines,
                    baseline_family=baseline.get("baseline_family"),
                    method_id=baseline.get("method_id"),
                    source_artifact_id=baseline.get(
                        "source_artifact_id",
                        artifact["artifact_id"],
                    ),
                    loss=baseline.get("test_loss"),
                )
        best_baseline = min(
            covered_baselines,
            key=lambda baseline: baseline["test_loss"],
        )
        results[task_id] = {
            "lcdU_test_loss": lcdU_test_loss,
            "best_covered_baseline_family": best_baseline["baseline_family"],
            "best_covered_baseline_method_id": best_baseline["method_id"],
            "best_covered_baseline_test_loss": best_baseline["test_loss"],
            "lcdU_leads_covered_baselines": (
                lcdU_test_loss < best_baseline["test_loss"]
            ),
            "lcdU_selected_source_artifact_id": selected_lcdU["source_artifact_id"],
            "lcdU_selected_heldout_loss": selected_lcdU["heldout_loss"],
            "covered_baselines": covered_baselines,
        }
    return results


def _append_loss(
    rows: list[dict[str, Any]],
    *,
    baseline_family: str,
    method_id: str,
    source_artifact_id: str,
    loss: Any,
) -> None:
    if not isinstance(loss, (int, float)):
        return
    rows.append(
        {
            "baseline_family": baseline_family,
            "method_id": method_id,
            "source_artifact_id": source_artifact_id,
            "test_loss": float(loss),
        }
    )


def _overall_status(*, lcdU_leads: bool, missing_families: list[str]) -> str:
    if not lcdU_leads:
        return "strong_baseline_lcdu_not_leading"
    if missing_families:
        return "strong_baseline_partial_lcdu_leads"
    return "strong_baseline_lcdu_leads"


def _llm_accounting(llm_validation_artifacts: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total_call_count": sum(
            artifact.get("llm_accounting", {}).get("total_call_count", 0)
            for artifact in llm_validation_artifacts
        ),
        "total_input_tokens": sum(
            artifact.get("llm_accounting", {}).get("total_input_tokens", 0)
            for artifact in llm_validation_artifacts
        ),
        "total_output_tokens": sum(
            artifact.get("llm_accounting", {}).get("total_output_tokens", 0)
            for artifact in llm_validation_artifacts
        ),
        "parse_failure_count": sum(
            artifact.get("llm_accounting", {}).get("parse_failure_count", 0)
            for artifact in llm_validation_artifacts
        ),
    }


def _risk_flags(*, lcdU_leads: bool, missing_families: list[str]) -> list[str]:
    flags = [
        "not_customer_field_validation",
    ]
    if missing_families:
        flags.append("strong_baseline_family_coverage_incomplete")
    if not lcdU_leads:
        flags.append("covered_baseline_exceeds_lcdu")
    return flags


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU ANES strong baseline matrix must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
