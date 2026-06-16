import json
import subprocess
import sys

from experiments.r6_mechanism_propagation_trace import (
    build_r6_mechanism_propagation_trace,
)


def test_r6_mechanism_propagation_trace_builds_three_proxy_dynamic_paths():
    report = build_r6_mechanism_propagation_trace(
        artifact_id="r6-mechanism-propagation-trace-test",
        run_id="r6-mechanism-propagation-trace-run",
    )

    assert report["schema_version"] == "r6-mechanism-propagation-trace-v1"
    assert report["status"] == "mechanism_propagation_trace_ready"
    assert report["trace_summary"] == {
        "case_count": 3,
        "trace_round_count": 3,
        "exposure_graph_count": 3,
        "dynamic_path_count": 6,
        "distinct_from_static_prior_path_count": 3,
        "field_outcome_validated": False,
    }
    assert report["acceptance_gates"] == {
        "mechanism_trace_present": True,
        "dynamic_path_distinct_from_static_prior": True,
        "field_outcome_validated": False,
        "product_guard_required": True,
    }
    by_source = {trace["source_key"]: trace for trace in report["case_traces"]}
    assert set(by_source) == {
        "htops_cost_pressure",
        "anes_health_heldout",
        "anes_climate_heldout",
    }
    htops = by_source["htops_cost_pressure"]
    assert htops["case_id"] == "generic-public-service-policy-change"
    assert htops["exposure_graph"]["nodes"][0]["segment_id"] == (
        "service_dependent_low_trust"
    )
    assert htops["propagation_rounds"][0]["round"] == 1
    assert htops["dynamic_paths"][0]["path_type"] == "peer_amplified_risk_diffusion"
    assert htops["dynamic_paths"][0]["static_prior_can_express_path"] is False
    assert "mechanism_trace_not_field_validation" in report["risk_flags"]
    json.dumps(report, allow_nan=False)


def test_r6_mechanism_propagation_trace_accepts_positional_args():
    report = build_r6_mechanism_propagation_trace(
        "r6-positional",
        "r6-positional-run",
    )

    assert report["artifact_id"] == "r6-positional"
    assert report["run_id"] == "r6-positional-run"
    assert report["trace_summary"]["case_count"] == 3


def test_r6_mechanism_propagation_trace_empty_proxy_list_is_explicit_input():
    report = build_r6_mechanism_propagation_trace(
        "r6-empty-proxy-list",
        "r6-empty-proxy-list-run",
        public_outcome_proxies=[],
    )

    assert report["trace_summary"]["case_count"] == 0
    assert report["trace_summary"]["dynamic_path_count"] == 0
    assert report["acceptance_gates"]["mechanism_trace_present"] is False
    json.dumps(report, allow_nan=False)


def test_r6_mechanism_propagation_trace_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-mechanism-propagation-trace.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_mechanism_propagation_trace.py",
            "--artifact-id",
            "r6-mechanism-propagation-trace-cli",
            "--run-id",
            "r6-mechanism-propagation-trace-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_text().endswith("\n")
    report = json.loads(output.read_text())
    assert report["schema_version"] == "r6-mechanism-propagation-trace-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-mechanism-propagation-trace-cli",
        "dynamic_path_count": 6,
        "output": str(output),
        "status": "mechanism_propagation_trace_ready",
    }
