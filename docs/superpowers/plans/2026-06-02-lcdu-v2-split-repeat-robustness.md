# LCDU-hybrid v2 Split Repeat Robustness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用多个 split salt 验证 LCDU-hybrid v2 constrained selection 的平均效果提升和 worst-segment 风险是否稳定。

**Architecture:** 新增独立 robustness matrix，不改写既有 microdata ingestion artifact 的固定 split contract。每个 repeat 用相同 calibration/heldout/test 比例但不同 hash salt 生成临时 microdata artifact，再调用现有 hierarchical calibration builder，最后聚合 win rate、worst guard pass rate 和失败类型。

**Tech Stack:** Python 标准库、现有 ANES ingestion helper、现有 LCDU-hybrid v2 builder、pytest、JSON artifact。

---

## 文件结构

- Create: `experiments/lcdu_anes_split_repeat_robustness_matrix.py`
  - 从 ANES CSV 读取行。
  - 对每个 split salt 生成 calibration/heldout/test projection。
  - 调用 `build_lcdu_anes_hierarchical_calibration_matrix`。
  - 聚合 repeat-level 和 task-level 稳健性指标。

- Create: `tests/test_lcdu_anes_split_repeat_robustness_matrix.py`
  - 验证多 salt repeat 能聚合。
  - 验证 artifact 区分 weighted win 与 test worst guard failure。
  - 验证 CLI 写 JSON。

- Output: `experiments/results/lcdu_split_repeat_robustness/lcdu-anes-split-repeat-robustness-current-001.json`
  - 当前 ANES 切片的正式 split/repeat 结果。

## Task 1: 新增测试

- [x] **Step 1: 写 builder 测试**

测试要求：

- 使用已有 finer schema 测试风格的合成 ANES rows。
- 传入 `split_salts=["salt-a", "salt-b"]`。
- 断言 artifact 包含：
  - `schema_version`
  - `repeat_count`
  - `task_summary`
  - `constrained_anchor_win_rate`
  - `test_worst_guard_pass_rate`

- [x] **Step 2: 写 CLI 测试**

CLI 命令：

```bash
python experiments/lcdu_anes_split_repeat_robustness_matrix.py \
  --input-csv <tmp csv> \
  --output <tmp json> \
  --artifact-id split-repeat-test \
  --split-salts salt-a salt-b
```

Expected: stdout 包含 `repeat_count=2`。

- [x] **Step 3: 跑测试确认失败**

```bash
pytest tests/test_lcdu_anes_split_repeat_robustness_matrix.py -q
```

Expected: module import fail。

## Task 2: 实现 split/repeat robustness matrix

- [x] **Step 1: 创建脚本**

核心函数：

```python
def build_lcdu_anes_split_repeat_robustness_matrix(
    *,
    rows: list[dict[str, str]],
    artifact_id: str,
    split_salts: list[str],
    k_grid: list[float] | None = None,
    max_worst_segment_delta: float = 0.0,
) -> dict[str, Any]:
    ...
```

- [x] **Step 2: 实现 salted split projection**

规则：

- `sha256(f"{salt}:{case_id}") % 5`
- remainder `{0,1,2}` -> calibration
- remainder `{3}` -> heldout
- remainder `{4}` -> test

- [x] **Step 3: 聚合任务指标**

每个 task 输出：

- `repeat_count`
- `constrained_anchor_win_count`
- `constrained_anchor_win_rate`
- `test_worst_guard_pass_count`
- `test_worst_guard_pass_rate`
- `joint_success_count`
- `joint_success_rate`
- `mean_test_loss_delta_vs_anchor`
- `mean_test_worst_segment_delta_vs_anchor`
- `failure_modes`

- [x] **Step 4: CLI**

默认：

```bash
--input-csv data/raw/anes_2024/anes2024_sda_lcdu_subset.csv
--split-salts salt-001 salt-002 salt-003 salt-004 salt-005
--output experiments/results/lcdu_split_repeat_robustness/lcdu-anes-split-repeat-robustness-current-001.json
```

## Task 3: 运行与验证

- [x] **Step 1: 跑新增测试**

```bash
pytest tests/test_lcdu_anes_split_repeat_robustness_matrix.py -q
```

- [x] **Step 2: 生成正式 artifact**

```bash
python experiments/lcdu_anes_split_repeat_robustness_matrix.py
```

- [x] **Step 3: 跑相邻测试和全量测试**

```bash
pytest tests/test_lcdu_anes_hierarchical_calibration_matrix.py tests/test_lcdu_anes_split_repeat_robustness_matrix.py -q
pytest -q
git diff --check
```

## Task 4: Prior/K Ablation Matrix

**Goal:** 在 split/repeat 结果为 mixed 后，拆解 prior family 与 k 的影响，判断稳定性不足来自 `party/global/income/neighbor` 选择、k-grid，还是 heldout 到 test 的外推。

**Files:**
- Create: `experiments/lcdu_anes_hierarchical_ablation_matrix.py`
- Create: `tests/test_lcdu_anes_hierarchical_ablation_matrix.py`
- Output: `experiments/results/lcdu_hierarchical_ablation/lcdu-anes-hierarchical-ablation-current-001.json`

- [x] **Step 1: 写 ablation 测试**

测试应断言 artifact 包含：

- `prior_family_summary`
- `k_summary`
- `selected_method_summary`
- 每个 summary 有 `joint_success_rate`、`win_rate`、`test_worst_guard_pass_rate`

- [x] **Step 2: 实现 ablation builder**

Builder 从每个 split salt 的 hierarchical calibration task result 中读取：

- `heldout_loss_by_method`
- `heldout_worst_loss_by_method`
- `test_loss_by_method`
- `test_worst_loss_by_method`
- `constrained_selection.selected_method_id`

并解析 method id：

- `lcdu_hierarchical_global_k_*`
- `lcdu_hierarchical_party_k_*`
- `lcdu_hierarchical_income_k_*`
- `lcdu_hierarchical_neighbor_k_*`

- [x] **Step 3: 生成正式 ablation artifact**

```bash
python experiments/lcdu_anes_hierarchical_ablation_matrix.py
```

- [x] **Step 4: 验证**

```bash
pytest tests/test_lcdu_anes_hierarchical_ablation_matrix.py -q
pytest tests/test_lcdu_anes_hierarchical_calibration_matrix.py tests/test_lcdu_anes_split_repeat_robustness_matrix.py tests/test_lcdu_anes_hierarchical_ablation_matrix.py -q
```

## Self-Review

- Spec coverage: 覆盖 split/repeat 稳健性、weighted win、worst guard、失败类型。
- Placeholder scan: 无占位内容。
- Type consistency: `split_salts`、`k_grid`、`max_worst_segment_delta` 在 builder/CLI/test 中一致。
