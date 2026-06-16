# R6 Gap Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 R6.2 gap closure 第一阶段，把理论、数据、方法、Product 四类 gap 变成可计算、可审计、可阻断的 artifact 链路。

**Architecture:** 新增 theory framework、outcome/holdout registry、behavioral update operator v2、gap closure report 四个 Research artifact，并把 gap closure summary 接入 Product evidence cards 和 R6 evidence report。所有新增输出必须保持 `ccf_a_main_contribution_ready=false`、`field_outcome_validated=false`、`runtime_default_allowed=false`，直到独立 holdout 或 field outcome 通过。

**Tech Stack:** Python 标准库、现有 `experiments/r6_contracts.py`、现有 R6 mechanism / Product / evidence report 模块、pytest。

---

## 文件结构

- Create: `experiments/r6_theory_framework.py`
  - 负责输出形式化问题定义、风险发现价值函数、误差归因、guard constraints。
- Create: `tests/test_r6_gap_closure_theory.py`
  - 验证 theory artifact schema、gate、blocked claims、CLI。
- Create: `experiments/r6_outcome_holdout_registry.py`
  - 负责登记当前 public proxy、独立性判断、缺失 holdout / field outcome 槽位。
- Create: `tests/test_r6_outcome_holdout_registry.py`
  - 验证 registry 不把 same-source / out-of-condition proxy 当作 independent holdout。
- Create: `experiments/r6_behavioral_update_operator_v2.py`
  - 负责生成含 error attribution 和 transfer preconditions 的结构化 operator v2 candidate。
- Create: `tests/test_r6_behavioral_update_operator_v2.py`
  - 验证 v2 candidate 不是 prompt patch，且 runtime default 继续阻断。
- Create: `experiments/r6_gap_closure_report.py`
  - 负责汇总四类 gap 状态，输出 gap closure 总判定。
- Create: `tests/test_r6_gap_closure_report.py`
  - 验证 gap 状态、remaining gaps、claim boundary、CLI。
- Modify: `experiments/r6_product_evidence_cards.py`
  - 增加可选 `gap_closure_report` ingestion，新增 gap closure card。
- Modify: `experiments/r6_evidence_report.py`
  - 增加 gap closure summary 和 gates，保留现有 Product guard。
- Modify: `tests/test_r6_method_gate_transfer_protocol.py`
  - 将新 CLI 纳入 R6 artifact smoke。
- Modify: `tests/test_r6_evidence_report.py`
  - 验证 evidence report 暴露 gap closure summary。
- Modify: `docs/CURRENT_STATE.md`
  - 记录 R6.2 第一阶段状态。

---

### Task 1: Theory Framework Artifact

**Files:**
- Create: `experiments/r6_theory_framework.py`
- Test: `tests/test_r6_gap_closure_theory.py`

- [ ] **Step 1: Write the failing tests**

Add `tests/test_r6_gap_closure_theory.py`:

```python
import json
import subprocess
import sys

from experiments.r6_theory_framework import build_r6_theory_framework


def test_r6_theory_framework_defines_problem_value_and_guards():
    report = build_r6_theory_framework(
        artifact_id="r6-theory-framework-test",
        run_id="r6-gap-closure-run",
    )

    assert report["schema_version"] == "r6-theory-framework-v1"
    assert report["status"] == "theory_framework_ready"
    assert report["formal_problem"]["static_prior_role"] == "simulation_foundation"
    assert report["formal_problem"]["interaction_role"] == "risk_discovery_layer"
    assert report["risk_discovery_value_function"] == {
        "formula": (
            "recovered_static_prior_miss - false_alarm_penalty "
            "- guard_violation_penalty - overfit_penalty"
        ),
        "optimization_target": "auditable_risk_discovery_not_raw_accuracy_superiority",
    }
    assert report["acceptance_gates"] == {
        "formal_problem_definition_present": True,
        "risk_discovery_value_defined": True,
        "error_attribution_defined": True,
        "runtime_default_allowed": False,
        "field_outcome_validated": False,
    }
    assert "accuracy superiority" in " ".join(report["blocked_claims"])
    assert "field validated" in " ".join(report["blocked_claims"])
    json.dumps(report, allow_nan=False)


def test_r6_theory_framework_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-theory-framework.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_theory_framework.py",
            "--artifact-id",
            "r6-theory-framework-cli",
            "--run-id",
            "r6-gap-closure-run",
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
    assert report["schema_version"] == "r6-theory-framework-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-theory-framework-cli",
        "output": str(output),
        "status": "theory_framework_ready",
    }
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_gap_closure_theory.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r6_theory_framework'`.

