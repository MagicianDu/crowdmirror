from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact
from experiments.r6_public_outcome_proxy import build_r6_public_outcome_proxy


R6_PROXY_MAPPING_REVIEW_SCHEMA_VERSION = "r6-proxy-mapping-review-v1"
R6_PROXY_MAPPING_CLAIM_BOUNDARY = (
    "R6 proxy mapping review only; proxy labels are not direct field outcomes "
    "or direct attitude truth."
)


def build_r6_proxy_mapping_review(
    *,
    artifact_id: str,
    run_id: str,
    public_outcome_proxies: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    proxies = public_outcome_proxies or [
        build_r6_public_outcome_proxy(
            artifact_id=f"{artifact_id}-htops-proxy",
            run_id=run_id,
        ),
        build_r6_public_outcome_proxy(
            artifact_id=f"{artifact_id}-anes-health-proxy",
            run_id=run_id,
            source_key="anes_health_heldout",
        ),
    ]
    mappings = [_mapping_record(proxy) for proxy in proxies]
    review = {
        "schema_version": R6_PROXY_MAPPING_REVIEW_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "mapping_review_ready",
        "public_proxy_count": len(proxies),
        "source_count": len({mapping["source_artifact_id"] for mapping in mappings}),
        "overall_mapping_status": "proxy_usable_with_boundary",
        "mappings": mappings,
        "required_report_wording": [
            "Use public proxy as bounded outcome signal, not as field validation.",
            "Report mapping rationale before using proxy error as model evidence.",
            "Do not accept global updates from same-case proxy feedback.",
        ],
        "source_refs": [proxy["artifact_id"] for proxy in proxies],
        "claim_boundaries": [R6_PROXY_MAPPING_CLAIM_BOUNDARY],
        "claim_boundary": R6_PROXY_MAPPING_CLAIM_BOUNDARY,
        "risk_flags": [
            "proxy_mapping_not_direct_truth",
            "public_proxy_not_field_validation",
            "same_case_feedback_not_global_acceptance",
        ],
        "blocking_gaps": [
            "needs_human_mapping_review_before_paper_claim",
            "needs_real_release_outcome_before_customer_validation_claim",
        ],
    }
    assert_strict_json(review)
    return review


def write_r6_proxy_mapping_review(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_proxy_mapping_review(**kwargs))


def _mapping_record(proxy: dict[str, Any]) -> dict[str, Any]:
    mapping = proxy["mapping_review"]
    public_source = proxy["public_source"]
    return {
        "source_key": proxy["source_key"],
        "source_artifact_id": public_source["source_artifact_id"],
        "source_name": public_source["source_name"],
        "mapped_case_id": proxy["target_case_id"],
        "target_response_option": mapping["target_response_option"],
        "mapping_direction": "reject_proxy",
        "mapping_rationale": mapping["mapping_rationale"],
        "observed_reject_proxy": proxy["metrics"]["observed_reject_proxy"],
        "usable_row_count": public_source["usable_row_count"],
        "split_role": public_source["split_role"],
        "mapping_status": "proxy_usable_with_boundary",
        "invalid_claims": [
            "not_direct_attitude_truth",
            "not_field_validation",
            "not_customer_behavior_outcome",
            "not_global_update_acceptance",
        ],
        "required_boundary": mapping["claim_boundary"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_proxy_mapping_review(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    review = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": review["artifact_id"],
                "output": str(output_path),
                "status": review["status"],
                "public_proxy_count": review["public_proxy_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
