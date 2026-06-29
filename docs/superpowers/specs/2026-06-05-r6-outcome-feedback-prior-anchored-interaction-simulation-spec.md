# R6 结果反馈约束的先验锚定交互仿真框架 Spec

## 1. 文档目的

本 spec 定义 R4/R5 之后 Research 与 Product 的共同新主线：

> **R6-OFPIS：结果反馈约束的先验锚定交互仿真框架**

英文工作名：

> **Outcome-Feedback Prior-Anchored Interaction Simulation**

R6 的目标不是继续证明某个 prompt、persona、TextGrad、LCDU、R4 interaction 或 R5 mechanism-state 变体在单一静态数据集上更准，而是重新定义项目本体：

> 基于真实人口、客户或群体先验，构建一个可审计的交互仿真沙盘，用于在政策、规则、价格、权益、服务变更发布前评估人群反应，并在真实结果回流后持续校正方法。

R6 的核心价值包括两部分：

1. **发布前发现静态先验看不到的风险**：交互仿真即使未必直接更准，也可以暴露传播、情绪、从众、反弹、意见领袖和群体联动等静态数据无法预知的情境。
2. **发布后把真实结果变成方法更新信号**：当真实结果与仿真不一致时，系统必须能判断是先验、场景、网络、交互、影响权重、行为阈值还是输出解释出了问题，并把复盘结果写入下一轮方法改进。

## 2. 新定位

R6 的产品定位：

> **发布前反应评估与发布后反馈学习系统。**

R6 的研究定位：

> **强先验锚定、交互增益可解释、真实结果可回填的群体反应仿真方法框架。**

R6 不直接进入某一个垂直场景。航空公司调高某条航线票价或燃油费、平台调整会员权益、政府发布公共政策、企业变更服务规则，都只是该框架下的 case template。方法本体必须保持行业无关。

通用输入是：

- 变更对象：价格、规则、权益、限制、服务、政策、沟通口径。
- 目标人群：客户、居民、用户、员工、会员、利益相关方。
- 先验数据：人口结构、客户分层、历史行为、历史态度、价格敏感度、替代选择、信任或满意度。
- 场景描述：发布方式、传播渠道、解释文本、补偿策略、反对意见、媒体环境。
- 可选真实结果：发布后的行为、投诉、流失、转化、舆情、调查和业务指标。

通用输出是：

- 静态先验反应；
- 交互后风险偏移；
- 关键人群与风险节点；
- 情景对比；
- 不确定性边界；
- 发布后真实结果回填；
- 错误归因与下一轮方法更新建议。

## 3. 问题本质

已有强人口先验或客户先验并不是研究对手，而是仿真底座。

强先验回答：

> 在没有传播、交互、情绪扩散和群体影响时，这类人群大概率如何反应？

交互仿真回答：

> 当变更信息被发布、解释、转发、质疑、放大和讨论后，人群反应会如何相对静态先验发生偏移？

真实结果反馈回答：

> 仿真偏移与真实世界是否一致？如果不一致，错在什么层，下一轮应如何修正？

因此，R6 的核心不是单次 accuracy race，而是：

```text
static prior
  -> interaction scenario
  -> simulated shift
  -> risk and mechanism explanation
  -> real outcome ingestion
  -> error attribution
  -> method update
```

静态先验与交互仿真的关系要明确：

| 层 | 作用 | 不能宣称 |
| --- | --- | --- |
| 静态先验 | 给出人群代表性和无交互对照 | 不能覆盖传播、情绪和群体联动 |
| 交互仿真 | 发现静态先验盲区和二阶影响 | 没有真实 outcome 前不能宣称一定更准 |
| 真实结果反馈 | 校正先验、场景和交互机制 | 单个 case 不能证明跨域泛化 |

## 4. 与 MiroFish / OASIS 的差异

MiroFish / OASIS 对 R6 有工程启发，但 R6 不是它们的 wrapper。

R6 借鉴：

