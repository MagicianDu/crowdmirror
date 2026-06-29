from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Callable

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from circe.llm_client import LLMClient, LLMClientConfig, LLMResponse  # noqa: E402
from experiments.lcdu_anes_cross_task_validation import (  # noqa: E402
    _weighted_segment_jsd,
    _worst_segment_jsd,
)


LLM_VALIDATION_SCHEMA_VERSION = "lcdu-anes-llm-simulator-validation-v1"
MICRODATA_SCHEMA_VERSION = "lcdu-anes-public-microdata-ingestion-v1"
DEFAULT_METHOD_IDS = [
    "raw_prompt",
    "aggregate_anchor_prompt",
    "lcdu_segment_anchor_prompt",
]

TASK_PROMPTS = {
    "public_health_medical_insurance_attitude_v1": {
        "question": (
            "A public survey asks respondents to place themselves on a 7-point "
            "scale between a government medical insurance plan and private "
            "medical insurance."
        ),
        "option_descriptions": {
            "government_insurance_plan": (
                "Respondent leans toward a government insurance plan."
            ),
            "mixed_or_middle_position": (
                "Respondent is in the middle or gives a mixed position."
            ),
            "private_insurance_plan": (
                "Respondent leans toward private medical insurance."
            ),
        },
    },
    "climate_energy_regulation_attitude_v1": {
        "question": (
            "A public survey asks respondents to place themselves on a 7-point "
            "scale between stronger environmental protection and protecting "
            "business from regulatory burden."
        ),
        "option_descriptions": {
            "support_more_regulation_or_spending": (
                "Respondent leans toward stronger environmental protection."
            ),
            "mixed_or_status_quo": (
                "Respondent is in the middle or gives a mixed position."
            ),
            "oppose_more_regulation_or_spending": (
                "Respondent leans toward protecting business from regulatory burden."
            ),
        },
    },
}

