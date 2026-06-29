# R9 证据约束交互世界模型 Spec

## 1. 背景判断

当前项目的 Product 定位已经明确：

> 人群反应趋势与风险区间模拟器。

这意味着产品不承诺精确预测单点结果，而是提供：

1. 趋势方向。
2. 可信数值区间。
3. 风险分布。
4. 异常群体。
5. 机制解释。
6. 真实结果回流后的复盘与更新。

R6 到 R8 已经完成了证据链、Product guard、failure diagnosis、outcome replay 和多轮方法探索，但当前 Research 方法仍不足以全面支撑 Product 核心价值。

R8 的 stop-loss 结论是：

- `research_decision=keep_r8_as_diagnostic_asset`
- `not_beating_fixed_rule_baseline`
- `insufficient_metric_dominance`
- `l1_l2_gate_blocked`
- `field_customer_outcome_missing`
- `runtime_default_guard_blocked`

这说明当前问题不是报告包装不足，也不是测试链路不完整，而是方法本体还不够强。继续在 R8 上做局部 patch、score 调参、prompt/persona 调优或固定规则修补，预期收益不高。

R9 的目标是重启方法层创新，但保留 R6/R8 已经形成的 Product guard 和失败诊断能力。

## 2. R9 总目标

R9 的目标不是重新追求“点预测击败静态先验”，而是回答一个更贴近产品价值的问题：

> 在强静态先验存在的情况下，能否通过外部证据、机制学习和交互传播，稳定提升趋势判断、区间校准、风险排序、异常群体识别和决策价值，并在不可靠时自动降级为诊断输出。

R9 要支撑 Product 的核心价值，需要做到四点：

1. **可发现**：发现静态先验看不到的二阶风险、局部异常和交互放大。
2. **可约束**：所有风险信号必须被外部证据、机制约束或 holdout guard 约束。
3. **可复盘**：真实 outcome 回来后，系统能解释错在哪里，并生成受约束更新。
4. **可降级**：方法不可靠时，不污染 Product runtime，只进入 failure diagnosis 和 replay。

R9 的最低成功标准不是“所有指标都赢”，而是形成一个比 R8 更强、更可迁移、更可验证的 Research 方法候选，并明确它是否值得继续成为 Product core method 的基础。

## 3. R8 暴露的底层问题

R8 失败不是单一 bug，而是三个结构性问题叠加。

### 3.1 数据证据太弱

当前主要依赖少量 public proxy fixture。它们可以支持诊断和 smoke validation，但不足以证明方法泛化。

具体表现：

1. case 数量太少，容易被固定规则记住。
2. public proxy 与真实业务 outcome 仍有距离。
3. 缺少同 family、同触发条件、独立 outcome 的 holdout。
4. 缺少 segment-level outcome label。

### 3.2 方法学习太浅

R8 名义上是可学习机制算子，但实际正向信号仍没有稳定超过固定规则 baseline。

具体表现：

1. 机制激活和传播边权没有形成可靠迁移。
2. false alarm 与 missed risk 无法同时稳定控制。
3. outcome 回流后的更新候选仍被 guard 阻断。
4. 学习目标没有足够外部证据约束，容易变成当前 fixture 校准。

### 3.3 交互仿真不够真实

Product 价值依赖人群交互，但当前方法更多是结构化风险偏移和后验诊断，交互传播还没有成为真正的主引擎。

具体表现：

1. 人群节点缺少持续状态、记忆和影响历史。
2. 交互图更多是参数表，不是动态传播过程。
3. LLM 或 agent 尚未稳定参与机制生成、异常发现和反事实解释。
4. 多轮传播没有形成可审计的机制轨迹和风险区间贡献。

## 4. R9 核心方法：证据约束交互世界模型

R9 的主方法命名为：

> 证据约束交互世界模型。

它不是单一算法，而是一个组合式方法框架：

```text
静态先验
  + 外部相似案例证据
  + 机制因果算子
  + 多主体交互 rollout
  + 结果反馈校准
  + Product guard
  -> 趋势 / 区间 / 风险排序 / 异常群体 / 机制解释
```

核心原则：

