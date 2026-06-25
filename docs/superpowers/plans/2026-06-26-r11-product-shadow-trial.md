# R11 Product Shadow Trial Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 R11 L1 public-use proxy holdout 接入 Product shadow trial，使 Product 后台运行 R11 并生成 source-backed evidence card，但不改变客户可见主结论和 runtime default。

**Architecture:** 新增 `experiments/r11_product_shadow_trial.py` 生成 shadow-only artifact；扩展 `r6_product_customer_value_report.py` 让 customer report 可消费 shadow evidence card；扩展 `r6_product_api_manifest.py` 暴露 `/r6/product/r11-shadow-trial` endpoint 并验证 runtime boundary。所有输出继续保留 `field_outcome_validated=false`、`runtime_default_allowed=false`、`product_core_method_ready=false`。

**Tech Stack:** Python 标准库、pytest、现有 artifact helper、现有 Product report/API manifest contract。

---

### Task 1: Shadow Trial Artifact

**Files:**
- Create: `tests/test_r11_product_shadow_trial.py`
- Create: `experiments/r11_product_shadow_trial.py`

- [x] **Step 1: Write the failing test**

```python
def test_r11_product_shadow_trial_creates_shadow_only_evidence_card():
    holdout = build_r11_external_holdout_validation(...)
    trial = build_r11_product_shadow_trial(..., r11_external_holdout_validation=holdout)
    assert trial["trial_contract"]["shadow_only"] is True
    assert trial["customer_visible_primary_decision"]["r11_can_override_primary_decision"] is False
    assert trial["acceptance_gates"]["runtime_default_allowed"] is False
```

- [x] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_r11_product_shadow_trial.py -q`

Expected: FAIL with missing `experiments.r11_product_shadow_trial`.

- [x] **Step 3: Write minimal implementation**

Implement `build_r11_product_shadow_trial()` with:

- schema version `r11-product-shadow-trial-v1`
- status `r11_product_shadow_trial_ready_guarded`
- `shadow_evidence_card`
- `customer_visible_primary_decision`
- `outcome_review_handoff`
- blocked claims and source refs

- [x] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_r11_product_shadow_trial.py -q`

Expected: PASS.

### Task 2: Product Report and API Manifest Integration

**Files:**
- Modify: `experiments/r6_product_customer_value_report.py`
- Modify: `tests/test_r6_product_customer_value_report.py`
- Modify: `experiments/r6_product_api_manifest.py`
- Modify: `tests/test_r6_product_api_manifest.py`

- [x] **Step 1: Write failing integration tests**

Add tests that assert:

- `r11_shadow_trial` appears in `customer_sections`.
- `display_payload["r11_shadow_trial"]` exists.
- R11 shadow section uses `claim_status=shadow_only`.
- R11 cannot override primary decision.
- API manifest includes `r11_product_shadow_trial` artifact ref and `/r6/product/r11-shadow-trial` endpoint.

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_product_customer_value_report.py::test_product_customer_value_report_can_show_r11_shadow_trial tests/test_r6_product_api_manifest.py::test_r6_product_api_manifest_exposes_guarded_artifact_contract -q
```

Expected: FAIL before implementation.

- [x] **Step 3: Implement report/API integration**

Update builders and CLI:

- `build_r6_product_customer_value_report(..., r11_product_shadow_trial=None)`
- CLI argument `--r11-product-shadow-trial-path`
- source registry entry for `r11-product-shadow-trial-current-001`
- API manifest default path and required artifact for `r11_product_shadow_trial`
- endpoint `/r6/product/r11-shadow-trial`

- [x] **Step 4: Run tests to verify pass**

Run:

```bash
.venv/bin/python -m pytest tests/test_r11_product_shadow_trial.py tests/test_r6_product_customer_value_report.py tests/test_r6_product_api_manifest.py -q
```

Expected: PASS.

### Task 3: Current Artifacts, Docs, and Commit

**Files:**
- Create: `experiments/results/r11_product_shadow_trial/r11-product-shadow-trial-current-001.json`
- Modify: `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json`
- Modify: `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json`
- Modify: `docs/CURRENT_STATE.md`
- Modify: `docs/active-spec.md`
- Modify: `docs/superpowers/specs/2026-06-26-r11-learnable-interaction-risk-discoverer-spec.md`

- [x] **Step 1: Generate current artifacts**

Run:

```bash
.venv/bin/python experiments/r11_product_shadow_trial.py --artifact-id r11-product-shadow-trial-current-001 --run-id r11-l2-current --r11-external-holdout-validation-path experiments/results/r11_external_holdout_validation/r11-external-holdout-validation-current-001.json --output experiments/results/r11_product_shadow_trial/r11-product-shadow-trial-current-001.json
.venv/bin/python experiments/r6_product_customer_value_report.py --artifact-id r6-product-customer-value-report-current-001 --run-id r11-l2-product-current --output experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json --r8-robustness-holdout-gate-path experiments/results/r8_robustness_holdout_gate/r8-robustness-holdout-gate-current-001.json --r8-stop-loss-diagnosis-path experiments/results/r8_stop_loss_diagnosis/r8-stop-loss-diagnosis-current-001.json --r8-product-failure-diagnosis-package-path experiments/results/r8_product_failure_diagnosis_package/r8-product-failure-diagnosis-package-current-001.json --r9-combination-comparison-path experiments/results/r9_combination_comparison/r9-combination-comparison-current-001.json --r9-synthetic-mechanism-lab-path experiments/results/r9_synthetic_mechanism_lab/r9-synthetic-mechanism-lab-current-001.json --r9-false-alarm-gate-redesign-path experiments/results/r9_false_alarm_gate_redesign/r9-false-alarm-gate-redesign-current-001.json --r9-holdout-guard-path experiments/results/r9_holdout_guard/r9-holdout-guard-current-001.json --r11-product-shadow-trial-path experiments/results/r11_product_shadow_trial/r11-product-shadow-trial-current-001.json
.venv/bin/python experiments/r6_product_api_manifest.py --artifact-id r6-product-api-manifest-current-001 --run-id r11-l2-product-current --output experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json
```

- [x] **Step 2: Update docs**

Add R11 L2 status and boundary:

```markdown
R11 L2 已进入 Product shadow trial：后台运行、source-backed evidence card、outcome review handoff 已建立；客户可见主结论仍由 guarded baseline 输出，R11 不允许覆盖 primary decision。
```

- [x] **Step 3: Verify**

Run:

```bash
.venv/bin/python -m pytest -q
git diff --check
git status --short
```

- [x] **Step 4: Commit**

Run:

```bash
git add docs/CURRENT_STATE.md docs/active-spec.md docs/superpowers/specs/2026-06-26-r11-learnable-interaction-risk-discoverer-spec.md docs/superpowers/plans/2026-06-26-r11-product-shadow-trial.md experiments/r11_product_shadow_trial.py experiments/r6_product_customer_value_report.py experiments/r6_product_api_manifest.py tests/test_r11_product_shadow_trial.py tests/test_r6_product_customer_value_report.py tests/test_r6_product_api_manifest.py experiments/results/r11_product_shadow_trial/r11-product-shadow-trial-current-001.json experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json -f
git commit -m "feat: add R11 product shadow trial"
```