- 现实种子抽取；
- 图谱约束 persona；
- 行为过程建模；
- 动态记忆；
- 多 agent 交互；
- 报告与模拟世界互动。

R6 的差异：

| 维度 | MiroFish / OASIS | R6 |
| --- | --- | --- |
| 起点 | 现实事件材料、实体图谱、通用沙盘 | 人口/客户/群体先验和无交互对照 |
| 目标 | 构建可互动的平行数字世界 | 发布前反应评估与发布后反馈学习 |
| 评估 | 偏演示、报告和仿真运行 | 强制区分先验、交互偏移、真实 outcome、claim boundary |
| 方法边界 | 不内置 strong prior / no-interaction control / outcome learning contract | 先验锚定、交互消融、真实结果回填、错误归因是硬合同 |
| 产品价值 | 预测万物、数字沙盘 | 指导发布前风险判断、沟通策略和发布后复盘 |

R6 可以在后期接入 OASIS 风格 runtime，但第一阶段不依赖完整 OASIS。第一阶段优先建立方法合同、artifact chain、反馈学习协议和最小交互机制。

## 5. 与旧路线关系

| 旧路线 | R6 中的新定位 |
| --- | --- |
| LCDU / shrinkage prior | 静态强先验和 no-interaction control |
| DCL-PRS | 反例：不能把 LLM/persona runtime 直接包装成准确预测器 |
| S2PC / TextGrad / DSPy / GA | 可选候选生成或局部优化工具，不是主贡献 |
| MCR-Gate | gate、accepted/rejected ledger、failure diagnosis 基础设施 |
| R4-GPC-PRS | population/environment/interaction/memory/gate artifact 基础设施 |
| R5-MSPRC | 机制解释和审计层，可作为 interaction shift 的解释候选 |
| Product demo | 必须从合同夹具升级为真实 artifact ingestion 和反馈闭环 |

R6 不否定 R4/R5 已经建立的工程证据链。R6 继承它们的 artifact 合同和失败诊断经验，但改变主问题：

> 从“interaction 是否在静态 heldout 上击败强基线”，转为“interaction 是否提供静态先验无法覆盖的发布前风险假设，并能在真实 outcome 回来后被验证、归因和修正”。

## 6. 核心架构

R6 分为七层。

### L1 先验层：Prior Manifest

目标：

> 定义目标人群的无交互基础状态。

输入：

- 人口统计；
- 客户分层；
- 历史行为；
- 历史态度；
- 历史规则变更结果；
- segment 权重；
- 不确定性。

输出：

```json
{
  "schema_version": "r6-prior-manifest-v1",
  "target_population": "generic_customer_or_public_group",
  "segment_axis": ["segment", "sensitivity", "trust", "substitution"],
  "segments": [
    {
      "segment_id": "price_sensitive_low_trust",
      "weight": 0.18,
      "static_response_prior": {
        "accept": 0.22,
        "neutral": 0.31,
        "reject": 0.47
      },
      "uncertainty": 0.14,
      "source_refs": ["customer survey", "historical behavior"]
    }
  ],
  "claim_boundaries": ["static_prior_not_dynamic_prediction"]
}
```

验收要求：

- 必须有 segment 权重；
- 必须有 static response prior；
- 必须写明来源和不确定性；
- 必须支持 no-interaction control。

### L2 场景层：Scenario Manifest

目标：

> 将一次即将发布的变更抽象成可比较的情景。

场景不绑定行业，使用通用维度：

- 变更类型：price、rule、benefit、restriction、service、policy。
- 影响方向：成本增加、权益减少、便利性下降、信任冲击、风险降低、服务改善。
- 发布主体：官方、第三方、媒体、社区、意见领袖。
- 沟通策略：直接通知、解释原因、补偿、分阶段、沉默、反驳。
- 曝光渠道：官方渠道、社媒、媒体、社群、客服。

输出：

