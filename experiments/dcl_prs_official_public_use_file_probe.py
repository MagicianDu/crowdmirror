from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.dcl_prs_gss_public_use_download import GSS_2024_STATA_URL  # noqa: E402


OFFICIAL_FILE_PROBE_SCHEMA_VERSION = "dcl-prs-official-public-use-file-probe-v1"


def build_official_public_use_file_probe(
    *,
    artifact_id: str,
    gss_download_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gss_verified = _is_gss_download_verified(gss_download_manifest)
    probe = {
        "schema_version": OFFICIAL_FILE_PROBE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "official_public_use_file_probe_partial",
        "gss_download_verified": gss_verified,
        "eurobarometer_download_verified": False,
        "source_results": {
            "gss": {
                "source_id": "gss",
                "official_source_url": GSS_2024_STATA_URL,
                "download_status": (
                    "download_verified" if gss_verified else "direct_url_available"
                ),
                "requires_login": False,
                "local_manifest_artifact_id": (
                    gss_download_manifest.get("artifact_id")
                    if gss_download_manifest
                    else None
                ),
            },
            "eurobarometer": {
                "source_id": "eurobarometer",
                "official_source_url": (
                    "https://www.gesis.org/en/eurobarometer-data-service/"
                    "data-and-documentation"
                ),
                "catalogue_url": "https://search.gesis.org/?lang=en",
                "download_status": "login_required_not_downloaded",
                "requires_login": True,
                "blocking_condition": (
                    "GESIS catalogue requires sign-in/registration for "
                    "microdata analysis file download."
                ),
            },
        },
        "ccf_a_claim_status": "not_claimable",
        "product_claim_status": "data_access_partial",
        "next_gate": "complete_eurobarometer_authenticated_download",
        "risk_flags": [
            "gss_only_download_verified",
            "eurobarometer_login_required",
            "not_multi_dataset_microdata_ready",
            "not_model_quality_evidence",
        ],
        "claim_boundary": {
            "summary": (
                "This probe verifies official public-use file access status. "
                "Only GSS is locally downloaded when a verified manifest is "
                "provided; Eurobarometer remains login-gated."
            )
        },
    }
    _assert_strict_json(probe)
    return probe


def write_official_public_use_file_probe(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-official-public-use-file-probe-current-001",
    gss_download_manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    gss_manifest = (
        json.loads(Path(gss_download_manifest_path).read_text())
        if gss_download_manifest_path
        else None
    )
    probe = build_official_public_use_file_probe(
        artifact_id=artifact_id,
        gss_download_manifest=gss_manifest,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(probe, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "probe": probe}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gss-download-manifest-path")
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_official_public_use_file_probe",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-official-public-use-file-probe-current-001",
    )
    args = parser.parse_args()
    written = write_official_public_use_file_probe(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
        gss_download_manifest_path=args.gss_download_manifest_path,
    )
    print(
        json.dumps(
            {
                "gss_download_verified": written["probe"]["gss_download_verified"],
                "index": written["index_path"],
                "overall_status": written["probe"]["overall_status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _is_gss_download_verified(manifest: dict[str, Any] | None) -> bool:
    return (
        manifest is not None
        and manifest.get("schema_version") == "dcl-prs-gss-public-use-download-v1"
        and manifest.get("download_verified") is True
    )


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
