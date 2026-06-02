# DCL-PRS L1 Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first L1 gate artifacts for DCL-PRS: mechanism ablation, repair repeat acceptance, cross-domain task-slice smoke, Product cohort report evidence, and an upgraded integrated gate.

**Architecture:** Continue the artifact-first pattern from DCL-PRS L0. Each L1 module consumes an L0 artifact, emits a strict JSON gate artifact with claim boundaries, and the integrated gate recognizes completed L1 subgates without closing CCF-A/Product claims.

**Tech Stack:** Python standard library, `pytest`, deterministic JSON artifacts, existing `experiments/results/` convention.

---

## File Structure

- Create `experiments/dcl_prs_mechanism_ablation_matrix.py`
  - Consumes `dcl_prs_mechanism_program`.
  - Emits mechanism-level ablation impact smoke metrics.
- Create `experiments/dcl_prs_repair_repeat_acceptance_matrix.py`
  - Consumes `dcl_prs_failure_attribution`.
  - Emits deterministic salted repeat acceptance smoke metrics for repair candidates.
- Create `experiments/dcl_prs_cross_domain_task_slice_smoke.py`
  - Consumes `dcl_prs_public_dataset_ingestion`.
  - Emits task-slice field mapping smoke for GSS and Eurobarometer.
- Create `experiments/dcl_prs_product_cohort_report.py`
  - Consumes `dcl_prs_mechanism_program`, `dcl_prs_failure_attribution`, and `dcl_prs_dynamic_simulation`.
  - Emits Product-facing cohort report evidence and manifest skeleton.
- Modify `experiments/dcl_prs_gate_index.py`
  - Accept optional L1 artifacts.
  - Report L1 completed subgates and next gates.
- Create tests:
  - `tests/test_dcl_prs_mechanism_ablation_matrix.py`
  - `tests/test_dcl_prs_repair_repeat_acceptance_matrix.py`
  - `tests/test_dcl_prs_cross_domain_task_slice_smoke.py`
  - `tests/test_dcl_prs_product_cohort_report.py`
  - Extend `tests/test_dcl_prs_gate_index.py`

## Task 1: Mechanism Ablation Matrix

**Files:**
- Create: `experiments/dcl_prs_mechanism_ablation_matrix.py`
- Test: `tests/test_dcl_prs_mechanism_ablation_matrix.py`

- [ ] **Step 1: Write failing tests**

```python
from experiments.dcl_prs_mechanism_ablation_matrix import (
    build_mechanism_ablation_matrix,
)
from experiments.dcl_prs_mechanism_program import build_mechanism_program_index


def test_mechanism_ablation_matrix_identifies_nonzero_mechanism_impacts():
    matrix = build_mechanism_ablation_matrix(
        artifact_id="dcl-prs-mechanism-ablation-test",
        mechanism_program_index=build_mechanism_program_index(
            artifact_id="dcl-prs-mechanism-program-test"
        ),
    )

    assert matrix["schema_version"] == "dcl-prs-mechanism-ablation-matrix-v1"
    assert matrix["overall_status"] == "mechanism_ablation_matrix_ready"
    assert matrix["ablation_case_count"] >= 4
    assert matrix["nonzero_impact_rate"] > 0.0
    assert matrix["ccf_a_claim_status"] == "not_claimable"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
pytest tests/test_dcl_prs_mechanism_ablation_matrix.py -q
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement deterministic ablation**

Implement `build_mechanism_ablation_matrix()` by computing a signed support contribution for each mechanism and measuring the delta when each mechanism is removed.

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
pytest tests/test_dcl_prs_mechanism_ablation_matrix.py -q
```

Expected: PASS.

## Task 2: Repair Repeat Acceptance Matrix

**Files:**
- Create: `experiments/dcl_prs_repair_repeat_acceptance_matrix.py`
- Test: `tests/test_dcl_prs_repair_repeat_acceptance_matrix.py`

- [ ] **Step 1: Write failing tests**

