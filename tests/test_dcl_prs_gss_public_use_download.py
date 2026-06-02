import hashlib
import json
import subprocess
import sys

from experiments.dcl_prs_gss_public_use_download import (
    build_gss_public_use_download_manifest,
)


def test_gss_public_use_download_manifest_hashes_local_file(tmp_path):
    source_file = tmp_path / "2024_stata.zip"
    source_file.write_bytes(b"gss-public-use-fixture")

    manifest = build_gss_public_use_download_manifest(
        artifact_id="dcl-prs-gss-public-use-download-test",
        source_path=source_file,
    )

    assert manifest["schema_version"] == "dcl-prs-gss-public-use-download-v1"
    assert manifest["overall_status"] == "gss_public_use_download_verified"
    assert manifest["download_verified"] is True
    assert manifest["byte_count"] == len(b"gss-public-use-fixture")
    assert manifest["sha256"] == hashlib.sha256(
        b"gss-public-use-fixture"
    ).hexdigest()
    assert manifest["source_id"] == "gss"
    json.dumps(manifest, allow_nan=False)


def test_gss_public_use_download_script_writes_manifest(tmp_path):
    source_file = tmp_path / "2024_stata.zip"
    source_file.write_bytes(b"gss-public-use-fixture")
    output_dir = tmp_path / "manifest"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_gss_public_use_download.py",
            "--source-path",
            str(source_file),
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-gss-public-use-download-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "byte_count": len(b"gss-public-use-fixture"),
        "download_verified": True,
        "index": str(output_dir / "dcl-prs-gss-public-use-download-test.json"),
    }
