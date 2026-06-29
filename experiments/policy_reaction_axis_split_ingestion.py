from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.policy_reaction_axis_ingestion import (  # noqa: E402
    build_policy_reaction_public_axis_ingestion_artifact,
)
from experiments.policy_reaction_public_ingestion import (  # noqa: E402
    HTOPS_2506_PUF_MEMBER,
    HTOPS_2506_SOURCE_URL,
    _sha256_file,
    load_htops_2506_puf_rows,
)
from experiments.policy_reaction_split_ingestion import (  # noqa: E402
    _split_rows_by_scramid_modulo,
    _validate_split_config,
)


POLICY_REACTION_PUBLIC_AXIS_SPLIT_SCHEMA_VERSION = "policy-reaction-public-axis-split-v1"


def build_policy_reaction_axis_split_ingestion_artifact(
    rows: list[dict[str, Any]],
    *,
    artifact_id: str,
    source_url: str,
    source_file_name: str,
    source_file_sha256: str,
    zip_member: str,
    modulus: int,
    calibration_remainders: tuple[int, ...],
    evaluation_remainders: tuple[int, ...],
) -> dict[str, Any]:
    if not rows:
        raise ValueError("axis split ingestion artifact requires at least one PUF row")
    _validate_split_config(
        modulus=modulus,
        calibration_remainders=calibration_remainders,
        evaluation_remainders=evaluation_remainders,
    )
    split_rows = _split_rows_by_scramid_modulo(
        rows,
        modulus=modulus,
        calibration_remainders=calibration_remainders,
        evaluation_remainders=evaluation_remainders,
    )
    calibration = _build_axis_split_projection(
        split_rows["calibration"],
        artifact_id=f"{artifact_id}-calibration",
        source_url=source_url,
        source_file_name=source_file_name,
        source_file_sha256=source_file_sha256,
        zip_member=zip_member,
        split_name="calibration",
        parent_artifact_id=artifact_id,
    )
    evaluation = _build_axis_split_projection(
        split_rows["evaluation"],
        artifact_id=f"{artifact_id}-evaluation",
        source_url=source_url,
        source_file_name=source_file_name,
        source_file_sha256=source_file_sha256,
        zip_member=zip_member,
        split_name="evaluation",
        parent_artifact_id=artifact_id,
    )
    artifact = {
        "schema_version": POLICY_REACTION_PUBLIC_AXIS_SPLIT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": (
            "passed"
            if calibration["overall_status"] == "passed" and evaluation["overall_status"] == "passed"
            else "blocked_for_axis_split_ingestion"
        ),
        "source": calibration["source"],
        "split_config": {
            "assignment_field": "SCRAMID",
            "assignment_method": "sha256_modulo",
            "calibration_remainders": list(calibration_remainders),
            "evaluation_remainders": list(evaluation_remainders),
            "modulus": modulus,
        },
        "data_profile": {
            "puf_row_count": len(rows),
            "calibration_row_count": len(split_rows["calibration"]),
            "evaluation_row_count": len(split_rows["evaluation"]),
            "unassigned_row_count": len(split_rows["unassigned"]),
        },
        "splits": {
            "calibration": calibration,
            "evaluation": evaluation,
        },
        "claim_boundary": (
            "Axis split projections are same-source hashed row partitions only; not cross-source generalization evidence."
        ),
    }
    json.dumps(artifact, allow_nan=False)
    return artifact


def extract_axis_split_ingestion_artifact(
    split_artifact: dict[str, Any], split_name: str
) -> dict[str, Any]:
    if split_artifact.get("schema_version") != POLICY_REACTION_PUBLIC_AXIS_SPLIT_SCHEMA_VERSION:
        raise ValueError("unsupported axis split artifact schema_version")
    projection = split_artifact.get("splits", {}).get(split_name)
    if not isinstance(projection, dict):
        raise ValueError(f"split artifact missing split {split_name!r}")
    return copy.deepcopy(projection)


