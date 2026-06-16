# R6 Mechanism-Driven MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 R6 机制驱动交互学习第一轮 MVP，给出 `positive_signal` / `diagnostic_only` / `stop_loss` 三选一结论，同时保留 Product 诊断护栏。

**Architecture:** 新增机制传播、结构化行为更新、机制 ablation、operator holdout/readiness 四类 Research artifact，并把 summary 接入 Product evidence cards 和 R6 evidence report。所有新 artifact 只产生 diagnostic 或 guarded decision，不允许绕过既有 claim boundary。

**Tech Stack:** Python 标准库、现有 `experiments/r6_contracts.py`、现有 R6 public proxy / foundation / evidence report 模块、pytest。

---

## 文件结构

- Create: `experiments/r6_mechanism_propagation_trace.py`
  - 负责生成 segment-level exposure graph、传播轮次、动态风险路径、与静态先验不同的 path summary。
- Create: `tests/test_r6_mechanism_propagation_trace.py`
  - 验证 trace schema、默认 3 个 public proxy 输入、动态路径、CLI 写文件。
- Create: `experiments/r6_behavioral_update_operator.py`
  - 负责从 propagation trace、public proxy outcome error 中生成结构化 candidate operator update，默认阻断 runtime。
- Create: `tests/test_r6_behavioral_update_operator.py`
  - 验证 operator update 不是 prompt patch，含机制参数、归因、guard、blocked decision。
- Create: `experiments/r6_mechanism_ablation_report.py`
  - 负责比较 static prior、no-propagation interaction、random propagation、mechanism propagation、behavioral update candidate。
- Create: `tests/test_r6_mechanism_ablation_report.py`
  - 验证 strong baseline 对比、false alarm 不隐藏、结果落在 diagnostic boundary。
- Create: `experiments/r6_operator_holdout_validation.py`
  - 负责验证 behavioral update operator 在 holdout 上是否 non-regression，输出 accepted / blocked decision。
- Create: `experiments/r6_mechanism_research_readiness_report.py`
  - 负责把 propagation、ablation、operator validation 汇总为 Research 是否继续投入的 gate report。
- Create: `tests/test_r6_operator_validation_and_readiness.py`
  - 验证 operator holdout 和 readiness 报告不会把未通过更新包装成 CCF-A 主贡献。
- Modify: `experiments/r6_product_evidence_cards.py`
  - 增加可选机制 artifact ingestion，新增 propagation path 和 update guard cards。
- Modify: `experiments/r6_evidence_report.py`
  - 增加机制 MVP summary 和 remaining gaps，保持 existing Product guard。
- Modify: `tests/test_r6_method_gate_transfer_protocol.py`
  - 将新 CLI 纳入 R6 artifact CLI smoke。
- Modify: `tests/test_r6_evidence_report.py`
  - 验证 evidence report 保留 false alarm / claim boundary，并新增机制 MVP summary。
- Modify: `docs/CURRENT_STATE.md`
  - 记录第一轮机制 MVP 结果和 Product guard 状态。

---

### Task 1: Mechanism Propagation Trace

**Files:**
- Create: `experiments/r6_mechanism_propagation_trace.py`
- Test: `tests/test_r6_mechanism_propagation_trace.py`

- [ ] **Step 1: Write the failing schema and CLI tests**

Add `tests/test_r6_mechanism_propagation_trace.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_mechanism_propagation_trace.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r6_mechanism_propagation_trace'`.

- [ ] **Step 3: Implement the propagation trace artifact**

Create `experiments/r6_mechanism_propagation_trace.py`. The module must export:

- `R6_MECHANISM_PROPAGATION_TRACE_SCHEMA_VERSION = "r6-mechanism-propagation-trace-v1"`
- `build_r6_mechanism_propagation_trace(artifact_id: str, run_id: str, public_outcome_proxies: list[dict[str, Any]] | None = None) -> dict[str, Any]`
- `write_r6_mechanism_propagation_trace(output: str | Path, **kwargs: Any) -> Path`

Implementation requirements:

