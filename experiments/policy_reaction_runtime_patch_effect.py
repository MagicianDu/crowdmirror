from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


POLICY_REACTION_RUNTIME_PATCH_EFFECT_SCHEMA_VERSION = (
    "policy-reaction-runtime-patch-effect-v1"
)
OFFICIAL_SEGMENT_BENCHMARK_SCHEMA_VERSION = (
    "policy-reaction-official-segment-benchmark-v1"
)
PROMPT_PATCH_GATE_SCHEMA_VERSION = "policy-reaction-prompt-patch-gate-v1"
PRODUCT_WORKFLOW_REPORT_SCHEMA_VERSION = "crowdmirror-policy-workflow-report-v1"
DEFAULT_LOSS_METRIC = "weighted_choice_distribution_jsd"
RUNTIME_PATCH_EFFECT_CLAIM_BOUNDARY = (
    "Runtime-patch effect is a held-out public-data alignment comparison; not field validation."
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_runtime_patch_effect(
    *,
    baseline_heldout_benchmark: dict[str, Any],
    runtime_patch_heldout_benchmark: dict[str, Any],
    prompt_patch_gate: dict[str, Any],
    product_workflow_report: dict[str, Any],
    artifact_id: str,
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> dict[str, Any]:
    _validate_official_heldout_benchmark(
        baseline_heldout_benchmark,
        label="baseline_heldout_benchmark",
    )
    _validate_official_heldout_benchmark(
        runtime_patch_heldout_benchmark,
        label="runtime_patch_heldout_benchmark",
    )
    _validate_same_heldout_target(
        baseline_heldout_benchmark,
        runtime_patch_heldout_benchmark,
    )
    _validate_prompt_patch_gate(prompt_patch_gate)
    _validate_product_workflow_report(product_workflow_report, prompt_patch_gate)

    baseline_loss = _benchmark_loss(baseline_heldout_benchmark, loss_metric)
    runtime_patch_loss = _benchmark_loss(runtime_patch_heldout_benchmark, loss_metric)
    absolute_delta = _round_float(baseline_loss - runtime_patch_loss)
    relative_reduction = (
        _round_float(absolute_delta / baseline_loss) if baseline_loss > 0 else None
    )
    overall_status = _overall_status(absolute_delta)
    artifact = {
        "schema_version": POLICY_REACTION_RUNTIME_PATCH_EFFECT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": overall_status,
        "loss_metric": loss_metric,
        "baseline_loss": _round_float(baseline_loss),
        "runtime_patch_loss": _round_float(runtime_patch_loss),
        "absolute_loss_delta": absolute_delta,
        "relative_loss_reduction": relative_reduction,
        "baseline_heldout_benchmark_artifact_id": baseline_heldout_benchmark[
            "artifact_id"
        ],
        "runtime_patch_heldout_benchmark_artifact_id": runtime_patch_heldout_benchmark[
            "artifact_id"
        ],
        "baseline_prediction_artifact_id": baseline_heldout_benchmark.get(
            "prediction_artifact_id"
        ),
        "runtime_patch_prediction_artifact_id": runtime_patch_heldout_benchmark.get(
            "prediction_artifact_id"
        ),
        "heldout_source_ingestion_artifact_id": baseline_heldout_benchmark[
            "source_ingestion_artifact_id"
        ],
        "prompt_patch_gate_artifact_id": prompt_patch_gate["artifact_id"],
        "accepted_candidate_id": prompt_patch_gate["accepted_candidate_id"],
        "product_runtime_run_id": product_workflow_report["source_run_id"],
        "source_split_contract": {
            "candidate_generation": prompt_patch_gate["source_split_contract"][
                "candidate_generation"
            ],
            "candidate_acceptance": prompt_patch_gate["source_split_contract"][
                "candidate_acceptance"
            ],
            "runtime_effect_evaluation": "heldout",
        },
        "coverage": {
            "baseline_coverage_rate": _coverage_rate(baseline_heldout_benchmark),
            "runtime_patch_coverage_rate": _coverage_rate(
                runtime_patch_heldout_benchmark
            ),
        },
        "risk_flags": _risk_flags(overall_status, product_workflow_report),
        "claim_boundary": RUNTIME_PATCH_EFFECT_CLAIM_BOUNDARY,
        "claim_boundaries": _claim_boundaries(
            baseline_heldout_benchmark,
            runtime_patch_heldout_benchmark,
            prompt_patch_gate,
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_policy_reaction_runtime_patch_effect(
    path: str | Path,
    *,
    baseline_heldout_benchmark_path: str | Path,
    runtime_patch_heldout_benchmark_path: str | Path,
    prompt_patch_gate_path: str | Path,
    product_workflow_report_path: str | Path,
    artifact_id: str,
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> Path:
    artifact = build_policy_reaction_runtime_patch_effect(
        baseline_heldout_benchmark=load_json_artifact(baseline_heldout_benchmark_path),
        runtime_patch_heldout_benchmark=load_json_artifact(
            runtime_patch_heldout_benchmark_path
        ),
        prompt_patch_gate=load_json_artifact(prompt_patch_gate_path),
        product_workflow_report=load_json_artifact(product_workflow_report_path),
        artifact_id=artifact_id,
        loss_metric=loss_metric,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--baseline-heldout-benchmark",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-heldout-001.json"
        ),
    )
    parser.add_argument(
        "--runtime-patch-heldout-benchmark",
        required=True,
    )
    parser.add_argument(
        "--prompt-patch-gate",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-prompt-patch-gate-gpt-oss-20b-12x3-calibration-split-heldout-001.json"
        ),
    )
    parser.add_argument("--product-workflow-report", required=True)
    parser.add_argument(
        "--artifact-id",
        default=(
            "policy-reaction-runtime-patch-effect-gpt-oss-20b-12x3-"
            "calibration-split-heldout-001"
        ),
    )
    parser.add_argument("--loss-metric", default=DEFAULT_LOSS_METRIC)
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-runtime-patch-effect-gpt-oss-20b-12x3-"
            "calibration-split-heldout-001.json"
        ),
    )
    args = parser.parse_args()
    output_path = write_policy_reaction_runtime_patch_effect(
        args.output,
        baseline_heldout_benchmark_path=args.baseline_heldout_benchmark,
        runtime_patch_heldout_benchmark_path=args.runtime_patch_heldout_benchmark,
        prompt_patch_gate_path=args.prompt_patch_gate,
        product_workflow_report_path=args.product_workflow_report,
        artifact_id=args.artifact_id,
        loss_metric=args.loss_metric,
    )
    artifact = load_json_artifact(output_path)
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "output": str(output_path),
                "status": artifact["overall_status"],
                "baseline_loss": artifact["baseline_loss"],
                "runtime_patch_loss": artifact["runtime_patch_loss"],
                "relative_loss_reduction": artifact["relative_loss_reduction"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_official_heldout_benchmark(artifact: dict[str, Any], *, label: str) -> None:
    if artifact.get("schema_version") != OFFICIAL_SEGMENT_BENCHMARK_SCHEMA_VERSION:
        raise ValueError(f"{label} has unsupported schema_version")
    if artifact.get("overall_status") != "passed":
        raise ValueError(f"{label} must be passed")
    for field_name in (
        "artifact_id",
        "source_ingestion_artifact_id",
        "prediction_artifact_id",
        "benchmark_metrics",
        "segment_coverage",
    ):
        if field_name not in artifact:
            raise ValueError(f"{label} missing {field_name}")
    if _source_split(artifact) != "heldout":
        raise ValueError(f"{label} must use held-out evaluation split")
    if _coverage_rate(artifact) < 1.0:
        raise ValueError(f"{label} must have complete segment coverage")


def _validate_same_heldout_target(
    baseline: dict[str, Any],
    runtime_patch: dict[str, Any],
) -> None:
    if baseline["source_ingestion_artifact_id"] != runtime_patch[
        "source_ingestion_artifact_id"
    ]:
        raise ValueError("runtime patch comparison requires the same held-out target")


def _validate_prompt_patch_gate(gate: dict[str, Any]) -> None:
    if gate.get("schema_version") != PROMPT_PATCH_GATE_SCHEMA_VERSION:
        raise ValueError("prompt patch gate has unsupported schema_version")
    if gate.get("overall_status") != "accepted":
        raise ValueError("prompt patch gate must be accepted")
    for field_name in ("artifact_id", "accepted_candidate_id", "source_split_contract"):
        if field_name not in gate:
            raise ValueError(f"prompt patch gate missing {field_name}")
    source_split_contract = gate["source_split_contract"]
    if source_split_contract.get("candidate_generation") != "calibration":
        raise ValueError("prompt patch candidate must be generated from calibration")
    if source_split_contract.get("candidate_acceptance") != "heldout":
        raise ValueError("prompt patch candidate must be accepted on heldout")


def _validate_product_workflow_report(
    report: dict[str, Any],
    prompt_patch_gate: dict[str, Any],
) -> None:
    if report.get("schema_version") != PRODUCT_WORKFLOW_REPORT_SCHEMA_VERSION:
        raise ValueError("product workflow report has unsupported schema_version")
    if report.get("workflow_status") != "research_gate_passed":
        raise ValueError("product workflow report must pass research gate")
    if not report.get("source_run_id"):
        raise ValueError("product workflow report missing source_run_id")
    gate_ref = report.get("evidence_chain", {}).get("prompt_patch_gate", {})
    if gate_ref.get("artifact_id") != prompt_patch_gate["artifact_id"]:
        raise ValueError("product workflow report must reference prompt patch gate")


def _benchmark_loss(artifact: dict[str, Any], loss_metric: str) -> float:
    value = artifact.get("benchmark_metrics", {}).get(loss_metric)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"benchmark missing numeric {loss_metric}")
    return float(value)


def _coverage_rate(artifact: dict[str, Any]) -> float:
    value = artifact.get("segment_coverage", {}).get("coverage_rate")
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0.0
    return float(value)


def _source_split(artifact: dict[str, Any]) -> str:
    source = str(artifact.get("source_ingestion_artifact_id", "")).lower()
    if "evaluation" in source or "heldout" in source or "held-out" in source:
        return "heldout"
    if "calibration" in source:
        return "calibration"
    return "unknown"


def _overall_status(absolute_delta: float) -> str:
    if absolute_delta > 0:
        return "improved"
    if absolute_delta < 0:
        return "regressed"
    return "no_change"


def _risk_flags(overall_status: str, product_workflow_report: dict[str, Any]) -> list[str]:
    flags = list(product_workflow_report.get("risk_flags", []))
    if overall_status != "improved":
        flags.append("runtime_patch_did_not_improve_heldout_alignment")
    if "runtime_patch_effect_not_field_validation" not in flags:
        flags.append("runtime_patch_effect_not_field_validation")
    return _unique_strings(flags)


def _claim_boundaries(
    baseline_heldout_benchmark: dict[str, Any],
    runtime_patch_heldout_benchmark: dict[str, Any],
    prompt_patch_gate: dict[str, Any],
) -> list[str]:
    boundaries = [
        RUNTIME_PATCH_EFFECT_CLAIM_BOUNDARY,
        "The baseline and runtime-patch benchmarks use the same held-out "
        "HPS/HTOPS evaluation projection.",
        "This artifact compares segment-level distributional alignment only; it "
        "does not establish causal policy effects.",
    ]
    boundaries.extend(baseline_heldout_benchmark.get("claim_boundaries", []))
    boundaries.extend(runtime_patch_heldout_benchmark.get("claim_boundaries", []))
    boundaries.extend(prompt_patch_gate.get("claim_boundaries", []))
    return _unique_strings([boundary for boundary in boundaries if boundary])


def _unique_strings(values: list[str]) -> list[str]:
    unique = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def _round_float(value: float) -> float:
    return round(float(value), 12)


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
