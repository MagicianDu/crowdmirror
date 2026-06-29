from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from circe.llm_client import LLMClient, LLMClientConfig, LLMResponse  # noqa: E402


PREDICTION_SCHEMA_VERSION = "policy-reaction-segment-predictions-v1"
INGESTION_SCHEMA_VERSION = "policy-reaction-public-data-ingestion-v1"
DCL_RUNTIME_METHOD = "DCL-PRS-runtime"
DEFAULT_CALIBRATION_INGESTION_PATH = Path(
    "experiments/results/policy_reaction_benchmark/"
    "policy-reaction-htops-2506-calibration-ingestion-001.json"
)
DEFAULT_OUTPUT_PATH = Path(
    "experiments/results/policy_reaction_benchmark/"
    "policy-reaction-segment-predictions-dcl-prs-runtime-gpt-oss-20b-"
    "12x3-calibration-split-001.json"
)

CompletionFn = Callable[[str, str], LLMResponse]

SYSTEM_PROMPT = (
    "You are a policy reaction simulator. Given a public-policy scenario, a "
    "population segment, policy alternatives, and a calibration-only anchor "
    "distribution, output ONLY JSON probabilities over the alternatives. Do not "
    "include prose."
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_dcl_prs_runtime_policy_reaction_predictions(
    *,
    calibration_ingestion: dict[str, Any],
    artifact_id: str,
    provider: str,
    model: str,
    base_url: str | None,
    completion_fn: CompletionFn,
    llm_weight: float = 0.25,
    max_segments: int | None = None,
) -> dict[str, Any]:
    _validate_calibration_ingestion(calibration_ingestion)
    if llm_weight < 0.0 or llm_weight > 1.0:
        raise ValueError("llm_weight must be in [0, 1]")
    segment_items = sorted(
        calibration_ingestion["observed_policy_reaction_summary"]["by_segment"].items()
    )
    if max_segments is not None:
        segment_items = segment_items[:max_segments]

    segment_predictions = {}
    total_input_tokens = 0
    total_output_tokens = 0
    parse_failure_count = 0
    call_records = []
    for segment_key, segment_summary in segment_items:
        anchor = _normalize_distribution(
            segment_summary["weighted_mean_policy_reaction"]
        )
        options = list(anchor)
        response = completion_fn(
            SYSTEM_PROMPT,
            _build_user_prompt(
                segment_key=segment_key,
                options=options,
                anchor=anchor,
                row_count=int(segment_summary.get("row_count", 0)),
            ),
        )
        total_input_tokens += int(response.input_tokens)
        total_output_tokens += int(response.output_tokens)
        parsed = _parse_probabilities(response.content, options)
        parse_success = parsed is not None
        if not parse_success:
            parse_failure_count += 1
            parsed = anchor
        predicted = _blend_distribution(anchor=anchor, llm=parsed, llm_weight=llm_weight)
        segment_predictions[segment_key] = {
            "persona_count": int(segment_summary.get("row_count", 0)),
            "policy_probabilities": predicted,
            "constraint_anchor_distribution": anchor,
            "llm_raw_probabilities": parsed,
            "llm_parse_success": parse_success,
            "llm_weight": llm_weight,
        }
        call_records.append(
            {
                "segment": segment_key,
                "input_tokens": int(response.input_tokens),
                "output_tokens": int(response.output_tokens),
                "parse_success": parse_success,
            }
        )

    artifact = {
        "schema_version": PREDICTION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "model": model,
        "provider": provider,
        "base_url": base_url,
        "method_family": DCL_RUNTIME_METHOD,
        "prediction_scope": "dcl_prs_runtime_policy_reaction_calibration_constrained",
        "source_run_id": artifact_id,
        "source_calibration_ingestion_artifact_id": calibration_ingestion["artifact_id"],
        "source_split_contract": {
            "constraint_anchor": "calibration",
            "runtime_prediction_generation": "llm_over_calibration_constraints",
            "runtime_effect_evaluation": "heldout_required",
        },
        "segment_predictions": segment_predictions,
        "llm_accounting": {
            "total_call_count": len(call_records),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "parse_failure_count": parse_failure_count,
        },
        "call_records": call_records,
        "risk_flags": _risk_flags(
            base_url=base_url,
            parse_failure_count=parse_failure_count,
        ),
        "claim_boundary": (
            "DCL-PRS runtime predictions are generated from the calibration "
            "split and LLM policy-reaction reasoning. Held-out evaluation "
            "distributions are not used in this artifact."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_dcl_prs_runtime_policy_reaction_predictions(
    output: str | Path,
    *,
    calibration_ingestion_path: str | Path,
    artifact_id: str,
    provider: str,
    model: str,
    base_url: str | None,
    completion_fn: CompletionFn | None = None,
    llm_weight: float = 0.25,
    max_segments: int | None = None,
    max_tokens: int = 1200,
    timeout_seconds: float | None = 60.0,
) -> Path:
    if completion_fn is None:
        client = LLMClient(
            LLMClientConfig(
                provider=provider,
                base_url=base_url,
                model=model,
                max_tokens=max_tokens,
                temperature=0.0,
                timeout_seconds=timeout_seconds,
            )
        )
        completion_fn = client.chat
    artifact = build_dcl_prs_runtime_policy_reaction_predictions(
        calibration_ingestion=load_json_artifact(calibration_ingestion_path),
        artifact_id=artifact_id,
        provider=provider,
        model=model,
        base_url=base_url,
        completion_fn=completion_fn,
        llm_weight=llm_weight,
        max_segments=max_segments,
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--calibration-ingestion",
        default=str(DEFAULT_CALIBRATION_INGESTION_PATH),
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument(
        "--artifact-id",
        default=(
            "policy-reaction-segment-predictions-dcl-prs-runtime-gpt-oss-20b-"
            "12x3-calibration-split-001"
        ),
    )
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model", default="openai/gpt-oss-20b")
    parser.add_argument("--base-url", default="http://127.0.0.1:1234/v1")
    parser.add_argument("--llm-weight", type=float, default=0.25)
    parser.add_argument("--max-segments", type=int)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args()

    output_path = write_dcl_prs_runtime_policy_reaction_predictions(
        args.output,
        calibration_ingestion_path=args.calibration_ingestion,
        artifact_id=args.artifact_id,
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        llm_weight=args.llm_weight,
        max_segments=args.max_segments,
        max_tokens=args.max_tokens,
        timeout_seconds=args.timeout_seconds,
    )
    artifact = load_json_artifact(output_path)
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "segment_count": len(artifact["segment_predictions"]),
                "parse_failure_count": artifact["llm_accounting"][
                    "parse_failure_count"
                ],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_calibration_ingestion(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != INGESTION_SCHEMA_VERSION:
        raise ValueError("calibration ingestion has unsupported schema_version")
    if artifact.get("overall_status") != "passed":
        raise ValueError("calibration ingestion must be passed")
    by_segment = artifact.get("observed_policy_reaction_summary", {}).get("by_segment")
    if not isinstance(by_segment, dict) or not by_segment:
        raise ValueError("calibration ingestion missing by_segment distributions")
    for segment_key, segment in by_segment.items():
        if not isinstance(segment.get("weighted_mean_policy_reaction"), dict):
            raise ValueError(f"{segment_key} missing weighted_mean_policy_reaction")


def _build_user_prompt(
    *,
    segment_key: str,
    options: list[str],
    anchor: dict[str, float],
    row_count: int,
) -> str:
    return (
        "Task: simulate policy reaction probabilities for one survey segment.\n"
        f"Segment: {segment_key}\n"
        "Policy context: U.S. household cost pressure and public policy responses.\n"
        f"Policy alternatives: {json.dumps(options, sort_keys=True)}\n"
        "Calibration-only anchor distribution from a separate split:\n"
        f"{json.dumps(anchor, sort_keys=True)}\n"
        f"Calibration segment row count: {row_count}\n"
        "Use the anchor as a constraint, but adjust only when policy-reaction "
        "mechanisms imply a different distribution. Output exactly one JSON "
        "object with the same policy alternatives as keys."
    )


def _parse_probabilities(text: str, options: list[str]) -> dict[str, float] | None:
    json_match = re.search(r"\{.*?\}", text, flags=re.DOTALL)
    if not json_match:
        return None
    try:
        parsed = json.loads(json_match.group())
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    values = {}
    for option in options:
        value = parsed.get(option)
        if isinstance(value, bool) or not isinstance(value, int | float):
            return None
        values[option] = float(value)
    try:
        return _normalize_distribution(values)
    except ValueError:
        return None


def _blend_distribution(
    *,
    anchor: dict[str, float],
    llm: dict[str, float],
    llm_weight: float,
) -> dict[str, float]:
    blended = {
        option: anchor[option] * (1.0 - llm_weight) + llm[option] * llm_weight
        for option in anchor
    }
    return _normalize_distribution(blended)


def _normalize_distribution(raw: dict[str, Any]) -> dict[str, float]:
    if not raw:
        raise ValueError("distribution must not be empty")
    values = {}
    for key, value in raw.items():
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError("distribution values must be numeric")
        probability = float(value)
        if probability < 0.0:
            raise ValueError("distribution values must be non-negative")
        values[str(key)] = probability
    total = sum(values.values())
    if total <= 0.0:
        raise ValueError("distribution total must be positive")
    return {key: round(value / total, 12) for key, value in values.items()}


def _risk_flags(*, base_url: str | None, parse_failure_count: int) -> list[str]:
    flags = [
        "not_field_validation",
        "heldout_evaluation_required",
        "calibration_constrained_runtime_prediction",
    ]
    if base_url and ("127.0.0.1" in base_url or "localhost" in base_url):
        flags.append("local_model_only")
    if parse_failure_count:
        flags.append("llm_parse_failures_used_anchor_fallback")
    return flags


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("DCL-PRS runtime predictions must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
