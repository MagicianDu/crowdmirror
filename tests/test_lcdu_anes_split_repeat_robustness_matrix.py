import json
import subprocess
import sys

from experiments.lcdu_anes_split_repeat_robustness_matrix import (
    build_lcdu_anes_split_repeat_robustness_matrix,
)


def test_split_repeat_matrix_aggregates_constrained_lcdu_metrics():
    matrix = build_lcdu_anes_split_repeat_robustness_matrix(
        rows=_rows(),
        artifact_id="split-repeat-test",
        split_salts=["salt-a", "salt-b"],
        k_grid=[1, 10],
        max_worst_segment_delta=0.0,
    )

    assert matrix["schema_version"] == "lcdu-anes-split-repeat-robustness-matrix-v1"
    assert matrix["validation_type"] == "lcdu_split_repeat_robustness_matrix"
    assert matrix["repeat_count"] == 2
    assert matrix["split_salts"] == ["salt-a", "salt-b"]
    assert set(matrix["task_summary"]) == {
        "climate_energy_regulation_attitude_v1",
        "public_health_medical_insurance_attitude_v1",
    }

    for task_summary in matrix["task_summary"].values():
        assert task_summary["repeat_count"] == 2
        assert 0.0 <= task_summary["constrained_anchor_win_rate"] <= 1.0
        assert 0.0 <= task_summary["test_worst_guard_pass_rate"] <= 1.0
        assert 0.0 <= task_summary["joint_success_rate"] <= 1.0
        assert "mean_test_loss_delta_vs_anchor" in task_summary
        assert "mean_test_worst_segment_delta_vs_anchor" in task_summary
        assert isinstance(task_summary["failure_modes"], list)

    assert "not_customer_field_validation" in matrix["risk_flags"]
    json.dumps(matrix, allow_nan=False)


def test_split_repeat_matrix_records_failure_modes():
    matrix = build_lcdu_anes_split_repeat_robustness_matrix(
        rows=_rows(),
        artifact_id="split-repeat-test",
        split_salts=["salt-a", "salt-b"],
        k_grid=[50],
        max_worst_segment_delta=-1.0,
    )

    assert matrix["overall_status"] in {
        "split_repeat_robustness_signal_mixed",
        "split_repeat_robustness_signal_negative",
    }
    assert matrix["joint_success_repeat_count"] < matrix["total_task_repeat_count"]
    assert any(
        summary["failure_modes"]
        for summary in matrix["task_summary"].values()
    )


def test_split_repeat_matrix_script_writes_json(tmp_path):
    input_csv = tmp_path / "anes.csv"
    output = tmp_path / "split-repeat.json"
    _write_csv(input_csv, _rows())

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_anes_split_repeat_robustness_matrix.py",
            "--input-csv",
            str(input_csv),
            "--output",
            str(output),
            "--artifact-id",
            "split-repeat-test",
            "--split-salts",
            "salt-a",
            "salt-b",
            "--k-grid",
            "1",
            "10",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["repeat_count"] == 2
    persisted = json.loads(output.read_text())
    assert persisted["artifact_id"] == "split-repeat-test"
    assert persisted["repeat_count"] == 2


def _rows() -> list[dict[str, str]]:
    rows = []
    for case_id in range(1001, 1081):
        liberal = case_id % 2 == 0
        upper = case_id % 4 in {0, 1}
        rows.append(
            {
                "V240001": str(case_id),
                "V240103a": "1",
                "V241245": "2" if liberal else "6",
                "V241258": "2" if liberal else "6",
                "V241458x": "25" if case_id % 3 else "70",
                "V241465x": "4",
                "V241566x": "25" if upper else "8",
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
