from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


GSS_DOWNLOAD_SCHEMA_VERSION = "dcl-prs-gss-public-use-download-v1"
GSS_2024_STATA_URL = (
    "https://gss.norc.org/content/dam/gss/get-the-data/documents/stata/"
    "2024_stata.zip"
)


def build_gss_public_use_download_manifest(
    *,
    artifact_id: str,
    source_path: str | Path,
) -> dict[str, Any]:
    path = Path(source_path)
    if not path.exists():
        raise ValueError("source_path does not exist")
    payload = path.read_bytes()
    manifest = {
        "schema_version": GSS_DOWNLOAD_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "gss_public_use_download_verified",
        "source_id": "gss",
        "source_name": "General Social Survey 2024 Cross-section",
        "official_source_url": GSS_2024_STATA_URL,
        "local_path": str(path),
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "download_verified": True,
        "file_format": "stata_zip",
        "ccf_a_claim_status": "not_claimable",
        "product_claim_status": "data_file_verified_only",
        "next_gate": "bind_gss_public_use_variables_to_policy_tasks",
        "risk_flags": [
            "single_dataset_download_only",
            "variables_not_bound_to_policy_tasks",
            "not_model_quality_evidence",
        ],
        "claim_boundary": {
            "summary": (
                "This manifest verifies a local GSS public-use ZIP by size and "
                "SHA-256 only. It does not bind variables or validate DCL-PRS."
            )
        },
    }
    _assert_strict_json(manifest)
    return manifest


def write_gss_public_use_download_manifest(
    *,
    source_path: str | Path,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-gss-public-use-download-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    manifest = build_gss_public_use_download_manifest(
        artifact_id=artifact_id,
        source_path=source_path,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-path", required=True)
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_gss_public_use_download",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-gss-public-use-download-current-001",
    )
    args = parser.parse_args()
    written = write_gss_public_use_download_manifest(
        source_path=args.source_path,
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "byte_count": written["manifest"]["byte_count"],
                "download_verified": written["manifest"]["download_verified"],
                "index": written["index_path"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
