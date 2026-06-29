# LCDU-hybrid v2 Effect Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 LCDU-hybrid 从“数值平齐 deterministic anchor 的可审计框架”推进为“在稀疏 segment 与跨任务 split 上可稳定超过原始 anchor 的层级可靠性校准算法”。

**Architecture:** 新增一个独立的 ANES 层级校准实验 artifact，不改写既有 baseline/hybrid artifact 的历史语义。算法从 calibration split 生成候选分布，在 heldout split 选择候选，并只在 test split 报告最终 claim，避免 test peeking。

**Tech Stack:** Python 标准库、现有 `experiments/lcdu_anes_cross_task_validation.py` 的 JSD/loss 工具、pytest、JSON artifact。

---

## 背景判断

当前证据链显示：

- LCDU-soft 在 ANES 两个政策任务上未超过 deterministic anchor。
- LCDU-hybrid strict-copy 能把 LLM 输出修复到 deterministic anchor 数值平齐，但不能证明 accuracy win。
- 因此，继续调 prompt 不是最高优先级；需要增强“数值校准器”本身。

本阶段方法命名为 **LCDU-hybrid v2 / hierarchical reliability calibration**。

核心思想：

1. deterministic anchor 是每个 segment 的 calibration 经验分布。
2. 当 segment 样本小或噪声大时，直接复制经验分布容易过拟合。
3. v2 对每个 segment 做自适应收缩：样本越小，越向更高层 prior 或相似 segment prior 收缩；样本越大，越保留本 segment anchor。
4. 相似 segment prior 暂用可解释的结构化语义检索：共享 `party_or_ideology`、共享 `income`、或共享任一轴的邻域。

## 算法定义

对任务 `t`、segment `s`、政策选项 `y`：

- 原始 anchor：`p_anchor(y|s)`，来自 calibration split 的 segment 经验分布。
- 全局 prior：`p_global(y)`，来自 calibration split 的总体分布。
- 邻域 prior：`p_neighbor(y|s)`，来自与 `s` 共享结构轴的其他 segments。
- 样本量权重：`alpha_s = n_s / (n_s + k)`。
- 层级候选：`p_v2(y|s) = alpha_s * p_anchor(y|s) + (1 - alpha_s) * p_prior(y|s)`。

候选族：

- `lcdu_hierarchical_global_k_{k}`：向总体 prior 收缩。
- `lcdu_hierarchical_party_k_{k}`：向同 party/ideology 邻域收缩。
- `lcdu_hierarchical_income_k_{k}`：向同 income 邻域收缩。
- `lcdu_hierarchical_neighbor_k_{k}`：向共享任一结构轴的邻域收缩。

默认 `k_grid = [0.5, 1, 2, 5, 10, 20, 50]`。

选择规则：

- calibration split：生成候选。
- heldout split：选择 weighted JSD 最低候选。
- test split：报告最终 loss、相对 deterministic anchor 的 delta、worst segment delta。

## 文件结构

- Create: `experiments/lcdu_anes_hierarchical_calibration_matrix.py`
  - 构建 LCDU-hybrid v2 层级可靠性校准 artifact。
  - 复用现有 `_weighted_segment_jsd`、`_worst_segment_jsd` 和 `_mix_probabilities`。
  - 输出 strict JSON，保留 split gate 与 claim boundary。

- Create: `tests/test_lcdu_anes_hierarchical_calibration_matrix.py`
  - 覆盖候选生成、heldout 选择、test 不偷看、CLI 写 artifact。
  - 使用合成 microdata artifact 验证层级收缩能超过原始 anchor。

- Optional later Modify: `experiments/lcdu_anes_strong_baseline_matrix.py`
  - 本轮先不改强基线矩阵，避免污染既有判断。
  - 下一轮若 v2 artifact 通过，再作为新 LCDU method 输入 strong baseline。

## 验收标准

硬性验收：