- [ ] **Step 3: Implement `experiments/r6_theory_framework.py`**

Create the module with:

- `R6_THEORY_FRAMEWORK_SCHEMA_VERSION = "r6-theory-framework-v1"`
- `build_r6_theory_framework(*, artifact_id: str, run_id: str) -> dict[str, Any]`
- `write_r6_theory_framework(output: str | Path, **kwargs: Any) -> Path`
- CLI args: `--artifact-id`, `--run-id`, `--output`

Implementation requirements:

- Use `non_empty_string`, `assert_strict_json`, `write_json_artifact`, and `R6_CLAIM_BOUNDARY`.
- Include `formal_problem` with `static_prior_role`, `interaction_role`, `operator_definition`, `guarded_decision_rule`.
- Include `risk_discovery_value_function` exactly as tested.
- Include `error_attribution_components`: `static_prior_miss`, `propagation_direction_error`, `over_amplification`, `under_diffusion`, `topology_mismatch`, `outcome_mapping_noise`.
- Include `acceptance_gates` exactly as tested.
- Include `blocked_claims` containing English phrases `accuracy superiority`, `field validated`, `runtime default`.
- Set `claim_boundary` to `R6_CLAIM_BOUNDARY`.

- [ ] **Step 4: Verify Task 1**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_gap_closure_theory.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit Task 1**

Run:

```bash
git add experiments/r6_theory_framework.py tests/test_r6_gap_closure_theory.py
git commit -m "feat: add R6 theory framework artifact"
```

---

### Task 2: Outcome / Holdout Registry

**Files:**
- Create: `experiments/r6_outcome_holdout_registry.py`
- Test: `tests/test_r6_outcome_holdout_registry.py`

- [ ] **Step 1: Write the failing tests**

Add `tests/test_r6_outcome_holdout_registry.py`:

```python
import json
import subprocess
import sys

from experiments.r6_outcome_holdout_registry import build_r6_outcome_holdout_registry


def test_r6_outcome_holdout_registry_marks_missing_independent_holdouts():
    registry = build_r6_outcome_holdout_registry(
        artifact_id="r6-outcome-holdout-registry-test",
        run_id="r6-gap-closure-run",
    )

    assert registry["schema_version"] == "r6-outcome-holdout-registry-v1"
    assert registry["status"] == "holdout_registry_ready_missing_required_slots"
    assert registry["registry_summary"] == {
        "registered_outcome_count": 3,
        "independent_public_proxy_count": 0,
        "field_outcome_count": 0,
        "missing_required_slot_count": 3,
        "in_condition_independent_holdout_available": False,
    }
    by_key = {entry["source_key"]: entry for entry in registry["outcome_entries"]}
    assert by_key["htops_cost_pressure"]["independence_level"] == (
        "out_of_family_non_regression_proxy"
    )
    assert by_key["anes_health_heldout"]["independence_level"] == "source_case_proxy"
    assert by_key["anes_climate_heldout"]["independence_level"] == (
        "same_source_out_of_condition_proxy"
    )
    missing = {slot["slot_id"] for slot in registry["missing_required_slots"]}
    assert missing == {
        "independent_same_family_in_condition_holdout",
        "independent_supported_signal_holdout",
        "real_field_outcome",
    }
    assert registry["acceptance_gates"]["holdout_registry_present"] is True
    assert registry["acceptance_gates"]["independent_holdout_missing_slots_visible"] is True
    assert registry["acceptance_gates"]["field_outcome_validated"] is False
    json.dumps(registry, allow_nan=False)


def test_r6_outcome_holdout_registry_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-outcome-holdout-registry.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_outcome_holdout_registry.py",
            "--artifact-id",
            "r6-outcome-holdout-registry-cli",
            "--run-id",
            "r6-gap-closure-run",
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
    assert report["schema_version"] == "r6-outcome-holdout-registry-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-outcome-holdout-registry-cli",
        "output": str(output),
        "status": "holdout_registry_ready_missing_required_slots",
    }
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_outcome_holdout_registry.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r6_outcome_holdout_registry'`.

