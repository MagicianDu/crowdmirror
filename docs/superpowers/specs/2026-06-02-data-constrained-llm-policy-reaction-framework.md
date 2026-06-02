# 数据约束的 LLM 政策反应模拟框架中文 Spec

## 1. 文档目的

本 spec 定义下一阶段 Research / Product 的共同主线：

> 从继续优化 LCDU，转向探索一个由机制生成、自动修复、群体动态仿真组成的新方法空间。

这个转向基于当前实验结论：

- LCDU / LCDU-hybrid / LCDU-LCR-SG 已经证明有校准与审计价值；
- 但多轮探索后，继续在 `prior family / k / selector / gate / prompt` 之间局部搜索，难以稳定胜出强基线；
- `strong_baseline_lcdu_not_leading` 说明 LCDU 当前版本不能单独支撑 CCF-A 主贡献；
- Product 需要的不只是局部拟合改善，而是完整、可解释、可审计、可演化的政策反应模拟能力。

因此，LCDU 在新阶段不再作为唯一主算法继续硬推，而降级为：

1. 校准层；
2. 审计层；
3. 强基线；
4. Product runtime 的 evidence gate。

新的主贡献候选应来自更高层的方法框架。

## 2. 总体目标

新阶段目标是形成：

> **数据约束的 LLM 政策反应模拟框架**

英文工作名：

> **Data-Constrained LLM Policy Reaction Simulation**

缩写：

> **DCL-PRS**

核心主张：

> LLM 负责政策语义理解、反应机制生成、虚拟人解释和情景推演；统计校准负责约束、验收、误差归因和证据边界；社会仿真负责从个体态度扩展到群体动态。

这个框架必须同时服务两个目标：

### 2.1 Research 目标

形成可投稿 CCF-A 的方法贡献候选：

1. 有清晰问题定义；
2. 有算法框架，而不是单点 prompt 技巧；
3. 有可重复的实验协议；
4. 有强 baseline 对比；
5. 有失败边界和消融分析；
6. 能解释为什么 LLM 与统计校准的组合优于纯统计、纯 prompt、纯 agent simulation。

### 2.2 Product 目标

形成有客户说服力的核心能力：

1. 能解释政策反应从何而来；
2. 能指出哪些人群、机制、传播路径导致风险；
3. 能自动发现模拟偏差并提出修复；
4. 能把小规模 LLM 仿真变成可审计 evidence chain；
5. 能支持政策研究机构的工作流：政策输入、人群设定、反应预测、风险分群、传播推演、报告生成。

## 3. 当前 LCDU 路径的止损判断

本 spec 明确接受以下判断：

> 原有 LCDU 路径已经不适合作为唯一研究主线继续探索。

理由不是 LCDU 完全失败，而是它的边界已经比较清楚。

### 3.1 已证明的价值

LCDU 系列方法已经证明：

1. 数据约束比纯 LLM prompt 更可靠；
2. heldout / repeat / strong baseline gate 可以防止过度主张；
3. segment-level fallback / shrink 能提供可审计决策；
4. Product runtime 可以复用 LCDU 的 evidence chain。

### 3.2 暴露的上限

LCDU 系列也暴露了几个上限：

1. 主要搜索空间仍是局部分布校准；
2. 缺少“人为什么这样反应”的机制建模；
3. 对 fixed party prior 等强统计基线没有稳定优势；
4. prompt/persona 更新缺少自动化、细粒度、可验证的优化方向；
5. 静态态度预测无法支撑完整政策反应叙事。

### 3.3 新定位

LCDU 后续作为基础设施保留：

- 作为所有新方法的强 baseline；
- 作为所有候选修复的 acceptance gate；
- 作为 Product 报告中的校准审计层；
- 作为 paper gate 的证据边界约束。

但不再把“再调一个 LCDU 变体”作为主要创新来源。

## 4. 三条正交创新路线