- `pytest tests/test_lcdu_anes_hierarchical_calibration_matrix.py -q` 通过。
- `python experiments/lcdu_anes_hierarchical_calibration_matrix.py` 能基于当前 ANES microdata artifact 写出结果。
- artifact 必须包含：
  - `schema_version`
  - `candidate_generation_split=calibration`
  - `candidate_acceptance_split=heldout`
  - `final_claim_check_split=test`
  - `test_anchor_loss`
  - `test_final_loss`
  - `test_loss_delta_vs_anchor`
  - `beats_deterministic_anchor`
  - `risk_flags`
  - `claim_boundary`

研究验收：

- 如果两个 ANES 任务均 `beats_deterministic_anchor=true`，则进入下一阶段：把 v2 纳入 strong baseline / paper gate。
- 如果只部分任务胜出，结论为 `hierarchical_lcdu_signal_mixed`，继续扩 task/schema/seed。
- 如果没有任务胜出，结论为 `hierarchical_lcdu_not_leading`，停止把该方法包装成 accuracy 改进，转向 auditability/counterfactual 或新方法。

产品验收：

- artifact 能解释每个任务选择了哪个 prior family 与 `k`。
- artifact 能给出 worst segment 改善或退化，支撑后续 cohort report 的可信度说明。

## Task 1: 新增测试

**Files:**
- Create: `tests/test_lcdu_anes_hierarchical_calibration_matrix.py`

- [ ] **Step 1: 写 failing test**

测试必须构造一个 calibration anchor 在稀疏 segment 上过拟合、heldout/test 更接近 party-level prior 的合成 artifact。

Run:

```bash
pytest tests/test_lcdu_anes_hierarchical_calibration_matrix.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'experiments.lcdu_anes_hierarchical_calibration_matrix'
```

## Task 2: 新增层级校准实现

**Files:**
- Create: `experiments/lcdu_anes_hierarchical_calibration_matrix.py`

- [ ] **Step 1: 实现 artifact builder**

核心函数：

```python
def build_lcdu_anes_hierarchical_calibration_matrix(
    *,
    microdata_artifact: dict[str, Any],
    artifact_id: str,
    k_grid: list[float] | None = None,
) -> dict[str, Any]:
    ...
```

必须生成候选、按 heldout 选择、在 test 报告效果。

- [ ] **Step 2: 实现 CLI**

Run:

```bash
python experiments/lcdu_anes_hierarchical_calibration_matrix.py \
  --microdata-artifact experiments/results/lcdu_public_task_microdata/lcdu-anes-2024-sda-public-microdata-001.json \
  --output experiments/results/lcdu_hierarchical_calibration/lcdu-anes-hierarchical-calibration-current-001.json \
  --artifact-id lcdu-anes-hierarchical-calibration-current-001
```

Expected stdout contains:

```json
{"artifact_id":"lcdu-anes-hierarchical-calibration-current-001","task_count":2}
```

## Task 3: 运行当前 artifact 并记录结论

**Files:**
- Create: `experiments/results/lcdu_hierarchical_calibration/lcdu-anes-hierarchical-calibration-current-001.json`

- [ ] **Step 1: 运行正式实验**

Run:

```bash
python experiments/lcdu_anes_hierarchical_calibration_matrix.py
```

- [ ] **Step 2: 检查结果**

确认每个任务都有：

- heldout selected method
- test loss
- deterministic anchor loss
- delta vs anchor
- worst segment delta

## Task 4: 定向验证

**Files:**
- Test: `tests/test_lcdu_anes_hierarchical_calibration_matrix.py`
- Test: related existing LCDU tests only when import contracts change.

- [ ] **Step 1: 跑新增测试**

```bash
pytest tests/test_lcdu_anes_hierarchical_calibration_matrix.py -q
```

- [ ] **Step 2: 跑相邻测试**

```bash
pytest tests/test_lcdu_anes_cross_task_validation.py tests/test_lcdu_anes_strong_baseline_matrix.py tests/test_lcdu_anes_hybrid_method_validation.py tests/test_lcdu_anes_hierarchical_calibration_matrix.py -q
```

- [ ] **Step 3: 检查格式**

```bash
git diff --check
```

## Self-Review

- Spec coverage: 已覆盖数值效果提升、split gate、baseline 对比、产品解释字段。
- Placeholder scan: 无 TBD、TODO、implement later。
- Type consistency: 新 artifact 只依赖现有 microdata artifact schema，不修改既有 schema。