- If `public_outcome_proxies` is `None`, build three proxies using `build_r6_public_outcome_proxy` for `htops_cost_pressure`, `anes_health_heldout`, and `anes_climate_heldout`.
- For each proxy, load its case template through `get_r6_case_template(proxy["target_case_id"])`.
- Build an `exposure_graph` with:
  - `nodes`: one node per prior segment, carrying `segment_id`, `weight`, `trust`, `sensitivity`, `static_reject_prior`.
  - `edges`: deterministic directed edges from high sensitivity / low trust segments to medium segments and from official high trust segments to low trust segments.
- Build `propagation_rounds` with exactly 3 rounds:
  - round 1: official exposure.
  - round 2: peer or community amplification.
  - round 3: memory accumulation and risk activation.
- Build two `dynamic_paths` per case:
  - `peer_amplified_risk_diffusion`
  - `memory_threshold_activation`
- Set every dynamic path field `static_prior_can_express_path` to `False`.
- Set status to `mechanism_propagation_trace_ready`.
- Add `risk_flags`: `mechanism_trace_not_field_validation`, `dynamic_path_requires_holdout_validation`.
- Add `blocking_gaps`: `needs_mechanism_ablation_validation`, `needs_operator_holdout_validation`, `needs_field_outcome_validation`.
- Add CLI with `--artifact-id`, `--run-id`, `--output`.

- [ ] **Step 4: Run the trace tests to verify pass**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_mechanism_propagation_trace.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit Task 1**

Run:

```bash
git add experiments/r6_mechanism_propagation_trace.py tests/test_r6_mechanism_propagation_trace.py
git commit -m "feat: add R6 mechanism propagation trace"
```

---

### Task 2: Behavioral Update Operator

**Files:**
- Create: `experiments/r6_behavioral_update_operator.py`
- Test: `tests/test_r6_behavioral_update_operator.py`

- [ ] **Step 1: Write the failing operator tests**

Add `tests/test_r6_behavioral_update_operator.py`:

```python
import json
import subprocess
import sys

from experiments.r6_behavioral_update_operator import (
    build_r6_behavioral_update_operator,
)


def test_r6_behavioral_update_operator_generates_structured_blocked_candidate():
    report = build_r6_behavioral_update_operator(
        artifact_id="r6-behavioral-update-operator-test",
        run_id="r6-behavioral-update-operator-run",
    )

    assert report["schema_version"] == "r6-behavioral-update-operator-v1"
    assert report["status"] == "behavioral_update_candidate_blocked_pending_holdout"
    assert report["operator_summary"] == {
        "candidate_update_count": 2,
        "prompt_patch_update_count": 0,
        "runtime_default_allowed_count": 0,
        "structured_operator_update_count": 2,
        "field_outcome_validated": False,
    }
    assert report["acceptance_gates"] == {
        "operator_update_structured": True,
        "prompt_patch_absent": True,
        "runtime_default_allowed": False,
        "operator_holdout_validated": False,
        "product_guard_required": True,
    }
    first = report["candidate_updates"][0]
    assert first["operator_id"] == "damp-rights-rule-over-amplification"
    assert first["update_target"] == "cap_or_damping_rule"
    assert first["runtime_decision"] == "blocked_pending_operator_holdout"
    assert first["derived_from_failure_boundary"] == (
        "interaction_over_amplifies_rejection_risk"
    )
    assert first["prompt_patch_text"] == ""
    assert first["parameter_delta"] == {
        "max_reject_delta_when_static_prior_close": 0.02,
        "static_prior_close_error_threshold": 0.03,
    }
    assert "operator_update_not_runtime_default" in report["risk_flags"]
    json.dumps(report, allow_nan=False)


def test_r6_behavioral_update_operator_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-behavioral-update-operator.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_behavioral_update_operator.py",
            "--artifact-id",
            "r6-behavioral-update-operator-cli",
            "--run-id",
            "r6-behavioral-update-operator-run",
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
    assert report["schema_version"] == "r6-behavioral-update-operator-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-behavioral-update-operator-cli",
        "candidate_update_count": 2,
        "output": str(output),
        "status": "behavioral_update_candidate_blocked_pending_holdout",
    }
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_behavioral_update_operator.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r6_behavioral_update_operator'`.

