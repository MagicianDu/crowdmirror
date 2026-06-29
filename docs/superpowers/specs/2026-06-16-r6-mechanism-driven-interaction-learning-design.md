# R6 机制驱动交互学习 Spec

## 1. 背景判断

截至 `2026-06-16`，R6 已经完成一轮风险发现方法验收：

- `decision-value metrics` 已可计算，但当前是 `decision_value_partial_high_false_alarm`。
- `risk-discovery holdout validation` 当前未通过。
- `Interaction Signal Validity Score` 产生了一个 source-supported 正向信号，但 holdout validation 结果是 `passed_holdout_count=0`、`contradicted_holdout_count=2`。
- 当前 scoring candidate 不能作为 CCF-A 主贡献算法，也不能进入 Product runtime default。

这不是 R6 问题定义失败，而是说明当前方法层不够强。后续 Research 不应继续围绕阈值、post-hoc score、prompt/persona patch 或单一 proxy 小修小补推进。R6 下一阶段要转向：

> 机制驱动的交互传播 + 可学习 behavioral update operator + 更真实 outcome 验证。

Product 侧已形成的 failure diagnosis、false-alarm gate、claim boundary、evidence cards 必须保留，作为新研究方法的外层可信护栏。

## 2. 新阶段目标

### 2.1 Research 目标

构建一个可以冲击 CCF-A 主贡献的 R6 方法候选：

```text
Static Prior
  -> Mechanism-Driven Interaction Propagation
  -> Behavioral Update Operator
  -> Outcome-Feedback Learning
  -> Guarded Deployment Decision
```

核心问题从“交互结果是否整体比静态先验更准”改为：

> 在强静态先验已经存在的情况下，显式建模人群交互传播机制，是否能发现静态先验无法表达的动态风险路径，并在 outcome 回流后学习可迁移的行为更新规则。

### 2.2 Product 目标

Product 不跟随 Research 新方法冒进。Product 要保留并强化：

1. 当前风险信号是否只是 diagnostic；
2. 是否有 holdout 或 field outcome 支持；
3. false alarm 来源是什么；
4. 哪些候选更新被阻断；
5. 面向客户可以说什么、不能说什么。

Product 的核心竞争力不是“永远预测准”，而是：

> 在发布前给出可审计风险假设，在发布后用真实结果解释失败边界，并阻断未经验证的自动更新。

## 3. 非目标

下一阶段不做以下事情：

1. 不把当前 Interaction Signal Validity Score 继续包装成主算法。
2. 不继续靠阈值调参降低 false alarm。
3. 不把 TextGrad、DSPy、GA、prompt/persona patch 作为主研究对象。
4. 不把单一垂直场景做成方法本体。
5. 不因为某个 same-case outcome feedback 有改善，就开放 runtime default。

## 4. 方法设计

### 4.1 交互传播机制

当前 R6 的交互层更接近风险偏移报告，缺少真实传播过程。新方法必须引入显式传播状态：

```text
agent_state_t = {
  static_prior,
  exposure_state_t,
  memory_state_t,
  peer_signal_t,
  institutional_signal_t,
  decision_state_t
}
```

传播机制至少包含：

| 组件 | 作用 |
| --- | --- |
| `exposure_graph` | 谁会影响谁，可以是 segment-level 或 cohort-level 图 |
| `influence_kernel` | 不同关系、身份、信任、利益冲突下的影响强度 |
| `memory_state` | 过去暴露、负面体验、价格敏感、权益感知的累积 |
| `activation_rule` | 什么时候从低关注变成高风险反应 |
| `decay_rule` | 风险感知如何衰减或被新信息覆盖 |

Research 要证明交互传播不是静态先验的重复表达，而是产生了可审计的动态路径，例如：

- 风险从一个高敏感 segment 扩散到相邻 segment；
- 小比例高影响群体改变整体风险排序；
- 多轮暴露后出现静态先验无法表达的阈值效应；
- 同一政策在不同网络结构下出现不同传播结果。

