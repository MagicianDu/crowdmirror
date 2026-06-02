import json
import subprocess
import sys

from experiments.dcl_prs_runtime_strong_baseline_trial import (
    build_dcl_prs_runtime_strong_baseline_trial,
)


def test_runtime_trial_blocks_without_dcl_prs_runtime_benchmarks():
    trial = build_dcl_prs_runtime_strong_baseline_trial(
        artifact_id="dcl-prs-runtime-strong-baseline-trial-test",
        benchmark_records=[
            _record("deterministic_anchor", task_id="gss_health", loss=0.08),
            _record("fixed_party_or_ideology_prior", task_id="gss_health", loss=0.04),
            _record("LCDU-LCR-SG", task_id="gss_health", loss=0.05),
        ],
    )

    assert trial["schema_version"] == "dcl-prs-runtime-strong-baseline-trial-v1"
    assert trial["overall_status"] == "runtime_strong_baseline_trial_blocked"
    assert trial["stable_strong_baseline_win_proven"] is False
    assert "dcl_prs_runtime_prediction_missing" in trial["blocking_gaps"]
    assert trial["primary_decision"]["research_claim"] == (
        "cannot_evaluate_dcl_prs_without_runtime_prediction"
    )
    json.dumps(trial, allow_nan=False)


def test_runtime_trial_rejects_dcl_prs_when_fixed_prior_is_better():
    trial = build_dcl_prs_runtime_strong_baseline_trial(
        artifact_id="dcl-prs-runtime-strong-baseline-trial-test",
        benchmark_records=[
            _record("deterministic_anchor", task_id="gss_health", loss=0.08),
            _record("fixed_party_or_ideology_prior", task_id="gss_health", loss=0.04),
            _record("LCDU-LCR-SG", task_id="gss_health", loss=0.05),
            _record("DCL-PRS-runtime", task_id="gss_health", loss=0.06),
        ],
    )

    assert trial["overall_status"] == "runtime_strong_baseline_trial_dcl_prs_not_leading"
    assert trial["stable_strong_baseline_win_proven"] is False
    assert trial["dcl_prs_leads_covered_baselines"] is False
    assert trial["task_results"]["gss_health"]["strong_baseline_task_pass"] is False
    assert "dcl_prs_not_better_than_fixed_party_or_ideology_prior" in trial[
        "blocking_gaps"
    ]


def test_runtime_trial_promotes_dcl_prs_only_when_it_beats_all_baselines_stably():
    trial = build_dcl_prs_runtime_strong_baseline_trial(
        artifact_id="dcl-prs-runtime-strong-baseline-trial-test",
        benchmark_records=[
            _record("deterministic_anchor", task_id="gss_health", repeat_id="seed11", loss=0.08),
            _record("fixed_party_or_ideology_prior", task_id="gss_health", repeat_id="seed11", loss=0.05),
            _record("LCDU-LCR-SG", task_id="gss_health", repeat_id="seed11", loss=0.06),
            _record("DCL-PRS-runtime", task_id="gss_health", repeat_id="seed11", loss=0.03),
            _record("deterministic_anchor", task_id="gss_health", repeat_id="seed17", loss=0.09),
            _record("fixed_party_or_ideology_prior", task_id="gss_health", repeat_id="seed17", loss=0.052),
            _record("LCDU-LCR-SG", task_id="gss_health", repeat_id="seed17", loss=0.061),
            _record("DCL-PRS-runtime", task_id="gss_health", repeat_id="seed17", loss=0.031),
            _record("deterministic_anchor", task_id="anes_climate", repeat_id="seed11", loss=0.10),
            _record("fixed_party_or_ideology_prior", task_id="anes_climate", repeat_id="seed11", loss=0.06),
            _record("LCDU-LCR-SG", task_id="anes_climate", repeat_id="seed11", loss=0.07),
            _record("DCL-PRS-runtime", task_id="anes_climate", repeat_id="seed11", loss=0.04),
            _record("deterministic_anchor", task_id="anes_climate", repeat_id="seed17", loss=0.11),
            _record("fixed_party_or_ideology_prior", task_id="anes_climate", repeat_id="seed17", loss=0.061),
            _record("LCDU-LCR-SG", task_id="anes_climate", repeat_id="seed17", loss=0.071),
            _record("DCL-PRS-runtime", task_id="anes_climate", repeat_id="seed17", loss=0.041),
        ],
    )

    assert trial["overall_status"] == "runtime_strong_baseline_trial_dcl_prs_leads"
    assert trial["stable_strong_baseline_win_proven"] is True
    assert trial["dcl_prs_leads_covered_baselines"] is True
    assert trial["task_count"] == 2
    assert trial["repeat_count"] == 2
    assert trial["blocking_gaps"] == []
    assert all(result["strong_baseline_task_pass"] for result in trial["task_results"].values())


def test_runtime_trial_script_writes_artifact(tmp_path):
    records = tmp_path / "records.json"
    output_dir = tmp_path / "trial"
    records.write_text(
        json.dumps(
            [
                _record("deterministic_anchor", task_id="gss_health", loss=0.08),
                _record("fixed_party_or_ideology_prior", task_id="gss_health", loss=0.04),
                _record("LCDU-LCR-SG", task_id="gss_health", loss=0.05),
                _record("DCL-PRS-runtime", task_id="gss_health", loss=0.06),
            ]
        )
    )

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_runtime_strong_baseline_trial.py",
            "--benchmark-records-path",
            str(records),
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-runtime-strong-baseline-trial-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-runtime-strong-baseline-trial-test.json"),
        "overall_status": "runtime_strong_baseline_trial_dcl_prs_not_leading",
        "stable_strong_baseline_win_proven": False,
    }


def _record(
    method_family: str,
    *,
    task_id: str,
    loss: float,
    repeat_id: str = "seed11",
) -> dict:
    return {
        "method_family": method_family,
        "task_id": task_id,
        "repeat_id": repeat_id,
        "benchmark": {
            "schema_version": "policy-reaction-official-segment-benchmark-v1",
            "artifact_id": f"{method_family}-{task_id}-{repeat_id}",
            "overall_status": "passed",
            "source_ingestion_artifact_id": f"{task_id}-heldout",
            "prediction_artifact_id": f"{method_family}-{task_id}-{repeat_id}-prediction",
            "benchmark_metrics": {
                "weighted_choice_distribution_jsd": loss,
                "worst_segment_choice_distribution_jsd": loss + 0.01,
            },
            "segment_coverage": {"coverage_rate": 1.0},
        },
    }