- [ ] **Step 3: Implement the behavioral update operator**

Create `experiments/r6_behavioral_update_operator.py`. The module must export:

- `R6_BEHAVIORAL_UPDATE_OPERATOR_SCHEMA_VERSION = "r6-behavioral-update-operator-v1"`
- `build_r6_behavioral_update_operator(artifact_id: str, run_id: str, propagation_trace: dict[str, Any] | None = None) -> dict[str, Any]`
- `write_r6_behavioral_update_operator(output: str | Path, **kwargs: Any) -> Path`

Implementation requirements:

- If `propagation_trace` is `None`, call `build_r6_mechanism_propagation_trace`.
- Emit two deterministic candidate updates:
  - `damp-rights-rule-over-amplification`, target `cap_or_damping_rule`, failure boundary `interaction_over_amplifies_rejection_risk`.
  - `boost-service-access-memory-activation`, target `activation_threshold`, failure boundary `static_prior_miss_under_interaction_diffusion`.
- Every candidate update must include:
  - `operator_id`
  - `update_target`
  - `parameter_delta`
  - `affected_segments`
  - `source_dynamic_paths`
  - `derived_from_failure_boundary`
  - `expected_repair`
  - `new_false_alarm_risk`
  - `runtime_decision`
  - `prompt_patch_text` set to empty string.
- Set `runtime_default_allowed` to `False`.
- Set `blocking_gaps`: `needs_operator_holdout_validation`, `needs_field_outcome_validation`.
- Add CLI with JSON stdout fields shown in the test.

- [ ] **Step 4: Run the operator tests to verify pass**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_behavioral_update_operator.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit Task 2**

Run:

```bash
git add experiments/r6_behavioral_update_operator.py tests/test_r6_behavioral_update_operator.py
git commit -m "feat: add R6 behavioral update operator"
```

---

### Task 3: Mechanism Ablation Report

**Files:**
- Create: `experiments/r6_mechanism_ablation_report.py`
- Test: `tests/test_r6_mechanism_ablation_report.py`

- [ ] **Step 1: Write the failing ablation tests**

Add `tests/test_r6_mechanism_ablation_report.py`:

```python
import json
import subprocess
import sys

from experiments.r6_mechanism_ablation_report import (
    build_r6_mechanism_ablation_report,
)


def test_r6_mechanism_ablation_report_keeps_static_prior_and_false_alarm_visible():
    report = build_r6_mechanism_ablation_report(
        artifact_id="r6-mechanism-ablation-report-test",
        run_id="r6-mechanism-ablation-report-run",
    )

    assert report["schema_version"] == "r6-mechanism-ablation-report-v1"
    assert report["status"] == "mechanism_ablation_diagnostic_only"
    assert report["method_summary"] == {
        "case_count": 3,
        "method_count": 5,
        "mechanism_positive_case_count": 1,
        "mechanism_regression_case_count": 2,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_gates"] == {
        "mechanism_trace_present": True,
        "dynamic_path_distinct_from_static_prior": True,
        "mechanism_ablation_positive": False,
        "false_alarm_not_hidden": True,
        "product_guard_preserved": True,
    }
    methods = {result["method"] for result in report["case_method_results"]}
    assert {
        "static_prior",
        "no_propagation_interaction",
        "random_propagation",
        "mechanism_propagation",
        "behavioral_update_candidate",
    } <= methods
    by_case_method = {
        (result["source_key"], result["method"]): result
        for result in report["case_method_results"]
    }
    assert by_case_method[
        ("htops_cost_pressure", "mechanism_propagation")
    ]["beats_static_prior"] is True
    assert by_case_method[
        ("anes_health_heldout", "mechanism_propagation")
    ]["beats_static_prior"] is False
    assert "mechanism_ablation_not_ccf_a_ready" in report["risk_flags"]
    assert "needs_operator_holdout_validation" in report["blocking_gaps"]
    json.dumps(report, allow_nan=False)


def test_r6_mechanism_ablation_report_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-mechanism-ablation-report.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_mechanism_ablation_report.py",
            "--artifact-id",
            "r6-mechanism-ablation-report-cli",
            "--run-id",
            "r6-mechanism-ablation-report-run",
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
    assert report["schema_version"] == "r6-mechanism-ablation-report-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-mechanism-ablation-report-cli",
        "mechanism_positive_case_count": 1,
        "output": str(output),
        "status": "mechanism_ablation_diagnostic_only",
    }
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_mechanism_ablation_report.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r6_mechanism_ablation_report'`.

