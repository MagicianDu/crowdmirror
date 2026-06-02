import json
import subprocess
import sys

from experiments.dcl_prs_gss_public_use_download import (
    build_gss_public_use_download_manifest,
)
from experiments.dcl_prs_official_public_use_file_probe import (
    build_official_public_use_file_probe,
)


def test_official_public_use_file_probe_marks_gss_download_and_eurobarometer_login():
    gss_manifest = {
        "schema_version": "dcl-prs-gss-public-use-download-v1",
        "artifact_id": "dcl-prs-gss-public-use-download-test",
        "download_verified": True,
        "byte_count": 123,
        "sha256": "abc",
    }

    probe = build_official_public_use_file_probe(
        artifact_id="dcl-prs-official-public-use-file-probe-test",
        gss_download_manifest=gss_manifest,
    )

    assert probe["schema_version"] == "dcl-prs-official-public-use-file-probe-v1"
    assert probe["overall_status"] == "official_public_use_file_probe_partial"
    assert probe["gss_download_verified"] is True
    assert probe["eurobarometer_download_verified"] is False
    assert probe["source_results"]["gss"]["download_status"] == "download_verified"
    assert probe["source_results"]["eurobarometer"]["download_status"] == (
        "login_required_not_downloaded"
    )
    assert probe["next_gate"] == "complete_eurobarometer_authenticated_download"
    json.dumps(probe, allow_nan=False)


def test_official_public_use_file_probe_script_writes_artifact(tmp_path):
    source_file = tmp_path / "2024_stata.zip"
    source_file.write_bytes(b"gss-public-use-fixture")
    gss_manifest = build_gss_public_use_download_manifest(
        artifact_id="dcl-prs-gss-public-use-download-test",
        source_path=source_file,
    )
    manifest_path = tmp_path / "gss_manifest.json"
    manifest_path.write_text(json.dumps(gss_manifest))
    output_dir = tmp_path / "probe"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_official_public_use_file_probe.py",
            "--gss-download-manifest-path",
            str(manifest_path),
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-official-public-use-file-probe-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "gss_download_verified": True,
        "index": str(output_dir / "dcl-prs-official-public-use-file-probe-test.json"),
        "overall_status": "official_public_use_file_probe_partial",
    }
