# R12 L0/L1 Case Registry and Operator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 R12 L0/L1：把 R11 HPS proxy holdout cases 转成 outcome-supervised learning case registry，并定义受先验保护的 causal interaction operator contract。

**Architecture:** 新增两个独立 artifact builder。`experiments/r12_outcome_case_registry.py` 只负责消费 R11 external holdout validation，生成 train / validation / holdout split 与 leakage guard；`experiments/r12_causal_interaction_operator.py` 只负责消费 case registry 与 R11 outcome feedback update，定义可学习参数、收缩规则、更新边界和 blocked claims。两者都不执行 outcome-supervised update，也不声明 Product core method。

**Tech Stack:** Python 标准库、pytest、现有 `experiments.r6_contracts` artifact helper。

---

## File Structure

- Create: `tests/test_r12_outcome_case_registry.py`
  - 验证 L0 case registry schema、split contract、outcome leakage guard、CLI 写文件。
- Create: `experiments/r12_outcome_case_registry.py`
  - 提供 `R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION`、`build_r12_outcome_case_registry()`、`write_r12_outcome_case_registry()` 和 CLI。
- Create: `tests/test_r12_causal_interaction_operator.py`
  - 验证 L1 operator contract、参数类型、收缩规则、no-prompt/persona guard、CLI 写文件。
- Create: `experiments/r12_causal_interaction_operator.py`
  - 提供 `R12_CAUSAL_INTERACTION_OPERATOR_SCHEMA_VERSION`、`build_r12_causal_interaction_operator()`、`write_r12_causal_interaction_operator()` 和 CLI。
- Create: `experiments/results/r12_outcome_case_registry/r12-outcome-case-registry-current-001.json`
  - 当前 L0 artifact，必须显式 `git add -f`。
- Create: `experiments/results/r12_causal_interaction_operator/r12-causal-interaction-operator-current-001.json`
  - 当前 L1 artifact，必须显式 `git add -f`。
- Modify: `docs/CURRENT_STATE.md`
  - 记录 R12 L0/L1 已实现和仍未 Product-ready 的边界。
- Modify: `docs/active-spec.md`
  - 记录 R12 L0/L1 current artifact 与下一步 R12 L2。

## Implementation Notes

R12 L0 只从 `r11-external-holdout-validation-current-001.json` 的 `external_holdout_cases` 读取 observed outcome proxy。当前 6 个 case 的 split 固定为：

- train: `hps_REGION_2`, `hps_METRO_STATUS_2`
- validation: `hps_REGION_1`, `hps_METRO_STATUS_1`
- holdout: `hps_REGION_3`, `hps_REGION_4`

固定 split 的原因是第一阶段样本很小，必须可复现并避免随机 seed 引入解释噪声。train split 覆盖两个 observed high-risk case；validation / holdout 保留未用于更新的低风险或边界 case，用于后续检验 negative transfer。

R12 L1 不计算 update。它只定义参数状态与 guard：

- mechanism weights: `price_pressure`, `trust_loss`, `service_friction`
- segment sensitivities: from L0 train high-risk segments
- interaction edge weights: `scenario_to_price_pressure`, `price_pressure_to_segment_reaction`, `segment_peer_amplification`
- uncertainty parameters: `interval_half_width`, `tail_risk_margin`, `posterior_shrinkage_strength`
- update bounds: bounded deltas per parameter type
- blocked updates: prompt/persona manual patch, runtime default, field validation claim

---

### Task 1: R12 Outcome Case Registry

**Files:**
- Create: `tests/test_r12_outcome_case_registry.py`
- Create: `experiments/r12_outcome_case_registry.py`
- Create: `experiments/results/r12_outcome_case_registry/r12-outcome-case-registry-current-001.json`

- [x] **Step 1: Write the failing test**

