# R6 Product-first Solid Value Spec

## 目标调整

R6 后续不再默认以 CCF-A 主贡献算法为验收目标。

当前目标调整为：

> 做出一个扎实、有理论和学术价值支撑、但重心明确向 Product 倾斜的发布前人群反应评估产品。

Research 仍然重要，但它的角色从“单独冲顶会主贡献”改为：

1. 给 Product 提供可信理论定义。
2. 给 Product 提供可审计证据链。
3. 给 Product 提供失败边界和 blocked claims。
4. 给 Product 提供结果回流后的误差归因和方法更新机制。

Product 的角色提升为主交付目标：

1. 客户能输入一个政策、规则、价格、权益或服务变更场景。
2. 系统能用强先验生成无交互基础状态。
3. 系统能展示交互仿真带来的风险偏移和潜在二阶影响。
4. 系统能明确告诉客户哪些结论可用、哪些结论不能宣称。
5. 真实 outcome 或 proxy 回来后，系统能复盘误差并生成受约束更新候选。

## 产品价值主张

R6 Product 不承诺“预测一定准确”。

R6 Product 承诺：

1. 比静态表格更适合做发布前风险讨论。
2. 比纯 LLM 角色扮演更可审计。
3. 比单次问卷预测更能表达交互传播和二阶风险。
4. 比黑箱模型更清楚地显示证据边界、失败边界和不能宣称的内容。
5. 真实结果回流后，可以把错误变成可记录、可比较、可阻断的学习资产。

## Research 保留目标

Research 后续只追求“扎实、有学术价值”，不追求默认 CCF-A。

可接受的 Research 贡献包括：

1. 强先验约束下的交互风险发现问题定义。
2. 静态先验、交互偏移、结果反馈之间的形式化关系。
3. 发布前风险发现价值函数。
4. 误差归因 taxonomy。
5. 受约束 behavioral update operator。
6. 可审计 claim gate 和 failure diagnosis。
7. public proxy / field outcome 回流后的 bounded learning protocol。

不再作为默认 Research 目标：

1. 单点算法击败强静态先验。
2. CCF-A 主贡献 readiness。
3. TextGrad / DSPy / prompt patch / persona patch 的单独优化胜出。
4. 为论文指标牺牲 Product 工作流闭环。

## Product 必须补齐的闭环

### 1. 场景输入

Product 必须支持一个结构化场景输入，而不是固定 demo 文案。

最小字段：

- `scenario_id`
- `change_type`
- `target_population`
- `impact_dimensions`
- `communication_plan`
- `alternative_scenarios`
- `decision_question`
- `assumptions`

### 2. 人群和先验

Product 必须展示：

- 使用了哪些人口、客户或群体先验。
- 哪些 segment 风险最高。
- 静态先验的基础分布是什么。
- 先验的来源和限制。

### 3. 交互仿真

Product 必须展示：

- 交互前后风险偏移。
- 哪些 segment 受影响最大。
- 哪些机制路径导致风险变化。
- 哪些变化只是 diagnostic，不是 validated prediction。

### 4. 证据卡

Product 必须基于 `r6_product_evidence_cards` 展示：

- `claim_status`
- `allowed_claims`
- `blocked_claims`
- `source_artifact_ids`
- `display_fields`

UI 或报告不得用静态 narrative fallback 自行生成未绑定 artifact 的结论。

### 5. 决策报告

Product 必须能导出一个客户可读报告，至少包含：

- 发布前风险摘要。
- 静态先验对照。
- 交互风险偏移。
- 高风险 segment。
- 证据边界。
- blocked claims。
- 建议下一步数据采集或发布后监测项。

### 6. 发布后复盘

Product 必须能接入真实 outcome 或 public proxy 后：

- 对比静态先验、交互仿真和 outcome。
- 标记正向信号、false alarm、missed risk。
- 生成误差归因。
- 生成候选更新。
- 用 gate 阻断未验证更新进入 runtime default。

## 验收标准

下一阶段完成时，必须能回答：

1. 客户是否能看懂“现在该担心什么”？
2. 客户是否能看懂“哪些结论不能相信到什么程度”？
3. 系统是否能导出一个不用口头解释也能成立的 evidence-backed report？
4. Product 是否没有静态 narrative fallback？
5. 每个客户可见结论是否都有 artifact source？
6. Research 是否没有被包装成过度 claim？
7. 发布后 outcome 回来后，系统是否知道如何复盘和更新？

## 当前边界

当前仍然不能宣称：

- `field_outcome_validated=true`
- `runtime_default_allowed=true`
- `ccf_a_main_contribution_ready=true`
- 交互仿真稳定比静态先验更准
- LLM agent 反应等价于真实人群反应

当前可以宣称：

- R6 已有可审计 artifact chain。
- R6 已能展示静态先验、交互风险偏移、失败边界和 blocked claims。
- R6 已有 Product evidence cards。
- R6 可以作为发布前风险讨论和发布后复盘的产品底座继续推进。