```python
from experiments.dcl_prs_failure_attribution import build_failure_attribution_index
from experiments.dcl_prs_repair_repeat_acceptance_matrix import (
    build_repair_repeat_acceptance_matrix,
)


def test_repair_repeat_acceptance_matrix_reports_accepted_and_rejected_candidates():
    matrix = build_repair_repeat_acceptance_matrix(
        artifact_id="dcl-prs-repair-repeat-test",
        failure_attribution_index=build_failure_attribution_index(
            artifact_id="dcl-prs-failure-attribution-test"
        ),
    )

    assert matrix["schema_version"] == "dcl-prs-repair-repeat-acceptance-matrix-v1"
    assert matrix["overall_status"] == "repair_repeat_acceptance_matrix_ready"
    assert matrix["repair_candidate_count"] == 4
    assert matrix["accepted_candidate_count"] >= 1
    assert matrix["rejected_candidate_count"] >= 1
    assert matrix["claim_boundary"]["uses_test_split_for_current_claim"] is False
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
pytest tests/test_dcl_prs_repair_repeat_acceptance_matrix.py -q
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement deterministic repeat acceptance**

Use fixed salts `["s0", "s1", "s2"]`. Candidate acceptance must be deterministic, based on repair action family and signed delta, not on test labels.

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
pytest tests/test_dcl_prs_repair_repeat_acceptance_matrix.py -q
```

Expected: PASS.

## Task 3: Cross-Domain Task Slice Smoke

**Files:**
- Create: `experiments/dcl_prs_cross_domain_task_slice_smoke.py`
- Test: `tests/test_dcl_prs_cross_domain_task_slice_smoke.py`

- [ ] **Step 1: Write failing tests**

```python
from experiments.dcl_prs_cross_domain_task_slice_smoke import (
    build_cross_domain_task_slice_smoke,
)
from experiments.dcl_prs_public_dataset_ingestion import (
    build_cross_domain_ingestion_index,
)


def test_cross_domain_task_slice_smoke_maps_required_fields_for_each_dataset():
    smoke = build_cross_domain_task_slice_smoke(
        artifact_id="dcl-prs-cross-domain-task-slice-smoke-test",
        cross_domain_ingestion=build_cross_domain_ingestion_index(
            artifact_id="dcl-prs-cross-domain-ingestion-test"
        ),
    )

    assert smoke["schema_version"] == "dcl-prs-cross-domain-task-slice-smoke-v1"
    assert smoke["overall_status"] == "cross_domain_task_slice_smoke_ready"
    assert smoke["dataset_count"] == 2
    assert smoke["mapped_task_slice_count"] == 2
    assert smoke["all_required_fields_mapped"] is True
    assert smoke["ccf_a_claim_status"] == "not_claimable"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
pytest tests/test_dcl_prs_cross_domain_task_slice_smoke.py -q
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement task-slice smoke**

For each task slice, check that `cohort`, `policy_or_question`, and `response_distribution` are mapped. Emit source-specific mapping records.

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
pytest tests/test_dcl_prs_cross_domain_task_slice_smoke.py -q
```

Expected: PASS.

## Task 4: Product Cohort Report Evidence

**Files:**
- Create: `experiments/dcl_prs_product_cohort_report.py`
- Test: `tests/test_dcl_prs_product_cohort_report.py`

- [ ] **Step 1: Write failing tests**

```python
from experiments.dcl_prs_dynamic_simulation import build_dynamic_simulation_trace
from experiments.dcl_prs_failure_attribution import build_failure_attribution_index
from experiments.dcl_prs_mechanism_program import build_mechanism_program_index
from experiments.dcl_prs_product_cohort_report import build_product_cohort_report


def test_product_cohort_report_contains_mechanism_repair_trace_and_uncertainty():
    mechanism = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-test"
    )
    report = build_product_cohort_report(
        artifact_id="dcl-prs-product-cohort-report-test",
        mechanism_program_index=mechanism,
        failure_attribution_index=build_failure_attribution_index(
            artifact_id="dcl-prs-failure-attribution-test"
        ),
        dynamic_simulation=build_dynamic_simulation_trace(
            artifact_id="dcl-prs-dynamic-simulation-test",
            mechanism_program_index=mechanism,
        ),
    )

    assert report["schema_version"] == "dcl-prs-product-cohort-report-v1"
    assert report["overall_status"] == "product_cohort_report_evidence_ready"
    assert report["report_sections"] == [
        "cohort_reaction_summary",
        "mechanism_explanation",
        "failure_attribution",
        "dynamic_trace",
        "uncertainty_and_claim_boundary",
    ]
    assert report["product_claim_status"] == "demo_evidence_only"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
pytest tests/test_dcl_prs_product_cohort_report.py -q
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement report artifact**

Build a compact report artifact with section coverage, evidence refs, cohort summaries, uncertainty disclosure, and runtime manifest skeleton.

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
pytest tests/test_dcl_prs_product_cohort_report.py -q
```

