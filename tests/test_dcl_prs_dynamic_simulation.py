import json
import subprocess
import sys

from experiments.dcl_prs_dynamic_simulation import build_dynamic_simulation_trace
from experiments.dcl_prs_mechanism_program import build_mechanism_program_index


def test_dynamic_simulation_trace_is_reproducible_and_bounded():
    trace = build_dynamic_simulation_trace(
        artifact_id="dcl-prs-dynamic-simulation-test",
        mechanism_program_index=build_mechanism_program_index(
            artifact_id="dcl-prs-mechanism-program-test"
        ),
    )

    assert trace["schema_version"] == "dcl-prs-dynamic-simulation-trace-v1"
    assert trace["overall_status"] == "dynamic_trace_ready_for_l0_gate"
    assert trace["time_step_count"] >= 3
    for step in trace["time_steps"]:
        assert 0.0 <= step["aggregate_support"] <= 1.0
        assert 0.0 <= step["polarization_index"] <= 1.0
        assert 0.0 <= step["volatility_index"] <= 1.0
    assert (
        trace["claim_boundary"]["simulation_status"]
        == "exploratory_not_field_validated"
    )
    json.dumps(trace, allow_nan=False)


def test_dynamic_simulation_trace_uses_mechanism_program_ids_as_inputs():
    mechanism_program_index = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-test"
    )
    trace = build_dynamic_simulation_trace(
        artifact_id="dcl-prs-dynamic-simulation-test",
        mechanism_program_index=mechanism_program_index,
    )

    assert trace["mechanism_program_refs"] == mechanism_program_index["program_ids"]
    assert trace["population"]["agent_count"] == 1000
    assert trace["interaction_model"]["network_type"] == "cohort_mixing"
    assert trace["next_gate"] == "run_product_cohort_report_evidence"


def test_dynamic_simulation_script_writes_artifact(tmp_path):
    output_dir = tmp_path / "dcl_prs_dynamic_simulation"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_dynamic_simulation.py",
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-dynamic-simulation-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-dynamic-simulation-test.json"),
        "time_step_count": 4,
    }
    assert (output_dir / "dcl-prs-dynamic-simulation-test.json").exists()