新阶段不做单一路径押注，而构造三条正交路线。每条路线都可以独立探索，也可以组合形成更强方法。

### 4.1 路线 A：机制生成线

### 目标

回答：

> 人群为什么会对某个政策产生支持、反对、摇摆或条件支持？

### 核心思想

从政策文本、人群属性、历史态度和上下文中生成可检验的反应机制，而不是直接生成最终态度概率。

候选机制包括：

- 利益感知；
- 制度信任；
- 价值冲突；
- 风险承受；
- 身份认同；
- 政党或意识形态框架；
- 对政策执行主体的信任；
- 对短期成本和长期收益的权衡；
- 对公平性、效率、自由、稳定等价值维度的排序。

### 方法对象

机制生成线的输出不是自然语言解释文本，而是结构化 mechanism program：

```json
{
  "policy_id": "public_health_medical_insurance_attitude_v1",
  "cohort_selector": {
    "party_or_ideology": "conservative",
    "income": "lower"
  },
  "mechanisms": [
    {
      "name": "fiscal_burden_concern",
      "direction": "decrease_support",
      "strength": 0.7,
      "evidence_source": "policy_semantics_and_cohort_prior"
    },
    {
      "name": "direct_benefit_expectation",
      "direction": "increase_support",
      "strength": 0.4,
      "evidence_source": "cohort_material_interest"
    }
  ],
  "uncertainty": 0.3
}
```

### 创新点

这条线的创新不在“LLM 写解释”，而在：

1. 把 LLM 输出约束成可校准的机制程序；
2. 让机制程序通过 heldout / repeat gate 验证；
3. 允许机制成为后续仿真和修复的中间状态；
4. 让论文从“拟合分布”提升到“生成并检验反应机制”。

### 主要风险

1. 机制变量可能过于主观；
2. LLM 可能生成看似合理但不可检验的解释；
3. 结构化机制如果不能带来预测增益，会退化成报告层解释。

### 第一阶段验收

机制生成线必须证明：

1. 机制程序可以稳定生成；
2. 机制变量能被映射到预测或校准动作；
3. 至少在一个政策任务上超过 LCDU/LCDU-SG；
4. 消融后能证明机制层不是空解释。

### 4.2 路线 B：失败归因与自动修复线

### 目标

回答：

> 当前模拟哪里错了，系统如何自动提出可验证修复？

### 核心思想

不再把失败当成实验日志，而是把失败转成结构化 error program，并自动生成 repair proposal。

错误类型包括：

- `persona_mispecified`：虚拟人画像或 cohort 描述错误；
- `policy_semantics_misread`：政策语义理解错误；
- `mechanism_missing`：缺少关键反应机制；
- `mechanism_direction_wrong`：机制方向错误；
- `cohort_weight_wrong`：群体权重或代表性错误；
- `interaction_path_missing`：缺少群体互动或传播路径；
- `over_shrinkage`：校准过度收缩；
- `under_shrinkage`：校准不足；
- `anchor_should_hold`：该 segment 不应更新。

### 方法对象

失败归因线的输出是 error attribution + repair candidate：

```json
{
  "task_id": "climate_energy_regulation_attitude_v1",
  "segment_key": "party_or_ideology=moderate|income=middle",
  "observed_failure": {
    "loss_delta_vs_anchor": 0.004,
    "worst_segment_regression": true
  },
  "error_attribution": [
    {
      "type": "mechanism_direction_wrong",
      "confidence": 0.62,
      "reason": "cost concern was over-weighted relative to environmental risk concern"
    }
  ],
  "repair_candidates": [
    {
      "action": "rebalance_mechanism_strength",
      "target": "environmental_risk_concern",
      "delta": 0.2
    }
  ]
}
```

### 创新点

这条线的创新在于：

1. 把 prompt/persona 优化从人工经验变成自动 error attribution；
2. 让每次失败都进入可审计的修复候选池；
3. repair proposal 必须由 heldout / repeat gate 接受，不能直接使用 test failure；
4. Product 可以展示“系统如何自我诊断和校准”。