CompletionFn = Callable[[str, str], LLMResponse]


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_lcdu_anes_llm_simulator_validation_artifact(
    *,
    microdata_artifact: dict[str, Any],
    artifact_id: str,
    provider: str,
    model: str,
    base_url: str | None,
    completion_fn: CompletionFn,
    max_segments_per_task: int = 2,
    segment_offset: int = 0,
    prompt_variant: str = "standard",
) -> dict[str, Any]:
    _validate_microdata_artifact(microdata_artifact)
    task_results = {}
    call_records = []
    total_input_tokens = 0
    total_output_tokens = 0
    parse_failure_count = 0

    for task_id in sorted(microdata_artifact["target_distributions"]):
        task_result, task_calls = _run_task_validation(
            task_id=task_id,
            splits=microdata_artifact["splits"],
            completion_fn=completion_fn,
            max_segments_per_task=max_segments_per_task,
            segment_offset=segment_offset,
            prompt_variant=prompt_variant,
        )
        task_results[task_id] = task_result
        call_records.extend(task_calls)
        total_input_tokens += sum(call["input_tokens"] for call in task_calls)
        total_output_tokens += sum(call["output_tokens"] for call in task_calls)
        parse_failure_count += sum(
            1 for call in task_calls if not call["parse_success"]
        )

    accepted_task_count = sum(
        1 for result in task_results.values() if result["candidate_accepted"]
    )
    test_improvement_task_count = sum(
        1
        for result in task_results.values()
        if result["test"]["final_loss"] < result["test"]["initial_loss"]
    )
    artifact = {
        "schema_version": LLM_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            accepted_task_count=accepted_task_count,
            test_improvement_task_count=test_improvement_task_count,
            task_count=len(task_results),
            parse_failure_count=parse_failure_count,
        ),
        "source_artifact_id": microdata_artifact["artifact_id"],
        "validation_type": "split_gated_llm_segment_simulator_smoke",
        "loss_metric": "weighted_choice_distribution_jsd",
        "candidate_generation_split": "calibration",
        "candidate_acceptance_split": "heldout",
        "final_claim_check_split": "test",
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "temperature": 0.0,
        "max_segments_per_task": max_segments_per_task,
        "segment_offset": segment_offset,
        "prompt_variant": prompt_variant,
        "method_ids": DEFAULT_METHOD_IDS,
        "task_count": len(task_results),
        "accepted_task_count": accepted_task_count,
        "test_improvement_task_count": test_improvement_task_count,
        "task_results": task_results,
        "llm_accounting": {
            "total_call_count": len(call_records),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "parse_failure_count": parse_failure_count,
        },
        "call_records": call_records,
        "risk_flags": _risk_flags(base_url=base_url, parse_failure_count=parse_failure_count),
        "claim_boundary": (
            "This artifact is a small split-gated LLM simulator smoke over ANES "
            "public-use tasks. It can indicate whether LLM prompts can consume "
            "aggregate or segment LCDU anchors, but it does not establish strong "
            "baseline superiority, cross-provider generalization, scale "
            "stability, or field prediction."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def build_blocked_llm_simulator_artifact(
    *,
    microdata_artifact: dict[str, Any],
    artifact_id: str,
    provider: str,
    model: str,
    base_url: str | None,
    error: Exception,
) -> dict[str, Any]:
    artifact = {
        "schema_version": LLM_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "blocked_provider_unavailable",
        "source_artifact_id": microdata_artifact.get("artifact_id"),
        "validation_type": "split_gated_llm_segment_simulator_smoke",
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "task_count": 0,
        "accepted_task_count": 0,
        "test_improvement_task_count": 0,
        "llm_accounting": {
            "total_call_count": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "parse_failure_count": 0,
        },
        "provider_error": {
            "error_type": type(error).__name__,
            "message": str(error)[:500],
        },
        "risk_flags": [
            "provider_unavailable",
            "not_llm_model_quality_evidence",
            "not_cross_provider_validation",
        ],
        "claim_boundary": (
            "LLM simulator validation was attempted but the provider call failed; "
            "this artifact is a blocked execution record, not model evidence."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_lcdu_anes_llm_simulator_validation_artifact(
    output: str | Path,
    *,
    microdata_artifact_path: str | Path,
    artifact_id: str,
    provider: str,
    model: str,
    base_url: str | None,
    max_segments_per_task: int,
    segment_offset: int,
    prompt_variant: str,
    execute: bool,
) -> dict[str, Any]:
    microdata_artifact = load_json_artifact(microdata_artifact_path)
    if not execute:
        artifact = _planned_artifact(
            microdata_artifact=microdata_artifact,
            artifact_id=artifact_id,
            provider=provider,
            model=model,
            base_url=base_url,
            max_segments_per_task=max_segments_per_task,
            segment_offset=segment_offset,
            prompt_variant=prompt_variant,
        )
    else:
        completion_fn = _build_completion_fn(
            provider=provider,
            model=model,
            base_url=base_url,
        )
        try:
            artifact = build_lcdu_anes_llm_simulator_validation_artifact(
                microdata_artifact=microdata_artifact,
                artifact_id=artifact_id,
                provider=provider,
                model=model,
                base_url=base_url,
                completion_fn=completion_fn,
                max_segments_per_task=max_segments_per_task,
                segment_offset=segment_offset,
                prompt_variant=prompt_variant,
            )
        except Exception as exc:  # Provider failures should still be auditable.
            artifact = build_blocked_llm_simulator_artifact(
                microdata_artifact=microdata_artifact,
                artifact_id=artifact_id,
                provider=provider,
                model=model,
                base_url=base_url,
                error=exc,
            )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"output_path": str(output_path), "artifact": artifact}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--microdata-artifact",
        default=(
            "experiments/results/lcdu_public_task_microdata/"
            "lcdu-anes-2024-sda-public-microdata-001.json"
        ),
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/lcdu_llm_simulator_validation/"
            "lcdu-anes-llm-simulator-validation-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-anes-llm-simulator-validation-current-001",
    )
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model", default="openai/gpt-oss-20b")
    parser.add_argument("--base-url", default="http://127.0.0.1:1234/v1")
    parser.add_argument("--max-segments-per-task", type=int, default=2)
    parser.add_argument("--segment-offset", type=int, default=0)
    parser.add_argument(
        "--prompt-variant",
        choices=["standard", "compact", "deliberative"],
        default="standard",
    )
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    written = write_lcdu_anes_llm_simulator_validation_artifact(
        args.output,
        microdata_artifact_path=args.microdata_artifact,
        artifact_id=args.artifact_id,
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        max_segments_per_task=args.max_segments_per_task,
        segment_offset=args.segment_offset,
        prompt_variant=args.prompt_variant,
        execute=args.execute,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "accepted_task_count": artifact["accepted_task_count"],
                "artifact_id": artifact["artifact_id"],
                "output": written["output_path"],
                "status": artifact["overall_status"],
                "task_count": artifact["task_count"],
                "total_call_count": artifact["llm_accounting"]["total_call_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _run_task_validation(
    *,
    task_id: str,
    splits: dict[str, Any],
    completion_fn: CompletionFn,
    max_segments_per_task: int,
    segment_offset: int,
    prompt_variant: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    calibration = splits["calibration"]["target_distributions"][task_id]
    heldout = splits["heldout"]["target_distributions"][task_id]
    test = splits["test"]["target_distributions"][task_id]
    selected_segments = _select_segments(
        calibration=calibration,
        heldout=heldout,
        test=test,
        max_segments=max_segments_per_task,
        segment_offset=segment_offset,
    )
    predictions = {method_id: {} for method_id in DEFAULT_METHOD_IDS}
    call_records = []
    for method_id in DEFAULT_METHOD_IDS:
        for segment_key in selected_segments:
            system, user = _build_prompt(
                task_id=task_id,
                method_id=method_id,
                segment_key=segment_key,
                calibration=calibration,
                prompt_variant=prompt_variant,
            )
            response = completion_fn(system, user)
            policy_options = list(calibration["overall"]["policy_probabilities"])
            parsed = _parse_distribution(response.content, policy_options)
            predictions[method_id][segment_key] = parsed["probabilities"]
            call_records.append(
                {
                    "task_id": task_id,
                    "segment_key": segment_key,
                    "method_id": method_id,
                    "prompt_hash": _sha256_text(system + "\n" + user),
                    "prompt_variant": prompt_variant,
                    "response_hash": _sha256_text(response.content),
                    "parse_success": parsed["parse_success"],
                    "parsed_policy_probabilities": parsed["probabilities"],
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                }
            )
    heldout_selected = _filter_segments(heldout["by_segment"], selected_segments)
    test_selected = _filter_segments(test["by_segment"], selected_segments)
    heldout_losses = {
        method_id: _weighted_segment_jsd(
            observed_by_segment=heldout_selected,
            predicted_by_segment=prediction,
        )
        for method_id, prediction in predictions.items()
    }
    heldout_worst = {
        method_id: _worst_segment_jsd(
            observed_by_segment=heldout_selected,
            predicted_by_segment=prediction,
        )
        for method_id, prediction in predictions.items()
    }
    initial_method_id = "raw_prompt"
    initial_loss = heldout_losses[initial_method_id]
    best_method_id = min(heldout_losses, key=heldout_losses.get)
    best_loss = heldout_losses[best_method_id]
    candidate_accepted = best_method_id != initial_method_id and best_loss < initial_loss
    final_method_id = best_method_id if candidate_accepted else initial_method_id
    test_losses = {
        method_id: _weighted_segment_jsd(
            observed_by_segment=test_selected,
            predicted_by_segment=prediction,
        )
        for method_id, prediction in predictions.items()
    }
    test_worst = {
        method_id: _worst_segment_jsd(
            observed_by_segment=test_selected,
            predicted_by_segment=prediction,
        )
        for method_id, prediction in predictions.items()
    }
    task_result = {
        "task_id": task_id,
        "target_variable_id": calibration["target_variable_id"],
        "selected_segments": selected_segments,
        "segment_offset": segment_offset,
        "prompt_variant": prompt_variant,
        "candidate_accepted": candidate_accepted,
        "accepted_method_id": final_method_id if candidate_accepted else None,
        "acceptance_reason": (
            "heldout_loss_improved"
            if candidate_accepted
            else "no_candidate_improved_heldout_loss"
        ),
        "heldout": {
            "initial_loss": initial_loss,
            "best_loss": best_loss,
            "final_loss": heldout_losses[final_method_id],
            "initial_worst_segment_loss": heldout_worst[initial_method_id],
            "final_worst_segment_loss": heldout_worst[final_method_id],
            "best_method_id": best_method_id,
            "loss_by_method": heldout_losses,
        },
        "test": {
            "initial_loss": test_losses[initial_method_id],
            "best_candidate_loss": test_losses[best_method_id],
            "final_loss": test_losses[final_method_id],
            "initial_worst_segment_loss": test_worst[initial_method_id],
            "final_worst_segment_loss": test_worst[final_method_id],
            "final_method_id": final_method_id,
            "loss_by_method": test_losses,
        },
        "segment_coverage": calibration["segment_schema_coverage"],
    }
    return task_result, call_records


def _select_segments(
    *,
    calibration: dict[str, Any],
    heldout: dict[str, Any],
    test: dict[str, Any],
    max_segments: int,
    segment_offset: int,
) -> list[str]:
    common_segments = (
        set(calibration["by_segment"])
        & set(heldout["by_segment"])
        & set(test["by_segment"])
    )
    ranked = sorted(
        common_segments,
        key=lambda segment_key: heldout["by_segment"][segment_key]["row_count"],
        reverse=True,
    )
    if not ranked:
        return []
    offset = segment_offset % len(ranked)
    rotated = ranked[offset:] + ranked[:offset]
    return rotated[:max_segments]


def _filter_segments(
    by_segment: dict[str, Any],
    selected_segments: list[str],
) -> dict[str, Any]:
    return {
        segment_key: by_segment[segment_key]
        for segment_key in selected_segments
        if segment_key in by_segment
    }


def _build_prompt(
    *,
    task_id: str,
    method_id: str,
    segment_key: str,
    calibration: dict[str, Any],
    prompt_variant: str,
) -> tuple[str, str]:
    task_prompt = TASK_PROMPTS[task_id]
    policy_options = list(calibration["overall"]["policy_probabilities"])
    segment_anchor = calibration["by_segment"][segment_key]["policy_probabilities"]
    aggregate_anchor = calibration["overall"]["policy_probabilities"]
    anchor_text = ""
    if method_id == "aggregate_anchor_prompt":
        anchor_text = (
            "\nCalibration aggregate prior from public microdata:\n"
            f"{json.dumps(aggregate_anchor, sort_keys=True)}\n"
            "Use it only as a soft prior."
        )
    elif method_id == "lcdu_segment_anchor_prompt":
        anchor_text = (
            "\nLCDU segment anchor from calibration public microdata:\n"
            f"{json.dumps(segment_anchor, sort_keys=True)}\n"
            "Treat this as a segment-specific soft constraint. Adjust only if "
            "the segment description strongly implies a different distribution."
        )
    system = (
        "You simulate survey response distributions for population segments. "
        "Return strict JSON only. The JSON object must use exactly the provided "
        "policy option keys and numeric probabilities that sum to 1."
    )
    if prompt_variant == "compact":
        system = (
            "Estimate survey response probabilities for a population segment. "
            "Return only strict JSON using the required option keys."
        )
    elif prompt_variant == "deliberative":
        system = (
            "You are calibrating a population-simulation survey respondent model. "
            "Reason internally about ideology and income, but output strict JSON "
            "only with exactly the provided policy option keys and probabilities "
            "summing to 1."
        )
    user = (
        f"Task: {task_id}\n"
        f"Survey item: {task_prompt['question']}\n"
        f"Segment: {_describe_segment(segment_key)}\n"
        "Policy options and meanings:\n"
        f"{json.dumps(task_prompt['option_descriptions'], sort_keys=True)}\n"
        f"{anchor_text}\n"
        "Return only a JSON object with these keys:\n"
        f"{json.dumps(policy_options)}"
    )
    if prompt_variant == "compact":
        user = (
            f"Task: {task_id}\nSegment: {_describe_segment(segment_key)}\n"
            f"Options: {json.dumps(task_prompt['option_descriptions'], sort_keys=True)}\n"
            f"{anchor_text}\n"
            f"JSON keys: {json.dumps(policy_options)}"
        )
    elif prompt_variant == "deliberative":
        user = (
            f"Task: {task_id}\n"
            f"Survey item: {task_prompt['question']}\n"
            f"Population segment: {_describe_segment(segment_key)}\n"
            "Estimate the segment-level distribution, not an individual answer. "
            "Use public-opinion priors cautiously and keep uncertainty visible.\n"
            "Policy options and meanings:\n"
            f"{json.dumps(task_prompt['option_descriptions'], sort_keys=True)}\n"
            f"{anchor_text}\n"
            "Return only a JSON object with these keys:\n"
            f"{json.dumps(policy_options)}"
        )
    return system, user


def _parse_distribution(text: str, policy_options: list[str]) -> dict[str, Any]:
    json_match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not json_match:
        return {
            "parse_success": False,
            "probabilities": _uniform(policy_options),
        }
    try:
        parsed = json.loads(json_match.group())
        probabilities = {
            policy_option: float(parsed.get(policy_option, 0.0))
            for policy_option in policy_options
        }
        if any(value < 0 or not math.isfinite(value) for value in probabilities.values()):
            raise ValueError("invalid probability")
        total = sum(probabilities.values())
        if total <= 0:
            raise ValueError("zero probability mass")
        return {
            "parse_success": True,
            "probabilities": {
                policy_option: probabilities[policy_option] / total
                for policy_option in policy_options
            },
        }
    except (json.JSONDecodeError, TypeError, ValueError):
        return {
            "parse_success": False,
            "probabilities": _uniform(policy_options),
        }


def _uniform(policy_options: list[str]) -> dict[str, float]:
    return {
        policy_option: 1.0 / len(policy_options)
        for policy_option in policy_options
    }


def _describe_segment(segment_key: str) -> str:
    parts = []
    for item in segment_key.split("|"):
        if "=" in item:
            axis, value = item.split("=", 1)
            parts.append(f"{axis.replace('_', ' ')}: {value.replace('_', ' ')}")
    return "; ".join(parts) if parts else segment_key


def _build_completion_fn(
    *,
    provider: str,
    model: str,
    base_url: str | None,
) -> CompletionFn:
    client = LLMClient(
        LLMClientConfig(
            provider=provider,
            model=model,
            base_url=base_url,
            max_tokens=256,
            temperature=0.0,
            timeout_seconds=90,
        )
    )
    return client.chat


def _planned_artifact(
    *,
    microdata_artifact: dict[str, Any],
    artifact_id: str,
    provider: str,
    model: str,
    base_url: str | None,
    max_segments_per_task: int,
    segment_offset: int,
    prompt_variant: str,
) -> dict[str, Any]:
    artifact = {
        "schema_version": LLM_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "planned_not_executed",
        "source_artifact_id": microdata_artifact.get("artifact_id"),
        "validation_type": "split_gated_llm_segment_simulator_smoke",
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "max_segments_per_task": max_segments_per_task,
        "segment_offset": segment_offset,
        "prompt_variant": prompt_variant,
        "task_count": len(microdata_artifact.get("target_distributions", {})),
        "accepted_task_count": 0,
        "test_improvement_task_count": 0,
        "llm_accounting": {
            "total_call_count": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "parse_failure_count": 0,
        },
        "risk_flags": [
            "not_executed",
            "not_llm_model_quality_evidence",
        ],
        "claim_boundary": (
            "This is an execution plan artifact only; rerun with --execute to "
            "produce LLM model evidence."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def _overall_status(
    *,
    accepted_task_count: int,
    test_improvement_task_count: int,
    task_count: int,
    parse_failure_count: int,
) -> str:
    if parse_failure_count:
        return "cross_task_llm_signal_mixed_parse_risk"
    if accepted_task_count == task_count and test_improvement_task_count == task_count:
        return "cross_task_llm_signal_positive"
    if accepted_task_count > 0 or test_improvement_task_count > 0:
        return "cross_task_llm_signal_mixed"
    return "cross_task_llm_signal_negative"


def _risk_flags(*, base_url: str | None, parse_failure_count: int) -> list[str]:
    flags = [
        "small_segment_smoke",
        "not_cross_provider_validation",
        "not_strong_baseline_matrix",
        "segment_schema_partial_coverage",
    ]
    if base_url and ("127.0.0.1" in base_url or "localhost" in base_url):
        flags.append("local_model_only")
    if parse_failure_count:
        flags.append("llm_parse_failure_observed")
    return flags


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate_microdata_artifact(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != MICRODATA_SCHEMA_VERSION:
        raise ValueError("microdata artifact has unsupported schema_version")
    if set(artifact.get("splits", {})) != {"calibration", "heldout", "test"}:
        raise ValueError("microdata artifact must include calibration/heldout/test")
    for split_name, split in artifact["splits"].items():
        if "target_distributions" not in split:
            raise ValueError(f"{split_name} split missing target distributions")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU ANES LLM simulator validation must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
