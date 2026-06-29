from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from pathlib import Path
from typing import Any
from zipfile import ZipFile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


GSS_POLICY_TASK_BINDING_SCHEMA_VERSION = "dcl-prs-gss-policy-task-binding-v1"
GSS_TASK_SLICE_ID = "gss_public_health_confidence_attitude_v1"

REQUIRED_VARIABLE_BINDINGS = {
    "cohort": {
        "age_group": "age",
        "education": "educ",
        "income": "realinc",
        "political_views": "polviews",
    },
    "policy_or_question": "conmedic",
    "response_distribution": "conmedic",
}


def build_gss_policy_task_binding(
    *,
    artifact_id: str,
    gss_download_manifest: dict[str, Any],
    stata_metadata: dict[str, Any],
) -> dict[str, Any]:
    _validate_gss_download_manifest(gss_download_manifest)
    variables = _variable_index(stata_metadata)
    cohort_bindings = {
        field_name: _bind_variable(
            variable_name=variable_name,
            field_role="cohort",
            variables=variables,
        )
        for field_name, variable_name in REQUIRED_VARIABLE_BINDINGS["cohort"].items()
    }
    policy_variable = REQUIRED_VARIABLE_BINDINGS["policy_or_question"]
    policy_binding = _bind_variable(
        variable_name=policy_variable,
        field_role="policy_or_question",
        variables=variables,
    )
    response_binding = {
        "field_role": "response_distribution",
        "source_variable_name": policy_variable,
        "response_values": variables[policy_variable].get("observed_response_values", []),
        "binding_status": "variable_bound",
    }
    required_fields_bound = all(
        item["binding_status"] == "variable_bound"
        for item in [*cohort_bindings.values(), policy_binding, response_binding]
    )
    binding = {
        "schema_version": GSS_POLICY_TASK_BINDING_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": (
            "gss_policy_task_variables_bound"
            if required_fields_bound
            else "gss_policy_task_variables_incomplete"
        ),
        "source_artifact_id": gss_download_manifest["artifact_id"],
        "task_slice_id": GSS_TASK_SLICE_ID,
        "source_id": "gss",
        "required_fields_bound": required_fields_bound,
        "field_bindings": {
            "cohort": cohort_bindings,
            "policy_or_question": policy_binding,
            "response_distribution": response_binding,
        },
        "metadata_summary": {
            "variable_count": stata_metadata.get("variable_count", len(variables)),
            "bound_variable_names": sorted(
                {
                    *REQUIRED_VARIABLE_BINDINGS["cohort"].values(),
                    policy_variable,
                }
            ),
        },
        "ccf_a_claim_status": "not_claimable",
        "product_claim_status": "data_binding_ready_not_runtime_validated",
        "next_gate": "run_gss_policy_task_ingestion_smoke",
        "risk_flags": [
            "single_dataset_binding_only",
            "no_real_effect_validation",
            "not_model_quality_evidence",
        ],
        "claim_boundary": {
            "uses_test_split_for_current_claim": False,
            "summary": (
                "This artifact binds verified GSS variables to the policy "
                "reaction task schema. It does not validate DCL-PRS model "
                "quality or cross-dataset generalization."
            ),
        },
    }
    _assert_strict_json(binding)
    return binding


def write_gss_policy_task_binding(
    *,
    gss_download_manifest_path: str | Path,
    source_path: str | Path,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-gss-policy-task-binding-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(Path(gss_download_manifest_path).read_text())
    metadata = extract_gss_stata_metadata(source_path=source_path)
    binding = build_gss_policy_task_binding(
        artifact_id=artifact_id,
        gss_download_manifest=manifest,
        stata_metadata=metadata,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(binding, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "binding": binding}


def extract_gss_stata_metadata(*, source_path: str | Path) -> dict[str, Any]:
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
                return _extract_tabular_metadata(extracted)
    return _extract_tabular_metadata(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gss-download-manifest-path", required=True)
    parser.add_argument("--source-path", required=True)
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_gss_policy_task_binding",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-gss-policy-task-binding-current-001",
    )
    args = parser.parse_args()
    written = write_gss_policy_task_binding(
        gss_download_manifest_path=args.gss_download_manifest_path,
        source_path=args.source_path,
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "overall_status": written["binding"]["overall_status"],
                "required_fields_bound": written["binding"]["required_fields_bound"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _extract_tabular_metadata(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".dta":
        return _extract_stata_metadata(path)
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
    variables = {name: {"name": name} for name in header}
    return {"variable_count": len(variables), "variables": variables}


def _extract_stata_metadata(path: Path) -> dict[str, Any]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("pandas is required to read GSS Stata metadata") from exc

    try:
        data = pd.read_stata(path, convert_categoricals=True)
    except ValueError:
        return _extract_csv_header_metadata(path)
    variables = {}
    for column in data.columns:
        series = data[column].dropna()
        observed = [
            str(value)
            for value in series.astype(str).value_counts().sort_index().index[:20]
        ]
        variables[str(column)] = {
            "name": str(column),
            "observed_response_values": observed,
        }
    return {"variable_count": len(variables), "variables": variables}


def _extract_csv_header_metadata(path: Path) -> dict[str, Any]:
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
    variables = {name: {"name": name} for name in header}
    return {"variable_count": len(variables), "variables": variables}


def _variable_index(metadata: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_variables = metadata.get("variables")
    if not isinstance(raw_variables, dict):
        raise ValueError("stata_metadata must contain variables")
    variables = {str(name): value for name, value in raw_variables.items()}
    required = {
        *REQUIRED_VARIABLE_BINDINGS["cohort"].values(),
        REQUIRED_VARIABLE_BINDINGS["policy_or_question"],
    }
    missing = sorted(name for name in required if name not in variables)
    if missing:
        raise ValueError(f"stata_metadata missing required variables: {missing}")
    return variables


def _bind_variable(
    *,
    variable_name: str,
    field_role: str,
    variables: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    variable = variables[variable_name]
    return {
        "field_role": field_role,
        "variable_name": variable_name,
        "variable_metadata": variable,
        "binding_status": "variable_bound",
    }


def _validate_gss_download_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != "dcl-prs-gss-public-use-download-v1":
        raise ValueError("gss_download_manifest has unsupported schema_version")
    if manifest.get("download_verified") is not True:
        raise ValueError("gss_download_manifest must be download_verified")
    if not isinstance(manifest.get("artifact_id"), str):
        raise ValueError("gss_download_manifest must contain artifact_id")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
