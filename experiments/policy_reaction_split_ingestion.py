from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.policy_reaction_public_ingestion import (  # noqa: E402
    HTOPS_2506_PUF_MEMBER,
    HTOPS_2506_SOURCE_URL,
    build_policy_reaction_public_ingestion_artifact,
    load_htops_2506_puf_rows,
)


POLICY_REACTION_PUBLIC_DATA_SPLIT_SCHEMA_VERSION = (
    "policy-reaction-public-data-split-v1"
)
DEFAULT_SPLIT_MODULUS = 2
DEFAULT_CALIBRATION_REMAINDERS = (0,)
DEFAULT_EVALUATION_REMAINDERS = (1,)
CALIBRATION_CLAIM_BOUNDARY = (
    "Calibration official HPS/HTOPS split for prompt/persona anchoring; "
    "not model-quality validation."
)
EVALUATION_CLAIM_BOUNDARY = (
    "Held-out official HPS/HTOPS split for leakage-aware evaluation; "
    "not model-quality validation."
)
SPLIT_CLAIM_BOUNDARY = (
    "Official HPS/HTOPS row split for leakage-aware calibration/evaluation "
    "separation; not cross-source generalization evidence."
)


def build_policy_reaction_split_ingestion_artifact(
    rows: list[dict[str, Any]],
    *,
    artifact_id: str,
    source_url: str,
    source_file_name: str,
    source_file_sha256: str,
    zip_member: str,
    modulus: int = DEFAULT_SPLIT_MODULUS,
    calibration_remainders: tuple[int, ...] = DEFAULT_CALIBRATION_REMAINDERS,
    evaluation_remainders: tuple[int, ...] = DEFAULT_EVALUATION_REMAINDERS,
) -> dict[str, Any]:
    if not rows:
        raise ValueError("split ingestion artifact requires at least one PUF row")
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
    calibration = _build_split_projection(
        split_rows["calibration"],
        artifact_id=f"{artifact_id}-calibration",
        source_url=source_url,
        source_file_name=source_file_name,
        source_file_sha256=source_file_sha256,
        zip_member=zip_member,
        split_name="calibration",
        claim_boundary=CALIBRATION_CLAIM_BOUNDARY,
        parent_artifact_id=artifact_id,
    )
    evaluation = _build_split_projection(
        split_rows["evaluation"],
        artifact_id=f"{artifact_id}-evaluation",
        source_url=source_url,
        source_file_name=source_file_name,
        source_file_sha256=source_file_sha256,
        zip_member=zip_member,
        split_name="evaluation",
        claim_boundary=EVALUATION_CLAIM_BOUNDARY,
        parent_artifact_id=artifact_id,
    )

    overall_status = (
        "passed"
        if calibration["overall_status"] == "passed"
        and evaluation["overall_status"] == "passed"
        else "blocked_for_split_ingestion"
    )
    artifact = {
        "schema_version": POLICY_REACTION_PUBLIC_DATA_SPLIT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": overall_status,
        "source": {
            "source_id": "hps_htops_food_cost_core",
            "source_release_id": "htops_hps_2506",
            "source_url": source_url,
            "source_file_name": source_file_name,
            "source_file_sha256": source_file_sha256,
            "zip_member": zip_member,
        },
        "split_config": {
            "assignment_field": "SCRAMID",
            "assignment_method": "sha256_modulo",
            "calibration_remainders": list(calibration_remainders),
            "evaluation_remainders": list(evaluation_remainders),
            "modulus": modulus,
        },
        "data_profile": {
            "puf_row_count": len(rows),
            "assigned_row_count": sum(len(value) for value in split_rows.values()),
            "unassigned_row_count": len(split_rows["unassigned"]),
            "calibration_row_count": len(split_rows["calibration"]),
            "evaluation_row_count": len(split_rows["evaluation"]),
        },
        "splits": {
            "calibration": calibration,
            "evaluation": evaluation,
        },
        "claim_boundary": SPLIT_CLAIM_BOUNDARY,
        "claim_boundaries": [
            SPLIT_CLAIM_BOUNDARY,
            "The calibration split may be used to derive prompt/persona or prior "
            "anchors.",
            "The evaluation split is a row-level holdout from the same public "
            "source and release, so it does not establish cross-period or "
            "cross-source generalization.",
        ],
    }
    _assert_strict_json(artifact)
    return artifact


