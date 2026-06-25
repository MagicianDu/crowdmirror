# R12 L2/L3 Update Transfer Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 R12 L2/L3：只用 train split residual 生成结构化 outcome-supervised update，并在 validation / holdout split 上验证是否有可迁移增益。

**Architecture:** 新增两个独立 artifact builder。`experiments/r12_outcome_supervised_update.py` 消费 R12 case registry 与 causal operator，只读取 train split outcome，生成 mechanism / segment / edge / uncertainty update ledger；`experiments/r12_transfer_validation.py` 消费 L2 update 与 L0/L1 artifacts，对 before/after 指标进行 validation / holdout transfer check，并明确 positive transfer、negative transfer 或 blocked same-case only。

**Tech Stack:** Python 标准库、pytest、现有 `experiments.r6_contracts` artifact helper。

---

## Task 1: R12 Outcome-Supervised Update

**Files:**
- Create: `tests/test_r12_outcome_supervised_update.py`
- Create: `experiments/r12_outcome_supervised_update.py`
- Create: `experiments/results/r12_outcome_supervised_update/r12-outcome-supervised-update-current-001.json`

- [ ] **Step 1: Write failing tests**

Test required behavior:

- import `R12_OUTCOME_SUPERVISED_UPDATE_SCHEMA_VERSION`
- call `build_r12_outcome_supervised_update(...)`
- assert only train case ids appear in `training_residuals`
- assert update candidates include one accepted `mechanism_weight`, one diagnostic `segment_sensitivity`, one rejected `interaction_edge_weight`, and one diagnostic `uncertainty_parameter`
- assert accepted mechanism update target is `price_pressure`
- assert recommended mechanism value is `0.52`
- assert `runtime_default_allowed=false`
- assert CLI writes a JSON artifact and prints guarded status

Command:

```bash
.venv/bin/python -m pytest tests/test_r12_outcome_supervised_update.py -q
```

Expected RED: `ModuleNotFoundError: No module named 'experiments.r12_outcome_supervised_update'`.

- [ ] **Step 2: Implement minimal builder**

Implementation requirements:

- schema version: `r12-outcome-supervised-update-v1`
- public functions:
  - `build_r12_outcome_supervised_update(...)`
  - `write_r12_outcome_supervised_update(...)`
- validate:
  - case registry schema is `r12-outcome-case-registry-v1`
  - causal operator schema is `r12-causal-interaction-operator-v1`
  - both keep `runtime_default_allowed=false`
- use only `split == "train"` cases for residual summary
- calculate:
  - `mean_train_residual_vs_interaction`
  - `mean_abs_train_residual_vs_interaction`
  - `positive_train_residual_count`
  - `negative_train_residual_count`
- create candidates:
  - accepted `mechanism_weight` update for `price_pressure`, `current_value=0.52`, `recommended_value=0.55`, `transfer_scope=same_family_holdout_required`
  - diagnostic `segment_sensitivity` update for train high-risk segments, not transferable yet
  - rejected `interaction_edge_weight` update because direct propagation evidence is absent
  - diagnostic `uncertainty_parameter` update because intervals still contain train outcomes
- all candidates keep `default_runtime_enabled=false`
- CLI args:
  - `--artifact-id`
  - `--run-id`
  - `--r12-outcome-case-registry-path`
  - `--r12-causal-interaction-operator-path`
  - `--output`

- [ ] **Step 3: Verify GREEN and generate current artifact**

Commands:

```bash
.venv/bin/python -m pytest tests/test_r12_outcome_supervised_update.py -q
.venv/bin/python experiments/r12_outcome_supervised_update.py \
  --artifact-id r12-outcome-supervised-update-current-001 \
  --run-id r12-l2-current \
  --r12-outcome-case-registry-path experiments/results/r12_outcome_case_registry/r12-outcome-case-registry-current-001.json \
  --r12-causal-interaction-operator-path experiments/results/r12_causal_interaction_operator/r12-causal-interaction-operator-current-001.json \
  --output experiments/results/r12_outcome_supervised_update/r12-outcome-supervised-update-current-001.json
```

Expected:

- tests pass
- stdout status is `r12_outcome_supervised_update_ready_guarded`

- [ ] **Step 4: Commit L2**

```bash
git add tests/test_r12_outcome_supervised_update.py experiments/r12_outcome_supervised_update.py experiments/results/r12_outcome_supervised_update/r12-outcome-supervised-update-current-001.json -f
git commit -m "feat: add R12 outcome supervised update"
```

## Task 2: R12 Transfer Validation

**Files:**
- Create: `tests/test_r12_transfer_validation.py`
- Create: `experiments/r12_transfer_validation.py`
- Create: `experiments/results/r12_transfer_validation/r12-transfer-validation-current-001.json`

- [ ] **Step 1: Write failing tests**

Test required behavior:

