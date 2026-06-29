from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


R6_CLAIM_BOUNDARY = (
    "R6 foundation artifact. It supports prior-anchored interaction risk "
    "diagnosis and outcome-feedback learning only; it is not accuracy "
    "superiority evidence, not cross-domain validation, and not customer field "
    "validation."
)

R6_UPDATE_STATUSES = {
    "accepted",
    "case_local",
    "diagnostic_only",
    "rejected",
    "needs_more_outcomes",
}


def assert_strict_json(payload: Any) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("payload is not JSON serializable") from exc


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def write_json_artifact(path: str | Path, payload: dict[str, Any]) -> Path:
    assert_strict_json(payload)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return output


def non_empty_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def positive_integer(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def finite_number(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be finite")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def source_refs(value: Any, *, field: str = "source_refs") -> list[str]:
    return _non_empty_string_list(value, field=field)


def claim_boundaries(value: Any) -> list[str]:
    return _non_empty_string_list(value, field="claim_boundaries")


def risk_flags(value: Any) -> list[str]:
    return _non_empty_string_list(value, field="risk_flags")


def probability_distribution(
    value: Any,
    *,
    options: list[str],
    field: str,
) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a probability distribution object")
    options = [non_empty_string(option, field=f"{field}.option") for option in options]
    distribution: dict[str, float] = {}
    for option in options:
        if option not in value:
            raise ValueError(f"{field} missing option: {option}")
        probability = finite_number(value[option], field=f"{field}.{option}")
        if probability < 0 or probability > 1:
            raise ValueError(f"{field}.{option} must be between 0 and 1")
        distribution[option] = probability
    extra = set(value) - set(options)
    if extra:
        raise ValueError(f"{field} contains unknown options: {sorted(extra)}")
    if not math.isclose(sum(distribution.values()), 1.0, abs_tol=1e-9):
        raise ValueError(f"{field} must sum to 1.0")
    return distribution


def rounded_distribution(value: dict[str, float], *, digits: int = 2) -> dict[str, float]:
    return {key: round(probability, digits) for key, probability in value.items()}


def _non_empty_string_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    items = []
    for index, item in enumerate(value):
        items.append(non_empty_string(item, field=f"{field}[{index}]"))
    if not items:
        raise ValueError(f"{field} must contain at least one item")
    return items
