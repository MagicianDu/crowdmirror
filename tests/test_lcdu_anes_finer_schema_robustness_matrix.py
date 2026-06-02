import json
import subprocess
import sys

from experiments.lcdu_anes_finer_schema_robustness_matrix import (
    build_lcdu_anes_finer_schema_robustness_matrix,
)


def test_finer_schema_matrix_marks_positive_when_anchor_transfers():
    matrix = build_lcdu_anes_finer_schema_robustness_matrix(
        rows=_rows(),
        artifact_id="finer-schema-test",
        source_file_name="test.csv",
        schema_grid=[["party_or_ideology", "income"], ["party_or_ideology", "income", "age"]],
    )

    assert matrix["schema_version"] == "lcdu-anes-finer-schema-robustness-matrix-v1"
    assert matrix["overall_status"] == "finer_schema_robustness_signal_positive"
    assert matrix["positive_schema_count"] == 2
    assert matrix["max_axis_count"] == 3
    for schema in matrix["schema_results"]:
        assert schema["schema_status"] == "schema_positive"
        for task in schema["task_results"].values():
            assert task["candidate_accepted"] is True
            assert task["test_improved"] is True
    json.dumps(matrix, allow_nan=False)


def test_finer_schema_matrix_marks_insufficient_when_common_segments_missing():
    rows = _rows()
    rows = [dict(row, V241458x="21") for row in rows]
    rows[-1]["V241458x"] = "70"
    matrix = build_lcdu_anes_finer_schema_robustness_matrix(
        rows=rows,
        artifact_id="finer-schema-test",
        source_file_name="test.csv",
        schema_grid=[["party_or_ideology", "income", "age"]],
        min_segment_rows_per_split=2,
    )

    assert matrix["overall_status"] == "finer_schema_robustness_signal_negative"
    assert "finer_schema_instability_or_sparsity_observed" in matrix["risk_flags"]


def test_finer_schema_matrix_script_writes_json(tmp_path):
    input_csv = tmp_path / "anes.csv"
    output = tmp_path / "finer.json"
    _write_csv(input_csv, _rows())

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_anes_finer_schema_robustness_matrix.py",
            "--input-csv",
            str(input_csv),
            "--output",
            str(output),
            "--artifact-id",
            "finer-schema-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["status"] == (
        "finer_schema_robustness_signal_positive"
    )
    assert json.loads(output.read_text())["artifact_id"] == "finer-schema-test"


def _rows() -> list[dict[str, str]]:
    rows = []
    for split_group, case_ids in {
        "calibration": ["5", "10", "15", "20"],
        "heldout": ["2", "7", "12", "17"],
        "test": ["1", "6", "11", "16"],
    }.items():
        for index, case_id in enumerate(case_ids):
            liberal = index % 2 == 0
            rows.append(
                {
                    "V240001": case_id,
                    "V240103a": "1",
                    "V241245": "2" if liberal else "6",
                    "V241258": "2" if liberal else "6",
                    "V241458x": "25" if index < 2 else "70",
                    "V241465x": "4",
                    "V241566x": "8" if liberal else "25",
                    "V241177": "2" if liberal else "6",
                    "V241550": "1",
                    "V241501x": "1",
                }
            )
    return rows


def _write_csv(path, rows):
    fields = [
        "V240001",
        "V240103a",
        "V241245",
        "V241258",
        "V241458x",
        "V241465x",
        "V241566x",
        "V241177",
        "V241550",
        "V241501x",
    ]
    path.write_text(
        ",".join(fields)
        + "\n"
        + "\n".join(",".join(row[field] for field in fields) for row in rows)
        + "\n"
    )