- [ ] **Step 3: Implement the mechanism ablation report**

Create `experiments/r6_mechanism_ablation_report.py`. The module must export:

- `R6_MECHANISM_ABLATION_REPORT_SCHEMA_VERSION = "r6-mechanism-ablation-report-v1"`
- `build_r6_mechanism_ablation_report(artifact_id: str, run_id: str, propagation_trace: dict[str, Any] | None = None, behavioral_update_operator: dict[str, Any] | None = None) -> dict[str, Any]`
- `write_r6_mechanism_ablation_report(output: str | Path, **kwargs: Any) -> Path`

Implementation requirements:

- Use the three default public proxies through propagation trace.
- For each case produce five methods:
  - `static_prior`
  - `no_propagation_interaction`
  - `random_propagation`
  - `mechanism_propagation`
  - `behavioral_update_candidate`
- Use observed reject proxy from each public proxy.
- Preserve current evidence boundary:
  - HTOPS mechanism propagation beats static prior.
  - ANES health and ANES climate mechanism propagation do not beat static prior.
  - `behavioral_update_candidate` remains `blocked_pending_operator_holdout`.
- Set `status` to `mechanism_ablation_diagnostic_only`.
- Set `mechanism_ablation_positive` to `False` because positive signal is not generalized.
- Add `risk_flags`: `mechanism_ablation_not_ccf_a_ready`, `false_alarm_visible`, `runtime_default_blocked`.
- Add CLI with JSON stdout fields shown in the test.

- [ ] **Step 4: Run the ablation tests to verify pass**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_mechanism_ablation_report.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit Task 3**

Run:

```bash
git add experiments/r6_mechanism_ablation_report.py tests/test_r6_mechanism_ablation_report.py
git commit -m "feat: add R6 mechanism ablation report"
```

---

### Task 4: Operator Holdout Validation And Mechanism Readiness

**Files:**
- Create: `experiments/r6_operator_holdout_validation.py`
- Create: `experiments/r6_mechanism_research_readiness_report.py`
- Test: `tests/test_r6_operator_validation_and_readiness.py`

- [ ] **Step 1: Write failing holdout and readiness tests**

Add `tests/test_r6_operator_validation_and_readiness.py`:

```python
import json
import subprocess
import sys

from experiments.r6_mechanism_research_readiness_report import (
    build_r6_mechanism_research_readiness_report,
)
from experiments.r6_operator_holdout_validation import (
    build_r6_operator_holdout_validation,
)


def test_r6_operator_holdout_validation_blocks_unvalidated_runtime_update():
    report = build_r6_operator_holdout_validation(
        artifact_id="r6-operator-holdout-validation-test",
        run_id="r6-operator-holdout-validation-run",
    )

    assert report["schema_version"] == "r6-operator-holdout-validation-v1"
    assert report["status"] == "operator_holdout_validation_failed_current_public_proxies"
    assert report["validation_summary"] == {
        "candidate_update_count": 2,
        "holdout_trial_count": 4,
        "passed_trial_count": 0,
        "non_regression_trial_count": 2,
        "failed_trial_count": 2,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_gates"] == {
        "operator_update_structured": True,
        "operator_holdout_non_regression": False,
        "runtime_default_allowed": False,
        "field_outcome_validated": False,
        "product_guard_required": True,
    }
    assert "needs_operator_holdout_validation" in report["blocking_gaps"]
    assert "operator_update_blocked" in report["risk_flags"]
    json.dumps(report, allow_nan=False)


def test_r6_mechanism_research_readiness_report_returns_diagnostic_only():
    report = build_r6_mechanism_research_readiness_report(
        artifact_id="r6-mechanism-research-readiness-test",
        run_id="r6-mechanism-research-readiness-run",
    )

    assert report["schema_version"] == "r6-mechanism-research-readiness-report-v1"
    assert report["status"] == "mechanism_research_diagnostic_only"
    assert report["decision"] == {
        "mechanism_mvp_result": "diagnostic_only",
        "continue_research_with_constraints": True,
        "ccf_a_main_contribution_ready": False,
        "runtime_default_allowed": False,
    }
    assert report["readiness_gates"]["mechanism_trace_present"] is True
    assert report["readiness_gates"]["dynamic_path_distinct_from_static_prior"] is True
    assert report["readiness_gates"]["operator_holdout_non_regression"] is False
    assert report["readiness_gates"]["product_guard_preserved"] is True
    assert "needs_operator_holdout_validation" in report["blocking_gaps"]
    json.dumps(report, allow_nan=False)


def test_r6_mechanism_readiness_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-mechanism-research-readiness-report.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_mechanism_research_readiness_report.py",
            "--artifact-id",
            "r6-mechanism-research-readiness-cli",
            "--run-id",
            "r6-mechanism-research-readiness-run",
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
    assert report["schema_version"] == "r6-mechanism-research-readiness-report-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-mechanism-research-readiness-cli",
        "mechanism_mvp_result": "diagnostic_only",
        "output": str(output),
        "status": "mechanism_research_diagnostic_only",
    }
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_operator_validation_and_readiness.py -q
```