- [ ] **Step 3: Implement `experiments/r6_outcome_holdout_registry.py`**

Create the module with:

- `R6_OUTCOME_HOLDOUT_REGISTRY_SCHEMA_VERSION = "r6-outcome-holdout-registry-v1"`
- `build_r6_outcome_holdout_registry(*, artifact_id: str, run_id: str) -> dict[str, Any]`
- `write_r6_outcome_holdout_registry(output: str | Path, **kwargs: Any) -> Path`
- CLI args: `--artifact-id`, `--run-id`, `--output`

Implementation requirements:

- Build deterministic `outcome_entries` for `htops_cost_pressure`, `anes_health_heldout`, `anes_climate_heldout`.
- Each entry includes `source_key`, `outcome_type`, `independence_level`, `case_family`, `in_condition_holdout`, `field_outcome_validated`, `accepted_for_generalization`.
- Add `missing_required_slots` with exactly the three slot ids in the test.
- Set `acceptance_gates.holdout_registry_present=true`.
- Set `acceptance_gates.independent_holdout_missing_slots_visible=true`.
- Set `acceptance_gates.field_outcome_validated=false`.
- Include `blocking_gaps`: `needs_independent_same_family_operator_holdout`, `needs_independent_supported_signal_holdout`, `needs_real_or_field_outcome_proxy`.

- [ ] **Step 4: Verify Task 2**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_outcome_holdout_registry.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit Task 2**

Run:

```bash
git add experiments/r6_outcome_holdout_registry.py tests/test_r6_outcome_holdout_registry.py
git commit -m "feat: add R6 outcome holdout registry"
```

---

### Task 3: Behavioral Update Operator v2

**Files:**
- Create: `experiments/r6_behavioral_update_operator_v2.py`
- Test: `tests/test_r6_behavioral_update_operator_v2.py`

- [ ] **Step 1: Write the failing tests**

Add `tests/test_r6_behavioral_update_operator_v2.py`:

```python
import json
import subprocess
import sys

from experiments.r6_behavioral_update_operator_v2 import (
    build_r6_behavioral_update_operator_v2,
)


def test_r6_behavioral_update_operator_v2_adds_error_attribution_and_transfer_guards():
    report = build_r6_behavioral_update_operator_v2(
        artifact_id="r6-behavioral-update-operator-v2-test",
        run_id="r6-gap-closure-run",
    )

    assert report["schema_version"] == "r6-behavioral-update-operator-v2"
    assert report["status"] == "operator_v2_structured_blocked_missing_holdout"
    assert report["operator_v2_summary"] == {
        "candidate_update_count": 3,
        "same_case_repair_count": 1,
        "transfer_candidate_count": 2,
        "runtime_default_allowed_count": 0,
        "prompt_patch_update_count": 0,
    }
    assert report["acceptance_gates"]["operator_v2_structured"] is True
    assert report["acceptance_gates"]["operator_v2_runtime_default_allowed"] is False
    assert report["acceptance_gates"]["independent_holdout_available"] is False
    candidate = report["candidate_updates"][0]
    assert candidate["operator_family"] == "over_amplification_damping"
    assert candidate["error_attribution"]["primary_component"] == "over_amplification"
    assert candidate["acceptance_status"] == "blocked_missing_independent_holdout"
    assert candidate["runtime_default_allowed"] is False
    assert candidate["prompt_patch_text"] == ""
    assert "independent_same_family_in_condition_holdout" in candidate[
        "transfer_preconditions"
    ]
    json.dumps(report, allow_nan=False)


def test_r6_behavioral_update_operator_v2_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-behavioral-update-operator-v2.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_behavioral_update_operator_v2.py",
            "--artifact-id",
            "r6-behavioral-update-operator-v2-cli",
            "--run-id",
            "r6-gap-closure-run",
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
    assert report["schema_version"] == "r6-behavioral-update-operator-v2"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-behavioral-update-operator-v2-cli",
        "output": str(output),
        "status": "operator_v2_structured_blocked_missing_holdout",
    }
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_behavioral_update_operator_v2.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r6_behavioral_update_operator_v2'`.

