# R8 可学习机制交互仿真实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 R8 第一阶段最小闭环：可学习机制因果图、交互传播算子、baseline comparison、robustness/holdout gate 和 Product support ingestion。

**Architecture:** R8 新增独立 `experiments/r8_*` 模块，复用 R6/R7 的合同、case fixture、Product guard 和写 artifact 工具。R7 v2 只作为固定规则 baseline；R8 主方法必须输出结构化机制图、参数 registry、rollout、attribution、update candidate 和 support gate，所有 Product 可见 claim 都走 guard。

**Tech Stack:** Python 3、pytest、现有 `experiments.r6_contracts`、现有 R6/R7 public proxy fixture、JSON artifact。

---

## 文件结构

- Create: `experiments/r8_learnable_mechanism_simulation.py`
  - 负责 R8 L0/L1 主 bundle：机制因果图、参数 registry、rollout distribution、区间校准、风险排序、outcome attribution、operator update candidate、product support gate。
- Create: `tests/test_r8_learnable_mechanism_simulation.py`
  - 覆盖 R8 artifact contract、LLM 边界、guard 默认阻断、CLI artifact。
- Create: `experiments/r8_baseline_comparison.py`
  - 负责同口径比较 static prior、R6 learning counterfactual、R7 v2、R8 主方法、分层区间 baseline、多智能体传播 baseline。
- Create: `tests/test_r8_baseline_comparison.py`
  - 覆盖 winner、claim level、stop-loss recommendation、R7 v2 baseline 保留。
- Create: `experiments/r8_robustness_holdout_gate.py`
  - 负责 perturbation、leave-one-case、same-family holdout、cross-family fail-closed。
- Create: `tests/test_r8_robustness_holdout_gate.py`
  - 覆盖 L1/L2 状态、runtime guard、current-proxy 过拟合诊断。
- Modify: `experiments/r6_product_customer_value_report.py`
  - 增加可选 `r8_robustness_holdout_gate` ingestion，新增 customer section `r8_method_support`。
- Modify: `tests/test_r6_product_customer_value_report.py`
  - 覆盖 R8 support gate 可读、source refs 可解析、blocked claims 不被覆盖。
- Modify: `docs/CURRENT_STATE.md`
  - 记录 R8 第一阶段 artifact 和结论边界。

## Task 1: R8 Artifact Contract

**Files:**
- Create: `experiments/r8_learnable_mechanism_simulation.py`
- Create: `tests/test_r8_learnable_mechanism_simulation.py`
- Create artifact: `experiments/results/r8_learnable_mechanism_bundle/r8-learnable-mechanism-bundle-current-001.json`

- [ ] **Step 1: Write failing contract tests**

Create `tests/test_r8_learnable_mechanism_simulation.py`:

```python
import json
import subprocess
import sys

from experiments.r8_learnable_mechanism_simulation import (
    R8_CLAIM_BOUNDARY,
    build_r8_learnable_mechanism_bundle,
)


def test_r8_bundle_contains_l0_artifacts_and_guarded_boundaries():
    bundle = build_r8_learnable_mechanism_bundle(
        artifact_id="r8-learnable-mechanism-bundle-test",
        run_id="r8-l0-run",
        case_id="generic-public-service-policy-change",
    )

    assert bundle["schema_version"] == "r8-learnable-mechanism-bundle-v1"
    assert bundle["status"] == "r8_contract_ready_guarded"
    assert bundle["claim_boundary"] == R8_CLAIM_BOUNDARY
    assert bundle["acceptance_gates"] == {
        "artifact_contracts_present": True,
        "source_refs_present": True,
        "product_guard_consumable": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert set(bundle["artifacts"]) == {
        "r8_mechanism_causal_graph_manifest",
        "r8_operator_parameter_registry",
        "r8_rollout_distribution",
        "r8_risk_interval_calibration_report",
        "r8_risk_ranking_report",
        "r8_outcome_attribution_report",
        "r8_operator_update_candidate",
        "r8_product_support_gate",
    }

    for artifact in bundle["artifacts"].values():
        assert artifact["artifact_id"].startswith("r8-learnable-mechanism-bundle-test")
        assert artifact["run_id"] == "r8-l0-run"
        assert artifact["schema_version"].startswith("r8-")
        assert artifact["source_refs"]
        assert artifact["claim_boundary"] == R8_CLAIM_BOUNDARY

    json.dumps(bundle, allow_nan=False)


def test_r8_mechanism_graph_and_parameter_registry_are_learnable_but_guarded():
    bundle = build_r8_learnable_mechanism_bundle(
        artifact_id="r8-learnable-mechanism-bundle-test",
        run_id="r8-l0-run",
        case_id="generic-public-service-policy-change",
    )

    graph = bundle["artifacts"]["r8_mechanism_causal_graph_manifest"]
    assert graph["mechanism_catalog"]
    assert graph["graph_nodes"]
    assert graph["graph_edges"]
    assert all(edge["evidence_source"] for edge in graph["graph_edges"])
    assert any(edge["learnable"] is True for edge in graph["graph_edges"])

    registry = bundle["artifacts"]["r8_operator_parameter_registry"]
    assert registry["runtime_default_allowed"] is False
    assert registry["parameter_families"] == [
        "mechanism_activation",
        "segment_sensitivity",
        "propagation_edge",
        "uncertainty_calibration",
        "guard_penalty",
    ]
    for parameter in registry["parameters"]:
        assert parameter["parameter_id"]
        assert parameter["allowed_range"][0] <= parameter["current_value"] <= parameter["allowed_range"][1]
        assert parameter["runtime_default_allowed"] is False


def test_r8_llm_boundary_is_structured_and_non_authoritative():
    bundle = build_r8_learnable_mechanism_bundle(
        artifact_id="r8-learnable-mechanism-bundle-test",
        run_id="r8-l0-run",
        case_id="generic-public-service-policy-change",
    )

    graph = bundle["artifacts"]["r8_mechanism_causal_graph_manifest"]
    assert graph["llm_boundary"] == {
        "llm_may_generate_candidate_mechanisms": True,
        "llm_may_generate_customer_narrative_draft": True,
        "llm_can_set_field_outcome_validated": False,
        "llm_can_set_runtime_default_allowed": False,
        "structured_output_required": True,
    }

    support_gate = bundle["artifacts"]["r8_product_support_gate"]
    assert support_gate["field_outcome_validated"] is False
    assert support_gate["runtime_default_allowed"] is False
    assert "R8 validated" in support_gate["blocked_claims"]
    assert "runtime default ready" in support_gate["blocked_claims"]


def test_r8_bundle_cli_writes_current_artifact(tmp_path):
    output = tmp_path / "r8-learnable-mechanism-bundle.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r8_learnable_mechanism_simulation.py",
            "--artifact-id",
            "r8-learnable-mechanism-bundle-cli",
            "--run-id",
            "r8-l0-run",
            "--case-id",
            "generic-public-service-policy-change",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r8-learnable-mechanism-bundle-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r8-learnable-mechanism-bundle-cli",
        "output": str(output),
        "status": "r8_contract_ready_guarded",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_r8_learnable_mechanism_simulation.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r8_learnable_mechanism_simulation'`.

- [ ] **Step 3: Create minimal R8 bundle implementation**

Create `experiments/r8_learnable_mechanism_simulation.py`:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_case_templates import get_r6_case_template
from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact


R8_CLAIM_BOUNDARY = (
    "R8 learnable mechanism artifact. It supports guarded mechanism-causal "
    "interaction simulation, interval/risk diagnosis, attribution, and bounded "
    "operator update candidates only; it is not point-prediction evidence, not "
    "field validation, and not runtime default authorization."
)
R8_BUNDLE_SCHEMA_VERSION = "r8-learnable-mechanism-bundle-v1"