Create `tests/test_r12_outcome_case_registry.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_outcome_case_registry import (
    R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION,
    build_r12_outcome_case_registry,
)


def test_r12_outcome_case_registry_builds_fixed_split_without_runtime_escalation():
    registry = build_r12_outcome_case_registry(
        artifact_id="r12-outcome-case-registry-test",
        run_id="r12-l0-test",
        r11_external_holdout_validation=_load_current_r11_external_holdout(),
    )

    assert registry["schema_version"] == R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION
    assert registry["status"] == "r12_outcome_case_registry_ready_guarded"
    assert registry["claim_level"] == "outcome_supervised_learning_material_only"
    assert registry["case_registry_contract"] == {
        "source_backed_public_proxy": True,
        "split_strategy": "fixed_hps_segment_split_v1",
        "train_outcome_read_allowed": True,
        "validation_outcome_read_allowed_for_training": False,
        "holdout_outcome_read_allowed_for_training": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert registry["split_summary"] == {
        "case_count": 6,
        "train_count": 2,
        "validation_count": 2,
        "holdout_count": 2,
        "observed_high_risk_train_count": 2,
        "observed_high_risk_validation_count": 0,
        "observed_high_risk_holdout_count": 0,
    }
    assert {case["case_id"] for case in registry["cases"] if case["split"] == "train"} == {
        "hps_REGION_2",
        "hps_METRO_STATUS_2",
    }
    assert registry["leakage_guard"] == {
        "train_case_ids_with_observed_outcome_available": [
            "hps_METRO_STATUS_2",
            "hps_REGION_2",
        ],
        "validation_case_ids_blocked_for_training": [
            "hps_METRO_STATUS_1",
            "hps_REGION_1",
        ],
        "holdout_case_ids_blocked_for_training": [
            "hps_REGION_3",
            "hps_REGION_4",
        ],
        "outcome_leakage_blocked": True,
    }
    assert registry["acceptance_gates"] == {
        "case_registry_ready": True,
        "minimum_case_count_present": True,
        "train_validation_holdout_split_present": True,
        "outcome_leakage_blocked": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert "runtime_default_allowed=true" in registry["blocked_claims"]
    json.dumps(registry, allow_nan=False)


def test_r12_outcome_case_registry_cases_have_learning_fields():
    registry = build_r12_outcome_case_registry(
        artifact_id="r12-outcome-case-registry-test",
        run_id="r12-l0-test",
        r11_external_holdout_validation=_load_current_r11_external_holdout(),
    )

    by_id = {case["case_id"]: case for case in registry["cases"]}
    train = by_id["hps_METRO_STATUS_2"]
    assert train["learning_role"] == "train_outcome_supervision"
    assert train["scenario_shock"] == "hps_price_pressure_proxy"
    assert train["mechanism_labels"] == ["price_pressure"]
    assert train["outcome_proxy"]["name"] == "PRICESTRESS"
    assert train["outcome_proxy"]["observed_value"] == 0.55329
    assert train["prediction_state"] == {
        "static_prior_prediction": 0.454619,
        "interaction_prediction": 0.498821,
        "residual_vs_interaction": 0.054469,
        "residual_vs_static_prior": 0.098671,
    }
    assert train["guard_flags"] == {
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
        "eligible_for_runtime_update": False,
    }


def test_r12_outcome_case_registry_cli_writes_artifact(tmp_path):
    r11_path = tmp_path / "r11-external-holdout.json"
    output = tmp_path / "r12-outcome-case-registry.json"
    r11_path.write_text(json.dumps(_load_current_r11_external_holdout(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_outcome_case_registry.py",
            "--artifact-id",
            "r12-outcome-case-registry-cli",
            "--run-id",
            "r12-l0-test",
            "--r11-external-holdout-validation-path",
            str(r11_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r12-outcome-case-registry-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-outcome-case-registry-cli",
        "output": str(output),
        "status": "r12_outcome_case_registry_ready_guarded",
    }


def _load_current_r11_external_holdout():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r11_external_holdout_validation/"
            "r11-external-holdout-validation-current-001.json"
        ).read_text()
    )
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_r12_outcome_case_registry.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r12_outcome_case_registry'`.

- [x] **Step 3: Write minimal implementation**

Create `experiments/r12_outcome_case_registry.py` with these public functions and behavior:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    assert_strict_json,
    load_json_artifact,
    non_empty_string,
    write_json_artifact,
)
from experiments.r11_external_holdout_validation import (
    R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION,
)