def extract_split_ingestion_artifact(
    split_artifact: dict[str, Any],
    split_name: str,
) -> dict[str, Any]:
    if split_artifact.get("schema_version") != (
        POLICY_REACTION_PUBLIC_DATA_SPLIT_SCHEMA_VERSION
    ):
        raise ValueError("unsupported split artifact schema_version")
    splits = split_artifact.get("splits")
    if not isinstance(splits, dict) or split_name not in splits:
        raise ValueError(f"split artifact missing split {split_name!r}")
    projection = copy.deepcopy(splits[split_name])
    _assert_strict_json(projection)
    return projection


def write_policy_reaction_split_ingestion_artifacts(
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
) -> dict[str, str]:
    rows = load_htops_2506_puf_rows(puf_path, zip_member=zip_member)
    artifact = build_policy_reaction_split_ingestion_artifact(
        rows,
        artifact_id=artifact_id,
        source_url=source_url,
        source_file_name=source_file_name,
        source_file_sha256=source_file_sha256,
        zip_member=zip_member,
    )

    output_path = Path(path)
    calibration_path = Path(calibration_output_path)
    evaluation_path = Path(evaluation_output_path)
    for target_path, payload in (
        (output_path, artifact),
        (calibration_path, extract_split_ingestion_artifact(artifact, "calibration")),
        (evaluation_path, extract_split_ingestion_artifact(artifact, "evaluation")),
    ):
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )

    return {
        "calibration_output_path": str(calibration_path),
        "evaluation_output_path": str(evaluation_path),
        "output_path": str(output_path),
        "status": artifact["overall_status"],
    }


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
        default="policy-reaction-htops-2506-split-ingestion-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-htops-2506-split-ingestion-001.json"
        ),
    )
    parser.add_argument(
        "--calibration-output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-htops-2506-calibration-ingestion-001.json"
        ),
    )
    parser.add_argument(
        "--evaluation-output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-htops-2506-evaluation-ingestion-001.json"
        ),
    )
    args = parser.parse_args()

    source_file_sha256 = args.source_file_sha256 or _sha256_file(args.puf)
    written = write_policy_reaction_split_ingestion_artifacts(
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


def _build_split_projection(
    rows: list[dict[str, Any]],
    *,
    artifact_id: str,
    source_url: str,
    source_file_name: str,
    source_file_sha256: str,
    zip_member: str,
    split_name: str,
    claim_boundary: str,
    parent_artifact_id: str,
) -> dict[str, Any]:
    artifact = build_policy_reaction_public_ingestion_artifact(
        rows,
        artifact_id=artifact_id,
        source_url=source_url,
        source_file_name=source_file_name,
        source_file_sha256=source_file_sha256,
        zip_member=zip_member,
    )
    artifact["source"]["source_split"] = split_name
    artifact["source"]["parent_split_artifact_id"] = parent_artifact_id
    artifact["claim_boundary"] = claim_boundary
    artifact["claim_boundaries"] = [
        claim_boundary,
        "This split projection preserves the public ingestion schema so official "
        "segment benchmarks can consume it directly.",
        "It is separated by hashed public-use row id, not by source, geography, "
        "or survey period.",
    ]
    _assert_strict_json(artifact)
    return artifact


def _split_rows_by_scramid_modulo(
    rows: list[dict[str, Any]],
    *,
    modulus: int,
    calibration_remainders: tuple[int, ...],
    evaluation_remainders: tuple[int, ...],
) -> dict[str, list[dict[str, Any]]]:
    split_rows: dict[str, list[dict[str, Any]]] = {
        "calibration": [],
        "evaluation": [],
        "unassigned": [],
    }
    for row in rows:
        if "SCRAMID" not in row or row["SCRAMID"] == "":
            split_rows["unassigned"].append(row)
            continue
        remainder = _sha256_modulo(row["SCRAMID"], modulus)
        if remainder in calibration_remainders:
            split_rows["calibration"].append(row)
        elif remainder in evaluation_remainders:
            split_rows["evaluation"].append(row)
        else:
            split_rows["unassigned"].append(row)
    return split_rows


def _validate_split_config(
    *,
    modulus: int,
    calibration_remainders: tuple[int, ...],
    evaluation_remainders: tuple[int, ...],
) -> None:
    if modulus <= 1:
        raise ValueError("split modulus must be greater than 1")
    all_remainders = set(calibration_remainders) | set(evaluation_remainders)
    if any(remainder < 0 or remainder >= modulus for remainder in all_remainders):
        raise ValueError("split remainders must be within [0, modulus)")
    if set(calibration_remainders) & set(evaluation_remainders):
        raise ValueError("calibration and evaluation remainders must not overlap")
    if not calibration_remainders or not evaluation_remainders:
        raise ValueError("calibration and evaluation remainders must be non-empty")


def _sha256_modulo(value: Any, modulus: int) -> int:
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()
    return int(digest, 16) % modulus


def _sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