Expected: FAIL with `ModuleNotFoundError` for the new operator validation or readiness module.

- [ ] **Step 3: Implement operator holdout validation**

Create `experiments/r6_operator_holdout_validation.py`. The module must export:

- `R6_OPERATOR_HOLDOUT_VALIDATION_SCHEMA_VERSION = "r6-operator-holdout-validation-v1"`
- `build_r6_operator_holdout_validation(artifact_id: str, run_id: str, behavioral_update_operator: dict[str, Any] | None = None, mechanism_ablation_report: dict[str, Any] | None = None) -> dict[str, Any]`
- `write_r6_operator_holdout_validation(output: str | Path, **kwargs: Any) -> Path`

Implementation requirements:

- If inputs are absent, build `behavioral_update_operator` and `mechanism_ablation_report`.
- Build two holdout trials per candidate update:
  - one same-family trial using ANES health / climate as current public proxy holdout.
  - one out-of-family non-regression trial using HTOPS.
- Current MVP must block runtime default:
  - `passed_trial_count=0`
  - `non_regression_trial_count=2`
  - `failed_trial_count=2`
  - `runtime_default_allowed=False`
- Preserve all source artifact ids in `source_refs`.
- Add CLI with `--artifact-id`, `--run-id`, `--output`; stdout must include `artifact_id`, `output`, and `status`.

- [ ] **Step 4: Implement mechanism research readiness report**

Create `experiments/r6_mechanism_research_readiness_report.py`. The module must export:

- `R6_MECHANISM_RESEARCH_READINESS_REPORT_SCHEMA_VERSION = "r6-mechanism-research-readiness-report-v1"`
- `build_r6_mechanism_research_readiness_report(artifact_id: str, run_id: str, propagation_trace: dict[str, Any] | None = None, behavioral_update_operator: dict[str, Any] | None = None, mechanism_ablation_report: dict[str, Any] | None = None, operator_holdout_validation: dict[str, Any] | None = None) -> dict[str, Any]`
- `write_r6_mechanism_research_readiness_report(output: str | Path, **kwargs: Any) -> Path`

Implementation requirements:

- Set decision to `diagnostic_only` when trace exists but operator holdout fails.
- Set `continue_research_with_constraints=True`.
- Set `ccf_a_main_contribution_ready=False`.
- Set `runtime_default_allowed=False`.
- Include readiness gates listed in the test.
- Include blocking gaps from ablation and operator holdout reports.
- Add CLI with JSON stdout fields shown in the test.