- [ ] **Step 3: Implement `experiments/r6_behavioral_update_operator_v2.py`**

Create the module with:

- `R6_BEHAVIORAL_UPDATE_OPERATOR_V2_SCHEMA_VERSION = "r6-behavioral-update-operator-v2"`
- `build_r6_behavioral_update_operator_v2(*, artifact_id: str, run_id: str, holdout_registry: dict[str, Any] | None = None, theory_framework: dict[str, Any] | None = None) -> dict[str, Any]`
- `write_r6_behavioral_update_operator_v2(output: str | Path, **kwargs: Any) -> Path`
- CLI args: `--artifact-id`, `--run-id`, `--output`

Implementation requirements:

- If inputs are absent, build `r6_theory_framework` and `r6_outcome_holdout_registry`.
- Generate exactly three candidates:
  - `operator_family="over_amplification_damping"`
  - `operator_family="under_diffusion_boost"`
  - `operator_family="trust_modifier_reweighting"`
- Each candidate includes `error_attribution`, `operator_family`, `target_segments`, `parameter_delta`, `transfer_preconditions`, `acceptance_status`, `runtime_default_allowed=false`, `prompt_patch_text=""`.
- Summary counts must match the test.
- Include `blocking_gaps`: `needs_independent_same_family_operator_holdout`, `needs_signal_validity_holdout_validation`, `needs_real_or_field_outcome_proxy`.

- [ ] **Step 4: Verify Task 3**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_behavioral_update_operator_v2.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit Task 3**

Run:

```bash
git add experiments/r6_behavioral_update_operator_v2.py tests/test_r6_behavioral_update_operator_v2.py
git commit -m "feat: add R6 behavioral update operator v2"
```

---

### Task 4: Gap Closure Report

**Files:**
- Create: `experiments/r6_gap_closure_report.py`
- Test: `tests/test_r6_gap_closure_report.py`

- [ ] **Step 1: Write the failing tests**

Add `tests/test_r6_gap_closure_report.py`:

```python
import json
import subprocess
import sys

from experiments.r6_gap_closure_report import build_r6_gap_closure_report


def test_r6_gap_closure_report_keeps_empirical_gaps_open():
    report = build_r6_gap_closure_report(
        artifact_id="r6-gap-closure-report-test",
        run_id="r6-gap-closure-run",
    )

    assert report["schema_version"] == "r6-gap-closure-report-v1"
    assert report["status"] == "gap_closure_artifact_ready"
    assert report["gap_statuses"] == {
        "theory_gap": "closed_by_artifact",
        "data_holdout_gap": "blocked_missing_data",
        "method_operator_gap": "partial_diagnostic",
        "product_gap": "closed_by_guarded_cards",
    }
    assert report["acceptance_gates"] == {
        "formal_problem_definition_present": True,
        "risk_discovery_value_defined": True,
        "holdout_registry_present": True,
        "independent_holdout_missing_slots_visible": True,
        "operator_v2_structured": True,
        "operator_v2_runtime_default_allowed": False,
        "gap_closure_report_present": True,
        "product_gap_cards_required": True,
        "ccf_a_main_contribution_ready": False,
        "field_outcome_validated": False,
    }
    assert "needs_independent_same_family_operator_holdout" in report["remaining_gaps"]
    assert "needs_real_or_field_outcome_proxy" in report["remaining_gaps"]
    json.dumps(report, allow_nan=False)


def test_r6_gap_closure_report_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-gap-closure-report.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_gap_closure_report.py",
            "--artifact-id",
            "r6-gap-closure-report-cli",
            "--run-id",
            "r6-gap-closure-run",
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
    assert report["schema_version"] == "r6-gap-closure-report-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-gap-closure-report-cli",
        "output": str(output),
        "status": "gap_closure_artifact_ready",
    }
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_gap_closure_report.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r6_gap_closure_report'`.

- [ ] **Step 3: Implement `experiments/r6_gap_closure_report.py`**

Create the module with:

- `R6_GAP_CLOSURE_REPORT_SCHEMA_VERSION = "r6-gap-closure-report-v1"`
- `build_r6_gap_closure_report(*, artifact_id: str, run_id: str, theory_framework: dict[str, Any] | None = None, holdout_registry: dict[str, Any] | None = None, operator_v2: dict[str, Any] | None = None) -> dict[str, Any]`
- `write_r6_gap_closure_report(output: str | Path, **kwargs: Any) -> Path`
- CLI args: `--artifact-id`, `--run-id`, `--output`

Implementation requirements:

- Build missing inputs from Task 1 to Task 3 modules.
- Set `status="gap_closure_artifact_ready"`.
- Set `gap_statuses` and `acceptance_gates` exactly as tested.
- Include `remaining_gaps` from registry and operator v2 blocking gaps, deduplicated and sorted.
- Include `source_refs` pointing to theory, registry, operator v2.
- Include `claim_boundaries` and `claim_boundary`.
- Include `blocked_claims` for CCF-A readiness, field validation, runtime default, and accuracy superiority.

- [ ] **Step 4: Verify Task 4**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_gap_closure_report.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit Task 4**

Run:

```bash
git add experiments/r6_gap_closure_report.py tests/test_r6_gap_closure_report.py
git commit -m "feat: add R6 gap closure report"
```

---

### Task 5: Product and Evidence Integration

**Files:**
- Modify: `experiments/r6_product_evidence_cards.py`
- Modify: `experiments/r6_evidence_report.py`
- Modify: `tests/test_r6_method_gate_transfer_protocol.py`
- Modify: `tests/test_r6_evidence_report.py`
- Modify: `docs/CURRENT_STATE.md`

- [ ] **Step 1: Write failing Product/evidence tests**

Extend `tests/test_r6_method_gate_transfer_protocol.py` with:

```python
from experiments.r6_gap_closure_report import build_r6_gap_closure_report


def test_r6_product_evidence_cards_ingest_gap_closure_report():
    gap_closure_report = build_r6_gap_closure_report(
        artifact_id="r6-product-cards-gap-closure-report",
        run_id="r6-gap-closure-run",
    )
    cards = build_r6_product_evidence_cards(
        artifact_id="r6-product-cards-gap-closure-test",
        run_id="r6-gap-closure-run",
        gap_closure_report=gap_closure_report,
    )

    card_ids = {card["card_id"] for card in cards["cards"]}
    assert "r6-gap-closure-status" in card_ids
    by_id = {card["card_id"]: card for card in cards["cards"]}
    gap_card = by_id["r6-gap-closure-status"]
    assert gap_card["claim_status"] == "gap_closure_artifact_ready_not_validated"
    assert "field validation 已完成" in gap_card["blocked_claims"]
    assert "runtime default 可以开启" in gap_card["blocked_claims"]
    assert cards["demo_api_contract"]["static_narrative_fallback_allowed"] is False
```

Extend `tests/test_r6_evidence_report.py` with:

```python
def test_r6_evidence_report_includes_gap_closure_summary():
    report = build_r6_evidence_report(
        artifact_id="r6-evidence-gap-closure-test",
        run_id="r6-gap-closure-run",
    )

    assert report["gap_closure_summary"] == {
        "status": "gap_closure_artifact_ready",
        "theory_gap": "closed_by_artifact",
        "data_holdout_gap": "blocked_missing_data",
        "method_operator_gap": "partial_diagnostic",
        "product_gap": "closed_by_guarded_cards",
    }
    assert report["acceptance_gates"]["gap_closure_report_present"] is True
    assert report["acceptance_gates"]["field_outcome_validated"] is False
    assert "needs_real_or_field_outcome_proxy" in report["remaining_gaps"]
```