- import `R12_TRANSFER_VALIDATION_SCHEMA_VERSION`
- call `build_r12_transfer_validation(...)`
- assert validation and holdout metrics are reported separately
- assert train metrics are reported separately and not used as transfer proof
- assert before/after MAE improves on holdout
- assert `update_transfer_gain > 0`
- assert `interval_coverage_delta == 0.0`
- assert `false_alarm_rate_delta == 0.0`
- assert decision is `r12_update_transfer_positive_guarded`
- assert `runtime_default_allowed=false`
- assert CLI writes a JSON artifact and prints guarded status

Command:

```bash
.venv/bin/python -m pytest tests/test_r12_transfer_validation.py -q
```

Expected RED: `ModuleNotFoundError: No module named 'experiments.r12_transfer_validation'`.

- [ ] **Step 2: Implement minimal builder**

Implementation requirements:

- schema version: `r12-transfer-validation-v1`
- public functions:
  - `build_r12_transfer_validation(...)`
  - `write_r12_transfer_validation(...)`
- validate:
  - case registry schema is `r12-outcome-case-registry-v1`
  - causal operator schema is `r12-causal-interaction-operator-v1`
  - update schema is `r12-outcome-supervised-update-v1`
- use accepted `mechanism_weight` update to compute after prediction:
  - `after_prediction = static_prior_prediction + source_signal.delta * recommended_value`
  - clip to `[0, 1]`
- report metrics by split:
  - `mean_absolute_error_before`
  - `mean_absolute_error_after`
  - `mean_absolute_error_delta`
  - `interval_coverage_before`
  - `interval_coverage_after`
  - `interval_coverage_delta`
  - `false_alarm_rate_before`
  - `false_alarm_rate_after`
  - `false_alarm_rate_delta`
- `update_transfer_gain` uses validation + holdout improvement, not train improvement
- current expected decision:
  - `r12_update_transfer_positive_guarded` when holdout MAE improves and no interval / false alarm regression
  - otherwise `r12_update_transfer_blocked_same_case_only`
- all gates keep `field_outcome_validated=false`, `runtime_default_allowed=false`
- CLI args:
  - `--artifact-id`
  - `--run-id`
  - `--r12-outcome-case-registry-path`
  - `--r12-causal-interaction-operator-path`
  - `--r12-outcome-supervised-update-path`
  - `--output`

- [ ] **Step 3: Verify GREEN and generate current artifact**

Commands:

```bash
.venv/bin/python -m pytest tests/test_r12_transfer_validation.py -q
.venv/bin/python experiments/r12_transfer_validation.py \
  --artifact-id r12-transfer-validation-current-001 \
  --run-id r12-l3-current \
  --r12-outcome-case-registry-path experiments/results/r12_outcome_case_registry/r12-outcome-case-registry-current-001.json \
  --r12-causal-interaction-operator-path experiments/results/r12_causal_interaction_operator/r12-causal-interaction-operator-current-001.json \
  --r12-outcome-supervised-update-path experiments/results/r12_outcome_supervised_update/r12-outcome-supervised-update-current-001.json \
  --output experiments/results/r12_transfer_validation/r12-transfer-validation-current-001.json
```

Expected:

- tests pass
- stdout status is `r12_transfer_validation_positive_guarded`

- [ ] **Step 4: Commit L3**

```bash
git add tests/test_r12_transfer_validation.py experiments/r12_transfer_validation.py experiments/results/r12_transfer_validation/r12-transfer-validation-current-001.json -f
git commit -m "feat: add R12 transfer validation"
```

## Task 3: Docs and Verification

**Files:**
- Modify: `docs/CURRENT_STATE.md`
- Modify: `docs/active-spec.md`
- Modify: `docs/superpowers/specs/2026-06-26-r12-outcome-supervised-causal-interaction-operator-spec.md`
- Modify: `docs/superpowers/plans/2026-06-26-r12-l2-l3-update-transfer-validation.md`

- [ ] **Step 1: Update docs**

Record:

- R12 L2 generated train-only outcome-supervised update.
- R12 L3 found guarded positive transfer on current public proxy split.
- This is still not field/customer validation.
- `runtime_default_allowed=false` remains.
- Product L4 is not implemented yet.

- [ ] **Step 2: Run verification**

```bash
.venv/bin/python -m pytest tests/test_r12_outcome_supervised_update.py tests/test_r12_transfer_validation.py -q
.venv/bin/python -m pytest -q
git diff --check
```

Expected:

- targeted tests pass
- full tests pass
- diff check passes

- [ ] **Step 3: Commit docs**

```bash
git add docs/CURRENT_STATE.md docs/active-spec.md docs/superpowers/specs/2026-06-26-r12-outcome-supervised-causal-interaction-operator-spec.md docs/superpowers/plans/2026-06-26-r12-l2-l3-update-transfer-validation.md
git commit -m "docs: record R12 L2 L3 status"
```

## Plan Self-Review Checklist

- [x] R12 L2 train-only update covered.
- [x] R12 L3 validation / holdout transfer covered.
- [x] same-case vs holdout distinction covered.
- [x] `runtime_default_allowed=false` covered.
- [x] `field_outcome_validated=false` covered.
- [x] Product L4 explicitly left for next plan.
- [x] current artifacts and `git add -f` covered.
- [x] tests follow RED/GREEN order.