- [ ] **Step 5: Run validation and readiness tests to verify pass**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_operator_validation_and_readiness.py -q
```

Expected: `3 passed`.

- [ ] **Step 6: Commit Task 4**

Run:

```bash
git add experiments/r6_operator_holdout_validation.py experiments/r6_mechanism_research_readiness_report.py tests/test_r6_operator_validation_and_readiness.py
git commit -m "feat: add R6 operator validation readiness"
```

---

### Task 5: Product Guard Integration And Current Artifacts

**Files:**
- Modify: `experiments/r6_product_evidence_cards.py`
- Modify: `experiments/r6_evidence_report.py`
- Modify: `tests/test_r6_method_gate_transfer_protocol.py`
- Modify: `tests/test_r6_evidence_report.py`
- Modify: `docs/CURRENT_STATE.md`
- Create result JSON files under:
  - `experiments/results/r6_mechanism_propagation_trace/`
  - `experiments/results/r6_behavioral_update_operator/`
  - `experiments/results/r6_mechanism_ablation_report/`
  - `experiments/results/r6_operator_holdout_validation/`
  - `experiments/results/r6_mechanism_research_readiness_report/`
  - `experiments/results/r6_evidence_report/`
  - `experiments/results/r6_product_evidence_cards/`

- [ ] **Step 1: Write failing Product and evidence report tests**

Patch `tests/test_r6_evidence_report.py` in `test_r6_evidence_report_answers_continue_or_stoploss_boundary` with assertions:

```python
    assert report["mechanism_research_readiness_summary"] == {
        "artifact_id": "r6-evidence-report-test-mechanism-research-readiness-report",
        "status": "mechanism_research_diagnostic_only",
        "mechanism_mvp_result": "diagnostic_only",
        "ccf_a_main_contribution_ready": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_gates"][
        "mechanism_driven_mvp_summary_present"
    ] is True
    assert report["acceptance_gates"]["product_guard_preserved"] is True
    assert "needs_operator_holdout_validation" in report["remaining_gaps"]
```

Patch product card expectations to verify the new cards:

```python
    card_ids = {card["card_id"] for card in report["product_evidence_cards"]["cards"]}
    assert "mechanism-propagation-path" in card_ids
    assert "behavioral-update-guard" in card_ids
```

If the current evidence report test does not expose `product_evidence_cards` directly, add the card assertions in `tests/test_r6_method_gate_transfer_protocol.py` where `build_r6_product_evidence_cards` is already exercised.

- [ ] **Step 2: Run focused tests to verify failure**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_r6_evidence_report.py::test_r6_evidence_report_answers_continue_or_stoploss_boundary \
  tests/test_r6_method_gate_transfer_protocol.py::test_r6_new_method_gate_clis_write_artifacts \
  -q
```

Expected: FAIL because evidence report has no `mechanism_research_readiness_summary`, Product cards lack two new card ids, and CLI list lacks new scripts.

- [ ] **Step 3: Modify `r6_product_evidence_cards.py`**

Implementation requirements:

- Add optional parameter:

```python
mechanism_research_readiness_report: dict[str, Any] | None = None
```

- If present, append two cards:
  - `mechanism-propagation-path`
    - `claim_status`: `diagnostic_trace_ready`
    - allowed claim: 系统能展示风险传播路径
    - blocked claim: 传播路径已经 field validated
  - `behavioral-update-guard`
    - `claim_status`: `blocked_update_guarded`
    - allowed claim: outcome feedback 可以生成结构化候选更新
    - blocked claim: 候选更新已可自动上线
- Keep `static_narrative_fallback_allowed=False`.
- Keep `accuracy_claim_blocked` in `risk_flags`.

- [ ] **Step 4: Modify `r6_evidence_report.py`**

Implementation requirements:

- Import `build_r6_mechanism_research_readiness_report`.
- Build the readiness report with artifact id:

```python
f"{artifact_id}-mechanism-research-readiness-report"
```

- Pass readiness report to `build_r6_product_evidence_cards`.
- Add:

```python
"mechanism_research_readiness_summary": {
    "artifact_id": mechanism_research_readiness["artifact_id"],
    "status": mechanism_research_readiness["status"],
    "mechanism_mvp_result": mechanism_research_readiness["decision"]["mechanism_mvp_result"],
    "ccf_a_main_contribution_ready": mechanism_research_readiness["decision"]["ccf_a_main_contribution_ready"],
    "runtime_default_allowed": mechanism_research_readiness["decision"]["runtime_default_allowed"],
}
```