1. 静态先验是底座，不是敌人。
2. 交互仿真负责发现静态先验无法表达的二阶风险。
3. 外部证据用于约束机制候选，避免模型自由发挥。
4. 多主体 rollout 用于生成机制假设和异常风险，不直接替代真实 outcome。
5. 最终输出必须经过校准、holdout、false-alarm gate 和 Product claim boundary。

## 5. 三条正交技术路线

R9 不再押注单点算法，而是并行推进三条尽量正交的技术路线。三条路线可以独立验证，也可以组合。

### 5.1 路线 A：证据约束机制算子

目标：

> 学习一个可迁移的机制更新算子，把 scenario shock、segment prior、mechanism graph 和 outcome residual 映射为受约束风险分布。

核心能力：

1. 机制激活学习。
2. 机制方向约束。
3. 传播边权学习。
4. 群体敏感度学习。
5. 区间校准。
6. false-alarm penalty。
7. non-regression guard。

方法形态：

```text
F_theta(static_prior, scenario_shock, mechanism_graph, interaction_graph)
  -> risk_distribution
  -> outcome_attribution
  -> bounded_update_candidate
```

R9 相比 R8 的区别：

1. 参数学习必须被外部证据约束，而不是只对当前 fixture 拟合。
2. 学习目标必须同时优化 trend、interval、ranking、false alarm 和 decision value。
3. 更新候选必须说明“改哪个机制、为什么改、会伤害什么指标”。

验收信号：

1. 相比 R8 在 false alarm 和 missed risk 上同时改善。
2. 相比 R7 v2 不只依赖固定规则。
3. 在 leave-one-case 或 perturbation 中保持 non-regression。
4. 失败时能生成可解释 attribution。

止损条件：

1. 不能超过 R7 v2 固定规则 baseline。
2. 只能通过记忆 case family 才能改善指标。
3. 更新候选持续被 runtime guard 阻断，且无法定位可修复机制。

### 5.2 路线 B：语义案例检索与先例约束

目标：

> 建立可审计的相似案例库，用历史政策、产品、价格、服务变更或公开调查 outcome 约束当前场景的机制候选和风险区间。

核心能力：

1. 场景语义解析。
2. 相似案例检索。
3. 机制先例抽取。
4. outcome proxy 对齐。
5. 证据强度评分。
6. 相似度驱动的区间校准。

方法形态：

```text
scenario
  -> semantic_query
  -> precedent_cases
  -> mechanism_prior
  -> calibrated_risk_interval
```

R9 相比旧路线的区别：

1. 不让 LLM 直接给预测值。
2. LLM 只负责结构化抽取候选机制、相似理由和证据字段。
3. 最终数值必须由可审计 case evidence 和 calibration rule 生成。
4. 检索失败时要显式降级为 low-evidence scenario。

验收信号：

1. 检索到的相似案例能提升机制选择质量。
2. 区间宽度随证据强度变化，而不是固定 floor。
3. 能解释“为什么这个场景没有足够证据”。
4. Product report 能展示 evidence-backed mechanism cards。

止损条件：

1. 相似案例只提供叙事，不能改善任何 guard metric。
2. 检索结果不可复现或无法溯源。
3. LLM 输出无法稳定结构化，导致 Product claim 不可审计。

### 5.3 路线 C：受约束多主体交互 rollout

目标：

> 构建带状态、记忆、影响和群体约束的多主体交互 rollout，用于发现二阶风险、异常群体和机制传播路径。

核心能力：

1. 虚拟群体节点。
2. 群体角色和约束 prompt。
3. 交互图传播。
4. 多轮状态更新。
5. 记忆与影响历史。
6. 异常风险生成。
7. 与结构化机制算子的结果融合。

方法形态：

```text
population_segments
  -> constrained_agents
  -> interaction_rounds
  -> mechanism_trace
  -> risk_signal_candidates
```

关键边界：

1. LLM agent 不能直接决定 field validation。
2. LLM rollout 不能单独作为数值预测证据。
3. LLM 输出必须被压缩成结构化机制 trace、risk signal 和 uncertainty contribution。
4. 所有 agent signal 必须经过路线 A/B 的证据约束和 Product guard。