def write_policy_reaction_axis_split_ingestion_artifacts(
    path: str | Path,
    *,
    calibration_output_path: str | Path,
    evaluation_output_path: str | Path,
    puf_path: str | Path,
    artifact_id: str,
    source_url: str,
    source_file_name: str,
    source_file_sha256: str,
    zip_member: str,
    modulus: int = 2,
    calibration_remainders: tuple[int, ...] = (0,),
    evaluation_remainders: tuple[int, ...] = (1,),
) -> dict[str, str]:
    rows = load_htops_2506_puf_rows(puf_path, zip_member=zip_member)
    artifact = build_policy_reaction_axis_split_ingestion_artifact(
        rows,
        artifact_id=artifact_id,
        source_url=source_url,
        source_file_name=source_file_name,
        source_file_sha256=source_file_sha256,
        zip_member=zip_member,
        modulus=modulus,
        calibration_remainders=calibration_remainders,
        evaluation_remainders=evaluation_remainders,
    )
    output_path = Path(path)
    calibration_path = Path(calibration_output_path)
    evaluation_path = Path(evaluation_output_path)
    for target_path, payload in (
        (output_path, artifact),
        (calibration_path, extract_axis_split_ingestion_artifact(artifact, "calibration")),
        (evaluation_path, extract_axis_split_ingestion_artifact(artifact, "evaluation")),
    ):
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
    return {
        "output_path": str(output_path),
        "calibration_output_path": str(calibration_path),
        "evaluation_output_path": str(evaluation_path),
        "status": artifact["overall_status"],
    }


def _build_axis_split_projection(
    rows: list[dict[str, Any]],
    *,
    artifact_id: str,
    source_url: str,
    source_file_name: str,
    source_file_sha256: str,
    zip_member: str,
    split_name: str,
    parent_artifact_id: str,
) -> dict[str, Any]:
    artifact = build_policy_reaction_public_axis_ingestion_artifact(
        rows,
        artifact_id=artifact_id,
        source_url=source_url,
        source_file_name=source_file_name,
        source_file_sha256=source_file_sha256,
        zip_member=zip_member,
    )
    artifact["source"]["source_split"] = split_name
    artifact["source"]["parent_split_artifact_id"] = parent_artifact_id
    artifact["claim_boundaries"] = [
        "This split projection preserves the axis ingestion schema so axis benchmarks can consume it directly.",
        "It is separated by hashed public-use row id, not by source, geography, or survey period.",
    ]
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--puf",
        default="data/raw/hps_htops_2506/HTOPS_HPS_2506_CSV.zip",
    )
    parser.add_argument("--zip-member", default=HTOPS_2506_PUF_MEMBER)
    parser.add_argument("--source-url", default=HTOPS_2506_SOURCE_URL)
    parser.add_argument("--source-file-name", default="HTOPS_HPS_2506_CSV.zip")
    parser.add_argument("--source-file-sha256", default=None)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-htops-2506-axis-split-ingestion-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-htops-2506-axis-split-ingestion-001.json"
        ),
    )
    parser.add_argument(
        "--calibration-output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-htops-2506-axis-calibration-ingestion-001.json"
        ),
    )
    parser.add_argument(
        "--evaluation-output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-htops-2506-axis-evaluation-ingestion-001.json"
        ),
    )
    args = parser.parse_args()
    source_file_sha256 = args.source_file_sha256 or _sha256_file(args.puf)
    written = write_policy_reaction_axis_split_ingestion_artifacts(
        args.output,
        calibration_output_path=args.calibration_output,
        evaluation_output_path=args.evaluation_output,
        puf_path=args.puf,
        artifact_id=args.artifact_id,
        source_url=args.source_url,
        source_file_name=args.source_file_name,
        source_file_sha256=source_file_sha256,
        zip_member=args.zip_member,
    )
    print(json.dumps(written, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