Expected: PASS.

## Task 5: Integrated Gate Upgrade

**Files:**
- Modify: `experiments/dcl_prs_gate_index.py`
- Modify: `tests/test_dcl_prs_gate_index.py`

- [ ] **Step 1: Add failing test for L1 complete gate**

The test must pass all L1 artifacts and assert completed subgates include:

```python
[
    "mechanism_ablation_matrix_ready",
    "repair_repeat_acceptance_matrix_ready",
    "cross_domain_task_slice_smoke_ready",
    "product_cohort_report_evidence_ready",
]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
pytest tests/test_dcl_prs_gate_index.py -q
```

Expected: FAIL until the gate accepts L1 artifacts.

- [ ] **Step 3: Implement L1 gate recognition**

Add optional parameters:

```python
mechanism_ablation_matrix: dict[str, Any] | None = None
repair_repeat_acceptance_matrix: dict[str, Any] | None = None
cross_domain_task_slice_smoke: dict[str, Any] | None = None
product_cohort_report: dict[str, Any] | None = None
```

L1 completion must not close `ccf_a_gate.status` or `product_gate.status`.

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
pytest tests/test_dcl_prs_gate_index.py -q
```

Expected: PASS.

## Task 6: Verification and Commit

**Files:**
- All DCL-PRS L1 modules, tests, and this plan.

- [ ] **Step 1: Run focused tests**

Run:

```bash
pytest tests/test_dcl_prs_*.py -q
```

Expected: PASS.

- [ ] **Step 2: Generate L1 artifacts**

Run:

```bash
python experiments/dcl_prs_mechanism_ablation_matrix.py --output-dir experiments/results/dcl_prs_mechanism_ablation_matrix
python experiments/dcl_prs_repair_repeat_acceptance_matrix.py --output-dir experiments/results/dcl_prs_repair_repeat_acceptance_matrix
python experiments/dcl_prs_cross_domain_task_slice_smoke.py --output-dir experiments/results/dcl_prs_cross_domain_task_slice_smoke
python experiments/dcl_prs_product_cohort_report.py --output-dir experiments/results/dcl_prs_product_cohort_report
python experiments/dcl_prs_gate_index.py --output-dir experiments/results/dcl_prs_gate_index
```

Expected: each command writes one JSON artifact and prints a JSON summary.

- [ ] **Step 3: Run full verification**

Run:

```bash
pytest -q
git diff --check
```

Expected: tests pass and no whitespace errors.

- [ ] **Step 4: Commit DCL-PRS L1 batch only**

Run:

```bash
git add docs/superpowers/plans/2026-06-02-dcl-prs-l1-gates.md experiments/dcl_prs_mechanism_ablation_matrix.py experiments/dcl_prs_repair_repeat_acceptance_matrix.py experiments/dcl_prs_cross_domain_task_slice_smoke.py experiments/dcl_prs_product_cohort_report.py experiments/dcl_prs_gate_index.py tests/test_dcl_prs_mechanism_ablation_matrix.py tests/test_dcl_prs_repair_repeat_acceptance_matrix.py tests/test_dcl_prs_cross_domain_task_slice_smoke.py tests/test_dcl_prs_product_cohort_report.py tests/test_dcl_prs_gate_index.py
git commit -m "feat: add DCL-PRS L1 gate artifacts"
```

Expected: commit succeeds without staging unrelated LCDU files.

## Self-Review

- Spec coverage: L1 covers mechanism ablation, repair repeat acceptance, cross-domain task-slice smoke, Product cohort report evidence, and integrated gate upgrade.
- Claim boundary: all L1 artifacts remain smoke/diagnostic evidence and do not close CCF-A/Product claims.
- Scope control: no external dataset download and no LLM API calls in this batch.
- Dirty worktree protection: stage only DCL-PRS L1 files listed above.