验收信号：

1. 能发现静态先验和路线 A/B 没有覆盖的异常群体。
2. 能生成可复现的机制传播 trace。
3. 能在 Product report 中解释“风险如何扩散或被缓冲”。
4. 不增加不可控 false alarm。

止损条件：

1. agent rollout 只产生叙事，不能转成可计算 artifact。
2. 输出对模型、temperature 或 prompt 过度敏感。
3. false alarm 明显增加且无法被 gate 阻断。

## 6. 组合算法空间

R9 的重点不是单独比较三条路线，而是探索它们的组合。

### 6.1 基础组合

第一阶段至少比较七种组合：

1. `A_only`：证据约束机制算子。
2. `B_only`：语义案例检索约束。
3. `C_only`：受约束多主体 rollout。
4. `A+B`：检索案例约束机制算子。
5. `A+C`：agent rollout 生成机制候选，机制算子校准输出。
6. `B+C`：检索案例约束 agent rollout 的角色、机制和风险范围。
7. `A+B+C`：完整证据约束交互世界模型。

### 6.2 组合预期

如果 R9 有价值，最可能的成功组合不是 `C_only`，而是 `A+B+C` 或 `A+B`。

原因：

1. `A` 提供可计算学习和 guard。
2. `B` 提供外部证据和迁移约束。
3. `C` 提供交互传播、异常发现和机制叙事。

三者组合后，Product 才能同时拿到：

1. 可解释机制。
2. 可审计证据。
3. 可计算指标。
4. 可回放交互路径。
5. 可降级 claim boundary。

### 6.3 组合失败解释

如果组合失败，必须区分失败原因：

1. 数据证据不足。
2. 检索相似度无效。
3. 机制算子不可迁移。
4. agent rollout 噪声过高。
5. guard 太严格但合理。
6. Product 指标定义不适合当前数据。

失败也要成为 Product 的能力：告诉客户“这个场景为什么证据不足、需要补什么 outcome、风险判断为何被阻断”。

## 7. LLM 的角色

R9 允许使用 LLM，但必须限定角色。

LLM 可以做：

1. 场景结构化解析。
2. 候选机制生成。
3. 相似案例摘要。
4. 群体角色反应草案。
5. 交互轮次文本化。
6. 失败诊断解释草案。

LLM 不可以做：

1. 直接设置 `field_outcome_validated=true`。
2. 直接设置 `runtime_default_allowed=true`。
3. 直接替代 outcome。
4. 单独给出客户可见数值预测。
5. 绕过 Product guard。

所有 LLM 输出必须经过：

1. JSON schema 校验。
2. source refs 绑定。
3. deterministic fallback。
4. repeat/seed 记录。
5. guard metric 验证。

本地模型、DeepSeek、OpenRouter 或其他 provider 都只能作为候选生成器或 agent rollout 引擎，不作为最终事实来源。

## 8. 数据策略

R9 不再泛泛增加数据集。新增数据必须服务于一个明确验证目标。

### 8.1 数据类型

需要四类数据：

1. `public_survey_outcome`：公开调查态度或行为 proxy。
2. `policy_event_outcome`：政策、价格、服务变更后的公开结果。
3. `business_decision_proxy`：产品、价格、客户反应的公开 proxy。
4. `synthetic_mechanism_lab`：有已知机制真值的半合成测试场。

### 8.2 为什么需要 synthetic mechanism lab

真实 outcome 太稀缺，不能只靠当前 public proxy 判断方法是否有潜力。

synthetic mechanism lab 的作用不是替代真实世界，而是验证：

1. 算子能否恢复已知机制方向。
2. 传播边权是否能被学习。
3. false alarm gate 是否能阻断无效传播。
4. agent rollout 是否能发现设定好的异常群体。

这类结果只能支持 method sanity，不支持 field validation。

### 8.3 数据验收边界

数据进入 R9 必须包含：

1. `scenario_id`
2. `source_type`
3. `measurement_window`
4. `segment_schema`
5. `observed_metric`
6. `proxy_mapping`
7. `known_limitations`
8. `allowed_claim_level`

