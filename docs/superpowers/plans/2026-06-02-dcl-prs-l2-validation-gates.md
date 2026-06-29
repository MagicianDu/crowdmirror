# DCL-PRS L2 Validation Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Advance DCL-PRS from L1 smoke artifacts to L2 validation gates: repeat ablation stability, repair effect validation, cross-domain microdata access audit, Product runtime manifest connection, and strong baseline comparison.

**Architecture:** Keep the evidence chain honest. L2 gates may close smoke-level blockers, but they must not pretend that official GSS/Eurobarometer microdata were downloaded or that DCL-PRS already beats strong baselines. The integrated gate should advance blocking gaps to the next real missing evidence layer.

**Tech Stack:** Python standard library, `pytest`, deterministic JSON artifacts, current DCL-PRS L0/L1 modules.

---

## File Structure

- Create `experiments/dcl_prs_mechanism_ablation_repeat_matrix.py`
  - Consumes mechanism ablation matrix.
  - Emits salt-level stability for mechanism impact.
- Create `experiments/dcl_prs_repair_effect_validation_matrix.py`
  - Consumes repair repeat acceptance matrix.
  - Emits deterministic effect validation for accepted/rejected repair candidates.
- Create `experiments/dcl_prs_cross_domain_microdata_slices.py`
  - Consumes cross-domain task slice smoke.
  - Emits official-source access audit and schema sample slice readiness without claiming official microdata download.
- Create `experiments/dcl_prs_product_runtime_manifest.py`
  - Consumes Product cohort report.
  - Emits runtime manifest connection evidence.
- Create `experiments/dcl_prs_strong_baseline_matrix.py`
  - Consumes L2 artifacts.
  - Emits strong baseline comparison with `dcl_prs_not_leading` status until real effect evidence exists.
- Modify `experiments/dcl_prs_gate_index.py`
  - Accept L2 artifacts and advance blocking gaps.
- Create tests for each new module and extend `tests/test_dcl_prs_gate_index.py`.

## Task 1: Mechanism Ablation Repeat Matrix

**Files:**
- Create: `experiments/dcl_prs_mechanism_ablation_repeat_matrix.py`
- Test: `tests/test_dcl_prs_mechanism_ablation_repeat_matrix.py`

- [ ] **Step 1: Write failing tests**

Assert schema version `dcl-prs-mechanism-ablation-repeat-matrix-v1`, status `mechanism_ablation_repeat_matrix_ready`, salt count 3, repeat case count equals ablation cases times salts, and stability rate is positive.

- [ ] **Step 2: Implement deterministic salted repeat**

Use salts `s0/s1/s2`. Preserve every ablation case id and perturb impact by a tiny deterministic salt adjustment. Mark cases stable when all salted impacts remain nonzero.

- [ ] **Step 3: Verify**

Run `pytest tests/test_dcl_prs_mechanism_ablation_repeat_matrix.py -q`.

## Task 2: Repair Effect Validation Matrix

**Files:**
- Create: `experiments/dcl_prs_repair_effect_validation_matrix.py`
- Test: `tests/test_dcl_prs_repair_effect_validation_matrix.py`

- [ ] **Step 1: Write failing tests**

Assert schema version `dcl-prs-repair-effect-validation-matrix-v1`, status `repair_effect_validation_matrix_ready`, accepted repairs have positive effect proxy, rejected repairs are not promoted, and test split is not used for current claim.

- [ ] **Step 2: Implement effect validation**

Use accepted/rejected decisions from repair repeat matrix. Compute deterministic effect proxy by action type. Keep this as diagnostic evidence only.

- [ ] **Step 3: Verify**

Run `pytest tests/test_dcl_prs_repair_effect_validation_matrix.py -q`.

## Task 3: Cross-Domain Microdata Access Audit

**Files:**
- Create: `experiments/dcl_prs_cross_domain_microdata_slices.py`
- Test: `tests/test_dcl_prs_cross_domain_microdata_slices.py`

