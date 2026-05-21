# LCDU 内部泛化第一阶段 TODO

**日期：** 2026-05-21

**范围：** 只做同任务内的 `segment granularity` 外推脚手架，不做新一轮大规模候选搜索。

## 1. 目标

把当前 `LCDU L3` 的研究证据，从“4 个固定 segment 上成立”，推进到“能够在同一政策任务下，用更细 demographic 轴做对齐评估”。

本阶段不回答方法是否已经广义通用，只回答一个更窄的问题：

> 官方观测分布和 Product 侧 cohort 输出，能否在 alternate segment schema 上对齐评估。

## 2. 本轮 TODO

1. 新增官方 `axis-level` ingestion artifact
   - 目标：把 HTOPS/HPS public ingestion 聚合到 Product 兼容的 demographic axis schema
   - 当前结果：已完成
   - 产出：
     - `/Users/dm/Documents/cc-社会计算器-worktrees/research/experiments/policy_reaction_axis_ingestion.py`
     - `policy-reaction-htops-2506-public-axis-ingestion-001.json`

2. 新增 `axis-level` benchmark
   - 目标：让 Research 可以直接在 alternate segment schema 上比较官方 observed 分布与 Product 预测分布
   - 当前结果：已完成
   - 产出：
     - `/Users/dm/Documents/cc-社会计算器-worktrees/research/experiments/policy_reaction_axis_benchmark.py`
     - `policy-reaction-axis-benchmark-lcdu-l3-h02-001.json`
     - `policy-reaction-axis-benchmark-lcdu-l3-i01-001.json`

3. 复用 Product 现有 `segment_policy_report` 作为预测端输入
   - 目标：不改 Product 契约，直接把现有 cohort 输出桥接到 axis-level benchmark
   - 当前结果：已完成
   - 产出：
     - `segment-policy-report-lcdu-l3-h02-001.json`
     - `segment-policy-report-lcdu-l3-i01-001.json`

4. 补测试和最小写盘验证
   - 目标：确认桥接层可以稳定生成 strict JSON，并在缺失 axis segment 时进入 blocked 状态
   - 当前结果：已完成
   - 产出：
     - `/Users/dm/Documents/cc-社会计算器-worktrees/research/tests/test_policy_reaction_axis_ingestion.py`
     - `/Users/dm/Documents/cc-社会计算器-worktrees/research/tests/test_policy_reaction_axis_benchmark.py`

## 3. 实现路径

### 3.1 官方侧

从现有 HTOPS/HPS public ingestion 复用同一套归一化逻辑，额外输出按以下轴聚合的 observed policy reaction：

- `income_band`
- `employment_status`
- `household_with_children`
- `food_sufficiency_status`
- `price_stress_level`

聚合键统一写成：

- `income_band=low`
- `employment_status=retired`

这样可以直接对齐 Product 侧 `segment_policy_report` 的 `segments` 键。

### 3.2 Product 侧

本轮不改 Product 代码，直接复用已有：

- `/Users/dm/Documents/cc-社会计算器-worktrees/product/src/crowdmirror/reports/segment_policy_report.py`

也就是把 Product 当作已满足输入契约的一端，Research 只补桥接评估层。

### 3.3 Benchmark 侧

新增一个 `axis-level` benchmark，输入：

1. 官方 `axis ingestion artifact`
2. Product `segment policy report`

输出：

- coverage
- matched axis-segment count
- weighted / mean JSD
- rank correlation
- per-axis-segment metrics

## 4. 测试方案

### 4.1 单元测试

至少覆盖：

1. axis ingestion 能从最小 PUF 行聚合出多个 axis segment
2. axis benchmark 能对齐 ingestion 和 segment report
3. 缺失 axis segment 时会正确进入 blocked 状态
4. 写盘结果是 strict JSON

### 4.2 本轮验证命令

至少运行：

```bash
pytest research/tests/test_policy_reaction_axis_ingestion.py
pytest research/tests/test_policy_reaction_axis_benchmark.py
```

如果实现涉及公共 helper，再补相关 targeted tests。

## 5. 验收标准

本轮完成的验收标准是：

1. Research 侧新增 `axis ingestion` 与 `axis benchmark` 两个脚本
2. 两者都能生成 strict JSON artifact
3. benchmark 能直接消费 Product 现有 `segment policy report`
4. targeted tests 通过
5. 不修改 `LCDU L3` 主候选结论，也不伪装成“已经证明泛化”

### 当前验收结果

已满足。

- 真实 public axis ingestion 已生成：
  `policy-reaction-htops-2506-public-axis-ingestion-001`
- 真实 Product segment report 已生成：
  - `segment-policy-report-lcdu-l3-h02-001`
  - `segment-policy-report-lcdu-l3-i01-001`
- 真实 axis benchmark 已生成：
  - `policy-reaction-axis-benchmark-lcdu-l3-h02-001`
  - `policy-reaction-axis-benchmark-lcdu-l3-i01-001`
- targeted tests：
  - `test_policy_reaction_axis_ingestion.py`
  - `test_policy_reaction_axis_benchmark.py`
  - `test_policy_reaction_official_benchmark.py`
  全部通过

### 当前结果摘要

这轮完成的是“桥接层成立”，不是“泛化已经成立”。

- `h02` axis benchmark:
  - `coverage_rate = 1.0`
  - `matched_segment_count = 14`
  - `weighted_choice_distribution_jsd = 0.009779743208737248`
  - `segment_rank_correlation = 0.5`
- `i01` axis benchmark:
  - `coverage_rate = 1.0`
  - `matched_segment_count = 14`
  - `weighted_choice_distribution_jsd = 0.009715886100179951`
  - `segment_rank_correlation = 0.5`

说明：

1. alternate segment schema 的数据契约已经打通；
2. `h02` / `i01` 在 axis-level 上并非完全失配，但也没有出现足够强的排序稳定性；
3. 这一步更适合作为“内部泛化诊断入口”，而不是“已经证明通用性”的证据。

## 6. 止损标准

如果发现以下任一情况，本轮就停：

1. 官方 public ingestion 无法稳定映射到 Product 的 axis schema
2. 需要重写 Product 输出契约才能对齐
3. 需要引入新的 task-specific 手工规则才能跑通

出现这些情况时，应先回到数据契约设计，而不是继续扩实验。
