# LCDU-hybrid v2 Constrained Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 LCDU-hybrid v2 增加 worst-segment non-inferiority guard，让层级校准候选不能通过牺牲局部人群风险换取平均 loss 改善。

**Architecture:** 保留现有 unconstrained selection 作为对照，在同一个 artifact 中新增 constrained selection。候选仍只从 calibration split 生成，选择仍只看 heldout split，test split 只用于最终 claim。

**Tech Stack:** Python 标准库、现有 LCDU ANES microdata artifact、pytest、JSON artifact。

---

## 文件结构

- Modify: `experiments/lcdu_anes_hierarchical_calibration_matrix.py`
  - 新增 CLI 参数 `--max-worst-segment-delta`。
  - 新增 constrained selection helper。
  - artifact 顶层新增 constrained/unconstrained task count。
  - task result 新增 `unconstrained_selection` 与 `constrained_selection`。

- Modify: `tests/test_lcdu_anes_hierarchical_calibration_matrix.py`
  - 新增 guard 避开 worst-segment regression 的测试。
  - 新增无候选满足 guard 时回退 anchor 的测试。
  - 更新 CLI 测试，确认 constrained 字段写入。

- Output: `experiments/results/lcdu_hierarchical_calibration/lcdu-anes-hierarchical-calibration-current-001.json`
  - 重新生成当前 ANES artifact。

## Task 1: 扩展测试

- [x] **Step 1: 写 constrained guard 测试**

在 `tests/test_lcdu_anes_hierarchical_calibration_matrix.py` 中新增测试：

```python
def test_constrained_selection_falls_back_when_worst_guard_blocks_candidate():
    artifact = build_lcdu_anes_hierarchical_calibration_matrix(
        microdata_artifact=_microdata_artifact(
            heldout_sparse_distribution="oppose",
            test_sparse_distribution="oppose",
        ),
        artifact_id="lcdu-hierarchical-test",
        k_grid=[1, 10, 50],
        max_worst_segment_delta=0.0,
    )

    task = artifact["task_results"]["task_sparse_party_prior"]
    assert task["unconstrained_selection"]["beats_deterministic_anchor"] is True
    assert task["constrained_selection"]["selected_method_id"] == "calibration_segment_anchor"
    assert task["constrained_selection"]["fallback_reason"] == "no_candidate_passed_worst_segment_guard"
    assert task["constrained_selection"]["heldout_worst_guard_pass"] is True
```

- [x] **Step 2: 更新 CLI 测试预期**

确认 stdout 包含：

```json
{
  "constrained_anchor_win_task_count": 0,
  "unconstrained_anchor_win_task_count": 1
}
```

- [x] **Step 3: 跑测试确认失败**

Run:

```bash
pytest tests/test_lcdu_anes_hierarchical_calibration_matrix.py -q
```

Expected: FAIL，原因是 builder 尚不接受 `max_worst_segment_delta` 或 artifact 尚无 constrained 字段。

## Task 2: 实现 constrained selection

- [x] **Step 1: 扩展函数签名**

在 `build_lcdu_anes_hierarchical_calibration_matrix` 和 `write_lcdu_anes_hierarchical_calibration_matrix` 增加：

```python
max_worst_segment_delta: float = 0.0
```

- [x] **Step 2: 增加选择 helper**

新增：

```python
def _select_constrained_method(
    *,
    heldout_losses: dict[str, float],
    heldout_worst_losses: dict[str, float],
    max_worst_segment_delta: float,
) -> tuple[str, str | None]:
    anchor_worst = heldout_worst_losses[ANCHOR_METHOD_ID]
    candidates = [
        method_id
        for method_id, loss in heldout_losses.items()
        if method_id != ANCHOR_METHOD_ID
        and loss < heldout_losses[ANCHOR_METHOD_ID]
        and heldout_worst_losses[method_id] - anchor_worst <= max_worst_segment_delta
    ]
    if not candidates:
        return ANCHOR_METHOD_ID, "no_candidate_passed_worst_segment_guard"
    return min(candidates, key=heldout_losses.get), None
```

- [x] **Step 3: 输出双 selection**

每个 task 同时输出：

```python
"unconstrained_selection": _selection_summary(...),
"constrained_selection": _selection_summary(...),
```

并保留旧字段兼容现有测试：

```python
"selected_method_id": unconstrained_method_id
```

- [x] **Step 4: CLI 增加参数**

```python
parser.add_argument("--max-worst-segment-delta", type=float, default=0.0)
```

## Task 3: 生成 artifact 并验证

- [x] **Step 1: 跑新增测试**

```bash
pytest tests/test_lcdu_anes_hierarchical_calibration_matrix.py -q
```

Expected: PASS。

- [x] **Step 2: 重新生成 ANES artifact**

```bash
python experiments/lcdu_anes_hierarchical_calibration_matrix.py
```

Expected stdout:

```json
{
  "artifact_id": "lcdu-anes-hierarchical-calibration-current-001",
  "task_count": 2
}
```

- [x] **Step 3: 跑相邻测试与全量测试**

```bash
pytest tests/test_lcdu_anes_cross_task_validation.py tests/test_lcdu_anes_strong_baseline_matrix.py tests/test_lcdu_anes_hybrid_method_validation.py tests/test_lcdu_anes_hierarchical_calibration_matrix.py -q
pytest -q
git diff --check
```

Expected: 全部通过。

## Self-Review

- Spec coverage: 覆盖线路 A 的 constrained selection、artifact 字段、测试、结果生成。
- Placeholder scan: 无占位任务。
- Type consistency: `max_worst_segment_delta` 在 builder、writer、CLI 和测试中一致。
