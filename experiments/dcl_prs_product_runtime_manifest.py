from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.dcl_prs_dynamic_simulation import (  # noqa: E402
    build_dynamic_simulation_trace,
)
from experiments.dcl_prs_failure_attribution import (  # noqa: E402
    build_failure_attribution_index,
)
from experiments.dcl_prs_mechanism_program import (  # noqa: E402
    build_mechanism_program_index,
)
from experiments.dcl_prs_product_cohort_report import (  # noqa: E402
    build_product_cohort_report,
)


PRODUCT_RUNTIME_MANIFEST_SCHEMA_VERSION = "dcl-prs-product-runtime-manifest-v1"


def build_product_runtime_manifest(
    *,
    artifact_id: str,
    product_cohort_report: dict[str, Any],
) -> dict[str, Any]:
    _validate_product_cohort_report(product_cohort_report)
    routes = [
        {
            "route_id": f"report.{section}",
            "section": section,
            "artifact_ref": product_cohort_report["artifact_id"],
            "route_status": "connected_to_artifact_section",
        }
        for section in product_cohort_report["report_sections"]
    ]
    manifest = {
        "schema_version": PRODUCT_RUNTIME_MANIFEST_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "product_runtime_manifest_connection_ready",
        "report_artifact_id": product_cohort_report["artifact_id"],
        "runtime_routes": routes,
        "route_count": len(routes),
        "evidence_refs": product_cohort_report["runtime_manifest"]["artifact_refs"],
        "product_claim_status": "runtime_connection_only",
        "customer_validation_status": "not_validated",
        "next_gate": "run_product_runtime_validation",
        "risk_flags": [
            "runtime_connection_only",
            "not_customer_validated",
            "not_live_ui_trace",
        ],
        "claim_boundary": {
            "summary": (
                "Runtime manifest connects report sections to artifact-backed "
                "routes. It does not prove customer readiness or live UI quality."
            )
        },
    }
    _assert_strict_json(manifest)
    return manifest


def write_product_runtime_manifest(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-product-runtime-manifest-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    mechanism = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-current-001"
    )
    failure = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-current-001"
    )
    dynamic = build_dynamic_simulation_trace(
        artifact_id="dcl-prs-dynamic-simulation-current-001",
        mechanism_program_index=mechanism,
    )
    report = build_product_cohort_report(
        artifact_id="dcl-prs-product-cohort-report-current-001",
        mechanism_program_index=mechanism,
        failure_attribution_index=failure,
        dynamic_simulation=dynamic,
    )
    manifest = build_product_runtime_manifest(
        artifact_id=artifact_id,
        product_cohort_report=report,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_product_runtime_manifest",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-product-runtime-manifest-current-001",
    )
    args = parser.parse_args()
    written = write_product_runtime_manifest(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "overall_status": written["manifest"]["overall_status"],
                "route_count": written["manifest"]["route_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_product_cohort_report(report: dict[str, Any]) -> None:
    if report.get("schema_version") != "dcl-prs-product-cohort-report-v1":
        raise ValueError("product_cohort_report has unsupported schema_version")
    if not report.get("report_sections"):
        raise ValueError("product_cohort_report must contain sections")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
