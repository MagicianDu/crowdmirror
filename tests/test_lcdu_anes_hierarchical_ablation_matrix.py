import json
import subprocess
import sys

from experiments.lcdu_anes_hierarchical_ablation_matrix import (
    build_lcdu_anes_hierarchical_ablation_matrix,
)
from tests.test_lcdu_anes_split_repeat_robustness_matrix import (
    _rows,
    _write_csv,
)


def test_hierarchical_ablation_matrix_summarizes_prior_family_and_k():
    matrix = build_lcdu_anes_hierarchical_ablation_matrix(
        rows=_rows(),
        artifact_id="ablation-test",
        split_salts=["salt-a", "salt-b"],
        k_grid=[1, 10],
        max_worst_segment_delta=0.0,
    )

    assert matrix["schema_version"] == "lcdu-anes-hierarchical-ablation-matrix-v1"
    assert matrix["validation_type"] == "lcdu_hierarchical_prior_k_ablation_matrix"
    assert matrix["repeat_count"] == 2
    assert matrix["task_count"] == 2
    assert "prior_family_summary" in matrix
    assert "prior_family_k_summary" in matrix
    assert "k_summary" in matrix
    assert "selected_method_summary" in matrix
    assert {"global", "party_or_ideology", "income", "shared_axis_neighbor"}.issubset(
        set(matrix["prior_family_summary"])
    )
    for summary in matrix["prior_family_summary"].values():
        assert 0.0 <= summary["win_rate"] <= 1.0
        assert 0.0 <= summary["test_worst_guard_pass_rate"] <= 1.0
        assert 0.0 <= summary["joint_success_rate"] <= 1.0
    for summary in matrix["prior_family_k_summary"].values():
        assert "prior_family" in summary
        assert "k" in summary
        assert 0.0 <= summary["joint_success_rate"] <= 1.0
    json.dumps(matrix, allow_nan=False)


def test_hierarchical_ablation_matrix_records_selected_method_frequency():
    matrix = build_lcdu_anes_hierarchical_ablation_matrix(
        rows=_rows(),
        artifact_id="ablation-test",
        split_salts=["salt-a", "salt-b"],
        k_grid=[1, 10],
        max_worst_segment_delta=0.0,
    )

    total_selected = sum(
        summary["selected_count"]
        for summary in matrix["selected_method_summary"].values()
    )
    assert total_selected == matrix["repeat_count"] * matrix["task_count"]


def test_hierarchical_ablation_matrix_script_writes_json(tmp_path):
    input_csv = tmp_path / "anes.csv"
    output = tmp_path / "ablation.json"
    _write_csv(input_csv, _rows())

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_anes_hierarchical_ablation_matrix.py",
            "--input-csv",
            str(input_csv),
            "--output",
            str(output),
            "--artifact-id",
            "ablation-test",
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
    assert persisted["artifact_id"] == "ablation-test"
    assert persisted["prior_family_summary"]