```json
{
  "schema_version": "r6-scenario-manifest-v1",
  "scenario_id": "rule_or_price_change_generic_001",
  "change_type": "price",
  "impact_dimensions": ["cost_increase", "fairness_concern", "substitution_pressure"],
  "communication_plan": {
    "source": "official",
    "message_frame": "cost_pass_through",
    "mitigation": "loyalty_compensation"
  },
  "alternative_scenarios": ["no_compensation", "phased_release"],
  "claim_boundaries": ["scenario_is_assumption_until_outcome_available"]
}
```

### L3 交互层：Interaction Simulation

目标：

> 在静态先验基础上模拟信息暴露、社会扩散、情绪影响和行为阈值变化。

交互机制应至少包括：

- exposure：谁看到什么信息；
- influence：谁影响谁；
- trust：信息源可信度；
- contagion：情绪或叙事扩散；
- resistance：反弹、惯性和抵抗；
- substitution：替代选择触发；
- threshold：行为转变阈值。

第一阶段使用轻量确定性或半随机交互 loop，不直接接完整 OASIS。

输出：

```json
{
  "schema_version": "r6-interaction-trace-v1",
  "rounds": 3,
  "events": [
    {
      "round": 1,
      "source_segment": "high_trust_official_followers",
      "target_segment": "price_sensitive_low_trust",
      "channel": "social_share",
      "mechanism": "fairness_concern_contagion",
      "response_shift": {
        "accept": -0.03,
        "neutral": -0.02,
        "reject": 0.05
      }
    }
  ],
  "risk_flags": ["interaction_shift_requires_outcome_validation"]
}
```

### L4 偏移报告层：Risk Shift Report

目标：

> 明确交互仿真相对静态先验发现了什么。

输出必须区分：

- static prior；
- interaction result；
- delta；
- risk segment；
- mechanism explanation；
- uncertainty；
- recommended observation after release。

示例：

```json
{
  "schema_version": "r6-risk-shift-report-v1",
  "overall_static_reject_rate": 0.31,
  "overall_interaction_reject_rate": 0.38,
  "delta": 0.07,
  "top_risk_segments": [
    {
      "segment_id": "price_sensitive_low_trust",
      "delta_reject": 0.13,
      "mechanisms": ["fairness_concern", "peer_amplification", "substitution_pressure"]
    }
  ],
  "claim_boundary": "risk_hypothesis_not_validated_outcome"
}
```

### L5 真实结果层：Outcome Manifest

目标：

> 将发布后的真实世界结果接回系统。

真实结果可以来自：

- 调查；
- 投诉；
- 客服工单；
- 流失；
- 转化；
- 留存；
- 社媒舆情；
- 销售或使用行为；
- 搜索、点击、曝光；
- 手工标注的事件复盘。

输出：

```json
{
  "schema_version": "r6-outcome-manifest-v1",
  "release_id": "release_001",
  "observation_window": "2026-06-01_to_2026-06-14",
  "metrics": {
    "complaint_rate": 0.042,
    "churn_rate": 0.087,
    "negative_sentiment_rate": 0.36,
    "conversion_delta": -0.11
  },
  "by_segment": {
    "price_sensitive_low_trust": {
      "observed_reject_proxy": 0.51,
      "observed_churn_proxy": 0.18
    }
  },
  "source_refs": ["crm export", "survey wave", "social monitoring"],
  "data_quality_flags": ["proxy_metric_not_direct_attitude"]
}
```

### L6 误差归因层：Learning Report

目标：

> 将“不准”转化为可学习信号，而不是停留在失败描述。

误差类型：

| 类型 | 含义 | 后续动作 |
| --- | --- | --- |
| prior_error | 静态先验低估或高估基础态度 | 更新 segment prior 或不确定性 |
| scenario_error | 场景编码漏掉关键解释或约束 | 更新 scenario taxonomy |
| network_error | 传播结构或关键节点假设错误 | 更新 network / influence graph |
| mechanism_error | 机制方向或强度错误 | 更新 mechanism catalog |
| threshold_error | 行为转化阈值错误 | 更新 behavior threshold |
| measurement_error | outcome 指标不能代表真实反应 | 修正观测指标和映射 |
| unexplained_error | 无法解释 | 进入人工复盘，不进入自动更新 |