### 4.2 Behavioral Update Operator

outcome 回流后，系统不能人工改 prompt，也不能只调后处理阈值。需要学习一个结构化行为更新算子：

```text
U_phi:
  (static_prior, mechanism_trace, outcome_error, guard_context)
  -> candidate_operator_update
```

更新对象不是自然语言 prompt，而是机制参数或结构：

| 更新对象 | 示例 |
| --- | --- |
| `susceptibility` | 某类 segment 对价格、权益、规则变化的敏感度 |
| `influence_weight` | peer、机构、媒体、专家信号的相对权重 |
| `activation_threshold` | 从观望到反对、流失、投诉的触发门槛 |
| `memory_decay` | 负面感知或正面补偿的持续时间 |
| `trust_modifier` | 不同信任状态对交互传播的放大或抑制 |
| `cap_or_damping_rule` | 静态先验已很确定时，限制交互过度放大 |

每个 candidate update 必须携带：

- 更新前后的机制差异；
- 对哪些 segment 生效；
- 从哪个 outcome error 推导；
- 预期修复的失败边界；
- 可能带来的新 false alarm；
- 是否通过 holdout / guard。

### 4.3 Outcome-Feedback Learning

新阶段的学习目标不是直接最小化 aggregate error，而是做误差归因：

```text
error = static_prior_miss
      + propagation_miss
      + over_amplification
      + under_diffusion
      + mapping_noise
```

系统要区分：

1. 静态先验本身漏报；
2. 交互传播方向正确但强度过大；
3. 交互传播方向错误；
4. 传播拓扑不合理；
5. public proxy 或 field outcome 与真实目标不一致。

只有当 outcome error 能被稳定归因到机制组件时，才允许生成 candidate operator update。

### 4.4 Product Guard 保留

现有 Product 诊断能力保留为所有新方法的外层验收：

```text
new_method_candidate
  -> decision-value metrics
  -> holdout validation
  -> false-alarm diagnosis
  -> claim boundary
  -> evidence cards
```

Product 展示必须继续区分：

- `supported_signal`
- `diagnostic_only`
- `rejected_false_alarm`
- `blocked_update`
- `runtime_default_allowed`

Research 换方法不改变 Product 的可信边界。

## 5. Artifact 合同

下一阶段新增 artifact 应使用 `r6_` 前缀，并与既有报告链路兼容。

建议新增：

1. `r6_mechanism_propagation_trace.py`
   - 输出 `r6-mechanism-propagation-trace-v1`
   - 记录 exposure graph、传播轮次、segment state、risk diffusion path。

2. `r6_behavioral_update_operator.py`
   - 输出 `r6-behavioral-update-operator-v1`
   - 从 outcome error 生成结构化 candidate operator update。

3. `r6_mechanism_ablation_report.py`
   - 输出 `r6-mechanism-ablation-report-v1`
   - 比较 static prior、无传播交互、随机传播、机制传播、反馈更新后传播。

4. `r6_operator_holdout_validation.py`
   - 输出 `r6-operator-holdout-validation-v1`
   - 验证 operator update 是否跨 case / same-family holdout 有效。

5. `r6_mechanism_research_readiness_report.py`
   - 输出 `r6-mechanism-research-readiness-report-v1`
   - 汇总是否具备 CCF-A 主贡献继续投入价值。

Product 侧已有 evidence cards 不新起炉灶，只扩展 ingestion：

- ingest propagation trace summary；
- ingest update operator decision；
- ingest false alarm and blocked update reason；
- preserve allowed / blocked claims。

## 6. 验收指标

### 6.1 Research Gate

新方法至少要满足以下 gate，才算出现正向研究信号：

