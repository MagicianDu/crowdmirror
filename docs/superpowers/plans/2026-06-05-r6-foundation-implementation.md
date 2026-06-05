# R6 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first R6 foundation chain: prior manifest, scenario manifest, interaction trace, risk shift report, outcome manifest, learning report, and update registry.

**Architecture:** Keep each R6 artifact in its own focused experiment module with strict JSON output, explicit claim boundaries, and deterministic fixture-friendly builders. A small shared contract module provides validation helpers, while a foundation pipeline module composes the seven artifacts for smoke and Product handoff.

**Tech Stack:** Python 3.11, plain dictionaries, `json`, `argparse`, `pytest`; no new dependencies.

---

## File Structure

- Create `experiments/r6_contracts.py`: shared constants and validation helpers.
- Create `experiments/r6_prior_manifest.py`: builds static no-interaction population/customer prior.
- Create `experiments/r6_scenario_manifest.py`: builds generic change scenario.
- Create `experiments/r6_interaction_trace.py`: builds deterministic lightweight interaction trace from prior and scenario.
- Create `experiments/r6_risk_shift_report.py`: compares static prior and interaction result.
- Create `experiments/r6_outcome_manifest.py`: normalizes release outcome or proxy outcome.
- Create `experiments/r6_learning_report.py`: attributes prediction-outcome error.
- Create `experiments/r6_update_registry.py`: records accepted/rejected/diagnostic update decisions.
- Create `experiments/r6_foundation_pipeline.py`: runs a generic fixture through the full R6 chain.
- Create `tests/test_r6_contracts.py`.
- Create `tests/test_r6_foundation_pipeline.py`.

## Task 1: R6 Shared Contracts

**Files:**
- Create: `experiments/r6_contracts.py`
- Test: `tests/test_r6_contracts.py`

- [ ] **Step 1: Write failing tests**

Create tests covering strict JSON checks, non-empty identifiers, probability distributions, source refs, claim boundaries, and update statuses.

- [ ] **Step 2: Run failing test**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_contracts.py -q
```

Expected: import failure for `experiments.r6_contracts`.

- [ ] **Step 3: Implement shared helpers**

Implement:

- `R6_CLAIM_BOUNDARY`
- `R6_UPDATE_STATUSES`
- `assert_strict_json(payload)`
- `non_empty_string(value, field)`
- `positive_integer(value, field)`
- `finite_number(value, field)`
- `source_refs(value, field="source_refs")`
- `claim_boundaries(value)`
- `risk_flags(value)`
- `probability_distribution(value, options, field)`
- `load_json_artifact(path)`
- `write_json_artifact(path, payload)`

- [ ] **Step 4: Run passing test**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_contracts.py -q
```

Expected: all tests pass.

## Task 2: R6 Manifest Builders

**Files:**
- Create: `experiments/r6_prior_manifest.py`
- Create: `experiments/r6_scenario_manifest.py`
- Create: `experiments/r6_interaction_trace.py`
- Create: `experiments/r6_risk_shift_report.py`
- Create: `experiments/r6_outcome_manifest.py`
- Create: `experiments/r6_learning_report.py`
- Create: `experiments/r6_update_registry.py`
- Test: `tests/test_r6_foundation_pipeline.py`

- [ ] **Step 1: Write failing integration tests**

Create one integration test that builds a price-change fixture without binding to aviation, verifies all seven schema versions, checks no-interaction control, checks interaction delta, checks outcome error attribution, and verifies update registry blocks unvalidated updates.

- [ ] **Step 2: Run failing integration test**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_foundation_pipeline.py -q
```

Expected: import failure for the new R6 modules.

- [ ] **Step 3: Implement minimal manifest builders**

Each builder must:

- validate `artifact_id` and `run_id`;
- preserve `source_refs`;
- preserve `claim_boundaries`;
- add R6-specific `risk_flags`;
- call strict JSON validation before returning;
- expose `write_*` helper.

- [ ] **Step 4: Run passing integration test**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_foundation_pipeline.py -q
```

Expected: all tests pass.

## Task 3: R6 Foundation Pipeline CLI

**Files:**
- Create: `experiments/r6_foundation_pipeline.py`
- Modify: `tests/test_r6_foundation_pipeline.py`

- [ ] **Step 1: Add CLI test**

Add a test that runs:

```bash
.venv/bin/python experiments/r6_foundation_pipeline.py --run-id r6-foundation-test --output /tmp/r6-foundation.json
```

and verifies the output file contains all seven artifact IDs and an overall `status` of `diagnostic_ready`.

- [ ] **Step 2: Run failing CLI test**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_foundation_pipeline.py::test_r6_foundation_pipeline_cli_writes_artifact -q
```

Expected: script missing or CLI output missing.

- [ ] **Step 3: Implement CLI**

Add `argparse` entrypoint with:

- `--artifact-id`
- `--run-id`
- `--output`

The CLI writes one JSON package with keys:

- `schema_version`
- `artifact_id`
- `run_id`
- `status`
- `prior_manifest`
- `scenario_manifest`
- `interaction_trace`
- `risk_shift_report`
- `outcome_manifest`
- `learning_report`
- `update_registry`
- `claim_boundaries`
- `risk_flags`

- [ ] **Step 4: Run CLI test**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_foundation_pipeline.py::test_r6_foundation_pipeline_cli_writes_artifact -q
```

Expected: pass.

## Task 4: Verification and Commit

**Files:**
- All R6 files from Tasks 1-3.

- [ ] **Step 1: Run focused R6 tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_contracts.py tests/test_r6_foundation_pipeline.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run compile check**

Run:

```bash
.venv/bin/python -m compileall experiments/r6_contracts.py experiments/r6_prior_manifest.py experiments/r6_scenario_manifest.py experiments/r6_interaction_trace.py experiments/r6_risk_shift_report.py experiments/r6_outcome_manifest.py experiments/r6_learning_report.py experiments/r6_update_registry.py experiments/r6_foundation_pipeline.py
```

Expected: exit code 0.

- [ ] **Step 3: Run diff check**

Run:

```bash
git diff --check -- experiments/r6_contracts.py experiments/r6_prior_manifest.py experiments/r6_scenario_manifest.py experiments/r6_interaction_trace.py experiments/r6_risk_shift_report.py experiments/r6_outcome_manifest.py experiments/r6_learning_report.py experiments/r6_update_registry.py experiments/r6_foundation_pipeline.py tests/test_r6_contracts.py tests/test_r6_foundation_pipeline.py
```

Expected: exit code 0.

- [ ] **Step 4: Commit only R6 foundation files**

Run:

```bash
git add docs/superpowers/plans/2026-06-05-r6-foundation-implementation.md experiments/r6_contracts.py experiments/r6_prior_manifest.py experiments/r6_scenario_manifest.py experiments/r6_interaction_trace.py experiments/r6_risk_shift_report.py experiments/r6_outcome_manifest.py experiments/r6_learning_report.py experiments/r6_update_registry.py experiments/r6_foundation_pipeline.py tests/test_r6_contracts.py tests/test_r6_foundation_pipeline.py
git commit -m "feat: add R6 foundation artifact chain"
```

Expected: commit includes only R6 plan, R6 modules, and R6 tests.

## Self-Review

- Spec coverage: covers R6 MVP artifact contracts, no-interaction control, risk shift, outcome ingestion, learning report, update registry, and Product claim boundary.
- Known gap: this plan does not implement full Product UI, large-scale OASIS runtime, public dataset ingestion, or cross-case outcome learning. Those are explicitly outside R6 foundation.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: all artifact builders consume and emit plain `dict[str, Any]` and write strict JSON artifacts.