### 主要风险

1. 错误归因可能不唯一；
2. 自动修复可能过拟合 heldout；
3. LLM 归因可能偏向叙事合理性而非统计有效性；
4. 修复搜索空间如果过大，成本会快速上升。

### 第一阶段验收

失败归因线必须证明：

1. 能把失败样本稳定归入有限错误类型；
2. 能自动生成 repair proposal；
3. repair proposal 有接受/拒绝机制；
4. 至少一个 repair family 在 repeat 上优于原方法；
5. 不使用 test split 直接闭环当前 claim。

### 4.3 路线 C：群体动态仿真线

### 目标

回答：

> 政策发布后，不同群体的态度如何通过信息、互动、组织和时间演化？

### 核心思想

从静态态度预测扩展到动态社会仿真。LLM agent 负责个体或机构的语义反应，外层系统负责网络结构、传播规则、校准约束和审计。

### 方法对象

动态仿真线的输出是 simulation trace：

```json
{
  "simulation_id": "policy_reaction_sim_001",
  "policy_id": "public_health_medical_insurance_attitude_v1",
  "population": {
    "agent_count": 1000,
    "cohort_schema": ["party_or_ideology", "income", "age_group"]
  },
  "interaction_model": {
    "network_type": "cohort_mixing",
    "influence_sources": ["media_frame", "policy_institution", "peer_discussion"]
  },
  "time_steps": [
    {
      "t": 0,
      "aggregate_support": 0.52,
      "polarization_index": 0.18
    },
    {
      "t": 5,
      "aggregate_support": 0.47,
      "polarization_index": 0.31
    }
  ]
}
```

### 创新点

这条线的创新在于：

1. 把政策反应从一次性态度估计扩展为动态过程；
2. 让 LLM agent 的输出受群体分布、网络结构和校准 gate 约束；
3. 同时产生 Product 叙事需要的过程证据；
4. 可以评估政策风险的时间演化，而不只是初始支持率。

### 主要风险

1. 缺少真实时间序列数据时，验证难度高；
2. LLM agent 成本较高；
3. 动态过程容易产生看似丰富但不可证伪的叙事；
4. 需要严格区分 calibrated prediction 与 exploratory simulation。

### 第一阶段验收

群体动态仿真线必须证明：

1. 可复现实验 trace；
2. agent 行为有 schema 约束；
3. 聚合态度不劣于静态 baseline；
4. 动态指标可计算，例如极化、波动、群体分歧、风险扩散；
5. 输出能进入 Product cohort report。

## 5. 组合创新空间

三条路线不是三个孤立项目，而是构成一个组合创新空间。

### 5.1 二元组合

### A × B：机制生成 + 自动修复

目标：

> 当预测失败时，系统能指出是哪类反应机制错了，并自动修复机制参数或机制集合。

潜在贡献：

- 从 prompt 优化转向 mechanism program optimization；
- 形成可解释、可验证的自动校准流程；
- 最可能成为第一篇论文的主算法。

### A × C：机制生成 + 群体动态

目标：

> 让个体或 cohort 的动态反应由机制驱动，而不是由裸 prompt 直接生成。

潜在贡献：

- 动态仿真有行为机制支撑；
- Product 报告能解释“为什么会扩散、为什么会极化”；
- 更接近社会计算的核心问题。

### B × C：自动修复 + 群体动态

目标：

> 当仿真轨迹偏离校准目标时，系统能定位是初始态度、传播结构、影响源还是人群机制导致偏差。

潜在贡献：

- 把动态仿真的不可控性变成可诊断对象；
- 形成 Product 中“仿真质量控制”的技术壁垒。

### 5.2 三元组合

最终目标是：

> 机制可解释、误差可归因、过程可模拟、结果可校准。

三元组合的完整流程：