- Add acceptance gates:
  - `mechanism_driven_mvp_summary_present=True`
  - `product_guard_preserved=True`
- Extend remaining gaps with mechanism readiness blocking gaps.

- [ ] **Step 5: Add new CLIs to method gate CLI smoke**

Patch the CLI list in `tests/test_r6_method_gate_transfer_protocol.py::test_r6_new_method_gate_clis_write_artifacts` with:

```python
(
    "experiments/r6_mechanism_propagation_trace.py",
    "r6-mechanism-propagation-trace-cli",
    "r6-mechanism-propagation-trace-v1",
),
(
    "experiments/r6_behavioral_update_operator.py",
    "r6-behavioral-update-operator-cli",
    "r6-behavioral-update-operator-v1",
),
(
    "experiments/r6_mechanism_ablation_report.py",
    "r6-mechanism-ablation-report-cli",
    "r6-mechanism-ablation-report-v1",
),
(
    "experiments/r6_operator_holdout_validation.py",
    "r6-operator-holdout-validation-cli",
    "r6-operator-holdout-validation-v1",
),
(
    "experiments/r6_mechanism_research_readiness_report.py",
    "r6-mechanism-research-readiness-cli",
    "r6-mechanism-research-readiness-report-v1",
),
```

- [ ] **Step 6: Run focused integration tests**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_r6_evidence_report.py::test_r6_evidence_report_answers_continue_or_stoploss_boundary \
  tests/test_r6_method_gate_transfer_protocol.py::test_r6_new_method_gate_clis_write_artifacts \
  -q
```

Expected: PASS.

- [ ] **Step 7: Generate current artifacts**

Run:

```bash
mkdir -p \
  experiments/results/r6_mechanism_propagation_trace \
  experiments/results/r6_behavioral_update_operator \
  experiments/results/r6_mechanism_ablation_report \
  experiments/results/r6_operator_holdout_validation \
  experiments/results/r6_mechanism_research_readiness_report \
  experiments/results/r6_product_evidence_cards \
  experiments/results/r6_evidence_report

.venv/bin/python experiments/r6_mechanism_propagation_trace.py \
  --artifact-id r6-mechanism-propagation-trace-current-001 \
  --run-id r6-mechanism-propagation-trace-current-001 \
  --output experiments/results/r6_mechanism_propagation_trace/r6-mechanism-propagation-trace-current-001.json

.venv/bin/python experiments/r6_behavioral_update_operator.py \
  --artifact-id r6-behavioral-update-operator-current-001 \
  --run-id r6-behavioral-update-operator-current-001 \
  --output experiments/results/r6_behavioral_update_operator/r6-behavioral-update-operator-current-001.json

.venv/bin/python experiments/r6_mechanism_ablation_report.py \
  --artifact-id r6-mechanism-ablation-report-current-001 \
  --run-id r6-mechanism-ablation-report-current-001 \
  --output experiments/results/r6_mechanism_ablation_report/r6-mechanism-ablation-report-current-001.json

.venv/bin/python experiments/r6_operator_holdout_validation.py \
  --artifact-id r6-operator-holdout-validation-current-001 \
  --run-id r6-operator-holdout-validation-current-001 \
  --output experiments/results/r6_operator_holdout_validation/r6-operator-holdout-validation-current-001.json

.venv/bin/python experiments/r6_mechanism_research_readiness_report.py \
  --artifact-id r6-mechanism-research-readiness-report-current-001 \
  --run-id r6-mechanism-research-readiness-report-current-001 \
  --output experiments/results/r6_mechanism_research_readiness_report/r6-mechanism-research-readiness-report-current-001.json

.venv/bin/python experiments/r6_product_evidence_cards.py \
  --artifact-id r6-product-evidence-cards-current-002 \
  --run-id r6-product-evidence-cards-current-002 \
  --output experiments/results/r6_product_evidence_cards/r6-product-evidence-cards-current-002.json

