from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from html import unescape
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)


R12_PUBLIC_TARGET_OUTCOME_AVAILABILITY_REFRESH_SCHEMA_VERSION = (
    "r12-public-target-outcome-availability-refresh-v1"
)

EXPECTED_PUBLIC_REPORT = (
    "July 2026 Air Travel Consumer Report (May 2026 Data)"
)
OFFICIAL_REPORTS_INDEX_URL = (
    "https://www.transportation.gov/individuals/"
    "aviation-consumer-protection/air-travel-consumer-reports"
)
LATEST_NEWS_URL = "https://www.transportation.gov/airconsumer/latest-news"


def build_r12_public_target_outcome_availability_refresh(
    *,
    artifact_id: str,
    run_id: str,
    checked_at: str,
    official_reports_index_snapshot: str,
    latest_news_snapshot: str = "",
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    checked_at = non_empty_string(checked_at, field="checked_at")
    official_reports_index_snapshot = non_empty_string(
        official_reports_index_snapshot,
        field="official_reports_index_snapshot",
    )
    _validate_usable_official_snapshot(official_reports_index_snapshot)

    combined_snapshot = "\n".join(
        [official_reports_index_snapshot, latest_news_snapshot]
    )
    normalized_snapshot = _normalize_text(combined_snapshot)
    target_report_found = EXPECTED_PUBLIC_REPORT in normalized_snapshot
    target_table_available = target_report_found and _target_table_hint_present(
        normalized_snapshot
    )
    latest_available_report = _latest_available_report(normalized_snapshot)
    target_pdf_url = (
        _target_pdf_url(combined_snapshot) if target_report_found else None
    )

    if target_report_found:
        status = (
            "r12_public_target_outcome_availability_refresh_target_report_found_not_ingested"
        )
        claim_level = "official_target_report_found_requires_raw_slice_ingestion"
        next_required_artifact = "r12_external_target_outcome_raw_slice_ingestion"
        allowed_claims = [
            (
                "target report is available but raw outcome slice is not "
                "ingested, so Product validation remains blocked."
            )
        ]
        acceptance_decision = (
            "accept_target_report_found_keep_revalidation_blocked_until_raw_slice_ingestion"
        )
    else:
        status = (
            "r12_public_target_outcome_availability_refresh_pending_target_report_not_found"
        )
        claim_level = "official_source_checked_target_outcome_not_available"
        next_required_artifact = (
            "r12_public_target_outcome_availability_refresh_or_customer_field_slice"
        )
        allowed_claims = [
            (
                "Official source snapshots were checked and the target report "
                "was not found."
            )
        ]
        acceptance_decision = (
            "accept_official_source_checked_keep_waiting_for_target_outcome_or_customer_slice"
        )

    report = {
        "schema_version": (
            R12_PUBLIC_TARGET_OUTCOME_AVAILABILITY_REFRESH_SCHEMA_VERSION
        ),
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "claim_level": claim_level,
        "availability_refresh_summary": {
            "checked_at": checked_at,
            "official_reports_index_url": OFFICIAL_REPORTS_INDEX_URL,
            "latest_news_url": LATEST_NEWS_URL,
            "official_reports_index_snapshot_sha256": _sha256_text(
                official_reports_index_snapshot
            ),
            "latest_news_snapshot_sha256": _sha256_text(latest_news_snapshot),
            "official_reports_index_snapshot_bytes": len(
                official_reports_index_snapshot.encode("utf-8")
            ),
            "latest_news_snapshot_bytes": len(
                latest_news_snapshot.encode("utf-8")
            ),
        },
        "public_source_availability": {
            "expected_public_report": EXPECTED_PUBLIC_REPORT,
            "latest_available_report": latest_available_report,
            "target_report_found": target_report_found,
            "target_pdf_url": target_pdf_url,
            "target_table_available": target_table_available,
        },
        "acceptance_gates": {
            "official_source_snapshot_checked": True,
            "target_report_found": target_report_found,
            "target_table_available": target_table_available,
            "target_outcome_artifact_present": False,
            "field_or_pre_outcome_revalidation_ready": False,
            "field_outcome_validated": False,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "acceptance_decision": acceptance_decision,
        "next_required_artifact": next_required_artifact,
        "source_refs": [
            "dot_air_travel_consumer_reports_index_snapshot",
            "dot_airconsumer_latest_news_snapshot",
        ],
        "source_registry": [
            {
                "artifact_id": "dot_air_travel_consumer_reports_index_snapshot",
                "path": OFFICIAL_REPORTS_INDEX_URL,
                "snapshot_sha256": _sha256_text(
                    official_reports_index_snapshot
                ),
            },
            {
                "artifact_id": "dot_airconsumer_latest_news_snapshot",
                "path": LATEST_NEWS_URL,
                "snapshot_sha256": _sha256_text(latest_news_snapshot),
            },
        ],
        "allowed_claims": allowed_claims,
        "blocked_claims": [
            "target outcome artifact present",
            "target outcome raw slice ingested",
            "pre-outcome/customer field revalidation passed",
            "field_outcome_validated=true",
            "Product default can use target outcome validation by default",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_public_target_outcome_availability_refresh(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_public_target_outcome_availability_refresh(**kwargs),
    )


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _validate_usable_official_snapshot(snapshot: str) -> None:
    normalized = _normalize_text(snapshot).lower()
    blocked_markers = [
        "access denied",
        "you don't have permission",
        "request blocked",
    ]
    if any(marker in normalized for marker in blocked_markers):
        raise ValueError("official source snapshot is not a usable ATCR page")
    if "air travel consumer report" not in normalized:
        raise ValueError("official source snapshot is not a usable ATCR page")


def _latest_available_report(normalized_snapshot: str) -> str:
    matches = re.findall(
        r"(January|February|March|April|May|June|July|August|September|October|November|December) "
        r"2026 Air Travel Consumer Report \([^)]+Data\)",
        normalized_snapshot,
    )
    report_matches = re.findall(
        r"((?:January|February|March|April|May|June|July|August|September|October|November|December) "
        r"2026 Air Travel Consumer Report \([^)]+Data\))",
        normalized_snapshot,
    )
    if not matches or not report_matches:
        return ""
    month_order = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
    }
    return max(
        report_matches,
        key=lambda title: month_order[title.split(" ", 1)[0]],
    )


def _target_table_hint_present(normalized_snapshot: str) -> bool:
    return "Table 3" in normalized_snapshot and "Consumer Complaints" in normalized_snapshot


def _target_pdf_url(snapshot: str) -> str | None:
    matches = re.findall(
        r'href=["\']([^"\']*July[^"\']*2026[^"\']*ATCR[^"\']*\.pdf)["\']',
        snapshot,
        flags=re.IGNORECASE,
    )
    return unescape(matches[0]) if matches else None


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--checked-at", required=True)
    parser.add_argument(
        "--official-reports-index-snapshot-path",
        required=True,
    )
    parser.add_argument("--latest-news-snapshot-path")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    index_snapshot = Path(
        args.official_reports_index_snapshot_path
    ).read_text()
    latest_news_snapshot = (
        Path(args.latest_news_snapshot_path).read_text()
        if args.latest_news_snapshot_path
        else ""
    )
    output_path = write_r12_public_target_outcome_availability_refresh(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        checked_at=args.checked_at,
        official_reports_index_snapshot=index_snapshot,
        latest_news_snapshot=latest_news_snapshot,
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["status"],
                "target_report_found": artifact["public_source_availability"][
                    "target_report_found"
                ],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