```text
政策输入
  -> 政策语义解析
  -> cohort / persona 构造
  -> 机制程序生成
  -> 静态态度初始化
  -> 群体动态仿真
  -> 与公开数据 / heldout / proxy target 对比
  -> 错误归因
  -> 修复候选生成
  -> LCDU gate 接受或拒绝
  -> Product evidence report
```

## 6. 第一阶段实验矩阵

第一阶段不追求完整三元系统，而是用 4 个任务覆盖关键组合。

### Task 1：Mechanism Program L0

目标：

> 建立机制程序 schema，并验证机制程序能否参与预测或校准。

输入：

- 当前 ANES/HPS/HOTPS 政策任务；
- 政策文本或政策摘要；
- cohort schema；
- 当前 LCDU/LCDU-SG baseline artifact。

输出：

- `mechanism_program` artifact；
- 机制到预测动作的映射；
- 机制消融结果。

验收：

- schema 稳定；
- 不含自由散文式不可解析输出；
- 至少一个任务上不劣于 anchor；
- 至少一个机制消融能改变结果。

### Task 2：Failure Attribution + Repair L0

目标：

> 把当前 LCDU/LCDU-SG 失败样本转成结构化错误归因，并自动生成 repair proposal。

输入：

- split/repeat 失败 artifact；
- worst segment regression；
- baseline comparison matrix。

输出：

- `error_attribution` artifact；
- `repair_candidate` artifact；
- accepted / rejected repair report。

验收：

- 错误类型有限且可统计；
- repair 不能直接使用 test label 闭环；
- repeat 上至少出现一个稳定不劣于 LCDU-SG 的 repair family；
- rejected candidate 必须保留原因。

### Task 3：Dynamic Cohort Simulation L0

目标：

> 跑通受约束的 cohort-level 动态仿真，而不是开放式 agent 聊天。

输入：

- cohort 初始化分布；
- 机制程序；
- 简化互动结构；
- 政策叙事或媒体 frame。

输出：

- simulation trace；
- aggregate attitude curve；
- polarization / volatility / divergence 指标；
- Product cohort report。

验收：

- trace 可复现；
- 每个 time step 有可审计 state；
- 动态结果不能脱离校准边界；
- 至少产生一个 Product 可展示报告。

### Task 4：Integrated Gate L0

目标：

> 建立三条路线共享的统一 gate，防止新路线再次变成不可比较的孤立实验。

输入：

- Task 1-3 artifact；
- LCDU baseline；
- strong baseline matrix；
- Product evidence requirement。

输出：

- `dcl_prs_gate_index`；
- route coverage ledger；
- paper claim boundary；
- product readiness score。

验收：

- 所有 artifact 有 schema version；
- 所有 claim 区分 research evidence 和 product demo evidence；
- CCF-A gate 不允许被 single split 关闭；
- Product readiness 不允许只看 UI demo。

## 7. 验证方案

### 7.1 数据与 split

第一阶段继续使用现有公开数据切片，不重新定义 benchmark。

必须保留：

- calibration split；
- heldout split；
- test split；
- salted repeat；
- strong baseline comparison。

新增数据可作为第二阶段扩展，但不能在第一阶段替代当前可复现协议。

### 7.2 Baseline

每条新路线至少比较：

1. deterministic anchor；
2. fixed party / ideology prior；
3. 当前 LCDU accepted method；
4. LCDU-LCR-SG；
5. 纯 LLM prompt 直接预测；
6. 无机制动态仿真。

### 7.3 指标

Research 指标：

- weighted JSD；
- worst segment delta；
- repeat success rate；
- beats strong baseline rate；
- accepted / rejected repair ratio；
- mechanism ablation impact；
- cross-task consistency。

Product 指标：

- report completeness；
- cohort trace coverage；
- explanation auditability；
- calibration evidence completeness；
- scenario reproducibility；
- customer-facing uncertainty disclosure。

### 7.4 Claim Boundary