| Gate | 验收标准 |
| --- | --- |
| `mechanism_trace_present` | 每个 case 有可审计传播 trace，不只是 aggregate score |
| `dynamic_path_distinct_from_static_prior` | 至少一个风险路径无法由静态先验直接表达 |
| `mechanism_ablation_positive` | 机制传播优于 no-propagation / random-propagation baseline |
| `operator_update_structured` | outcome feedback 产生结构化机制更新，不是 prompt patch |
| `operator_holdout_non_regression` | candidate update 在 holdout 上不伤害静态先验底座 |
| `false_alarm_not_hidden` | false alarm 必须被报告，不能被平均指标掩盖 |
| `product_guard_preserved` | Product evidence cards 仍能显示 claim boundary |

### 6.2 CCF-A 候选 Gate

要重新成为 CCF-A 主贡献候选，至少需要：

1. 形式化传播状态、更新算子和验收目标；
2. 至少两类不同 case family 的机制传播验证；
3. 强 baseline 对比，包括 static prior、random propagation、no-propagation interaction、post-hoc scoring；
4. holdout 或 field outcome 证明 operator update 不是 same-case overfit；
5. 失败边界和止损条件清晰；
6. Product 侧不能展示超出证据的准确性声明。

## 7. 止损条件

以下任一情况成立，应停止把该方法作为 CCF-A 主贡献推进：

1. 机制传播 trace 不能产生区别于静态先验的动态路径；
2. 机制传播只在 source case 有效，holdout 全部退化；
3. behavioral update operator 只能修复 same-case，不能跨 case non-regression；
4. false alarm 下降依赖 case/source 标签记忆；
5. Product guard 被迫放宽才能展示正向结论；
6. 新方法的复杂度明显增加，但 decision value 没有超过当前 R6 diagnostic baseline。

如果触发止损，Research 降级为负结果和方法诊断资产；Product 保留 failure diagnosis / guarded evidence capability。

## 8. 第一轮实现计划边界

第一轮只做 MVP，不追求一次证明 CCF-A：

1. 设计 segment-level exposure graph 和 propagation trace schema。
2. 在现有 3 个 public proxy fixture 上生成机制传播 trace。
3. 增加 no-propagation、random-propagation、mechanism-propagation 三个 baseline。
4. 生成第一版 behavioral update candidate，但默认 `runtime_default_allowed=false`。
5. 把 propagation / update summary 接入 Product evidence cards。
6. 用现有 gates 复核：decision value、holdout、false alarm、claim boundary。

第一轮验收结论只允许三种：

- `positive_signal`: 机制传播带来区别于静态先验的风险路径，并且没有破坏 Product guard；
- `diagnostic_only`: trace 有解释力，但 holdout / false alarm 仍未过；
- `stop_loss`: 机制传播没有新增信息或只增加复杂度。

## 9. 与 Product 的关系

Product 保留当前能力，并围绕新 Research 方法增加两类说明：

1. 风险传播叙事：展示风险如何从源 segment 传播到其他 cohort。
2. 更新阻断叙事：展示 outcome feedback 为什么生成候选更新，以及为什么暂不进入 runtime default。

Product 不承诺：

- 交互仿真一定更准；
- 新机制已经 field validated；
- blocked update 可以自动上线；
- public proxy 等价于真实客户行为。

Product 可以承诺：

- 风险假设可审计；
- false alarm 可诊断；
- 更新决策有证据边界；
- Research 失败不会污染 runtime default。

## 10. 当前结论

当前 R6 scoring candidate 已经不适合作为主贡献继续优化。R6 下一阶段值得继续的理由是：

1. 问题定义仍成立：强静态先验缺少交互传播和结果反馈学习。
2. Product guard 已经形成可信边界，可以保护新方法探索不被包装成过度声明。
3. Research 若要形成壁垒，必须从 post-hoc scoring 转向机制传播和结构化更新算子。

因此下一阶段主线是：

> Research 探索机制驱动交互学习；Product 保留并强化可审计诊断与 claim boundary。