- [ ] **Step 2: Run failing Product/evidence tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_method_gate_transfer_protocol.py::test_r6_product_evidence_cards_ingest_gap_closure_report tests/test_r6_evidence_report.py::test_r6_evidence_report_includes_gap_closure_summary -q
```

Expected: FAIL because `gap_closure_report` parameter and `gap_closure_summary` do not exist yet.

- [ ] **Step 3: Update Product cards**

Modify `build_r6_product_evidence_cards`:

- Add optional parameter `gap_closure_report: dict[str, Any] | None = None`.
- If absent, leave existing behavior unchanged except current default 7 mechanism cards remain.
- If present, append one card:
  - `card_id="r6-gap-closure-status"`
  - `title="R6.2 gap closure 状态"`
  - `claim_status="gap_closure_artifact_ready_not_validated"`
  - `allowed_claims` includes `理论、数据、方法和 Product gap 已被结构化管理`
  - `blocked_claims` includes `field validation 已完成`, `runtime default 可以开启`, `R6 已达到 CCF-A 主贡献`
  - `source_artifact_ids=[gap_closure_report["artifact_id"]]`

- [ ] **Step 4: Update evidence report**

Modify `experiments/r6_evidence_report.py`:

- Import `build_r6_gap_closure_report`.
- Build `gap_closure_report` inside `build_r6_evidence_report`.
- Add top-level `gap_closure_summary` with fields tested in Step 1.
- Add acceptance gate `gap_closure_report_present`.
- Ensure `field_outcome_validated` remains False.
- Merge gap closure remaining gaps into top-level `remaining_gaps`.
- Add source ref to the gap closure artifact.

- [ ] **Step 5: Update CLI smoke list**

Modify `tests/test_r6_method_gate_transfer_protocol.py` CLI command list:

```python
(
    "experiments/r6_theory_framework.py",
    "r6-theory-framework-cli",
    "r6-theory-framework-v1",
),
(
    "experiments/r6_outcome_holdout_registry.py",
    "r6-outcome-holdout-registry-cli",
    "r6-outcome-holdout-registry-v1",
),
(
    "experiments/r6_behavioral_update_operator_v2.py",
    "r6-behavioral-update-operator-v2-cli",
    "r6-behavioral-update-operator-v2",
),
(
    "experiments/r6_gap_closure_report.py",
    "r6-gap-closure-report-cli",
    "r6-gap-closure-report-v1",
),
```

- [ ] **Step 6: Update current state doc**

Append to `docs/CURRENT_STATE.md`:

```markdown
42. R6.2 gap closure 第一阶段计划接入 theory framework、outcome/holdout registry、behavioral update operator v2 和 gap closure report。目标是关闭定义不清和证据链不可审计 gap；独立 holdout、field outcome、runtime default 和 CCF-A 主贡献仍保持 blocked。
```

- [ ] **Step 7: Verify Task 5**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_method_gate_transfer_protocol.py::test_r6_product_evidence_cards_ingest_gap_closure_report tests/test_r6_evidence_report.py::test_r6_evidence_report_includes_gap_closure_summary -q
.venv/bin/python -m pytest tests/test_r6_*.py -q
```

Expected:

- First command: `2 passed`
- Second command: all R6 tests pass

- [ ] **Step 8: Commit Task 5**

Run:

```bash
git add experiments/r6_product_evidence_cards.py experiments/r6_evidence_report.py tests/test_r6_method_gate_transfer_protocol.py tests/test_r6_evidence_report.py docs/CURRENT_STATE.md
git commit -m "feat: integrate R6 gap closure evidence"
```

---

### Task 6: Current Artifacts and Final Verification

**Files:**
- Create: `experiments/results/r6_theory_framework/r6-theory-framework-current-001.json`
- Create: `experiments/results/r6_outcome_holdout_registry/r6-outcome-holdout-registry-current-001.json`
- Create: `experiments/results/r6_behavioral_update_operator_v2/r6-behavioral-update-operator-v2-current-001.json`
- Create: `experiments/results/r6_gap_closure_report/r6-gap-closure-report-current-001.json`
- Create or update: `experiments/results/r6_product_evidence_cards/r6-product-evidence-cards-current-003.json`
- Create or update: `experiments/results/r6_evidence_report/r6-evidence-report-current-014.json`

- [ ] **Step 1: Generate current artifacts**

Run:

