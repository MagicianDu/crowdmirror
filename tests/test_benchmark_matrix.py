import json
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.benchmark_matrix import build_benchmark_plan


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_benchmark_plan_covers_required_domains_and_ablations():
    plan = build_benchmark_plan(mode="dry-run", manifest_dir="experiments/results/manifests")
    domains = {item["domain"] for item in plan}
    ablations = {item["ablation"] for item in plan}

    assert len(plan) == 9
    assert domains == {"semi_synthetic_choice", "swissmetro_choice", "voter_emergence"}
    assert ablations == {"causal_only", "emergence_only", "joint"}


def test_benchmark_plan_records_baselines():
    plan = build_benchmark_plan(mode="dry-run", manifest_dir="experiments/results/manifests")
    required_baselines = {"mnl", "uncalibrated_llm", "prompt_only"}

    assert all(required_baselines.issubset(item["baselines"]) for item in plan)


def test_benchmark_plan_records_required_entry_shape():
    manifest_dir = "experiments/results/manifests"
    plan = build_benchmark_plan(mode="local", manifest_dir=manifest_dir)

    assert len({item["run_id"] for item in plan}) == len(plan)
    assert all(
        set(item) == {"run_id", "mode", "domain", "ablation", "baselines", "manifest_dir"}
        for item in plan
    )
    assert all(item["mode"] == "local" for item in plan)
    assert all(item["manifest_dir"] == manifest_dir for item in plan)


def test_benchmark_plan_rejects_unknown_mode():
    with pytest.raises(ValueError, match="mode must be dry-run, local, or live"):
        build_benchmark_plan(mode="field", manifest_dir="experiments/results/manifests")


def test_benchmark_matrix_script_writes_plan(tmp_path):
    output = tmp_path / "benchmark-plan.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/benchmark_matrix.py",
            "--mode",
            "dry-run",
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {"output": str(output), "run_count": 9}
    payload = json.loads(output.read_text())
    assert len(payload) == 9
    assert payload[0]["mode"] == "dry-run"
