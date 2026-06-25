# R11 Outcome Feedback Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 R11 shadow trial 补一个 outcome feedback update artifact，自动生成机制权重、群体敏感度、传播边权和区间不确定性的受约束更新候选。

**Architecture:** 新增 `experiments/r11_outcome_feedback_update.py`。该模块消费 `r11_product_shadow_trial`、`r11_external_holdout_validation` 和一个 observed outcome feedback packet，计算 case-level residual、生成四类 update candidates，并输出 accepted / rejected / diagnostic_only ledger。当前 current artifact 使用 public proxy replay，不宣称客户 field outcome。

**Tech Stack:** Python 标准库、pytest、现有 artifact helper。

---

### Task 1: Outcome Feedback Update Artifact

**Files:**
- Create: `tests/test_r11_outcome_feedback_update.py`
- Create: `experiments/r11_outcome_feedback_update.py`

- [x] **Step 1: Write the failing test**

```python
def test_r11_outcome_feedback_update_generates_bounded_candidate_ledger():
    update = build_r11_outcome_feedback_update(
        artifact_id="r11-outcome-feedback-update-test",
        run_id="r11-l3-test",
        r11_product_shadow_trial=shadow,
        r11_external_holdout_validation=holdout,
        observed_feedback=feedback,
    )
    assert update["update_gate"]["runtime_default_allowed"] is False
    assert update["update_gate"]["prompt_or_persona_manual_patch_allowed"] is False
    assert {item["status"] for item in update["update_candidates"]} == {
        "accepted",
        "rejected",
        "diagnostic_only",
    }
```

- [x] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_r11_outcome_feedback_update.py -q`

Expected: FAIL with missing `experiments.r11_outcome_feedback_update`.

- [x] **Step 3: Write minimal implementation**

Implement:

- schema version `r11-outcome-feedback-update-v1`
- feedback packet normalization
- residual summary
- four update candidates:
  - `mechanism_weight`
  - `segment_sensitivity`
  - `propagation_edge`
  - `interval_uncertainty`
- `accepted / rejected / diagnostic_only` status ledger
- runtime default blocked gate

- [x] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_r11_outcome_feedback_update.py -q`

Expected: PASS.

### Task 2: Current Artifact and Docs

**Files:**
- Create: `experiments/results/r11_outcome_feedback_update/r11-outcome-feedback-update-current-001.json`
- Modify: `docs/CURRENT_STATE.md`
- Modify: `docs/active-spec.md`
- Modify: `docs/superpowers/specs/2026-06-26-r11-learnable-interaction-risk-discoverer-spec.md`

- [x] **Step 1: Generate current artifact**

Run:

```bash
.venv/bin/python experiments/r11_outcome_feedback_update.py \
  --artifact-id r11-outcome-feedback-update-current-001 \
  --run-id r11-l3-current \
  --r11-product-shadow-trial-path experiments/results/r11_product_shadow_trial/r11-product-shadow-trial-current-001.json \
  --r11-external-holdout-validation-path experiments/results/r11_external_holdout_validation/r11-external-holdout-validation-current-001.json \
  --output experiments/results/r11_outcome_feedback_update/r11-outcome-feedback-update-current-001.json
```

Expected: guarded stdout with `status=r11_outcome_feedback_update_ready_guarded`.

- [x] **Step 2: Update docs**

Add L3 state:

```markdown
R11 L3 已生成受约束 outcome feedback update ledger，但 current artifact 使用 public proxy replay，不是客户 field outcome；runtime default 继续 blocked。
```

- [x] **Step 3: Verify**

Run:

```bash
.venv/bin/python -m pytest tests/test_r11_outcome_feedback_update.py tests/test_r11_product_shadow_trial.py -q
.venv/bin/python -m pytest -q
git diff --check
```

- [x] **Step 4: Commit**

Run:

```bash
git add docs/CURRENT_STATE.md docs/active-spec.md docs/superpowers/specs/2026-06-26-r11-learnable-interaction-risk-discoverer-spec.md docs/superpowers/plans/2026-06-26-r11-outcome-feedback-update.md experiments/r11_outcome_feedback_update.py tests/test_r11_outcome_feedback_update.py experiments/results/r11_outcome_feedback_update/r11-outcome-feedback-update-current-001.json -f
git commit -m "feat: add R11 outcome feedback update"
```
