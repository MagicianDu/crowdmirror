from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from zipfile import ZipFile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


GSS_POLICY_TASK_INGESTION_SMOKE_SCHEMA_VERSION = (
    "dcl-prs-gss-policy-task-ingestion-smoke-v1"
)


def build_gss_policy_task_ingestion_smoke(
    *,
    artifact_id: str,
    gss_policy_task_binding: dict[str, Any],
    records: list[dict[str, Any]],
    cohort_slice_limit: int = 20,
) -> dict[str, Any]:
    _validate_gss_policy_task_binding(gss_policy_task_binding)
    policy_variable = _policy_variable(gss_policy_task_binding)
    cohort_variables = _cohort_variables(gss_policy_task_binding)
    valid_records = [
        record
        for record in records
        if _normal_value(record.get(policy_variable)) is not None
    ]
    response_values = [
        _normal_value(record.get(policy_variable)) for record in valid_records
    ]
    response_distribution = _distribution(
        [value for value in response_values if value is not None]
    )
    smoke = {
        "schema_version": GSS_POLICY_TASK_INGESTION_SMOKE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "gss_policy_task_ingestion_smoke_ready",
        "source_artifact_id": gss_policy_task_binding["artifact_id"],
        "source_id": "gss",
        "task_slice_id": "gss_public_health_confidence_attitude_v1",
        "policy_variable": policy_variable,
        "cohort_variables": cohort_variables,
        "row_count": len(records),
        "valid_policy_response_count": len(valid_records),
        "response_distribution": response_distribution,
        "cohort_slice_distributions": _cohort_slice_distributions(
            records=valid_records,
            policy_variable=policy_variable,
            cohort_variables=cohort_variables,
            cohort_slice_limit=cohort_slice_limit,
        ),
        "ccf_a_claim_status": "not_claimable",
        "product_claim_status": "single_task_data_smoke_ready",
        "next_gate": "run_real_repair_effect_validation",
        "risk_flags": [
            "single_dataset_smoke_only",
            "single_policy_question_only",
            "not_model_quality_evidence",
        ],
        "claim_boundary": {
            "uses_test_split_for_current_claim": False,
            "summary": (
                "This artifact computes observable GSS policy-response "
                "distributions from bound public-use variables. It does not "
                "prove DCL-PRS calibration quality or CCF-A readiness."
            ),
        },
    }
    _assert_strict_json(smoke)
    return smoke


def write_gss_policy_task_ingestion_smoke(
    *,
    gss_policy_task_binding_path: str | Path,
    source_path: str | Path,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-gss-policy-task-smoke-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    binding = json.loads(Path(gss_policy_task_binding_path).read_text())
    records = read_gss_records(source_path=source_path)
    smoke = build_gss_policy_task_ingestion_smoke(
        artifact_id=artifact_id,
        gss_policy_task_binding=binding,
        records=records,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(smoke, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "smoke": smoke}


def read_gss_records(*, source_path: str | Path) -> list[dict[str, Any]]:
    path = Path(source_path)
    if not path.exists():
        raise ValueError("source_path does not exist")
    if path.suffix.lower() == ".zip":
        with ZipFile(path) as archive:
            dta_names = [name for name in archive.namelist() if name.lower().endswith(".dta")]
            if not dta_names:
                raise ValueError("source_path zip does not contain a .dta file")
            with tempfile.TemporaryDirectory() as temp_dir:
                extracted = Path(temp_dir) / Path(dta_names[0]).name
                extracted.write_bytes(archive.read(dta_names[0]))
                return _read_tabular_records(extracted)
    return _read_tabular_records(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gss-policy-task-binding-path", required=True)
    parser.add_argument("--source-path", required=True)
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_gss_policy_task_ingestion_smoke",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-gss-policy-task-smoke-current-001",
    )
    args = parser.parse_args()
    written = write_gss_policy_task_ingestion_smoke(
        gss_policy_task_binding_path=args.gss_policy_task_binding_path,
        source_path=args.source_path,
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "overall_status": written["smoke"]["overall_status"],
                "valid_policy_response_count": written["smoke"][
                    "valid_policy_response_count"
                ],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _read_tabular_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".dta":
        return _read_stata_records(path)
    with path.open(newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_stata_records(path: Path) -> list[dict[str, Any]]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("pandas is required to read GSS Stata records") from exc

    data = pd.read_stata(path, convert_categoricals=True)
    return data.to_dict(orient="records")


def _validate_gss_policy_task_binding(binding: dict[str, Any]) -> None:
    if binding.get("schema_version") != "dcl-prs-gss-policy-task-binding-v1":
        raise ValueError("gss_policy_task_binding has unsupported schema_version")
    if binding.get("overall_status") != "gss_policy_task_variables_bound":
        raise ValueError("gss_policy_task_binding must be variables_bound")
    if binding.get("required_fields_bound") is not True:
        raise ValueError("gss_policy_task_binding must bind required fields")


def _policy_variable(binding: dict[str, Any]) -> str:
    field_bindings = binding["field_bindings"]
    return str(
        field_bindings["response_distribution"].get(
            "source_variable_name",
            field_bindings["policy_or_question"]["variable_name"],
        )
    )


def _cohort_variables(binding: dict[str, Any]) -> dict[str, str]:
    return {
        axis_name: str(axis_binding["variable_name"])
        for axis_name, axis_binding in binding["field_bindings"]["cohort"].items()
    }


def _cohort_slice_distributions(
    *,
    records: list[dict[str, Any]],
    policy_variable: str,
    cohort_variables: dict[str, str],
    cohort_slice_limit: int,
) -> dict[str, dict[str, Any]]:
    output = {}
    for axis_name, variable_name in cohort_variables.items():
        grouped: dict[str, list[str]] = defaultdict(list)
        for record in records:
            cohort_value = _normal_value(record.get(variable_name))
            response_value = _normal_value(record.get(policy_variable))
            if cohort_value is not None and response_value is not None:
                grouped[cohort_value].append(response_value)
        top_groups = sorted(
            grouped.items(),
            key=lambda item: (-len(item[1]), item[0]),
        )[:cohort_slice_limit]
        output[axis_name] = {
            cohort_value: {
                "valid_policy_response_count": len(values),
                "response_distribution": _distribution(values),
            }
            for cohort_value, values in top_groups
        }
    return output


def _distribution(values: list[str]) -> dict[str, Any]:
    counts = dict(sorted(Counter(values).items()))
    denominator = sum(counts.values())
    probabilities = {
        key: count / denominator if denominator else 0.0
        for key, count in counts.items()
    }
    return {"counts": counts, "probabilities": probabilities}


def _normal_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "nat"}:
        return None
    return text


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
