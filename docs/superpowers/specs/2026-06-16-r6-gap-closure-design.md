# R6.2 Gap Closure 中文 Spec

## 1. 当前基线

截至 `2026-06-16`，R6 已完成机制驱动 MVP 第一轮。当前结论是：

- Research 状态：`mechanism_research_diagnostic_only`
- CCF-A 主贡献：`ccf_a_main_contribution_ready=false`
- Product runtime default：`runtime_default_allowed=false`
- Product guard：已保留并扩展，当前 7 张 evidence cards 能展示 claim boundary

这说明 R6 已有可审计证据链，但还没有完成四类关键 gap：

1. 独立 holdout / field outcome gap
2. behavioral update operator 泛化 gap
3. 理论定义 gap
4. Product 市场说服链路 gap

R6.2 的目标不是用当前 3 个 public proxy 强行宣布方法成立，而是把这四类 gap 改造成可计算、可阻断、可复现的研发闭环。

## 2. 总目标

R6.2 要建立一套 gap closure 体系：

```text
Formal R6 Theory
  -> Outcome / Holdout Registry
  -> Behavioral Update Operator v2
  -> Gap Closure Report
  -> Product Evidence Guard
```

每个 gap 必须有明确状态：

- `closed_by_artifact`: 已由形式化 artifact 或可复现实验关闭
- `partial_diagnostic`: 有诊断证据，但不足以通过泛化验证
- `blocked_missing_data`: 缺少独立 holdout 或 field outcome
- `blocked_guard_failed`: Product 或 runtime guard 未通过

任何 gap 只有在证据满足 gate 后才能升级。没有独立 holdout 或 field outcome 时，系统必须继续阻断准确性优越、field validated、runtime default 三类声明。

## 3. 理论定义

### 3.1 形式化问题

R6 的核心问题定义为：

```text
Given:
  P0(y | x, g): static prior over responses for segment g
  G = (V, E): segment-level or cohort-level exposure graph
  M_theta: mechanism propagation operator
  O: public proxy or field outcome observation
  C: product and research guard context

Learn / evaluate:
  U_phi(P0, M_theta, O, C) -> candidate behavioral update

Subject to:
  static prior is the simulation foundation,
  interaction is a risk-discovery layer,
  candidate updates are blocked until holdout / field validation passes.
```

这里的研究目标不是简单最大化预测准确率，而是验证：

1. 交互机制是否产生静态先验无法表达的动态风险路径；
2. 这些风险路径是否能发现静态先验漏报；
3. 真实 outcome 回来后，系统是否能把误差归因到机制组件；
4. candidate update 是否能在独立 holdout 上 non-regression；
5. Product 是否始终保留 claim boundary。

### 3.2 风险发现价值函数

R6.2 使用风险发现价值函数约束方法优化：

```text
V = recovered_static_prior_miss
    - false_alarm_penalty
    - guard_violation_penalty
    - overfit_penalty
```

其中：

- `recovered_static_prior_miss`: 交互层发现静态先验漏报的数量或权重
- `false_alarm_penalty`: 交互层制造但 outcome 不支持的风险信号
- `guard_violation_penalty`: 任何未验证却进入 Product/runtime 的声明
- `overfit_penalty`: same-case 改善但 holdout 不成立的候选更新

这使 R6 的优化目标从“单次准确率更高”转向“可审计风险发现 + 可阻断更新 + 可学习失败边界”。

### 3.3 误差归因

outcome error 必须被拆成机制组件：

```text
error =
  static_prior_miss
  + propagation_direction_error
  + over_amplification
  + under_diffusion
  + topology_mismatch
  + outcome_mapping_noise
```

只有当误差能被归因到机制组件时，才允许生成 behavioral update candidate。若误差主要来自 mapping noise 或缺少独立 outcome，candidate 必须保持 `diagnostic_only` 或 `blocked_missing_data`。

## 4. 四条 Gap Closure 线

### 4.1 Theory Gap Closure

新增 theory artifact，把问题定义、变量、价值函数、gate 和 blocked claims 固化成机器可读结构。

验收标准：

- 有 `r6-theory-framework-v1` schema。
- 显式定义 static prior、interaction mechanism、behavioral update operator、risk discovery value、guard constraints。
- CCF-A readiness 能引用该 artifact。
- 只能关闭“理论定义缺失”这一项，不能因此关闭 empirical validation gap。

### 4.2 Outcome / Holdout Gap Closure

新增 outcome / holdout registry，管理当前所有 public proxy、候选公开数据、真实 field outcome 和缺失槽位。

registry 必须区分：

- `field_outcome`
- `independent_public_proxy`
- `same_source_public_proxy`
- `source_case_proxy`
- `missing_required_slot`