```bash
mkdir -p experiments/results/r6_theory_framework experiments/results/r6_outcome_holdout_registry experiments/results/r6_behavioral_update_operator_v2 experiments/results/r6_gap_closure_report
.venv/bin/python experiments/r6_theory_framework.py --artifact-id r6-theory-framework-current-001 --run-id r6-gap-closure-current-001 --output experiments/results/r6_theory_framework/r6-theory-framework-current-001.json
.venv/bin/python experiments/r6_outcome_holdout_registry.py --artifact-id r6-outcome-holdout-registry-current-001 --run-id r6-gap-closure-current-001 --output experiments/results/r6_outcome_holdout_registry/r6-outcome-holdout-registry-current-001.json
.venv/bin/python experiments/r6_behavioral_update_operator_v2.py --artifact-id r6-behavioral-update-operator-v2-current-001 --run-id r6-gap-closure-current-001 --output experiments/results/r6_behavioral_update_operator_v2/r6-behavioral-update-operator-v2-current-001.json
.venv/bin/python experiments/r6_gap_closure_report.py --artifact-id r6-gap-closure-report-current-001 --run-id r6-gap-closure-current-001 --output experiments/results/r6_gap_closure_report/r6-gap-closure-report-current-001.json
.venv/bin/python experiments/r6_product_evidence_cards.py --artifact-id r6-product-evidence-cards-current-003 --run-id r6-gap-closure-current-001 --output experiments/results/r6_product_evidence_cards/r6-product-evidence-cards-current-003.json
.venv/bin/python experiments/r6_evidence_report.py --artifact-id r6-evidence-report-current-014 --run-id r6-gap-closure-current-001 --output experiments/results/r6_evidence_report/r6-evidence-report-current-014.json
```

Expected: each command prints JSON containing `output` and `status`.

- [ ] **Step 2: Verify artifact summary**

Run:

```bash
jq '{status, acceptance_gates, remaining_gaps}' experiments/results/r6_gap_closure_report/r6-gap-closure-report-current-001.json
jq '{card_count, card_ids:[.cards[].card_id], fallback:.demo_api_contract.static_narrative_fallback_allowed}' experiments/results/r6_product_evidence_cards/r6-product-evidence-cards-current-003.json
jq '{status, gap_closure_summary, acceptance_gates, remaining_gaps}' experiments/results/r6_evidence_report/r6-evidence-report-current-014.json
```

Expected:

- gap closure report status is `gap_closure_artifact_ready`
- product cards include `r6-gap-closure-status`
- evidence report includes `gap_closure_summary`
- `field_outcome_validated=false`
- `ccf_a_main_contribution_ready=false`

- [ ] **Step 3: Run final verification**

Run:

```bash
.venv/bin/python -m py_compile experiments/r6_theory_framework.py experiments/r6_outcome_holdout_registry.py experiments/r6_behavioral_update_operator_v2.py experiments/r6_gap_closure_report.py experiments/r6_product_evidence_cards.py experiments/r6_evidence_report.py
.venv/bin/python -m pytest tests/test_r6_*.py -q
.venv/bin/python -m pytest -q
git diff --check
```

Expected:

- py_compile exits 0
- R6 tests pass
- full pytest passes
- `git diff --check` exits 0

- [ ] **Step 4: Commit Task 6**

Run:

```bash
git add experiments/results/r6_theory_framework/r6-theory-framework-current-001.json experiments/results/r6_outcome_holdout_registry/r6-outcome-holdout-registry-current-001.json experiments/results/r6_behavioral_update_operator_v2/r6-behavioral-update-operator-v2-current-001.json experiments/results/r6_gap_closure_report/r6-gap-closure-report-current-001.json experiments/results/r6_product_evidence_cards/r6-product-evidence-cards-current-003.json experiments/results/r6_evidence_report/r6-evidence-report-current-014.json
git commit -m "data: add R6 gap closure current artifacts"
```

---

## Self-Review

- Spec coverage: Tasks 1-4 cover theory, holdout/data, method operator, and gap closure report. Task 5 covers Product/evidence integration. Task 6 covers artifacts and verification.
- Placeholder scan: no open placeholders are required for implementation.
- Type consistency: all new builders use `artifact_id`, `run_id`, `output`, schema version, `status`, `acceptance_gates`, `source_refs`, `claim_boundary`, and `blocking_gaps` patterns already used by R6 modules.
- Boundary check: this plan does not claim field outcome validation, CCF-A readiness, or runtime default enablement.
