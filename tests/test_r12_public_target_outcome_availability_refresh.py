import json
import subprocess
import sys

from experiments.r12_public_target_outcome_availability_refresh import (
    R12_PUBLIC_TARGET_OUTCOME_AVAILABILITY_REFRESH_SCHEMA_VERSION,
    build_r12_public_target_outcome_availability_refresh,
)


PENDING_OFFICIAL_INDEX = """
<h1>Air Travel Consumer Reports</h1>
<a href="/resources/june-2026-air-travel-consumer-report-april-2026">
June 2026 Air Travel Consumer Report (April 2026 Data)
</a>
<a href="/resources/may-2026-air-travel-consumer-report-march-and">
May 2026 Air Travel Consumer Report (March and January - March 2026 Data)
</a>
"""


TARGET_FOUND_OFFICIAL_INDEX = """
<h1>Air Travel Consumer Reports</h1>
<a href="/resources/july-2026-air-travel-consumer-report-may-2026">
July 2026 Air Travel Consumer Report (May 2026 Data)
</a>
<a href="/sites/dot.gov/files/2026-07/July%202026%20ATCR.pdf">
July 2026 ATCR.pdf
</a>
<p>Data Included in this Report: Consumer Complaints, Table 3.</p>
"""


def test_r12_public_target_outcome_availability_refresh_records_pending_snapshot():
    report = build_r12_public_target_outcome_availability_refresh(
        artifact_id="r12-public-target-outcome-availability-refresh-test",
        run_id="r12-l33-test",
        checked_at="2026-06-28T15:40:00Z",
        official_reports_index_snapshot=PENDING_OFFICIAL_INDEX,
        latest_news_snapshot="Posted June 18, 2026",
    )

    assert report["schema_version"] == (
        R12_PUBLIC_TARGET_OUTCOME_AVAILABILITY_REFRESH_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_public_target_outcome_availability_refresh_pending_target_report_not_found"
    )
    assert report["claim_level"] == (
        "official_source_checked_target_outcome_not_available"
    )
    assert report["public_source_availability"] == {
        "expected_public_report": (
            "July 2026 Air Travel Consumer Report (May 2026 Data)"
        ),
        "latest_available_report": (
            "June 2026 Air Travel Consumer Report (April 2026 Data)"
        ),
        "target_report_found": False,
        "target_pdf_url": None,
        "target_table_available": False,
    }
    assert report["acceptance_gates"] == {
        "official_source_snapshot_checked": True,
        "target_report_found": False,
        "target_table_available": False,
        "target_outcome_artifact_present": False,
        "field_or_pre_outcome_revalidation_ready": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert report["next_required_artifact"] == (
        "r12_public_target_outcome_availability_refresh_or_customer_field_slice"
    )
    assert "target outcome artifact present" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_public_target_outcome_availability_refresh_detects_target_but_stays_closed():
    report = build_r12_public_target_outcome_availability_refresh(
        artifact_id="r12-public-target-outcome-availability-refresh-test",
        run_id="r12-l33-target-found-test",
        checked_at="2026-06-28T15:40:00Z",
        official_reports_index_snapshot=TARGET_FOUND_OFFICIAL_INDEX,
        latest_news_snapshot=(
            "DOT released July 2026 Air Travel Consumer Report "
            "(May 2026 Data)."
        ),
    )

    assert report["status"] == (
        "r12_public_target_outcome_availability_refresh_target_report_found_not_ingested"
    )
    assert report["claim_level"] == (
        "official_target_report_found_requires_raw_slice_ingestion"
    )
    assert report["public_source_availability"][
        "latest_available_report"
    ] == "July 2026 Air Travel Consumer Report (May 2026 Data)"
    assert report["public_source_availability"]["target_report_found"] is True
    assert report["public_source_availability"]["target_table_available"] is True
    assert report["public_source_availability"]["target_pdf_url"] == (
        "/sites/dot.gov/files/2026-07/July%202026%20ATCR.pdf"
    )
    assert report["acceptance_gates"]["target_report_found"] is True
    assert report["acceptance_gates"]["target_table_available"] is True
    assert report["acceptance_gates"]["target_outcome_artifact_present"] is False
    assert report["acceptance_gates"][
        "field_or_pre_outcome_revalidation_ready"
    ] is False
    assert report["acceptance_gates"]["product_default_allowed"] is False
    assert report["next_required_artifact"] == (
        "r12_external_target_outcome_raw_slice_ingestion"
    )
    assert "target report is available but raw outcome slice is not ingested" in report[
        "allowed_claims"
    ][0]
    assert "field_outcome_validated=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_public_target_outcome_availability_refresh_rejects_access_denied_snapshot():
    try:
        build_r12_public_target_outcome_availability_refresh(
            artifact_id="r12-public-target-outcome-availability-refresh-test",
            run_id="r12-l33-access-denied-test",
            checked_at="2026-06-28T15:40:00Z",
            official_reports_index_snapshot="<H1>Access Denied</H1>",
            latest_news_snapshot="",
        )
    except ValueError as exc:
        assert "official source snapshot is not a usable ATCR page" in str(exc)
    else:
        raise AssertionError("expected access denied snapshot to be rejected")


def test_r12_public_target_outcome_availability_refresh_cli_writes_artifact(
    tmp_path,
):
    index_path = tmp_path / "official-index.html"
    news_path = tmp_path / "latest-news.html"
    output = tmp_path / "availability-refresh.json"
    index_path.write_text(PENDING_OFFICIAL_INDEX)
    news_path.write_text("Posted June 18, 2026")

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_public_target_outcome_availability_refresh.py",
            "--artifact-id",
            "r12-public-target-outcome-availability-refresh-cli",
            "--run-id",
            "r12-l33-cli-test",
            "--checked-at",
            "2026-06-28T15:40:00Z",
            "--official-reports-index-snapshot-path",
            str(index_path),
            "--latest-news-snapshot-path",
            str(news_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == (
        "r12-public-target-outcome-availability-refresh-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-public-target-outcome-availability-refresh-cli",
        "output": str(output),
        "status": (
            "r12_public_target_outcome_availability_refresh_pending_target_report_not_found"
        ),
        "target_report_found": False,
    }