R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION = "r12-outcome-case-registry-v1"
TRAIN_CASE_IDS = ["hps_REGION_2", "hps_METRO_STATUS_2"]
VALIDATION_CASE_IDS = ["hps_REGION_1", "hps_METRO_STATUS_1"]
HOLDOUT_CASE_IDS = ["hps_REGION_3", "hps_REGION_4"]


def build_r12_outcome_case_registry(
    *,
    artifact_id: str,
    run_id: str,
    r11_external_holdout_validation: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_r11_external_holdout(r11_external_holdout_validation)
    raw_cases = r11_external_holdout_validation["external_holdout_cases"]
    cases = [_registry_case(case) for case in raw_cases]
    cases.sort(key=lambda item: (item["split_order"], item["case_id"]))
    for case in cases:
        del case["split_order"]
    report = {
        "schema_version": R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r12_outcome_case_registry_ready_guarded",
        "claim_level": "outcome_supervised_learning_material_only",
        "case_registry_contract": {
            "source_backed_public_proxy": True,
            "split_strategy": "fixed_hps_segment_split_v1",
            "train_outcome_read_allowed": True,
            "validation_outcome_read_allowed_for_training": False,
            "holdout_outcome_read_allowed_for_training": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "split_summary": _split_summary(cases),
        "leakage_guard": _leakage_guard(cases),
        "cases": cases,
        "acceptance_gates": {
            "case_registry_ready": True,
            "minimum_case_count_present": len(cases) >= 6,
            "train_validation_holdout_split_present": _split_set(cases)
            == {"train", "validation", "holdout"},
            "outcome_leakage_blocked": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [r11_external_holdout_validation["artifact_id"]],
        "blocked_claims": [
            "R12 field validated",
            "R12 Product core method ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "validation or holdout outcome used for training",
            "prompt/persona manual patch as automatic calibration",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report
```

Continue the implementation with private helpers:

```python
def write_r12_outcome_case_registry(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r12_outcome_case_registry(**kwargs))


def _validate_r11_external_holdout(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION:
        raise ValueError("r11_external_holdout_validation.schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r11_external_holdout_validation.acceptance_gates must be an object")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r11 external holdout must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r11 external holdout must not allow runtime default")
    cases = artifact.get("external_holdout_cases")
    if not isinstance(cases, list) or len(cases) < 6:
        raise ValueError("r11 external holdout must contain at least 6 cases")


def _registry_case(case: dict[str, Any]) -> dict[str, Any]:
    case_id = non_empty_string(case.get("case_id"), field="case.case_id")
    split, learning_role, order = _split(case_id)
    observed = round(float(case["holdout_outcome_proxy"]), 6)
    interaction = round(float(case["r11_prediction"]), 6)
    static_prior = round(float(case["static_prior_prediction"]), 6)
    return {
        "case_id": case_id,
        "split": split,
        "split_order": order,
        "learning_role": learning_role,
        "scenario_shock": "hps_price_pressure_proxy",
        "segment_labels": {
            "segment_column": case["segment_column"],
            "segment_value": str(case["segment_value"]),
        },
        "mechanism_labels": ["price_pressure"],
        "source_signal": {
            "name": "PRICECONCERN",
            "risk_share": round(float(case["source_signal_risk_share"]), 6),
            "delta": round(float(case["source_signal_delta"]), 6),
        },
        "outcome_proxy": {
            "name": "PRICESTRESS",
            "observed_value": observed,
            "observed_high_risk": bool(case["observed_high_risk"]),
        },
        "prediction_state": {
            "static_prior_prediction": static_prior,
            "interaction_prediction": interaction,
            "residual_vs_interaction": round(observed - interaction, 6),
            "residual_vs_static_prior": round(observed - static_prior, 6),
        },
        "risk_interval": case["risk_interval"],
        "guard_flags": {
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
            "eligible_for_runtime_update": False,
        },
    }


def _split(case_id: str) -> tuple[str, str, int]:
    if case_id in TRAIN_CASE_IDS:
        return "train", "train_outcome_supervision", 0
    if case_id in VALIDATION_CASE_IDS:
        return "validation", "validation_transfer_check", 1
    if case_id in HOLDOUT_CASE_IDS:
        return "holdout", "holdout_transfer_check", 2
    raise ValueError(f"case id is not assigned to an R12 split: {case_id}")
```

Finish with summary, leakage guard and CLI:

```python
def _split_summary(cases: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "case_count": len(cases),
        "train_count": sum(1 for case in cases if case["split"] == "train"),
        "validation_count": sum(1 for case in cases if case["split"] == "validation"),
        "holdout_count": sum(1 for case in cases if case["split"] == "holdout"),
        "observed_high_risk_train_count": sum(
            1
            for case in cases
            if case["split"] == "train" and case["outcome_proxy"]["observed_high_risk"]
        ),
        "observed_high_risk_validation_count": sum(
            1
            for case in cases
            if case["split"] == "validation" and case["outcome_proxy"]["observed_high_risk"]
        ),
        "observed_high_risk_holdout_count": sum(
            1
            for case in cases
            if case["split"] == "holdout" and case["outcome_proxy"]["observed_high_risk"]
        ),
    }


def _leakage_guard(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "train_case_ids_with_observed_outcome_available": sorted(
            case["case_id"] for case in cases if case["split"] == "train"
        ),
        "validation_case_ids_blocked_for_training": sorted(
            case["case_id"] for case in cases if case["split"] == "validation"
        ),
        "holdout_case_ids_blocked_for_training": sorted(
            case["case_id"] for case in cases if case["split"] == "holdout"
        ),
        "outcome_leakage_blocked": True,
    }


def _split_set(cases: list[dict[str, Any]]) -> set[str]:
    return {case["split"] for case in cases}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--r11-external-holdout-validation-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_outcome_case_registry(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r11_external_holdout_validation=load_json_artifact(
            args.r11_external_holdout_validation_path
        ),
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/python -m pytest tests/test_r12_outcome_case_registry.py -q
```

Expected: PASS with `3 passed`.

- [x] **Step 5: Generate current L0 artifact**

Run:

```bash
.venv/bin/python experiments/r12_outcome_case_registry.py \
  --artifact-id r12-outcome-case-registry-current-001 \
  --run-id r12-l0-current \
  --r11-external-holdout-validation-path experiments/results/r11_external_holdout_validation/r11-external-holdout-validation-current-001.json \
  --output experiments/results/r12_outcome_case_registry/r12-outcome-case-registry-current-001.json
```

Expected stdout:

```json
{"artifact_id": "r12-outcome-case-registry-current-001", "output": "experiments/results/r12_outcome_case_registry/r12-outcome-case-registry-current-001.json", "status": "r12_outcome_case_registry_ready_guarded"}
```

- [x] **Step 6: Commit L0**

Run:

```bash
git add tests/test_r12_outcome_case_registry.py experiments/r12_outcome_case_registry.py experiments/results/r12_outcome_case_registry/r12-outcome-case-registry-current-001.json -f
git commit -m "feat: add R12 outcome case registry"
```

### Task 2: R12 Causal Interaction Operator

**Files:**
- Create: `tests/test_r12_causal_interaction_operator.py`
- Create: `experiments/r12_causal_interaction_operator.py`
- Create: `experiments/results/r12_causal_interaction_operator/r12-causal-interaction-operator-current-001.json`

- [x] **Step 1: Write the failing test**

Create `tests/test_r12_causal_interaction_operator.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_causal_interaction_operator import (
    R12_CAUSAL_INTERACTION_OPERATOR_SCHEMA_VERSION,
    build_r12_causal_interaction_operator,
)


def test_r12_causal_interaction_operator_defines_bounded_parameters():
    operator = build_r12_causal_interaction_operator(
        artifact_id="r12-causal-interaction-operator-test",
        run_id="r12-l1-test",
        r12_outcome_case_registry=_load_current_case_registry(),
        r11_outcome_feedback_update=_load_current_r11_feedback_update(),
    )

    assert operator["schema_version"] == R12_CAUSAL_INTERACTION_OPERATOR_SCHEMA_VERSION
    assert operator["status"] == "r12_causal_interaction_operator_ready_guarded"
    assert operator["operator_contract"] == {
        "operator_id": "r12_oscio_l1",
        "updates_are_structured_parameters_only": True,
        "prompt_or_persona_manual_patch_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert set(operator["parameter_state"]) == {
        "mechanism_weights",
        "segment_sensitivities",
        "interaction_edge_weights",
        "uncertainty_parameters",
    }
    assert operator["parameter_state"]["mechanism_weights"]["price_pressure"] == {
        "value": 0.52,
        "prior": 0.5,
        "lower_bound": 0.35,
        "upper_bound": 0.75,
        "source": "r11_feedback_diagnostic_price_pressure",
    }
    assert operator["parameter_state"]["segment_sensitivities"]["hps_METRO_STATUS_2"] == {
        "value": 1.09,
        "prior": 1.0,
        "lower_bound": 0.8,
        "upper_bound": 1.25,
        "source": "r11_segment_sensitivity_shadow_accepted",
    }
    assert operator["update_bounds"]["segment_sensitivity"] == {
        "max_abs_delta": 0.12,
        "requires_holdout_before_default": True,
    }
    assert operator["acceptance_gates"] == {
        "operator_contract_ready": True,
        "structured_parameter_state_present": True,
        "train_cases_only_used_for_parameter_initialization": True,
        "prompt_or_persona_manual_patch_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert "prompt/persona manual patch as automatic calibration" in operator["blocked_claims"]
    json.dumps(operator, allow_nan=False)


def test_r12_causal_interaction_operator_records_prior_shrinkage_and_edge_guard():
    operator = build_r12_causal_interaction_operator(
        artifact_id="r12-causal-interaction-operator-test",
        run_id="r12-l1-test",
        r12_outcome_case_registry=_load_current_case_registry(),
        r11_outcome_feedback_update=_load_current_r11_feedback_update(),
    )

    assert operator["prior_shrinkage_rules"] == {
        "static_prior_is_base_distribution": True,
        "interaction_layer_updates_are_bounded": True,
        "small_sample_updates_shrink_toward_prior": True,
        "posterior_shrinkage_strength": 0.65,
        "validation_or_holdout_outcome_not_used_for_initialization": True,
    }
    assert operator["interaction_edge_update_guard"] == {
        "direct_propagation_evidence_present": False,
        "edge_update_status": "rejected",
        "rejection_reason": "r11 feedback packet lacks direct interaction propagation evidence",
    }
    assert operator["next_required_artifact"] == "r12_outcome_supervised_update"


def test_r12_causal_interaction_operator_cli_writes_artifact(tmp_path):
    registry_path = tmp_path / "r12-case-registry.json"
    feedback_path = tmp_path / "r11-feedback-update.json"
    output = tmp_path / "r12-causal-interaction-operator.json"
    registry_path.write_text(json.dumps(_load_current_case_registry(), allow_nan=False))
    feedback_path.write_text(json.dumps(_load_current_r11_feedback_update(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_causal_interaction_operator.py",
            "--artifact-id",
            "r12-causal-interaction-operator-cli",
            "--run-id",
            "r12-l1-test",
            "--r12-outcome-case-registry-path",
            str(registry_path),
            "--r11-outcome-feedback-update-path",
            str(feedback_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r12-causal-interaction-operator-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-causal-interaction-operator-cli",
        "output": str(output),
        "status": "r12_causal_interaction_operator_ready_guarded",
    }


def _load_current_case_registry():
    repo_root = Path(__file__).resolve().parents[1]
    path = (
        repo_root
        / "experiments/results/r12_outcome_case_registry/"
        "r12-outcome-case-registry-current-001.json"
    )
    if path.exists():
        return json.loads(path.read_text())
    from experiments.r12_outcome_case_registry import build_r12_outcome_case_registry

    return build_r12_outcome_case_registry(
        artifact_id="r12-outcome-case-registry-fixture",
        run_id="r12-l1-test",
        r11_external_holdout_validation=json.loads(
            (
                repo_root
                / "experiments/results/r11_external_holdout_validation/"
                "r11-external-holdout-validation-current-001.json"
            ).read_text()
        ),
    )


def _load_current_r11_feedback_update():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r11_outcome_feedback_update/"
            "r11-outcome-feedback-update-current-001.json"
        ).read_text()
    )
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_r12_causal_interaction_operator.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r12_causal_interaction_operator'`.

- [x] **Step 3: Write minimal implementation**

Create `experiments/r12_causal_interaction_operator.py` with these public functions and behavior:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    assert_strict_json,
    load_json_artifact,
    non_empty_string,
    write_json_artifact,
)
from experiments.r11_outcome_feedback_update import (
    R11_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION,
)
from experiments.r12_outcome_case_registry import (
    R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION,
)


R12_CAUSAL_INTERACTION_OPERATOR_SCHEMA_VERSION = (
    "r12-causal-interaction-operator-v1"
)


def build_r12_causal_interaction_operator(
    *,
    artifact_id: str,
    run_id: str,
    r12_outcome_case_registry: dict[str, Any],
    r11_outcome_feedback_update: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_case_registry(r12_outcome_case_registry)
    _validate_feedback_update(r11_outcome_feedback_update)
    report = {
        "schema_version": R12_CAUSAL_INTERACTION_OPERATOR_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r12_causal_interaction_operator_ready_guarded",
        "claim_level": "operator_contract_only",
        "operator_contract": {
            "operator_id": "r12_oscio_l1",
            "updates_are_structured_parameters_only": True,
            "prompt_or_persona_manual_patch_allowed": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "parameter_state": _parameter_state(
            case_registry=r12_outcome_case_registry,
            feedback_update=r11_outcome_feedback_update,
        ),
        "prior_shrinkage_rules": {
            "static_prior_is_base_distribution": True,
            "interaction_layer_updates_are_bounded": True,
            "small_sample_updates_shrink_toward_prior": True,
            "posterior_shrinkage_strength": 0.65,
            "validation_or_holdout_outcome_not_used_for_initialization": True,
        },
        "update_bounds": {
            "mechanism_weight": {
                "max_abs_delta": 0.08,
                "requires_holdout_before_default": True,
            },
            "segment_sensitivity": {
                "max_abs_delta": 0.12,
                "requires_holdout_before_default": True,
            },
            "interaction_edge_weight": {
                "max_abs_delta": 0.05,
                "requires_direct_propagation_evidence": True,
            },
            "uncertainty_parameter": {
                "max_abs_delta": 0.05,
                "requires_interval_miss_or_tail_risk_evidence": True,
            },
        },
        "interaction_edge_update_guard": {
            "direct_propagation_evidence_present": False,
            "edge_update_status": "rejected",
            "rejection_reason": (
                "r11 feedback packet lacks direct interaction propagation evidence"
            ),
        },
        "acceptance_gates": {
            "operator_contract_ready": True,
            "structured_parameter_state_present": True,
            "train_cases_only_used_for_parameter_initialization": True,
            "prompt_or_persona_manual_patch_allowed": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [
            r12_outcome_case_registry["artifact_id"],
            r11_outcome_feedback_update["artifact_id"],
        ],
        "next_required_artifact": "r12_outcome_supervised_update",
        "blocked_claims": [
            "R12 outcome-supervised update already validated",
            "R12 Product core method ready",
            "prompt/persona manual patch as automatic calibration",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report
```

Continue implementation with validation and parameter helpers:

```python
def write_r12_causal_interaction_operator(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r12_causal_interaction_operator(**kwargs))


def _validate_case_registry(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION:
        raise ValueError("r12_outcome_case_registry.schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12_outcome_case_registry.acceptance_gates must be an object")
    if gates.get("outcome_leakage_blocked") is not True:
        raise ValueError("r12 outcome case registry must block outcome leakage")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 outcome case registry must not allow runtime default")


def _validate_feedback_update(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R11_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION:
        raise ValueError("r11_outcome_feedback_update.schema_version is invalid")
    gate = artifact.get("update_gate")
    if not isinstance(gate, dict):
        raise ValueError("r11_outcome_feedback_update.update_gate must be an object")
    if gate.get("runtime_default_allowed") is not False:
        raise ValueError("r11 feedback update must not allow runtime default")
    if gate.get("prompt_or_persona_manual_patch_allowed") is not False:
        raise ValueError("prompt/persona patch must be blocked")


def _parameter_state(
    *,
    case_registry: dict[str, Any],
    feedback_update: dict[str, Any],
) -> dict[str, Any]:
    train_cases = [case for case in case_registry["cases"] if case["split"] == "train"]
    accepted_segment = next(
        candidate
        for candidate in feedback_update["update_candidates"]
        if candidate["update_type"] == "segment_sensitivity"
        and candidate["status"] == "accepted"
    )
    mechanism = next(
        candidate
        for candidate in feedback_update["update_candidates"]
        if candidate["update_type"] == "mechanism_weight"
    )
    return {
        "mechanism_weights": {
            "price_pressure": {
                "value": round(0.5 + float(mechanism["recommended_delta"]), 2),
                "prior": 0.5,
                "lower_bound": 0.35,
                "upper_bound": 0.75,
                "source": "r11_feedback_diagnostic_price_pressure",
            },
            "trust_loss": {
                "value": 0.3,
                "prior": 0.3,
                "lower_bound": 0.1,
                "upper_bound": 0.55,
                "source": "r12_prior_contract",
            },
            "service_friction": {
                "value": 0.25,
                "prior": 0.25,
                "lower_bound": 0.05,
                "upper_bound": 0.5,
                "source": "r12_prior_contract",
            },
        },
        "segment_sensitivities": _segment_sensitivities(
            train_cases=train_cases,
            accepted_segment=accepted_segment,
        ),
        "interaction_edge_weights": {
            "scenario_to_price_pressure": {
                "value": 0.6,
                "prior": 0.55,
                "lower_bound": 0.3,
                "upper_bound": 0.8,
                "source": "hps_price_pressure_proxy",
            },
            "price_pressure_to_segment_reaction": {
                "value": 0.52,
                "prior": 0.5,
                "lower_bound": 0.3,
                "upper_bound": 0.75,
                "source": "r11_external_holdout_transfer",
            },
            "segment_peer_amplification": {
                "value": 0.0,
                "prior": 0.0,
                "lower_bound": 0.0,
                "upper_bound": 0.2,
                "source": "blocked_until_direct_propagation_evidence",
            },
        },
        "uncertainty_parameters": {
            "interval_half_width": {
                "value": 0.1,
                "prior": 0.1,
                "lower_bound": 0.08,
                "upper_bound": 0.2,
                "source": "r11_external_holdout_interval",
            },
            "tail_risk_margin": {
                "value": 0.03,
                "prior": 0.03,
                "lower_bound": 0.02,
                "upper_bound": 0.08,
                "source": "r11_high_risk_threshold_margin",
            },
            "posterior_shrinkage_strength": {
                "value": 0.65,
                "prior": 0.65,
                "lower_bound": 0.5,
                "upper_bound": 0.9,
                "source": "r12_prior_protection",
            },
        },
    }
```

Finish with segment sensitivity helper and CLI:

```python
def _segment_sensitivities(
    *,
    train_cases: list[dict[str, Any]],
    accepted_segment: dict[str, Any],
) -> dict[str, Any]:
    sensitivities = {}
    for case in train_cases:
        delta = (
            float(accepted_segment["recommended_delta"])
            if case["case_id"] == accepted_segment["target"]
            else 0.04
        )
        sensitivities[case["case_id"]] = {
            "value": round(1.0 + delta, 2),
            "prior": 1.0,
            "lower_bound": 0.8,
            "upper_bound": 1.25,
            "source": (
                "r11_segment_sensitivity_shadow_accepted"
                if case["case_id"] == accepted_segment["target"]
                else "r12_train_high_risk_segment_prior"
            ),
        }
    return sensitivities


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--r12-outcome-case-registry-path", required=True)
    parser.add_argument("--r11-outcome-feedback-update-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_causal_interaction_operator(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_outcome_case_registry=load_json_artifact(
            args.r12_outcome_case_registry_path
        ),
        r11_outcome_feedback_update=load_json_artifact(
            args.r11_outcome_feedback_update_path
        ),
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/python -m pytest tests/test_r12_causal_interaction_operator.py -q
```

Expected: PASS with `3 passed`.

- [x] **Step 5: Generate current L1 artifact**

Run:

```bash
.venv/bin/python experiments/r12_causal_interaction_operator.py \
  --artifact-id r12-causal-interaction-operator-current-001 \
  --run-id r12-l1-current \
  --r12-outcome-case-registry-path experiments/results/r12_outcome_case_registry/r12-outcome-case-registry-current-001.json \
  --r11-outcome-feedback-update-path experiments/results/r11_outcome_feedback_update/r11-outcome-feedback-update-current-001.json \
  --output experiments/results/r12_causal_interaction_operator/r12-causal-interaction-operator-current-001.json
```

Expected stdout:

```json
{"artifact_id": "r12-causal-interaction-operator-current-001", "output": "experiments/results/r12_causal_interaction_operator/r12-causal-interaction-operator-current-001.json", "status": "r12_causal_interaction_operator_ready_guarded"}
```

- [x] **Step 6: Commit L1**

Run:

```bash
git add tests/test_r12_causal_interaction_operator.py experiments/r12_causal_interaction_operator.py experiments/results/r12_causal_interaction_operator/r12-causal-interaction-operator-current-001.json -f
git commit -m "feat: add R12 causal interaction operator"
```

### Task 3: Docs and Verification

**Files:**
- Modify: `docs/CURRENT_STATE.md`
- Modify: `docs/active-spec.md`
- Modify: `docs/superpowers/specs/2026-06-26-r12-outcome-supervised-causal-interaction-operator-spec.md`

- [x] **Step 1: Update docs**

Add current-state entries with these facts:

```markdown
R12 L0 case registry 已实现为 `experiments/r12_outcome_case_registry.py`、`tests/test_r12_outcome_case_registry.py` 和 `r12-outcome-case-registry-current-001`。它把 R11 HPS public-use proxy holdout 的 6 个 cases 固定拆分为 train / validation / holdout，并明确 validation / holdout outcome 不允许进入训练。该 artifact 只证明 outcome-supervised learning material 已准备好，仍保持 `field_outcome_validated=false`、`runtime_default_allowed=false`。

R12 L1 causal interaction operator 已实现为 `experiments/r12_causal_interaction_operator.py`、`tests/test_r12_causal_interaction_operator.py` 和 `r12-causal-interaction-operator-current-001`。它定义 mechanism weights、segment sensitivities、interaction edge weights、uncertainty parameters、prior shrinkage rules 和 update bounds，但不执行 outcome-supervised update。下一步必须进入 R12 L2，并且只有 validation / holdout transfer gain 成立后才能进入 Product support gate。
```

- [x] **Step 2: Run targeted tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_r12_outcome_case_registry.py tests/test_r12_causal_interaction_operator.py -q
```

Expected: PASS with `6 passed`.

- [x] **Step 3: Run full verification**

Run:

```bash
.venv/bin/python -m pytest -q
git diff --check
```

Expected:

- pytest exits 0.
- `git diff --check` exits 0.

- [x] **Step 4: Commit docs**

Run:

```bash
git add docs/CURRENT_STATE.md docs/active-spec.md docs/superpowers/specs/2026-06-26-r12-outcome-supervised-causal-interaction-operator-spec.md
git commit -m "docs: record R12 L0 L1 status"
```

## Plan Self-Review Checklist

- [x] R12 L0 case registry covered.
- [x] R12 L1 causal interaction operator covered.
- [x] outcome leakage guard covered.
- [x] no prompt/persona update guard covered.
- [x] `field_outcome_validated=false` covered.
- [x] `runtime_default_allowed=false` covered.
- [x] current artifacts and `git add -f` covered.
- [x] tests follow RED/GREEN order.
- [x] R12 L2/L3 are explicitly left for next plan.
