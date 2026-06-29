# S2PC L1 Runtime Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 S2PC 从 L0 单个 deterministic candidate 推进到 L1 多候选 runtime search，使每个候选都能被 Product 独立消费、被 Research held-out gate 独立接受或拒绝。

**Architecture:** Research 侧先生成 `policy-reaction-s2pc-l1-candidate-set-v1`，保留 beam 中多个 candidate 的 prompt components、参数 provenance 和 split contract。Product 侧暂时复用已实现的 `policy-reaction-s2pc-candidate-v1` runtime 注入口，因此 L1 需要提供从 candidate set 导出单个候选 artifact 的函数。后续 L1.2 再批量跑 Product runtime、生成 effect matrix，并引入 LLM-assisted semantic rewrite 作为候选生成轴。

**Tech Stack:** Python 3.13, pytest, strict JSON artifacts, existing CIRCE Research/Product artifact conventions.

---

## Scope

本计划只做 L1 runtime search 的基础设施首个切片：

- 生成多候选 candidate set。
- 从 candidate set 导出 Product runtime 可消费的单候选 artifact。
- 生成当前 calibration benchmark 的 L1 candidate set artifact。
- 不在本切片批量调用本地 LLM，不声称 S2PC runtime 效果改善。

## Task 1: Research L1 Candidate Set Core

**Files:**
- Modify: `src/circe/calibration/s2pc.py`
- Modify: `tests/test_policy_reaction_s2pc.py`

- [ ] **Step 1: Write failing tests**

Add tests that import:

```python
from circe.calibration.s2pc import (
    S2PC_L1_CANDIDATE_SET_SCHEMA_VERSION,
    build_s2pc_l1_candidate_set_artifact,
    extract_s2pc_candidate_from_l1_set,
)
```

Test behavior:

```python
def test_build_s2pc_l1_candidate_set_keeps_multiple_runtime_candidates():
    residuals = mine_policy_reaction_residuals(_calibration_benchmark(), min_magnitude=0.05)
    matches = retrieve_semantic_factors(residuals, default_semantic_factor_catalog(), top_k=2)
    patches = compile_semantic_matches_to_parameter_patches(matches, default_semantic_factor_catalog())
    search = run_constrained_parameter_beam_search(patches, beam_width=3)

    candidate_set = build_s2pc_l1_candidate_set_artifact(
        candidate_set_id="policy-reaction-s2pc-l1-candidate-set-test",
        calibration_benchmark=_calibration_benchmark(),
        residual_artifact=residuals,
        semantic_matches=matches,
        parameter_patches=patches,
        search_result=search,
    )

    assert candidate_set["schema_version"] == S2PC_L1_CANDIDATE_SET_SCHEMA_VERSION
    assert candidate_set["candidate_count"] == 3
    assert candidate_set["candidates"][0]["candidate_prompt_components"]["calibration_anchor"]
    assert candidate_set["source_split_contract"]["candidate_acceptance"] == "heldout_required"
    json.dumps(candidate_set, allow_nan=False)
```

```python
def test_extract_s2pc_candidate_from_l1_set_is_product_runtime_compatible():
    candidate_set = _build_l1_candidate_set_fixture()
    candidate = extract_s2pc_candidate_from_l1_set(
        candidate_set,
        candidate_id=candidate_set["candidates"][1]["candidate_id"],
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["generator"] == "s2pc_l1_multi_candidate_runtime_search"
    assert candidate["candidate_prompt_components"]
    assert candidate["source_split_contract"]["candidate_acceptance"] == "heldout_required"
    json.dumps(candidate, allow_nan=False)
```

- [ ] **Step 2: Run RED**

```bash
.venv/bin/python -m pytest tests/test_policy_reaction_s2pc.py::test_build_s2pc_l1_candidate_set_keeps_multiple_runtime_candidates tests/test_policy_reaction_s2pc.py::test_extract_s2pc_candidate_from_l1_set_is_product_runtime_compatible -q
```

Expected: import error for missing L1 functions/constants.

- [ ] **Step 3: Implement minimal L1 core**

Add:

- `S2PC_L1_CANDIDATE_SET_SCHEMA_VERSION = "policy-reaction-s2pc-l1-candidate-set-v1"`
- `build_s2pc_l1_candidate_set_artifact(...)`
- `extract_s2pc_candidate_from_l1_set(...)`

The candidate set must preserve calibration-only generation and heldout-required acceptance.

- [ ] **Step 4: Run GREEN**

```bash
.venv/bin/python -m pytest tests/test_policy_reaction_s2pc.py::test_build_s2pc_l1_candidate_set_keeps_multiple_runtime_candidates tests/test_policy_reaction_s2pc.py::test_extract_s2pc_candidate_from_l1_set_is_product_runtime_compatible -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/circe/calibration/s2pc.py tests/test_policy_reaction_s2pc.py
git commit -m "feat: add s2pc l1 candidate set"
```

## Task 2: Candidate Set CLI

**Files:**
- Modify: `experiments/policy_reaction_s2pc_gate.py`
- Test: `tests/test_policy_reaction_s2pc.py`

Add a writer function that builds and writes `policy-reaction-s2pc-l1-candidate-set-current-001.json`. The CLI must not evaluate or accept the candidates; it only writes candidate-generation evidence.

## Task 3: Runtime Search Execution Matrix

**Files:**
- Product runtime command artifacts under `product/experiments/results/`
- Research held-out benchmarks and runtime-effect artifacts under `research/experiments/results/policy_reaction_benchmark/`

Run Product separately for each L1 candidate exported from the set. Research evaluates each candidate against the same held-out target and builds a matrix with accepted/rejected status.

## Task 4: LLM-Assisted Semantic Rewrite Axis

Add an optional candidate-generation axis where a local/paid LLM proposes semantic rewrite text for `segment_prompt` and `calibration_anchor`, but the candidate must still pass the same Product runtime effect gate before any improvement claim.
