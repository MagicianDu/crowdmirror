# R11 External Holdout Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 R11 可学习交互风险发现器补一个外部 public-use proxy holdout artifact，判断 controlled lab 正向信号是否能进入更严格的下一阶段。

**Architecture:** 新增一个纯函数 artifact builder：读取 `r11_interaction_risk_discoverer` 和 `r10_hps_policy_reaction_ingestion`，把 HPS `PRICECONCERN` 作为外部信号、`PRICESTRESS` 作为独立 proxy outcome，按低敏感 segment 计算 trend、interval、risk ranking、false alarm、static prior miss recovery 和 abnormal segment recall。输出必须继续保留 `field_outcome_validated=false` 和 `runtime_default_allowed=false`。

**Tech Stack:** Python 标准库、pytest、现有 `experiments.r6_contracts` artifact helper。

---

### Task 1: R11 L1 测试合同

**Files:**
- Create: `tests/test_r11_external_holdout_validation.py`
- Create: `experiments/r11_external_holdout_validation.py`

- [x] **Step 1: Write the failing test**

```python
import json

from experiments.r11_external_holdout_validation import (
    R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION,
    build_r11_external_holdout_validation,
)
from experiments.r11_interaction_risk_discoverer import (
    build_r11_interaction_risk_discoverer,
)
from experiments.r10_hps_policy_reaction_ingestion import (
    build_r10_hps_policy_reaction_ingestion,
)
from tests.test_r10_hps_policy_reaction_ingestion import _write_hps_fixture_zip


def test_r11_external_holdout_validation_reports_proxy_holdout_without_escalation(tmp_path):
    r11 = build_r11_interaction_risk_discoverer(
        artifact_id="r11-l0-test",
        run_id="r11-l1-test",
    )
    hps = build_r10_hps_policy_reaction_ingestion(
        artifact_id="hps-ingestion-test",
        run_id="r11-l1-test",
        input_zip_path=_write_hps_fixture_zip(tmp_path),
    )

    report = build_r11_external_holdout_validation(
        artifact_id="r11-external-holdout-test",
        run_id="r11-l1-test",
        r11_interaction_risk_discoverer=r11,
        hps_ingestion=hps,
    )

    assert report["schema_version"] == R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION
    assert report["validation_contract"]["source_backed_public_use_proxy"] is True
    assert report["validation_contract"]["field_outcome_validated"] is False
    assert report["validation_contract"]["runtime_default_allowed"] is False
    assert report["acceptance_gates"]["external_public_use_holdout_present"] is True
    assert report["acceptance_gates"]["product_core_method_ready"] is False
    assert "R11 supports Product core method by default" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)
```

- [x] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_r11_external_holdout_validation.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r11_external_holdout_validation'`.

- [x] **Step 3: Write minimal implementation**

Implement:

```python
def build_r11_external_holdout_validation(...):
    validate r11 schema and hps schema
    derive holdout rows from PRICECONCERN -> PRICESTRESS segment profiles
    compute method metrics
    emit guarded report with status, gates, allowed_claims, blocked_claims
```

- [x] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_r11_external_holdout_validation.py -q`

Expected: PASS.

### Task 2: Current artifact and docs

**Files:**
- Create: `experiments/results/r11_external_holdout_validation/r11-external-holdout-validation-current-001.json`
- Modify: `docs/CURRENT_STATE.md`
- Modify: `docs/active-spec.md`
- Modify: `docs/superpowers/specs/2026-06-26-r11-learnable-interaction-risk-discoverer-spec.md`

- [x] **Step 1: Generate current artifact**

Run:

```bash
.venv/bin/python experiments/r11_external_holdout_validation.py \
  --artifact-id r11-external-holdout-validation-current-001 \
  --run-id r11-l1-current \
  --r11-path experiments/results/r11_interaction_risk_discoverer/r11-interaction-risk-discoverer-current-001.json \
  --hps-ingestion-path experiments/results/r10_hps_policy_reaction_ingestion/r10-hps-policy-reaction-ingestion-current-001.json \
  --output experiments/results/r11_external_holdout_validation/r11-external-holdout-validation-current-001.json
```

Expected: JSON stdout with artifact id, output path, and guarded status.

- [x] **Step 2: Update docs**

Add R11 L1 status:

```markdown
R11 L1 已完成 external public-use proxy holdout。该结果只证明 R11 从 controlled lab 进入 source-backed proxy holdout 审计；如果通过，也不能声明 field validation 或 Product runtime default。
```

- [x] **Step 3: Verify**

Run:

```bash
.venv/bin/python -m pytest tests/test_r11_external_holdout_validation.py tests/test_r11_interaction_risk_discoverer.py -q
.venv/bin/python -m pytest -q
git diff --check
```

Expected: all tests pass and no diff-check errors.

- [x] **Step 4: Commit**

Run:

```bash
git add docs/CURRENT_STATE.md docs/active-spec.md docs/superpowers/specs/2026-06-26-r11-learnable-interaction-risk-discoverer-spec.md docs/superpowers/plans/2026-06-26-r11-external-holdout-validation.md experiments/r11_external_holdout_validation.py tests/test_r11_external_holdout_validation.py experiments/results/r11_external_holdout_validation/r11-external-holdout-validation-current-001.json -f
git commit -m "feat: add R11 external holdout validation"
```