没有这些字段的数据只能进入 exploration，不能进入 Product-visible report。

## 9. 评估指标

R9 统一用以下指标验收所有路线和组合。

### 9.1 Product 核心指标

1. `trend_direction_accuracy`
2. `interval_coverage`
3. `interval_width_penalty`
4. `risk_ranking_quality`
5. `false_alarm_rate`
6. `static_prior_miss_recovery_rate`
7. `decision_value_score`
8. `abnormal_segment_precision`

### 9.2 Research 方法指标

1. `mechanism_direction_recovery`
2. `propagation_trace_consistency`
3. `case_retrieval_relevance`
4. `outcome_attribution_quality`
5. `holdout_non_regression_rate`
6. `update_candidate_acceptance_rate`
7. `seed_stability`
8. `provider_stability`

### 9.3 Guard 指标

1. `field_outcome_validated`
2. `runtime_default_allowed`
3. `source_backed_only`
4. `blocked_claims_preserved`
5. `diagnostic_downgrade_triggered`

## 10. 验收阶段

### 10.1 L0：合同与边界

目标：

1. R9 artifact schema 成立。
2. 三条路线都能生成结构化 artifact。
3. Product guard 不被覆盖。
4. 所有 source refs 可解析。

通过标准：

1. 单元测试通过。
2. JSON 严格序列化通过。
3. `field_outcome_validated=false`。
4. `runtime_default_allowed=false`。

### 10.2 L1：当前 proxy 非回归

目标：

验证 R9 在当前 public proxy fixture 上不比 R7/R8 更差。

通过标准：

1. false alarm 不高于 R7 v2。
2. static prior miss recovery 不低于 R7 v2。
3. interval coverage 不低于 R7 v2 或有合理 width penalty 解释。
4. decision value 不低于 R6/R7 guarded baseline。

### 10.3 L2：holdout 与扰动

目标：

验证 R9 不是记忆当前 fixture。

通过标准：

1. leave-one-case 通过。
2. same-family holdout 不回归。
3. perturbation pass rate 达到最低阈值。
4. near-threshold false alarm 可被 gate 阻断。

### 10.4 L3：机制恢复

目标：

在 synthetic mechanism lab 中验证方法能恢复已知机制。

通过标准：

1. 机制方向恢复率达标。
2. 传播路径一致性达标。
3. 异常群体识别达标。
4. 错误归因能定位到机制、传播边或数据不足。

### 10.5 L4：Product guarded support

目标：

让 Product 能安全展示 R9 能力。

通过标准：

1. Customer report 可消费 R9 support gate。
2. API manifest source registry 可解析 R9 artifact。
3. Product report 展示 trend/interval/risk/segment/mechanism/replay。
4. 未通过 field outcome 前仍保持 guarded/diagnostic claim。

## 11. 止损标准

R9 不是无限探索。满足任一条件时必须止损或降级：

1. `A+B+C` 组合仍不能超过 R7 v2 guarded baseline。
2. R9 只能在当前 fixture 上改善，holdout 全部失败。
3. false alarm 下降必须以 missed risk 增加为代价。
4. agent rollout 无法稳定结构化，且不能贡献可计算信号。
5. 检索案例无法提供可复现证据。
6. 方法复杂度显著增加，但 Product customer report 没有新增可解释价值。

止损后的处理：

1. R9 降级为 diagnostic method experiment。
2. R8 failure diagnosis package 继续作为 Product guard。
3. Product 重心转向 scenario intake、decision report、outcome review 和客户数据闭环。
4. Research 不再声称方法层技术壁垒，而是定位为证据约束决策支持系统。

## 12. Product 支撑方式

R9 如果成功，支撑 Product 的方式不是“预测更准”一句话，而是形成以下能力：

1. **证据约束的趋势判断**：告诉客户趋势方向来自哪些先例、机制和交互路径。
2. **风险区间而非点预测**：给出区间、宽度原因和证据强弱。
3. **异常群体识别**：指出哪些群体可能偏离平均先验。
4. **机制传播解释**：说明风险如何被放大、缓冲或转移。
5. **反事实策略沙盘**：比较不同干预对风险区间和群体分布的影响。
6. **真实 outcome replay**：真实结果回来后，定位错误并更新候选。
7. **失败诊断**：证据不足时明确告诉客户为什么不能给更强结论。

