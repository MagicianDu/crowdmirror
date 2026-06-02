from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any


RUNTIME_TRIAL_SCHEMA_VERSION = "dcl-prs-runtime-strong-baseline-trial-v1"
OFFICIAL_SEGMENT_BENCHMARK_SCHEMA_VERSION = (
    "policy-reaction-official-segment-benchmark-v1"
)
LOSS_METRIC = "weighted_choice_distribution_jsd"
WORST_SEGMENT_METRIC = "worst_segment_choice_distribution_jsd"
DCL_RUNTIME_METHOD = "DCL-PRS-runtime"
REQUIRED_BASELINE_FAMILIES = [
    "deterministic_anchor",
    "fixed_party_or_ideology_prior",
    "LCDU-LCR-SG",
]


def build_dcl_prs_runtime_strong_baseline_trial(
    *,
    artifact_id: str,
    benchmark_records: list[dict[str, Any]],
) -> dict[str, Any]:
    validated = [_validate_record(record) for record in benchmark_records]
    grouped = _group_records(validated)
    task_results = {
        task_id: _task_result(task_id=task_id, repeat_records=repeat_records)
        for task_id, repeat_records in sorted(grouped.items())
    }
    blocking_gaps = _blocking_gaps(validated=validated, task_results=task_results)
    stable_win = not blocking_gaps and bool(task_results)
    artifact = {
        "schema_version": RUNTIME_TRIAL_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            has_dcl_runtime=_has_method(validated, DCL_RUNTIME_METHOD),
            stable_win=stable_win,
        ),
        "validation_type": "dcl_prs_runtime_strong_baseline_trial",
        "loss_metric": LOSS_METRIC,
        "required_baseline_families": REQUIRED_BASELINE_FAMILIES,
        "dcl_runtime_method": DCL_RUNTIME_METHOD,
        "task_count": len(task_results),
        "repeat_count": _repeat_count(task_results),
        "benchmark_record_count": len(validated),
        "source_artifact_ids": [
            record["benchmark"]["artifact_id"] for record in validated
        ],
        "stable_strong_baseline_win_proven": stable_win,
        "dcl_prs_leads_covered_baselines": stable_win,
        "task_results": task_results,
        "blocking_gaps": blocking_gaps,
        "primary_decision": _primary_decision(
            has_dcl_runtime=_has_method(validated, DCL_RUNTIME_METHOD),
            stable_win=stable_win,
        ),
        "claim_boundary": (
            "This artifact evaluates DCL-PRS runtime predictions against "
            "deterministic anchor, fixed prior, and LCDU baselines on held-out "
            "public policy-reaction benchmarks. It does not generate runtime "
            "predictions and must not treat repair smoke artifacts as runtime "
            "evidence."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_dcl_prs_runtime_strong_baseline_trial(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-runtime-strong-baseline-trial-current-001",
    benchmark_records_path: str | Path | None = None,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    records = (
        _load_benchmark_records(Path(benchmark_records_path))
        if benchmark_records_path
        else []
    )
    artifact = build_dcl_prs_runtime_strong_baseline_trial(
        artifact_id=artifact_id,
        benchmark_records=records,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "artifact": artifact}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-records-path")
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_runtime_strong_baseline_trial",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-runtime-strong-baseline-trial-current-001",
    )
    args = parser.parse_args()
    written = write_dcl_prs_runtime_strong_baseline_trial(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
        benchmark_records_path=args.benchmark_records_path,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "overall_status": artifact["overall_status"],
                "stable_strong_baseline_win_proven": artifact[
                    "stable_strong_baseline_win_proven"
                ],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_record(record: dict[str, Any]) -> dict[str, Any]:
    for field_name in ("method_family", "task_id", "repeat_id", "benchmark"):
        if field_name not in record:
            raise ValueError(f"benchmark record missing {field_name}")
    benchmark = record["benchmark"]
    if benchmark.get("schema_version") != OFFICIAL_SEGMENT_BENCHMARK_SCHEMA_VERSION:
        raise ValueError("benchmark has unsupported schema_version")
    if benchmark.get("overall_status") != "passed":
        raise ValueError("benchmark must be passed")
    if _coverage_rate(benchmark) < 1.0:
        raise ValueError("benchmark must have complete segment coverage")
    _benchmark_loss(benchmark)
    _worst_segment_loss(benchmark)
    return {
        "method_family": str(record["method_family"]),
        "task_id": str(record["task_id"]),
        "repeat_id": str(record["repeat_id"]),
        "benchmark": benchmark,
    }


def _group_records(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, dict[str, dict[str, Any]]]]:
    grouped: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}
    for record in records:
        grouped.setdefault(record["task_id"], {}).setdefault(
            record["repeat_id"], {}
        )[record["method_family"]] = record
    return grouped