- [ ] **Step 1: Write failing tests**

Assert schema version `dcl-prs-cross-domain-microdata-slices-v1`, status `cross_domain_microdata_access_audit_ready`, official sources are GSS and Eurobarometer, `official_microdata_loaded` is false, and next gate is official public-use file download.

- [ ] **Step 2: Implement honest access audit**

Record official access URLs and schema sample slices. Do not claim official microdata rows were loaded.

- [ ] **Step 3: Verify**

Run `pytest tests/test_dcl_prs_cross_domain_microdata_slices.py -q`.

## Task 4: Product Runtime Manifest Connection

**Files:**
- Create: `experiments/dcl_prs_product_runtime_manifest.py`
- Test: `tests/test_dcl_prs_product_runtime_manifest.py`

- [ ] **Step 1: Write failing tests**

Assert schema version `dcl-prs-product-runtime-manifest-v1`, status `product_runtime_manifest_connection_ready`, report artifact ref is present, manifest has routes for report sections, and customer/runtime validation remains open.

- [ ] **Step 2: Implement manifest connection**

Convert Product cohort report sections into runtime route entries and evidence references.

- [ ] **Step 3: Verify**

Run `pytest tests/test_dcl_prs_product_runtime_manifest.py -q`.

## Task 5: Strong Baseline Matrix

**Files:**
- Create: `experiments/dcl_prs_strong_baseline_matrix.py`
- Test: `tests/test_dcl_prs_strong_baseline_matrix.py`

- [ ] **Step 1: Write failing tests**

Assert schema version `dcl-prs-strong-baseline-matrix-v1`, status `strong_baseline_dcl_prs_not_leading`, paper gate eligibility false, and covered baselines include deterministic anchor, LCDU-LCR-SG, fixed party prior, and DCL-PRS.

- [ ] **Step 2: Implement strong baseline comparison**

Use current L2 artifacts to report readiness but keep DCL-PRS not leading because no real multi-dataset effect validation or official microdata exists yet.

- [ ] **Step 3: Verify**

Run `pytest tests/test_dcl_prs_strong_baseline_matrix.py -q`.

## Task 6: Integrated Gate L2 Upgrade

**Files:**
- Modify: `experiments/dcl_prs_gate_index.py`
- Modify: `tests/test_dcl_prs_gate_index.py`

- [ ] **Step 1: Add L2 gate test**

Pass all L2 artifacts into `build_dcl_prs_gate_index()` and assert completed subgates include all L2 readiness flags.

- [ ] **Step 2: Implement L2 recognition**

Gate must advance gaps:

- `mechanism_ablation_repeat_missing` closes;
- `repair_effect_validation_missing` closes;
- `cross_domain_microdata_missing` becomes `cross_domain_microdata_download_missing`;
- `product_runtime_manifest_connection_missing` closes;
- `strong_baseline_win_missing` remains if strong baseline status is not leading.

- [ ] **Step 3: Verify**

Run `pytest tests/test_dcl_prs_gate_index.py -q`.

## Task 7: Verification and Commit

**Files:**
- All DCL-PRS L2 modules, tests, and this plan.

- [ ] **Step 1: Focused tests**

Run `pytest tests/test_dcl_prs_*.py -q`.

- [ ] **Step 2: Generate L2 artifacts**

Run each new L2 script plus `experiments/dcl_prs_gate_index.py`.

- [ ] **Step 3: Full verification**

Run `pytest -q` and `git diff --check`.

- [ ] **Step 4: Commit only DCL-PRS L2 files**

Stage the L2 plan, new L2 modules/tests, and gate edits. Do not stage old LCDU dirty files.

## Self-Review

- Spec coverage: covers all current required next gates.
- Claim boundary: official GSS/Eurobarometer microdata download is not faked.
- Product boundary: runtime manifest connection is not customer/runtime validation.
- Research boundary: strong baseline remains not leading until real effect and multi-dataset validation exist.