输出：

```json
{
  "schema_version": "r6-learning-report-v1",
  "prediction_vs_outcome": {
    "predicted_reject_rate": 0.38,
    "observed_reject_proxy": 0.44,
    "absolute_error": 0.06
  },
  "error_attribution": [
    {
      "type": "mechanism_error",
      "confidence": 0.62,
      "diagnosis": "fairness_concern was underweighted for low-trust segments",
      "recommended_update": {
        "mechanism": "fairness_concern",
        "target_segments": ["price_sensitive_low_trust"],
        "weight_delta": 0.08
      }
    }
  ],
  "update_policy": "human_review_required"
}
```

### L7 更新层：Update Registry

目标：

> 记录哪些方法更新被接受、拒绝或仅保留为诊断。

更新不应自动污染全局模型。所有更新必须有来源、适用范围和回滚条件。

状态：

- `accepted`：跨 case 或 holdout 验证通过；
- `case_local`：仅在当前 case 有效；
- `diagnostic_only`：解释有价值，但不进入下一轮默认参数；
- `rejected`：证据不足或造成回归；
- `needs_more_outcomes`：样本不足，等待更多真实结果。

## 7. Research 线目标

R6 Research 线的目标不是单次场景预测，而是形成可投稿的通用方法框架。

核心研究问题：

1. 如何用强先验生成有代表性的无交互人群底座？
2. 如何定义交互仿真相对静态先验的有效偏移？
3. 如何判断一个偏移是有机制解释的风险信号，而不是随机扰动？
4. 如何在真实 outcome 回来后做误差归因？
5. 如何把 outcome feedback 转换成受约束的方法更新？
6. 如何跨多个政策/规则/价格/权益变更任务验证，而不是过拟合某个行业？

最低研究贡献候选：

> R6 提供一个 outcome-feedback-gated interaction simulation framework，将静态先验、交互推演、真实结果回填和错误归因统一到可审计 artifact chain 中。

可投稿前必须补齐：

- 至少 3 类变更任务；
- 每类至少 2 个 case 或公开近似数据；
- 至少一个真实或公开 outcome proxy；
- no-interaction prior、uncalibrated interaction、prior-anchored interaction、outcome-feedback update 的消融；
- 对准确性、风险发现、错误归因和学习更新分别报告指标；
- 明确哪些 claim 可成立，哪些不能成立。

## 8. Product 线目标

R6 Product 线的目标是：

> 形成行业无关的发布前反应评估工作流。

产品不应直接宣称“预测一定准确”。产品应向用户展示：

- 当前静态先验怎么判断；
- 加入交互后哪里发生偏移；
- 哪些风险来自传播、情绪、替代选择或群体影响；
- 哪些结论缺少真实结果验证；
- 发布后应采集什么指标；
- 真实结果回来后系统如何复盘和更新。

Product MVP 工作流：

1. 用户输入变更说明和目标人群。
2. 系统生成 prior manifest。
3. 系统生成 scenario manifest。
4. 系统运行 no-interaction control。
5. 系统运行 interaction simulation。
6. 系统输出 risk shift report。
7. 用户发布后上传 outcome manifest。
8. 系统输出 learning report。
9. 系统将更新写入 update registry，等待人工确认或后续验证。

产品报告应包含：

- 静态先验结论；
- 交互偏移结论；
- 风险 segment；
- 关键机制；
- 情景对比；
- claim boundary；
- outcome collection checklist；
- 发布后复盘面板。

## 9. 验收指标

R6 不使用单一 accuracy 指标。第一阶段至少报告以下指标。

### 9.1 先验质量指标