这才是 Product 的可售卖价值：

> 不是替客户承诺未来一定发生什么，而是在发布前识别风险区间和关键群体，在发布后形成可复盘学习闭环。

## 13. 第一阶段任务

R9 第一阶段只做 MVP，不直接追 full product readiness。

### Task 1：R9 artifact contract

新增：

- `experiments/r9_evidence_constrained_world_model.py`
- `tests/test_r9_evidence_constrained_world_model.py`

输出：

- `r9_world_model_bundle`
- `r9_route_outputs`
- `r9_combination_matrix`
- `r9_product_support_gate`

验收：

1. 三条路线 artifact 均存在。
2. 七种组合均有统一指标结构、可计算字段和 source refs。
3. Product guard 默认阻断 field/runtime claim。

### Task 2：路线 A/B/C 最小可运行实现

新增：

- 证据约束机制算子。
- 语义案例检索 mock/fixture。
- 受约束多主体 rollout fixture。

验收：

1. 每条路线都能独立输出 trend/interval/risk/segment/mechanism。
2. 每条路线都能解释失败原因。
3. 所有输出可 strict JSON。

### Task 3：组合矩阵与 baseline comparison

新增：

- `experiments/r9_combination_matrix.py`
- `tests/test_r9_combination_matrix.py`

比较：

1. static prior。
2. R6 learning counterfactual。
3. R7 v2。
4. R8 diagnostic method。
5. R9 A/B/C/AB/AC/BC/ABC。

验收：

1. 同口径指标可计算。
2. winner 和 stop-loss recommendation 可生成。
3. 不能只报告成功组合，失败组合也必须记录。

### Task 4：holdout / perturbation / synthetic mechanism lab

新增：

- `experiments/r9_holdout_guard.py`
- `experiments/r9_synthetic_mechanism_lab.py`

验收：

1. 当前 public proxy leave-one-case。
2. perturbation。
3. near-threshold false alarm。
4. synthetic mechanism recovery。

### Task 5：Product ingestion

修改：

- `experiments/r6_product_customer_value_report.py`
- `experiments/r6_product_api_manifest.py`

验收：

1. Product report 可显示 R9 support gate。
2. R9 未通过时显示 failure diagnosis。
3. R9 通过 guarded gate 时显示 evidence-backed mechanism cards。
4. blocked claims 不被覆盖。

## 14. 第一阶段成功/失败判定

### 成功信号

满足以下条件可继续投入：

1. `A+B` 或 `A+B+C` 至少在两个 Product 核心指标上超过 R7 v2。
2. false alarm 不升高。
3. static prior miss recovery 不下降。
4. synthetic mechanism lab 显示机制方向或传播路径可恢复。
5. Product report 能展示比 R8 failure diagnosis 更强的证据链。

### 弱成功信号

满足以下条件可继续小规模探索：

1. 指标没有全面超过 R7 v2，但 failure diagnosis 明显更强。
2. synthetic lab 成立，public proxy 暂未成立。
3. 某一路线失败，但组合路线有可解释改善。

### 止损信号

满足以下条件应停止 R9 方法攻关：

1. 七种组合都不能超过 R7 v2。
2. 改善来自不可解释规则或 case 记忆。
3. agent rollout 无法被结构化和复现。
4. Product report 只能多展示叙事，不能增加决策价值。

## 15. 结论边界

R9 spec 当前只定义下一阶段方法探索目标，不声明 Research 已经成功。

当前可声明：

1. R8 已被降级为 diagnostic asset。
2. Product guard 已能阻断弱方法误用。
3. R9 将以证据约束、机制学习和交互 rollout 组合方式重新探索方法层技术壁垒。

当前不可声明：

1. R9 已经支撑 Product core method。
2. 系统已经 field validated。
3. 系统可以 runtime default 自动更新。
4. LLM agent 等价于真实人群。
5. 交互仿真已经稳定优于静态先验。