所有 artifact 必须声明：

- 是否使用 test split；
- 是否使用历史 test failure 诊断；
- 是否是 official research claim；
- 是否只是 diagnostic run；
- 是否可用于 Product demo；
- 是否可用于 paper gate。

## 8. 阶段性验收标准

### 8.1 继续推进标准

满足以下任一条件，可以进入下一阶段：

1. A × B 在 repeat 上稳定超过 LCDU-SG；
2. A × C 产生可校准、可解释的动态仿真 trace；
3. B × C 能自动定位动态仿真的主要误差来源；
4. Integrated Gate 证明新框架的 evidence chain 明显优于当前 Product demo。

### 8.2 止损标准

满足以下条件之一，需要止损或降级：

1. 机制程序不能带来任何可测增益；
2. 错误归因无法稳定复现；
3. repair proposal 大量被 heldout gate 拒绝；
4. 动态仿真只能生成叙事，不能进入校准指标；
5. 新框架在 Product 侧无法形成比 LCDU 报告更强的说服力。

### 8.3 CCF-A 候选标准

新框架要成为 CCF-A 主贡献候选，至少需要：

1. 明确算法定义；
2. 至少两个公开政策反应任务；
3. 至少一个跨任务泛化结果；
4. 强 baseline 胜出；
5. 消融证明三条路线或关键组合不是装饰模块；
6. 失败边界清晰；
7. 论文 claim 不依赖单个本地模型或单个 prompt。

### 8.4 Product 核心竞争力标准

新框架要成为 Product 核心能力，至少需要：

1. 输入一项政策后能生成完整反应分析链路；
2. 人群反应、机制解释、动态轨迹和校准证据可同时展示；
3. 客户能看到哪些结论可靠、哪些只是探索；
4. 系统能自动提出下一步数据需求或修复方向；
5. 小规模 LLM 运行也能形成可审计 evidence chain。

## 9. 第一轮实施顺序

虽然三条路线可以并行探索，但第一轮建议按以下依赖组织：

1. 先做 Task 4 的 artifact/gate skeleton，统一证据格式；
2. 并行做 Task 1 和 Task 2，因为机制生成与错误归因可以共享 segment failure corpus；
3. 在 Task 1 有稳定 mechanism program 后，启动 Task 3；
4. 最后用 Task 4 生成第一轮 route coverage ledger 和结论。

如果资源允许，可以开三个 worktree：

- `dcl-prs-mechanism`；
- `dcl-prs-repair`；
- `dcl-prs-simulation`。

但所有 worktree 必须写入同一类 artifact schema，避免再次出现路线不可比较。

## 10. 需要用户提供的帮助

第一阶段我可以先用当前公开数据和本地/已配置 API 推进，不强依赖额外材料。

但如果要提升 Research 和 Product 质量，后续最好由用户提供：

1. 真实政策研究机构更关心的 3-5 类政策题目；
2. Product 目标客户的典型报告格式；
3. 哪些结论最有商业说服力，例如风险预警、分群解释、政策沟通建议、舆情演化；
4. 是否允许引入更多公开数据源；
5. 是否允许把部分 LLM 运行成本用于机制生成和仿真 trace。

## 11. 本阶段结论

本 spec 的核心结论是：

> 后续不再把 LCDU 的局部效果提升作为主战场，而是以 DCL-PRS 为新的研究空间。LCDU 保留为校准和审计基础设施，新的创新点来自机制生成、失败归因自动修复、群体动态仿真，以及三者的可验证组合。

第一轮工作不以“跑出最好数字”为唯一目标，而以明确回答以下问题为目标：

1. 机制程序是否能成为可检验中间层？
2. 自动错误归因是否能替代人工 prompt/persona 调参？
3. 群体动态仿真是否能从 demo 叙事变成可校准证据？
4. 三条路线组合后是否形成比 LCDU 更强的 Research / Product 共同壁垒？