- segment coverage；
- prior uncertainty；
- source completeness；
- no-interaction reproducibility；
- by-segment calibration status。

### 9.2 交互偏移指标

- delta magnitude；
- delta concentration；
- segment-level shift consistency；
- seed/scale stability；
- mechanism attribution coverage；
- no-interaction contrast。

### 9.3 风险发现指标

- 是否发现静态先验 top risk 之外的新风险 segment；
- 是否给出机制解释；
- 是否给出发布后观测建议；
- 是否避免把风险假设包装成真实 outcome。

### 9.4 真实结果反馈指标

- prediction-outcome error；
- error attribution coverage；
- unexplained error rate；
- update acceptance rate；
- update regression rate；
- across-case reuse rate。

### 9.5 Product 可用性指标

- report 是否能解释“为什么有风险”；
- report 是否明确“不确定在哪里”；
- report 是否能指导发布后采集哪些数据；
- report 是否能在 outcome 回来后生成复盘；
- report 是否阻断未验证准确性宣称。

## 10. 测试方案

R6 第一阶段先做 contract-first 测试，不直接追完整仿真规模。

### 10.1 单元测试

覆盖：

- prior manifest schema；
- scenario manifest schema；
- interaction trace schema；
- risk shift report schema；
- outcome manifest schema；
- learning report schema；
- update registry schema。

每个 artifact 必须：

- 严格 JSON 可序列化；
- 包含 `schema_version`；
- 包含 `artifact_id`；
- 包含 `source_refs`；
- 包含 `claim_boundaries` 或 `claim_boundary`；
- 包含 `risk_flags`；
- 对缺失核心字段主动拒绝。

### 10.2 集成测试

构造至少 3 个行业无关 fixture：

1. 价格变更；
2. 权益或规则变更；
3. 公共服务或政策变更。

每个 fixture 跑：

```text
prior -> scenario -> no-interaction -> interaction -> risk shift -> outcome -> learning report
```

必须验证：

- no-interaction control 可复现；
- interaction result 与 static prior 的 delta 可解释；
- outcome manifest 可接入；
- learning report 能生成误差归因；
- update registry 不自动接受未验证更新。

### 10.3 对照实验

至少包含：

- static prior only；
- uncalibrated interaction；
- prior-anchored interaction；
- prior-anchored interaction + outcome feedback；
- random interaction noise baseline。

第一阶段不要求全部击败强统计基线，但必须证明：

- interaction shift 不是随机噪声；
- learning report 能区分可解释错误和不可解释错误；
- Product report 不会把未验证风险当作准确预测。

## 11. 验收标准

### 11.1 MVP 通过标准

R6 MVP 通过需要满足：

1. 七类 artifact 均实现为严格 schema。
2. 3 个行业无关 fixture 可完整跑通。
3. 每个 fixture 都有 no-interaction control。
4. 每个 risk shift report 都能解释相对静态先验的偏移。
5. 至少 1 个 fixture 接入 outcome manifest 并生成 learning report。
6. update registry 能明确记录 accepted / rejected / diagnostic_only / needs_more_outcomes。
7. Product report 能展示 claim boundary。
8. 所有测试通过。

### 11.2 Research 继续推进标准

R6 进入下一阶段 Research 需要满足：

1. 至少 3 个任务上 interaction shift 有稳定机制解释。
2. 至少 2 个任务上 outcome feedback 能产生非空且合理的 error attribution。
3. 至少 1 个任务显示 outcome feedback update 在后续 case 上减少错误。
4. random interaction baseline 被稳定拒绝。
5. no-interaction control 与 interaction result 的差异能被审计。
6. 没有把单 case 结果包装成跨域准确性结论。

### 11.3 Product 继续推进标准

R6 进入下一阶段 Product 需要满足：