def _task_result(
    *,
    task_id: str,
    repeat_records: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    repeat_results = {
        repeat_id: _repeat_result(repeat_id=repeat_id, records=records)
        for repeat_id, records in sorted(repeat_records.items())
    }
    failure_modes = _unique_strings(
        mode
        for result in repeat_results.values()
        for mode in result["failure_modes"]
    )
    baseline_rates = {
        baseline: _rate(
            sum(
                1
                for result in repeat_results.values()
                if result["beats_baselines"].get(baseline) is True
            ),
            len(repeat_results),
        )
        for baseline in REQUIRED_BASELINE_FAMILIES
    }
    strong_pass = (
        bool(repeat_results)
        and not failure_modes
        and all(result["strong_baseline_repeat_pass"] for result in repeat_results.values())
    )
    dcl_losses = [
        result["dcl_runtime_loss"]
        for result in repeat_results.values()
        if result["dcl_runtime_loss"] is not None
    ]
    return {
        "task_id": task_id,
        "repeat_count": len(repeat_results),
        "strong_baseline_task_pass": strong_pass,
        "dcl_runtime_loss_mean": _round_float(mean(dcl_losses))
        if dcl_losses
        else None,
        "beats_baseline_repeat_rates": baseline_rates,
        "worst_segment_guard_pass_rate": _rate(
            sum(
                1
                for result in repeat_results.values()
                if result["worst_segment_guard_pass"] is True
            ),
            len(repeat_results),
        ),
        "failure_modes": failure_modes,
        "repeat_results": repeat_results,
    }


def _repeat_result(
    *,
    repeat_id: str,
    records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    dcl_record = records.get(DCL_RUNTIME_METHOD)
    baseline_losses = {
        baseline: _benchmark_loss(records[baseline]["benchmark"])
        if baseline in records
        else None
        for baseline in REQUIRED_BASELINE_FAMILIES
    }
    baseline_worst_losses = {
        baseline: _worst_segment_loss(records[baseline]["benchmark"])
        if baseline in records
        else None
        for baseline in REQUIRED_BASELINE_FAMILIES
    }
    dcl_loss = _benchmark_loss(dcl_record["benchmark"]) if dcl_record else None
    dcl_worst = _worst_segment_loss(dcl_record["benchmark"]) if dcl_record else None
    beats = {
        baseline: (
            dcl_loss is not None
            and baseline_loss is not None
            and dcl_loss < baseline_loss
        )
        for baseline, baseline_loss in baseline_losses.items()
    }
    worst_guard = (
        dcl_worst is not None
        and all(value is not None for value in baseline_worst_losses.values())
        and dcl_worst < min(value for value in baseline_worst_losses.values() if value is not None)
    )
    failure_modes = []
    if dcl_record is None:
        failure_modes.append("dcl_prs_runtime_prediction_missing")
    for baseline, baseline_loss in baseline_losses.items():
        if baseline_loss is None:
            failure_modes.append(f"{baseline}_benchmark_missing")
        elif not beats[baseline]:
            failure_modes.append(f"dcl_prs_not_better_than_{baseline}")
    if dcl_record is not None and not worst_guard:
        failure_modes.append("dcl_prs_worst_segment_guard_failed")
    return {
        "repeat_id": repeat_id,
        "dcl_runtime_loss": _round_float(dcl_loss) if dcl_loss is not None else None,
        "baseline_losses": {
            baseline: _round_float(loss) if loss is not None else None
            for baseline, loss in baseline_losses.items()
        },
        "beats_baselines": beats,
        "worst_segment_guard_pass": worst_guard,
        "strong_baseline_repeat_pass": not failure_modes,
        "failure_modes": failure_modes,
    }


def _blocking_gaps(
    *,
    validated: list[dict[str, Any]],
    task_results: dict[str, dict[str, Any]],
) -> list[str]:
    gaps = []
    if not validated:
        gaps.append("benchmark_records_missing")
    if not _has_method(validated, DCL_RUNTIME_METHOD):
        gaps.append("dcl_prs_runtime_prediction_missing")
    for baseline in REQUIRED_BASELINE_FAMILIES:
        if not _has_method(validated, baseline):
            gaps.append(f"{baseline}_benchmark_missing")
    if len(task_results) < 2:
        gaps.append("multi_task_runtime_trial_missing")
    if _repeat_count(task_results) < 2:
        gaps.append("repeat_stability_missing")
    for result in task_results.values():
        for failure_mode in result["failure_modes"]:
            if failure_mode not in gaps:
                gaps.append(failure_mode)
    return gaps


def _overall_status(*, has_dcl_runtime: bool, stable_win: bool) -> str:
    if stable_win:
        return "runtime_strong_baseline_trial_dcl_prs_leads"
    if not has_dcl_runtime:
        return "runtime_strong_baseline_trial_blocked"
    return "runtime_strong_baseline_trial_dcl_prs_not_leading"


def _primary_decision(*, has_dcl_runtime: bool, stable_win: bool) -> dict[str, str]:
    if stable_win:
        return {
            "research_claim": "promote_dcl_prs_runtime_as_strong_baseline_candidate",
            "ccf_a_gate": "conditional_candidate_pending_cross_dataset_audit",
        }
    if not has_dcl_runtime:
        return {
            "research_claim": "cannot_evaluate_dcl_prs_without_runtime_prediction",
            "ccf_a_gate": "runtime_strong_baseline_trial_blocked",
        }
    return {
        "research_claim": "retire_dcl_prs_runtime_as_algorithm_main_claim",
        "ccf_a_gate": "not_passed_under_runtime_strong_baseline_trial",
    }


def _benchmark_loss(benchmark: dict[str, Any]) -> float:
    value = benchmark.get("benchmark_metrics", {}).get(LOSS_METRIC)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"benchmark missing numeric {LOSS_METRIC}")
    return float(value)


def _worst_segment_loss(benchmark: dict[str, Any]) -> float:
    value = benchmark.get("benchmark_metrics", {}).get(WORST_SEGMENT_METRIC)
    if value is None:
        return _benchmark_loss(benchmark)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"benchmark missing numeric {WORST_SEGMENT_METRIC}")
    return float(value)


def _coverage_rate(benchmark: dict[str, Any]) -> float:
    value = benchmark.get("segment_coverage", {}).get("coverage_rate")
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("benchmark missing numeric coverage_rate")
    return float(value)


def _repeat_count(task_results: dict[str, dict[str, Any]]) -> int:
    return max(
        (result["repeat_count"] for result in task_results.values()),
        default=0,
    )


def _has_method(records: list[dict[str, Any]], method_family: str) -> bool:
    return any(record["method_family"] == method_family for record in records)


def _load_benchmark_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, list):
        raise ValueError("benchmark records path must contain a JSON array")
    return payload


def _rate(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return _round_float(count / total)


def _round_float(value: float) -> float:
    return round(float(value), 12)


def _unique_strings(values) -> list[str]:
    unique = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("DCL-PRS runtime strong baseline trial must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