验收标准：

- 当前 HTOPS / ANES health / ANES climate 的独立性状态可计算。
- 至少列出三个缺失槽位：
  - independent same-family in-condition holdout
  - independent supported signal holdout
  - real field outcome
- 缺失槽位必须进入 evidence report remaining gaps。
- 不允许把同源或 out-of-condition proxy 当作 independent holdout。

### 4.3 Behavioral Update Operator v2

v2 不是 prompt patch，也不是单一 damping rule。它要把 outcome error 映射到结构化机制更新：

| 组件 | 可更新参数 |
| --- | --- |
| susceptibility | segment 对价格、权益、规则、服务中断的敏感度 |
| influence_weight | peer、机构、媒体、专家信号权重 |
| activation_threshold | 风险从观望到拒绝、投诉、流失的触发门槛 |
| memory_decay | 负面体验或补偿记忆的持续时间 |
| trust_modifier | 信任状态对传播放大/抑制的影响 |
| damping_rule | 静态先验已很确定时的交互过冲限制 |

验收标准：

- 每个 candidate update 必须包含 error attribution、operator family、target segment、parameter delta、transfer preconditions、blocked reason。
- v2 必须明确区分 `same_case_repair` 和 `transfer_candidate`。
- 没有独立 holdout 时，所有 candidate 继续 `runtime_default_allowed=false`。
- operator v2 可以关闭“prompt/persona 手工调参”gap，但不能关闭泛化 gap。

### 4.4 Product Gap Closure

Product 侧要把 gap 状态展示为客户可理解的证据链，而不是只显示 Research artifact。

新增或扩展 Product evidence cards：

- theory boundary card：说明 R6 方法目标和不能宣称的内容。
- holdout/data gap card：说明缺什么数据才能验证。
- operator v2 card：说明候选更新为何被阻断。
- field outcome learning card：说明真实结果回来后如何更新。

验收标准：

- Product card 必须继续包含 `claim_status`、`allowed_claims`、`blocked_claims`、`source_artifact_ids`。
- `static_narrative_fallback_allowed=false` 保持不变。
- blocked claims 必须包含 field validation、accuracy superiority、automatic runtime update。

## 5. R6.2 状态判定

R6.2 输出一个 gap closure report，整体状态只允许以下四类：

- `gap_closure_artifact_ready`: 理论、registry、operator v2、Product guard 都接入，但仍有 data gap。
- `gap_closure_partial`: 有部分 artifact 接入，但关键 gate 未闭合。
- `gap_closure_blocked_missing_data`: 主要阻断来自缺少独立 holdout / field outcome。
- `gap_closure_failed_guard`: 出现 Product guard 或 runtime guard 破坏。

当前预期目标是 `gap_closure_artifact_ready`。这代表“gap 已被结构化管理”，不代表“Research 已通过 CCF-A 主贡献验证”。

## 6. 验收标准

R6.2 第一阶段完成后，必须满足：

1. `formal_problem_definition_present=true`
2. `risk_discovery_value_defined=true`
3. `holdout_registry_present=true`
4. `independent_holdout_missing_slots_visible=true`
5. `operator_v2_structured=true`
6. `operator_v2_runtime_default_allowed=false`
7. `gap_closure_report_present=true`
8. `product_gap_cards_present=true`
9. `ccf_a_main_contribution_ready=false`
10. `field_outcome_validated=false`

这些验收标准允许关闭“定义不清”和“证据链不可审计”两类 gap，但不允许关闭“泛化验证”和“真实 outcome”两类 gap。

## 7. 止损条件

若出现以下任一情况，R6.2 不应继续包装成 Research 主贡献：

1. operator v2 只能复述 v1 damping rule，没有新增 error attribution。
2. registry 无法区分 independent holdout 与 same-source proxy。
3. Product evidence cards 为了展示正向结论而删除 blocked claims。
4. gap closure report 把 missing data 写成 passed。
5. 新增 artifact 不能被 pytest 和 CLI smoke 稳定复现。

止损时，R6.2 降级为 Product evidence governance 和 Research 负结果资产。

## 8. 第一阶段交付物

第一阶段只实现结构化 gap closure，不承诺找到新外部数据。

交付物：

1. `experiments/r6_theory_framework.py`
2. `experiments/r6_outcome_holdout_registry.py`
3. `experiments/r6_behavioral_update_operator_v2.py`
4. `experiments/r6_gap_closure_report.py`
5. Product evidence cards / evidence report 的 gap closure ingestion
6. 对应 pytest 和 CLI smoke
7. `docs/CURRENT_STATE.md` 更新

第一阶段完成后，项目状态应从“gap 模糊存在”推进到“gap 可计算、可审计、可阻断”。