1. 用户能输入通用变更场景，而非只能跑某个行业模板。
2. 报告能同时展示静态先验、交互偏移和真实 outcome 回填入口。
3. 报告能明确告诉用户发布后应采集哪些指标。
4. 报告能在 outcome 回来后生成复盘。
5. 报告能阻断未验证准确性宣称。

## 12. Claim Boundary

R6 第一阶段可以宣称：

- 系统能够把静态先验、交互仿真、真实结果反馈串成可审计链路。
- 系统能够识别交互仿真相对静态先验的风险偏移。
- 系统能够在真实 outcome 回来后做错误归因。
- 系统能够将错误归因转成受约束的更新候选。
- 系统不把未验证的交互偏移包装成真实准确性。

R6 第一阶段不能宣称：

- 系统已经证明比静态先验预测更准。
- 系统已经适用于所有行业。
- 单个航空、平台、公共政策或客户场景能证明方法泛化。
- LLM agent 交互本身等价于真实人群行为。
- 真实 outcome proxy 等价于完整态度真值。

## 13. 止损线

R6 也必须有止损线。

出现以下情况，应暂停 R6 作为主算法推进：

1. 交互偏移无法稳定区别于 random interaction noise。
2. learning report 大量输出 `unexplained_error`，无法形成可学习信号。
3. outcome feedback update 在后续 case 上持续造成回归。
4. Product report 只能展示复杂过程，不能给出清晰决策建议。
5. 系统仍然依赖单一垂直场景，无法抽象到通用变更类型。
6. claim boundary 无法阻止“未验证预测准确性”的过度表述。

即便 R6 止损，也应保留：

- artifact 合同；
- outcome feedback ingestion；
- learning report；
- Product 发布后复盘能力；
- 对 R4/R5 负结果的解释框架。

## 14. 第一阶段任务清单

Task 1：写 R6 schema 定义。

- `r6_prior_manifest`
- `r6_scenario_manifest`
- `r6_interaction_trace`
- `r6_risk_shift_report`
- `r6_outcome_manifest`
- `r6_learning_report`
- `r6_update_registry`

Task 2：实现 3 个行业无关 fixture。

- price change；
- rights/rule change；
- public service/policy change。

Task 3：实现 lightweight interaction loop。

- 支持 no-interaction control；
- 支持 seed/scale；
- 支持 deterministic replay；
- 支持 random noise baseline。

Task 4：实现 risk shift report。

- 输出 static vs interaction delta；
- 输出 top risk segments；
- 输出 mechanism explanation；
- 输出 claim boundary。

Task 5：实现 outcome ingestion。

- 支持真实 outcome 或 proxy outcome；
- 支持 by-segment 结果；
- 支持 data quality flags。

Task 6：实现 learning report。

- 输出 prediction vs outcome；
- 输出 error attribution；
- 输出 recommended update；
- 输出 update policy。

Task 7：实现 update registry。

- 记录 accepted / rejected / diagnostic_only / needs_more_outcomes；
- 阻止未验证更新进入默认运行参数。

Task 8：接入 Product report contract。

- 展示发布前风险；
- 展示发布后复盘；
- 展示 claim boundary；
- 展示下一轮应采集数据。

## 15. 最小交付形态

第一阶段交付不做完整 UI 和大规模 agent runtime。最小交付包括：

- 中文 spec；
- schema + tests；
- 3 个 fixture；
- 一个 CLI 或实验脚本跑通完整 artifact chain；
- 生成 1 份 Product 可消费的 report JSON；
- 文档回填当前结论和 gap。

## 16. 总结

R6 的关键转向是：

> 从“证明交互仿真一定更准”，转为“用强先验建立可信底座，用交互仿真发现静态数据盲区，用真实结果反馈持续校正方法”。

这使 Research 和 Product 同时回到现实价值：

- Research 获得一个有理论定义、可消融、可反馈学习、可跨场景验证的方法框架。
- Product 获得一个发布前评估和发布后复盘的通用工作流。

R6 不进入单一垂直场景。垂直场景只作为验证 case，不作为方法定义。