.venv/bin/python experiments/r6_evidence_report.py \
  --artifact-id r6-evidence-report-current-013 \
  --run-id r6-evidence-report-current-013 \
  --output experiments/results/r6_evidence_report/r6-evidence-report-current-013.json
```

Expected stdout statuses:

- `mechanism_propagation_trace_ready`
- `behavioral_update_candidate_blocked_pending_holdout`
- `mechanism_ablation_diagnostic_only`
- `operator_holdout_validation_failed_current_public_proxies`
- `mechanism_research_diagnostic_only`
- `product_evidence_cards_ready`
- `public_proxy_evidence_ready`

- [ ] **Step 8: Update docs**

Patch `docs/CURRENT_STATE.md`:

- Add new artifact file paths under R6 active artifacts.
- Add conclusion:

```markdown
40. R6 mechanism-driven MVP 第一轮已实现，当前结论是 `mechanism_research_diagnostic_only`：机制传播 trace 能展示区别于静态先验的动态路径，但 mechanism ablation 仍是 1 个 positive、2 个 regression，behavioral update operator 被 holdout gate 阻断，不能作为 CCF-A 主贡献或 runtime default。
41. Product guard 已保留并扩展：Product evidence cards 能展示 mechanism propagation path 和 behavioral update guard，但 blocked claims 继续禁止 field validation、accuracy superiority、automatic runtime update。
```

- [ ] **Step 9: Run verification**

Run:

```bash
.venv/bin/python -m py_compile \
  experiments/r6_mechanism_propagation_trace.py \
  experiments/r6_behavioral_update_operator.py \
  experiments/r6_mechanism_ablation_report.py \
  experiments/r6_operator_holdout_validation.py \
  experiments/r6_mechanism_research_readiness_report.py \
  experiments/r6_product_evidence_cards.py \
  experiments/r6_evidence_report.py

.venv/bin/python -m pytest tests/test_r6_*.py -q
.venv/bin/python -m pytest -q
git diff --check
```

Expected:

- R6 tests pass.
- Full tests pass.
- `git diff --check` has no output.

- [ ] **Step 10: Commit Task 5**

Run:

```bash
git add \
  experiments/r6_product_evidence_cards.py \
  experiments/r6_evidence_report.py \
  tests/test_r6_evidence_report.py \
  tests/test_r6_method_gate_transfer_protocol.py \
  docs/CURRENT_STATE.md

git add -f \
  experiments/results/r6_mechanism_propagation_trace/r6-mechanism-propagation-trace-current-001.json \
  experiments/results/r6_behavioral_update_operator/r6-behavioral-update-operator-current-001.json \
  experiments/results/r6_mechanism_ablation_report/r6-mechanism-ablation-report-current-001.json \
  experiments/results/r6_operator_holdout_validation/r6-operator-holdout-validation-current-001.json \
  experiments/results/r6_mechanism_research_readiness_report/r6-mechanism-research-readiness-report-current-001.json \
  experiments/results/r6_product_evidence_cards/r6-product-evidence-cards-current-002.json \
  experiments/results/r6_evidence_report/r6-evidence-report-current-013.json

git commit -m "feat: integrate R6 mechanism MVP evidence guard"
```

---

## Plan Self-Review

Spec coverage:

- 机制传播 trace: Task 1。
- Behavioral update operator: Task 2。
- 机制 ablation 和 strong baseline: Task 3。
- Operator holdout validation and readiness: Task 4。
- Product guard 保留和 evidence cards ingestion: Task 5。
- clear positive / diagnostic / stop_loss conclusion: Task 4 readiness decision and Task 5 evidence report summary。

Boundary checks:

- 当前 scoring candidate 保留为 diagnostic baseline，没有继续优化。
- Product guard 没有降级，新增 cards 仍有 blocked claims。
- 所有 runtime default 决策默认 blocked。
- Field outcome 仍为 false，没有把 public proxy 写成 field validation。

Implementation order:

1. Task 1 creates trace substrate.
2. Task 2 creates update candidate substrate.
3. Task 3 tests method value against baselines.
4. Task 4 decides Research readiness.
5. Task 5 connects Product and current artifacts.