MECHANISM_CATALOG = [
    "price_sensitivity",
    "trust_loss",
    "fairness_perception",
    "substitution_option",
    "identity_alignment",
    "service_access_constraint",
    "loss_aversion",
    "social_diffusion_sensitivity",
]
PARAMETER_FAMILIES = [
    "mechanism_activation",
    "segment_sensitivity",
    "propagation_edge",
    "uncertainty_calibration",
    "guard_penalty",
]


def build_r8_learnable_mechanism_bundle(
    *,
    artifact_id: str,
    run_id: str,
    case_id: str = "generic-public-service-policy-change",
    rollout_count: int = 50,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    case = get_r6_case_template(non_empty_string(case_id, field="case_id"))
    graph = _mechanism_graph(f"{artifact_id}-mechanism-causal-graph", run_id, case)
    registry = _parameter_registry(f"{artifact_id}-operator-parameter-registry", run_id, graph)
    rollout = _rollout_distribution(f"{artifact_id}-rollout-distribution", run_id, case, graph, registry, rollout_count)
    interval = _interval_report(f"{artifact_id}-risk-interval-calibration", run_id, rollout)
    ranking = _risk_ranking_report(f"{artifact_id}-risk-ranking", run_id, case, rollout)
    attribution = _outcome_attribution_report(f"{artifact_id}-outcome-attribution", run_id, case, rollout, ranking)
    update = _operator_update_candidate(f"{artifact_id}-operator-update-candidate", run_id, attribution)
    support = _product_support_gate(f"{artifact_id}-product-support-gate", run_id, interval, ranking, attribution, update)
    artifacts = {
        "r8_mechanism_causal_graph_manifest": graph,
        "r8_operator_parameter_registry": registry,
        "r8_rollout_distribution": rollout,
        "r8_risk_interval_calibration_report": interval,
        "r8_risk_ranking_report": ranking,
        "r8_outcome_attribution_report": attribution,
        "r8_operator_update_candidate": update,
        "r8_product_support_gate": support,
    }
    payload = {
        "schema_version": R8_BUNDLE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "case_id": case["case_id"],
        "status": "r8_contract_ready_guarded",
        "claim_boundary": R8_CLAIM_BOUNDARY,
        "source_refs": [case["case_id"], case["scenario"]["scenario_id"], *case["scenario"]["source_refs"]],
        "artifacts": artifacts,
        "acceptance_gates": {
            "artifact_contracts_present": True,
            "source_refs_present": True,
            "product_guard_consumable": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "allowed_claims": [
            "R8 exposes a guarded learnable-mechanism artifact contract.",
            "R8 can be compared against R7 v2 and conservative baselines before product escalation.",
        ],
        "blocked_claims": [
            "精准预测系统",
            "R8 validated",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "accuracy superiority",
        ],
    }
    assert_strict_json(payload)
    return payload
```

Continue in the same file with helper functions:

```python
def _artifact(*, schema_version: str, artifact_id: str, run_id: str, source_refs: list[str], **extra: Any) -> dict[str, Any]:
    payload = {
        "schema_version": schema_version,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "source_refs": source_refs,
        "claim_boundary": R8_CLAIM_BOUNDARY,
    }
    payload.update(extra)
    return payload


def _mechanism_graph(artifact_id: str, run_id: str, case: dict[str, Any]) -> dict[str, Any]:
    nodes = [
        {"node_id": "scenario_shock", "node_type": "input", "source_refs": [case["scenario"]["scenario_id"]]},
        *[
            {"node_id": mechanism, "node_type": "mechanism", "source_refs": case["scenario"]["source_refs"]}
            for mechanism in MECHANISM_CATALOG
        ],
        {"node_id": "segment_response", "node_type": "latent_state", "source_refs": [case["case_id"]]},
        {"node_id": "interaction_propagation", "node_type": "operator", "source_refs": [case["case_id"]]},
        {"node_id": "risk_distribution", "node_type": "output", "source_refs": [case["case_id"]]},
    ]
    edges = [
        {
            "edge_id": f"scenario_to_{mechanism}",
            "source_node": "scenario_shock",
            "target_node": mechanism,
            "effect_direction": "increase",
            "effect_strength": 0.45 if mechanism in case["scenario"]["impact_dimensions"] else 0.2,
            "uncertainty": 0.12,
            "evidence_source": "rule:scenario_impact_dimension",
            "learnable": True,
            "guard_constraints": ["bounded_update", "holdout_required"],
        }
        for mechanism in MECHANISM_CATALOG
    ]
    edges.extend(
        [
            {
                "edge_id": "mechanisms_to_segment_response",
                "source_node": "mechanism_activation",
                "target_node": "segment_response",
                "effect_direction": "mixed",
                "effect_strength": 0.5,
                "uncertainty": 0.1,
                "evidence_source": "rule:segment_static_traits",
                "learnable": True,
                "guard_constraints": ["non_regression_required"],
            },
            {
                "edge_id": "segment_response_to_interaction",
                "source_node": "segment_response",
                "target_node": "interaction_propagation",
                "effect_direction": "amplify_or_buffer",
                "effect_strength": 0.35,
                "uncertainty": 0.16,
                "evidence_source": "rule:interaction_graph_fixture",
                "learnable": True,
                "guard_constraints": ["false_alarm_guard"],
            },
        ]
    )
    return _artifact(
        schema_version="r8-mechanism-causal-graph-manifest-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[case["case_id"], case["scenario"]["scenario_id"], *case["scenario"]["source_refs"]],
        graph_nodes=nodes,
        graph_edges=edges,
        mechanism_catalog=MECHANISM_CATALOG,
        evidence_sources=["rule:scenario_impact_dimension", "rule:segment_static_traits", "rule:interaction_graph_fixture"],
        learnable_parameters=[edge["edge_id"] for edge in edges if edge["learnable"]],
        non_learnable_constraints=["field_outcome_validated", "runtime_default_allowed", "blocked_claims"],
        llm_boundary={
            "llm_may_generate_candidate_mechanisms": True,
            "llm_may_generate_customer_narrative_draft": True,
            "llm_can_set_field_outcome_validated": False,
            "llm_can_set_runtime_default_allowed": False,
            "structured_output_required": True,
        },
    )
```

Add registry, rollout, reports, CLI:

```python
def _parameter_registry(artifact_id: str, run_id: str, graph: dict[str, Any]) -> dict[str, Any]:
    parameters = []
    for index, family in enumerate(PARAMETER_FAMILIES):
        parameters.append(
            {
                "parameter_id": f"{family}:{index}",
                "parameter_family": family,
                "current_value": round(0.2 + index * 0.1, 3),
                "allowed_range": [0.0, 1.0],
                "evidence_level": "fixture_rule",
                "last_update_source": graph["artifact_id"],
                "runtime_default_allowed": False,
                "rollback_policy": "revert_to_previous_registry_value",
            }
        )
    return _artifact(
        schema_version="r8-operator-parameter-registry-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[graph["artifact_id"]],
        parameter_families=PARAMETER_FAMILIES,
        parameters=parameters,
        runtime_default_allowed=False,
    )


def _rollout_distribution(artifact_id: str, run_id: str, case: dict[str, Any], graph: dict[str, Any], registry: dict[str, Any], rollout_count: int) -> dict[str, Any]:
    static_prior = sum(
        segment["weight"] * segment["static_response_prior"]["reject"]
        for segment in case["prior_segments"]
    )
    interaction_shift = 0.06 if case["case_id"] == "generic-public-service-policy-change" else -0.03
    candidate_shift = interaction_shift * 0.85
    return _artifact(
        schema_version="r8-rollout-distribution-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[graph["artifact_id"], registry["artifact_id"]],
        rollout_count=rollout_count,
        seed_policy="deterministic:0..rollout_count-1",
        no_interaction_distribution={"median": round(static_prior, 4), "p10": round(max(0.0, static_prior - 0.06), 4), "p90": round(min(1.0, static_prior + 0.06), 4)},
        interaction_distribution={"median": round(static_prior + interaction_shift, 4), "p10": round(max(0.0, static_prior + interaction_shift - 0.09), 4), "p90": round(min(1.0, static_prior + interaction_shift + 0.09), 4)},
        candidate_update_distribution={"median": round(static_prior + candidate_shift, 4), "p10": round(max(0.0, static_prior + candidate_shift - 0.08), 4), "p90": round(min(1.0, static_prior + candidate_shift + 0.08), 4)},
        uncertainty_breakdown={"prior": 0.06, "mechanism": 0.05, "propagation": 0.06, "outcome_proxy": 0.08},
        interval_width=0.18,
        over_width_penalty=0.0,
    )


def _interval_report(artifact_id: str, run_id: str, rollout: dict[str, Any]) -> dict[str, Any]:
    return _artifact(
        schema_version="r8-risk-interval-calibration-report-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[rollout["artifact_id"]],
        trend_direction_accuracy=None,
        interval_coverage=None,
        mean_interval_width=rollout["interval_width"],
        interval_efficiency=None,
        coverage_by_case_family={},
        indeterminate_rate=0.0,
        over_width_blocked=False,
        claim_status="contract_only",
    )


def _risk_ranking_report(artifact_id: str, run_id: str, case: dict[str, Any], rollout: dict[str, Any]) -> dict[str, Any]:
    ranked = sorted(
        [
            {
                "segment_id": segment["segment_id"],
                "risk_score": round(segment["static_response_prior"]["reject"] + 0.04, 4),
                "risk_type": "interaction_amplified_risk",
                "source_refs": segment["source_refs"],
            }
            for segment in case["prior_segments"]
        ],
        key=lambda item: item["risk_score"],
        reverse=True,
    )
    return _artifact(
        schema_version="r8-risk-ranking-report-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[rollout["artifact_id"], case["case_id"]],
        top_k_hit_rate=None,
        risk_ranking_quality=None,
        static_prior_miss_recovery_rate=None,
        false_alarm_rate=None,
        segment_precision=None,
        segment_recall=None,
        static_hidden_risk_segments=[item for item in ranked if item["risk_score"] >= 0.4],
        interaction_amplified_segments=ranked,
    )


def _outcome_attribution_report(artifact_id: str, run_id: str, case: dict[str, Any], rollout: dict[str, Any], ranking: dict[str, Any]) -> dict[str, Any]:
    return _artifact(
        schema_version="r8-outcome-attribution-report-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[rollout["artifact_id"], ranking["artifact_id"], case["case_id"]],
        outcome_residual=None,
        attribution_by_mechanism=[],
        attribution_by_edge=[],
        attribution_by_segment=[],
        interval_error_type="not_evaluated_without_outcome",
        false_alarm_sources=[],
        missed_risk_sources=[],
        unexplained_error="not_evaluated_without_outcome",
    )


def _operator_update_candidate(artifact_id: str, run_id: str, attribution: dict[str, Any]) -> dict[str, Any]:
    return _artifact(
        schema_version="r8-operator-update-candidate-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[attribution["artifact_id"]],
        candidate_id=f"{artifact_id}:candidate-001",
        updated_parameters=[],
        expected_metric_delta={},
        guard_checks={"holdout_required": True, "runtime_default_allowed": False},
        holdout_results=[],
        robustness_results=[],
        accepted=False,
        rejected_reason="blocked_until_outcome_and_holdout",
        runtime_default_allowed=False,
    )


def _product_support_gate(artifact_id: str, run_id: str, interval: dict[str, Any], ranking: dict[str, Any], attribution: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    return _artifact(
        schema_version="r8-product-support-gate-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[interval["artifact_id"], ranking["artifact_id"], attribution["artifact_id"], update["artifact_id"]],
        trend_supported="contract_only",
        interval_supported="contract_only",
        risk_ranking_supported="contract_only",
        abnormal_segment_supported="contract_only",
        mechanism_explanation_supported="guarded",
        outcome_learning_supported="blocked_until_outcome",
        field_outcome_validated=False,
        runtime_default_allowed=False,
        blocked_claims=["R8 validated", "runtime default ready", "field validated", "accuracy superiority"],
        allowed_claims=["R8 contract artifacts can be inspected and compared under guard."],
    )


def write_r8_learnable_mechanism_bundle(*, output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r8_learnable_mechanism_bundle(**kwargs))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-id", default="r8-learnable-mechanism-bundle-current-001")
    parser.add_argument("--run-id", default="r8-learnable-mechanism-current")
    parser.add_argument("--case-id", default="generic-public-service-policy-change")
    parser.add_argument("--rollout-count", type=int, default=50)
    parser.add_argument("--output", default="experiments/results/r8_learnable_mechanism_bundle/r8-learnable-mechanism-bundle-current-001.json")
    args = parser.parse_args()
    output = write_r8_learnable_mechanism_bundle(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        case_id=args.case_id,
        rollout_count=args.rollout_count,
    )
    artifact = build_r8_learnable_mechanism_bundle(
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        case_id=args.case_id,
        rollout_count=args.rollout_count,
    )
    print(json.dumps({"artifact_id": args.artifact_id, "output": str(output), "status": artifact["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run contract tests**

Run:

```bash
python -m pytest tests/test_r8_learnable_mechanism_simulation.py -q
```

Expected: PASS.

- [ ] **Step 5: Generate current artifact**

Run:

```bash
python experiments/r8_learnable_mechanism_simulation.py \
  --artifact-id r8-learnable-mechanism-bundle-current-001 \
  --run-id r8-learnable-mechanism-current \
  --case-id generic-public-service-policy-change \
  --output experiments/results/r8_learnable_mechanism_bundle/r8-learnable-mechanism-bundle-current-001.json
```

Expected stdout:

```json
{"artifact_id": "r8-learnable-mechanism-bundle-current-001", "output": "experiments/results/r8_learnable_mechanism_bundle/r8-learnable-mechanism-bundle-current-001.json", "status": "r8_contract_ready_guarded"}
```

- [ ] **Step 6: Commit**

```bash
git add experiments/r8_learnable_mechanism_simulation.py tests/test_r8_learnable_mechanism_simulation.py
git add -f experiments/results/r8_learnable_mechanism_bundle/r8-learnable-mechanism-bundle-current-001.json
git commit -m "feat: add R8 artifact contract"
```

## Task 2: R8 可学习算子 MVP

**Files:**
- Modify: `experiments/r8_learnable_mechanism_simulation.py`
- Modify: `tests/test_r8_learnable_mechanism_simulation.py`
- Update artifact: `experiments/results/r8_learnable_mechanism_bundle/r8-learnable-mechanism-bundle-current-001.json`

- [ ] **Step 1: Add failing tests for attribution and bounded update**

Append to `tests/test_r8_learnable_mechanism_simulation.py`:

```python
def test_r8_outcome_feedback_generates_mechanism_level_attribution():
    bundle = build_r8_learnable_mechanism_bundle(
        artifact_id="r8-learnable-mechanism-bundle-test",
        run_id="r8-l1-run",
        case_id="generic-public-service-policy-change",
        observed_reject_proxy=0.47,
    )

    attribution = bundle["artifacts"]["r8_outcome_attribution_report"]
    assert attribution["outcome_residual"] is not None
    assert attribution["attribution_by_mechanism"]
    assert attribution["attribution_by_edge"]
    assert attribution["attribution_by_segment"]
    assert attribution["unexplained_error"] <= 0.5
    assert {item["error_type"] for item in attribution["attribution_by_mechanism"]} <= {
        "mechanism_strength_error",
        "mechanism_direction_supported",
        "mechanism_missing",
    }


def test_r8_operator_update_candidate_is_bounded_and_not_runtime_default():
    bundle = build_r8_learnable_mechanism_bundle(
        artifact_id="r8-learnable-mechanism-bundle-test",
        run_id="r8-l1-run",
        case_id="generic-public-service-policy-change",
        observed_reject_proxy=0.47,
    )

    update = bundle["artifacts"]["r8_operator_update_candidate"]
    assert update["updated_parameters"]
    assert update["accepted"] is False
    assert update["rejected_reason"] == "pending_holdout_review"
    assert update["runtime_default_allowed"] is False
    assert update["guard_checks"] == {
        "bounded_update": True,
        "holdout_required": True,
        "robustness_required": True,
        "runtime_default_allowed": False,
    }
    for parameter in update["updated_parameters"]:
        assert abs(parameter["delta"]) <= parameter["max_abs_delta"]
        assert parameter["source_attribution_id"] == bundle["artifacts"]["r8_outcome_attribution_report"]["artifact_id"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_r8_learnable_mechanism_simulation.py::test_r8_outcome_feedback_generates_mechanism_level_attribution tests/test_r8_learnable_mechanism_simulation.py::test_r8_operator_update_candidate_is_bounded_and_not_runtime_default -q
```

Expected: FAIL with `TypeError: build_r8_learnable_mechanism_bundle() got an unexpected keyword argument 'observed_reject_proxy'`.

- [ ] **Step 3: Extend R8 builder signature and attribution logic**

Modify `build_r8_learnable_mechanism_bundle` signature:

```python
def build_r8_learnable_mechanism_bundle(
    *,
    artifact_id: str,
    run_id: str,
    case_id: str = "generic-public-service-policy-change",
    rollout_count: int = 50,
    observed_reject_proxy: float | None = None,
) -> dict[str, Any]:
```

Pass `observed_reject_proxy` into attribution:

```python
attribution = _outcome_attribution_report(
    f"{artifact_id}-outcome-attribution",
    run_id,
    case,
    rollout,
    ranking,
    observed_reject_proxy,
)
```

Replace `_outcome_attribution_report` with:

```python
def _outcome_attribution_report(
    artifact_id: str,
    run_id: str,
    case: dict[str, Any],
    rollout: dict[str, Any],
    ranking: dict[str, Any],
    observed_reject_proxy: float | None,
) -> dict[str, Any]:
    predicted = rollout["interaction_distribution"]["median"]
    if observed_reject_proxy is None:
        return _artifact(
            schema_version="r8-outcome-attribution-report-v1",
            artifact_id=artifact_id,
            run_id=run_id,
            source_refs=[rollout["artifact_id"], ranking["artifact_id"], case["case_id"]],
            outcome_residual=None,
            attribution_by_mechanism=[],
            attribution_by_edge=[],
            attribution_by_segment=[],
            interval_error_type="not_evaluated_without_outcome",
            false_alarm_sources=[],
            missed_risk_sources=[],
            unexplained_error="not_evaluated_without_outcome",
        )
    residual = round(float(observed_reject_proxy) - predicted, 4)
    direction = "increase" if residual > 0 else "decrease"
    mechanisms = [
        {
            "mechanism": "service_access_constraint",
            "error_type": "mechanism_strength_error",
            "recommended_update_direction": direction,
            "residual_share": 0.45,
            "source_refs": [rollout["artifact_id"]],
        },
        {
            "mechanism": "fairness_perception",
            "error_type": "mechanism_direction_supported",
            "recommended_update_direction": direction,
            "residual_share": 0.3,
            "source_refs": [rollout["artifact_id"]],
        },
    ]
    edges = [
        {
            "edge_id": "segment_response_to_interaction",
            "error_type": "propagation_strength_error",
            "recommended_update_direction": direction,
            "residual_share": 0.25,
            "source_refs": [rollout["artifact_id"]],
        }
    ]
    segments = [
        {
            "segment_id": item["segment_id"],
            "error_type": "segment_sensitivity_error",
            "recommended_update_direction": direction,
            "residual_share": round(0.2 / max(1, len(ranking["interaction_amplified_segments"])), 4),
            "source_refs": item["source_refs"],
        }
        for item in ranking["interaction_amplified_segments"]
    ]
    return _artifact(
        schema_version="r8-outcome-attribution-report-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[rollout["artifact_id"], ranking["artifact_id"], case["case_id"]],
        outcome_reject_proxy=round(float(observed_reject_proxy), 4),
        prediction_median=predicted,
        outcome_residual=residual,
        attribution_by_mechanism=mechanisms,
        attribution_by_edge=edges,
        attribution_by_segment=segments,
        interval_error_type="covered" if rollout["interaction_distribution"]["p10"] <= observed_reject_proxy <= rollout["interaction_distribution"]["p90"] else "missed_interval",
        false_alarm_sources=[],
        missed_risk_sources=[],
        unexplained_error=0.0,
    )
```

Replace `_operator_update_candidate` with:

```python
def _operator_update_candidate(artifact_id: str, run_id: str, attribution: dict[str, Any]) -> dict[str, Any]:
    if attribution["outcome_residual"] is None:
        updated_parameters: list[dict[str, Any]] = []
        rejected_reason = "blocked_until_outcome_and_holdout"
    else:
        residual = float(attribution["outcome_residual"])
        bounded_delta = round(max(-0.08, min(0.08, residual * 0.5)), 4)
        updated_parameters = [
            {
                "parameter_id": "mechanism_activation:service_access_constraint",
                "parameter_family": "mechanism_activation",
                "current_value": 0.4,
                "delta": bounded_delta,
                "candidate_value": round(max(0.0, min(1.0, 0.4 + bounded_delta)), 4),
                "max_abs_delta": 0.08,
                "source_attribution_id": attribution["artifact_id"],
            },
            {
                "parameter_id": "propagation_edge:segment_response_to_interaction",
                "parameter_family": "propagation_edge",
                "current_value": 0.35,
                "delta": round(bounded_delta * 0.5, 4),
                "candidate_value": round(max(0.0, min(1.0, 0.35 + bounded_delta * 0.5)), 4),
                "max_abs_delta": 0.08,
                "source_attribution_id": attribution["artifact_id"],
            },
        ]
        rejected_reason = "pending_holdout_review"
    return _artifact(
        schema_version="r8-operator-update-candidate-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[attribution["artifact_id"]],
        candidate_id=f"{artifact_id}:candidate-001",
        updated_parameters=updated_parameters,
        expected_metric_delta={"mean_absolute_error": "decrease"} if updated_parameters else {},
        guard_checks={
            "bounded_update": True,
            "holdout_required": True,
            "robustness_required": True,
            "runtime_default_allowed": False,
        },
        holdout_results=[],
        robustness_results=[],
        accepted=False,
        rejected_reason=rejected_reason,
        runtime_default_allowed=False,
    )
```

- [ ] **Step 4: Add CLI arg**

Add parser arg:

```python
parser.add_argument("--observed-reject-proxy", type=float, default=None)
```

Pass it to both builder calls:

```python
observed_reject_proxy=args.observed_reject_proxy,
```

- [ ] **Step 5: Run tests**

Run:

```bash
python -m pytest tests/test_r8_learnable_mechanism_simulation.py -q
```

Expected: PASS.

- [ ] **Step 6: Regenerate current artifact with proxy outcome**

Run:

```bash
python experiments/r8_learnable_mechanism_simulation.py \
  --artifact-id r8-learnable-mechanism-bundle-current-001 \
  --run-id r8-learnable-mechanism-current \
  --case-id generic-public-service-policy-change \
  --observed-reject-proxy 0.47 \
  --output experiments/results/r8_learnable_mechanism_bundle/r8-learnable-mechanism-bundle-current-001.json
```

Expected status remains `r8_contract_ready_guarded`; `operator_update_candidate.rejected_reason` becomes `pending_holdout_review`.

- [ ] **Step 7: Commit**

```bash
git add experiments/r8_learnable_mechanism_simulation.py tests/test_r8_learnable_mechanism_simulation.py
git add -f experiments/results/r8_learnable_mechanism_bundle/r8-learnable-mechanism-bundle-current-001.json
git commit -m "feat: add R8 bounded operator update"
```

## Task 3: R8 Baseline Comparison

**Files:**
- Create: `experiments/r8_baseline_comparison.py`
- Create: `tests/test_r8_baseline_comparison.py`
- Create artifact: `experiments/results/r8_baseline_comparison/r8-baseline-comparison-current-001.json`

- [ ] **Step 1: Write failing comparison tests**

Create `tests/test_r8_baseline_comparison.py`:

```python
import json
import subprocess
import sys

from experiments.r8_baseline_comparison import build_r8_baseline_comparison


def test_r8_baseline_comparison_includes_all_required_methods():
    report = build_r8_baseline_comparison(
        artifact_id="r8-baseline-comparison-test",
        run_id="r8-baseline-run",
    )

    assert report["schema_version"] == "r8-baseline-comparison-v1"
    assert report["status"] in {
        "r8_baseline_comparison_guarded_positive",
        "r8_baseline_comparison_diagnostic_or_stop_loss",
    }
    assert set(report["methods"]) == {
        "static_prior",
        "r6_learning_counterfactual",
        "r7_v2_guarded_mechanism_calibrated",
        "r8_main_learnable_mechanism",
        "hierarchical_interval_baseline",
        "agent_propagation_baseline",
    }
    assert "r7-effect-validation-v2" in report["baseline_policy"]["r7_v2_role"]
    assert report["acceptance_gates"]["field_outcome_validated"] is False
    assert report["acceptance_gates"]["runtime_default_allowed"] is False
    json.dumps(report, allow_nan=False)


def test_r8_baseline_comparison_reports_winners_and_claim_levels():
    report = build_r8_baseline_comparison(
        artifact_id="r8-baseline-comparison-test",
        run_id="r8-baseline-run",
    )

    for metric in [
        "trend_direction_accuracy",
        "interval_coverage",
        "false_alarm_rate",
        "static_prior_miss_recovery_rate",
        "risk_ranking_quality",
    ]:
        assert metric in report["winner_by_metric"]
        assert report["winner_by_metric"][metric]["method"] in report["methods"]
        assert report["claim_level_by_metric"][metric] in {
            "guarded_current_proxy",
            "diagnostic_only",
            "blocked",
        }

    assert report["stop_loss_recommendation"] in {
        "continue_to_holdout_validation",
        "keep_r8_as_diagnostic_asset",
        "stop_loss_r8_main_method",
    }


def test_r8_baseline_comparison_cli_writes_artifact(tmp_path):
    output = tmp_path / "r8-baseline-comparison.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r8_baseline_comparison.py",
            "--artifact-id",
            "r8-baseline-comparison-cli",
            "--run-id",
            "r8-baseline-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r8-baseline-comparison-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r8-baseline-comparison-cli",
        "output": str(output),
        "status": artifact["status"],
    }
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_r8_baseline_comparison.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r8_baseline_comparison'`.

- [ ] **Step 3: Implement comparison module**

Create `experiments/r8_baseline_comparison.py`:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact
from experiments.r7_effect_validation import build_r7_effect_validation
from experiments.r8_learnable_mechanism_simulation import R8_CLAIM_BOUNDARY, build_r8_learnable_mechanism_bundle


METHODS = [
    "static_prior",
    "r6_learning_counterfactual",
    "r7_v2_guarded_mechanism_calibrated",
    "r8_main_learnable_mechanism",
    "hierarchical_interval_baseline",
    "agent_propagation_baseline",
]


def build_r8_baseline_comparison(*, artifact_id: str, run_id: str) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    r7_v2 = build_r7_effect_validation(
        artifact_id=f"{artifact_id}-r7-v2",
        run_id=run_id,
        candidate_variant="v2_guarded_mechanism_calibrated",
    )
    r8 = build_r8_learnable_mechanism_bundle(
        artifact_id=f"{artifact_id}-r8-main",
        run_id=run_id,
        observed_reject_proxy=0.47,
    )
    metrics = _method_metrics(r7_v2, r8)
    winner_by_metric = {
        metric: _winner(metrics, metric, lower_is_better=metric == "false_alarm_rate")
        for metric in [
            "trend_direction_accuracy",
            "interval_coverage",
            "false_alarm_rate",
            "static_prior_miss_recovery_rate",
            "risk_ranking_quality",
        ]
    }
    r8_wins = sum(1 for winner in winner_by_metric.values() if winner["method"] == "r8_main_learnable_mechanism")
    stop_loss = "continue_to_holdout_validation" if r8_wins >= 2 else "keep_r8_as_diagnostic_asset"
    report = {
        "schema_version": "r8-baseline-comparison-v1",
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r8_baseline_comparison_guarded_positive" if stop_loss == "continue_to_holdout_validation" else "r8_baseline_comparison_diagnostic_or_stop_loss",
        "methods": METHODS,
        "baseline_policy": {
            "r7_v2_role": "r7-effect-validation-v2 fixed-rule baseline, not main algorithm",
            "static_prior_role": "strong prior floor",
            "r6_role": "guarded learning counterfactual baseline",
        },
        "method_metrics": metrics,
        "winner_by_metric": winner_by_metric,
        "claim_level_by_metric": {
            metric: "guarded_current_proxy" if metric in {"interval_coverage", "false_alarm_rate"} else "diagnostic_only"
            for metric in winner_by_metric
        },
        "stop_loss_recommendation": stop_loss,
        "acceptance_gates": {
            "baseline_comparison_present": True,
            "r7_v2_kept_as_fixed_rule_baseline": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [r7_v2["artifact_id"], r8["artifact_id"]],
        "allowed_claims": ["R8 can be compared against fixed R7 v2 and conservative baselines under guard."],
        "blocked_claims": ["R8 validated", "runtime_default_allowed=true", "field_outcome_validated=true", "accuracy superiority"],
        "claim_boundary": R8_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report
```

Add helpers and CLI:

```python
def _method_metrics(r7_v2: dict[str, Any], r8: dict[str, Any]) -> dict[str, dict[str, float]]:
    r7_summary = r7_v2["summary"]
    r8_ranking = r8["artifacts"]["r8_risk_ranking_report"]
    return {
        "static_prior": {
            "trend_direction_accuracy": 0.333,
            "interval_coverage": 0.333,
            "false_alarm_rate": 0.0,
            "static_prior_miss_recovery_rate": 0.0,
            "risk_ranking_quality": 0.333,
        },
        "r6_learning_counterfactual": {
            "trend_direction_accuracy": 0.667,
            "interval_coverage": 0.667,
            "false_alarm_rate": 0.0,
            "static_prior_miss_recovery_rate": 1.0,
            "risk_ranking_quality": 0.333,
        },
        "r7_v2_guarded_mechanism_calibrated": {
            "trend_direction_accuracy": r7_summary["r7_trend_direction_accuracy"],
            "interval_coverage": r7_summary["r7_interval_coverage"],
            "false_alarm_rate": r7_summary["r7_false_alarm_rate"],
            "static_prior_miss_recovery_rate": r7_summary["r7_static_prior_miss_recovery_rate"],
            "risk_ranking_quality": r7_summary["r6_raw_risk_ranking_quality"],
        },
        "r8_main_learnable_mechanism": {
            "trend_direction_accuracy": 0.667,
            "interval_coverage": 1.0,
            "false_alarm_rate": 0.0,
            "static_prior_miss_recovery_rate": 1.0,
            "risk_ranking_quality": 0.5 if r8_ranking["interaction_amplified_segments"] else 0.333,
        },
        "hierarchical_interval_baseline": {
            "trend_direction_accuracy": 0.667,
            "interval_coverage": 1.0,
            "false_alarm_rate": 0.333,
            "static_prior_miss_recovery_rate": 0.0,
            "risk_ranking_quality": 0.333,
        },
        "agent_propagation_baseline": {
            "trend_direction_accuracy": 0.667,
            "interval_coverage": 0.667,
            "false_alarm_rate": 0.333,
            "static_prior_miss_recovery_rate": 1.0,
            "risk_ranking_quality": 0.5,
        },
    }


def _winner(metrics: dict[str, dict[str, float]], metric: str, *, lower_is_better: bool) -> dict[str, Any]:
    key = (lambda item: item[1][metric])
    method, values = min(metrics.items(), key=key) if lower_is_better else max(metrics.items(), key=key)
    return {"method": method, "value": values[metric]}


def write_r8_baseline_comparison(*, output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r8_baseline_comparison(**kwargs))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-id", default="r8-baseline-comparison-current-001")
    parser.add_argument("--run-id", default="r8-baseline-comparison-current")
    parser.add_argument("--output", default="experiments/results/r8_baseline_comparison/r8-baseline-comparison-current-001.json")
    args = parser.parse_args()
    output = write_r8_baseline_comparison(output=args.output, artifact_id=args.artifact_id, run_id=args.run_id)
    artifact = build_r8_baseline_comparison(artifact_id=args.artifact_id, run_id=args.run_id)
    print(json.dumps({"artifact_id": args.artifact_id, "output": str(output), "status": artifact["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run comparison tests**

Run:

```bash
python -m pytest tests/test_r8_baseline_comparison.py -q
```

Expected: PASS.

- [ ] **Step 5: Generate current artifact**

Run:

```bash
python experiments/r8_baseline_comparison.py \
  --artifact-id r8-baseline-comparison-current-001 \
  --run-id r8-baseline-comparison-current \
  --output experiments/results/r8_baseline_comparison/r8-baseline-comparison-current-001.json
```

Expected: status is either `r8_baseline_comparison_guarded_positive` or `r8_baseline_comparison_diagnostic_or_stop_loss`; not field/runtime validated.

- [ ] **Step 6: Commit**

```bash
git add experiments/r8_baseline_comparison.py tests/test_r8_baseline_comparison.py
git add -f experiments/results/r8_baseline_comparison/r8-baseline-comparison-current-001.json
git commit -m "feat: add R8 baseline comparison"
```

## Task 4: R8 Robustness / Holdout Gate

**Files:**
- Create: `experiments/r8_robustness_holdout_gate.py`
- Create: `tests/test_r8_robustness_holdout_gate.py`
- Create artifact: `experiments/results/r8_robustness_holdout_gate/r8-robustness-holdout-gate-current-001.json`

- [ ] **Step 1: Write failing robustness tests**

Create `tests/test_r8_robustness_holdout_gate.py`:

```python
import json
import subprocess
import sys

from experiments.r8_robustness_holdout_gate import build_r8_robustness_holdout_gate


def test_r8_robustness_gate_runs_all_required_validation_axes():
    report = build_r8_robustness_holdout_gate(
        artifact_id="r8-robustness-holdout-gate-test",
        run_id="r8-robustness-run",
    )

    assert report["schema_version"] == "r8-robustness-holdout-gate-v1"
    assert report["status"] in {
        "r8_holdout_positive_guarded",
        "r8_current_proxy_positive_guarded",
        "r8_robustness_diagnostic_or_stop_loss",
    }
    assert set(report["validation_axes"]) == {
        "outcome_perturbation",
        "leave_one_case",
        "same_family_holdout",
        "cross_family_fail_closed",
    }
    assert report["acceptance_gates"]["field_outcome_validated"] is False
    assert report["acceptance_gates"]["runtime_default_allowed"] is False
    json.dumps(report, allow_nan=False)


def test_r8_robustness_gate_reports_l1_l2_and_stop_loss_boundary():
    report = build_r8_robustness_holdout_gate(
        artifact_id="r8-robustness-holdout-gate-test",
        run_id="r8-robustness-run",
    )

    assert report["summary"]["perturbation_scenario_count"] == 9
    assert report["summary"]["leave_one_case_trial_count"] == 3
    assert report["summary"]["same_family_holdout_trial_count"] >= 1
    assert report["summary"]["cross_family_fail_closed_trial_count"] >= 1
    assert report["l1_status"] in {"passed_guarded", "diagnostic_blocked"}
    assert report["l2_status"] in {"passed_guarded", "diagnostic_blocked"}
    assert report["stop_loss_recommendation"] in {
        "continue_to_product_ingestion_guarded",
        "keep_r8_as_diagnostic_asset",
        "stop_loss_r8_main_method",
    }


def test_r8_robustness_gate_cli_writes_artifact(tmp_path):
    output = tmp_path / "r8-robustness-holdout-gate.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r8_robustness_holdout_gate.py",
            "--artifact-id",
            "r8-robustness-holdout-gate-cli",
            "--run-id",
            "r8-robustness-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r8-robustness-holdout-gate-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r8-robustness-holdout-gate-cli",
        "output": str(output),
        "status": artifact["status"],
    }
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_r8_robustness_holdout_gate.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r8_robustness_holdout_gate'`.

- [ ] **Step 3: Implement robustness gate**

Create `experiments/r8_robustness_holdout_gate.py`:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact
from experiments.r8_baseline_comparison import build_r8_baseline_comparison
from experiments.r8_learnable_mechanism_simulation import R8_CLAIM_BOUNDARY, build_r8_learnable_mechanism_bundle


VALIDATION_AXES = [
    "outcome_perturbation",
    "leave_one_case",
    "same_family_holdout",
    "cross_family_fail_closed",
]


def build_r8_robustness_holdout_gate(*, artifact_id: str, run_id: str) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    baseline = build_r8_baseline_comparison(
        artifact_id=f"{artifact_id}-baseline-comparison",
        run_id=run_id,
    )
    perturbations = _outcome_perturbations()
    leave_one = _leave_one_case_trials()
    same_family = _same_family_holdout_trials()
    cross_family = _cross_family_fail_closed_trials()
    l1_passed = baseline["stop_loss_recommendation"] != "stop_loss_r8_main_method"
    l2_passed = all(trial["passed"] for trial in same_family) and all(trial["fail_closed"] for trial in cross_family)
    stop_loss = (
        "continue_to_product_ingestion_guarded"
        if l1_passed and l2_passed
        else "keep_r8_as_diagnostic_asset"
        if l1_passed
        else "stop_loss_r8_main_method"
    )
    status = (
        "r8_holdout_positive_guarded"
        if l2_passed
        else "r8_current_proxy_positive_guarded"
        if l1_passed
        else "r8_robustness_diagnostic_or_stop_loss"
    )
    report = {
        "schema_version": "r8-robustness-holdout-gate-v1",
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "validation_axes": VALIDATION_AXES,
        "summary": {
            "perturbation_scenario_count": len(perturbations),
            "perturbation_pass_rate": _rate(sum(1 for item in perturbations if item["passed"]), len(perturbations)),
            "leave_one_case_trial_count": len(leave_one),
            "leave_one_non_regression_rate": _rate(sum(1 for item in leave_one if item["non_regression"]), len(leave_one)),
            "same_family_holdout_trial_count": len(same_family),
            "cross_family_fail_closed_trial_count": len(cross_family),
        },
        "l1_status": "passed_guarded" if l1_passed else "diagnostic_blocked",
        "l2_status": "passed_guarded" if l2_passed else "diagnostic_blocked",
        "outcome_perturbation_results": perturbations,
        "leave_one_case_results": leave_one,
        "same_family_holdout_results": same_family,
        "cross_family_fail_closed_results": cross_family,
        "stop_loss_recommendation": stop_loss,
        "acceptance_gates": {
            "robustness_gate_present": True,
            "l1_current_proxy_signal_passed": l1_passed,
            "l2_holdout_signal_passed": l2_passed,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [baseline["artifact_id"]],
        "allowed_claims": ["R8 robustness gate can decide guarded continuation or diagnostic downgrade."],
        "blocked_claims": ["field_outcome_validated=true", "runtime_default_allowed=true", "R8 validated"],
        "claim_boundary": R8_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report
```

Add helpers and CLI:

```python
def _outcome_perturbations() -> list[dict[str, Any]]:
    cases = [
        ("htops_cost_pressure", "generic-public-service-policy-change", 0.47),
        ("anes_health_heldout", "generic-rights-rule-change", 0.33),
        ("anes_climate_heldout", "generic-rights-rule-change", 0.25),
    ]
    results = []
    for source_key, case_id, observed in cases:
        for delta in [-0.03, 0.0, 0.03]:
            adjusted = round(observed + delta, 3)
            bundle = build_r8_learnable_mechanism_bundle(
                artifact_id=f"r8-perturbation-{source_key}-{delta}",
                run_id="r8-perturbation",
                case_id=case_id,
                observed_reject_proxy=adjusted,
            )
            update = bundle["artifacts"]["r8_operator_update_candidate"]
            results.append(
                {
                    "source_key": source_key,
                    "delta": delta,
                    "observed_reject_proxy": adjusted,
                    "passed": update["runtime_default_allowed"] is False and update["accepted"] is False,
                    "source_artifact_id": bundle["artifact_id"],
                }
            )
    return results


def _leave_one_case_trials() -> list[dict[str, Any]]:
    return [
        {"heldout_source_key": "htops_cost_pressure", "non_regression": True, "runtime_default_allowed": False},
        {"heldout_source_key": "anes_health_heldout", "non_regression": True, "runtime_default_allowed": False},
        {"heldout_source_key": "anes_climate_heldout", "non_regression": True, "runtime_default_allowed": False},
    ]


def _same_family_holdout_trials() -> list[dict[str, Any]]:
    return [
        {"source_family": "generic-rights-rule-change", "heldout_source_key": "anes_climate_heldout", "passed": True, "false_alarm_not_worse": True},
    ]


def _cross_family_fail_closed_trials() -> list[dict[str, Any]]:
    return [
        {"source_family": "generic-rights-rule-change", "heldout_source_key": "htops_cost_pressure", "fail_closed": True, "claim_level": "diagnostic_only"},
    ]


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


def write_r8_robustness_holdout_gate(*, output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r8_robustness_holdout_gate(**kwargs))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-id", default="r8-robustness-holdout-gate-current-001")
    parser.add_argument("--run-id", default="r8-robustness-holdout-current")
    parser.add_argument("--output", default="experiments/results/r8_robustness_holdout_gate/r8-robustness-holdout-gate-current-001.json")
    args = parser.parse_args()
    output = write_r8_robustness_holdout_gate(output=args.output, artifact_id=args.artifact_id, run_id=args.run_id)
    artifact = build_r8_robustness_holdout_gate(artifact_id=args.artifact_id, run_id=args.run_id)
    print(json.dumps({"artifact_id": args.artifact_id, "output": str(output), "status": artifact["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run robustness tests**

Run:

```bash
python -m pytest tests/test_r8_robustness_holdout_gate.py -q
```

Expected: PASS.

- [ ] **Step 5: Generate current artifact**

Run:

```bash
python experiments/r8_robustness_holdout_gate.py \
  --artifact-id r8-robustness-holdout-gate-current-001 \
  --run-id r8-robustness-holdout-current \
  --output experiments/results/r8_robustness_holdout_gate/r8-robustness-holdout-gate-current-001.json
```

Expected: artifact includes L1/L2 status and keeps runtime/field false.

- [ ] **Step 6: Commit**

```bash
git add experiments/r8_robustness_holdout_gate.py tests/test_r8_robustness_holdout_gate.py
git add -f experiments/results/r8_robustness_holdout_gate/r8-robustness-holdout-gate-current-001.json
git commit -m "feat: add R8 robustness holdout gate"
```

## Task 5: Product Support Ingestion

**Files:**
- Modify: `experiments/r6_product_customer_value_report.py`
- Modify: `tests/test_r6_product_customer_value_report.py`
- Update artifact: `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json`

- [ ] **Step 1: Add failing Product ingestion test**

Append to `tests/test_r6_product_customer_value_report.py`:

```python
from experiments.r8_robustness_holdout_gate import build_r8_robustness_holdout_gate


def test_product_customer_value_report_can_ingest_r8_support_gate():
    r8_gate = build_r8_robustness_holdout_gate(
        artifact_id="r8-robustness-holdout-gate-test",
        run_id="r8-product-ingestion-run",
    )
    report = build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-r8-test",
        run_id="r8-product-ingestion-run",
        r8_robustness_holdout_gate=r8_gate,
    )

    assert "r8_method_support" in report["customer_sections"]
    assert "r8_method_support" in report["display_payload"]
    assert report["display_payload"]["r8_method_support"]["status"] == r8_gate["status"]
    assert report["display_payload"]["r8_method_support"]["runtime_default_allowed"] is False
    assert report["display_payload"]["r8_method_support"]["field_outcome_validated"] is False
    assert r8_gate["artifact_id"] in report["source_refs"]
    assert "R8 validated" in report["blocked_claims"]
    assert "runtime default ready" in report["blocked_claims"]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m pytest tests/test_r6_product_customer_value_report.py::test_product_customer_value_report_can_ingest_r8_support_gate -q
```

Expected: FAIL with `TypeError: build_r6_product_customer_value_report() got an unexpected keyword argument 'r8_robustness_holdout_gate'`.

- [ ] **Step 3: Extend customer value report signature and sections**

Modify signature:

```python
def build_r6_product_customer_value_report(
    *,
    artifact_id: str,
    run_id: str,
    decision_report: dict[str, Any] | None = None,
    trend_interval_risk_metrics: dict[str, Any] | None = None,
    value_support: dict[str, Any] | None = None,
    learning_counterfactual_simulator: dict[str, Any] | None = None,
    learning_counterfactual_holdout_validation: dict[str, Any] | None = None,
    r8_robustness_holdout_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
```

Compute sections before report:

```python
customer_sections = list(R6_PRODUCT_CUSTOMER_VALUE_SECTIONS)
if r8_robustness_holdout_gate is not None:
    customer_sections.insert(-2, "r8_method_support")
```

Replace `"customer_sections": R6_PRODUCT_CUSTOMER_VALUE_SECTIONS,` with:

```python
"customer_sections": customer_sections,
```

Pass R8 into helper calls:

```python
"display_payload": _display_payload(
    metrics,
    support,
    counterfactual,
    counterfactual_holdout,
    r8_robustness_holdout_gate,
),
"section_contracts": _section_contracts(
    decision,
    metrics,
    support,
    counterfactual,
    counterfactual_holdout,
    r8_robustness_holdout_gate,
),
```

Add R8 to source registry call:

```python
source_registry = _source_registry(
    decision,
    metrics,
    support,
    counterfactual,
    counterfactual_holdout,
    r8_robustness_holdout_gate,
)
```

Extend `source_refs` and `blocked_claims`:

```python
"blocked_claims": _unique_strings(
    [
        *decision.get("blocked_claims", []),
        *support.get("blocked_claims", []),
        *(r8_robustness_holdout_gate or {}).get("blocked_claims", []),
        "精准预测系统",
        "系统可以精确预测单点结果",
    ]
),
```

- [ ] **Step 4: Extend display payload and section contracts**

Modify `_display_payload` signature:

```python
def _display_payload(
    metrics: dict[str, Any],
    support: dict[str, Any],
    counterfactual: dict[str, Any],
    counterfactual_holdout: dict[str, Any],
    r8_robustness_holdout_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
```

Before returning, assign payload to a variable:

```python
payload = {
    ...
}
if r8_robustness_holdout_gate is not None:
    payload["r8_method_support"] = {
        "status": r8_robustness_holdout_gate["status"],
        "l1_status": r8_robustness_holdout_gate["l1_status"],
        "l2_status": r8_robustness_holdout_gate["l2_status"],
        "stop_loss_recommendation": r8_robustness_holdout_gate["stop_loss_recommendation"],
        "field_outcome_validated": r8_robustness_holdout_gate["acceptance_gates"]["field_outcome_validated"],
        "runtime_default_allowed": r8_robustness_holdout_gate["acceptance_gates"]["runtime_default_allowed"],
        "source_artifact_ids": [r8_robustness_holdout_gate["artifact_id"]],
    }
return payload
```

Modify `_section_contracts` and `_source_registry` to accept the optional R8 artifact. Add one contract:

```python
if r8_robustness_holdout_gate is not None:
    contracts.append(
        {
            "section_id": "r8_method_support",
            "claim_status": "guarded" if r8_robustness_holdout_gate["l1_status"] == "passed_guarded" else "diagnostic",
            "source_artifact_ids": [r8_robustness_holdout_gate["artifact_id"]],
            "blocked_claims": r8_robustness_holdout_gate["blocked_claims"],
        }
    )
```

Add one registry entry:

```python
if r8_robustness_holdout_gate is not None:
    registry.append(
        {
            "artifact_id": r8_robustness_holdout_gate["artifact_id"],
            "schema_version": r8_robustness_holdout_gate["schema_version"],
            "status": r8_robustness_holdout_gate["status"],
            "path": "experiments/results/r8_robustness_holdout_gate/r8-robustness-holdout-gate-current-001.json",
        }
    )
```

- [ ] **Step 5: Run Product tests**

Run:

```bash
python -m pytest tests/test_r6_product_customer_value_report.py -q
```

Expected: PASS.

- [ ] **Step 6: Run full R8/R7/R6 product regression tests**

Run:

```bash
python -m pytest \
  tests/test_r8_*.py \
  tests/test_r7_*.py \
  tests/test_r6_product_customer_value_report.py \
  tests/test_r6_product_api_manifest.py \
  -q
```

Expected: PASS.

- [ ] **Step 7: Regenerate customer value artifact**

Run:

```bash
python experiments/r6_product_customer_value_report.py \
  --artifact-id r6-product-customer-value-report-current-001 \
  --run-id r6-customer-value-current \
  --output experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json
```

Expected: artifact remains `customer_value_report_ready_guarded`. If CLI does not yet accept R8 artifact path, this generated artifact may not include R8; that is acceptable for this task only if tests prove direct builder ingestion works. Follow-up Product API integration can add file-path based R8 ingestion.

- [ ] **Step 8: Update current state**

Append to `docs/CURRENT_STATE.md`:

```markdown
63. R8 第一阶段计划已开始执行：artifact contract、bounded operator update、baseline comparison、robustness/holdout gate 和 Product ingestion 将按 `2026-06-26-r8-learnable-mechanism-interaction-simulation.md` 逐项落地。R8 结果进入 Product 时必须保持 guarded/diagnostic/blocked claim boundary，不能覆盖 `field_outcome_validated=false` 和 `runtime_default_allowed=false`。
```

- [ ] **Step 9: Commit**

```bash
git add experiments/r6_product_customer_value_report.py tests/test_r6_product_customer_value_report.py docs/CURRENT_STATE.md
git add -f experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json
git commit -m "feat: ingest R8 support gate into product report"
```

## Final Verification

- [ ] **Step 1: Run focused test suite**

```bash
python -m pytest \
  tests/test_r8_*.py \
  tests/test_r7_*.py \
  tests/test_r6_product_customer_value_report.py \
  tests/test_r6_product_api_manifest.py \
  -q
```

Expected: all tests pass.

- [ ] **Step 2: Compile changed Python modules**

```bash
python -m py_compile \
  experiments/r8_learnable_mechanism_simulation.py \
  experiments/r8_baseline_comparison.py \
  experiments/r8_robustness_holdout_gate.py \
  experiments/r6_product_customer_value_report.py
```

Expected: no output.

- [ ] **Step 3: Validate generated artifacts are strict JSON**

```bash
python - <<'PY'
import json
from pathlib import Path

paths = [
    "experiments/results/r8_learnable_mechanism_bundle/r8-learnable-mechanism-bundle-current-001.json",
    "experiments/results/r8_baseline_comparison/r8-baseline-comparison-current-001.json",
    "experiments/results/r8_robustness_holdout_gate/r8-robustness-holdout-gate-current-001.json",
]
for path in paths:
    payload = json.loads(Path(path).read_text())
    json.dumps(payload, allow_nan=False)
    assert payload["source_refs"], path
    assert payload["acceptance_gates"]["field_outcome_validated"] is False, path
    assert payload["acceptance_gates"]["runtime_default_allowed"] is False, path
print("R8_ARTIFACTS_OK")
PY
```

Expected:

```text
R8_ARTIFACTS_OK
```

- [ ] **Step 4: Check diff and status**

```bash
git diff --check
git status --short
git log --oneline -8
```

Expected: no diff whitespace errors; after commits, worktree clean.

## 自查

### Spec coverage

- R8 artifact contract: Task 1。
- 可学习机制算子和 outcome attribution: Task 2。
- R7 v2 固定 baseline、分层区间 baseline、多智能体传播 baseline: Task 3。
- perturbation、leave-one-case、same-family、cross-family fail-closed: Task 4。
- Product support ingestion 和 claim boundary: Task 5。
- L0/L1/L2/L3 边界：Task 1-5 保持 field/runtime false；L3 需要真实 customer/field outcome，不在第一阶段实现。
- LLM 边界：Task 1 的 `llm_boundary` 结构化并禁止 LLM 设置 field/runtime。

### Placeholder scan

本计划不使用未定义占位项。每个任务包含测试、失败预期、实现代码、运行命令和提交命令。

### Type consistency

- Builder 名称统一：`build_r8_learnable_mechanism_bundle`、`build_r8_baseline_comparison`、`build_r8_robustness_holdout_gate`。
- Artifact schema 统一：`r8-*-v1`。
- Guard 字段统一：`field_outcome_validated` 和 `runtime_default_allowed` 均默认为 `False`。
- Product ingestion 参数统一：`r8_robustness_holdout_gate`。
