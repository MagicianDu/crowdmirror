# 并行正交技术主线设计

## 1. 文档目的

这份 spec 用来解决当前 research 线的一个结构性问题：

> 不能再沿着单一路径反复微调，而要先固定共同出发点、共同目标、共同 gate，再设计 4 条尽量正交的技术主线并行赛马，最终得到明确路线结论。

本 spec 不直接定义具体实验脚本实现，而定义：

1. 固定起点；
2. 固定目标；
3. 固定验收标准；
4. 每轮 4 条正交主线；
5. 总轮次与止损规则；
6. Research / Product 双线如何共享同一条判断逻辑。

## 2. 固定出发点

### 2.1 任务范围

任务固定在当前 `policy-reaction` research lane：

1. 数据任务不变；
2. baseline 不变；
3. Product runtime evidence chain 不变；
4. 目标不是重新发明 benchmark，而是在现有 benchmark 上找到更强更新路线。

### 2.2 当前已知事实

当前已经形成的稳定事实有：

1. `LCDU L3 h02/i01` 是当前已接受主方法；
2. `S2PC`、`Route-B`、`LCDU L5 axis repair` 都没有成为新主线；
3. `LRP L0/L1` 说明更高层表示不是死路，但目前只有弱单轴信号；
4. 当前最重要的问题不是“完全没有信号”，而是：
   - 很多路线只能产生局部或弱单轴正向；
   - 很难明显超过 `LCDU L3`。

## 3. 固定目标

### 3.1 总目标

本阶段的总目标不是“多跑一些实验”，而是：

> 在有限轮次内判断，是否存在一条比 `LCDU L3` 更强的新技术主线；如果没有，就明确停止新路线扩展，回到 `LCDU L3` 主线固化。

### 3.2 Research / Product 双主线等权目标

#### Research 目标

1. 找到可重复、可审计、边界清楚的方法增量；
2. 如果没有更强方法，也要形成可辩护的负结果结论；
3. 不把弱信号包装成新主贡献。

#### Product 目标

1. 所有主线都必须能落回统一 runtime evidence chain；
2. 任何有效路线都必须能转成 Product 可调用能力；
3. 任何失败路线都要留下可审计资产，而不是只有实验日志。

## 4. 统一验收标准

所有主线共享同一套 gate。

### 4.1 双基线

每条主线必须同时比较两条基线：

1. `calibration-split held-out baseline`
2. `当前 research 最优 accepted method`，即 `LCDU L3 h02/i01`

### 4.2 优先目标

本阶段固定为：

> 幅度优先

也就是先看是否能明显超过 `LCDU L3`，再决定是否值得进入 repeat / stability / generalization。

### 4.3 路线级判定

对每条主线，第一轮判断只分三类：

1. **失败**
   - 没有超过 baseline
2. **弱信号**
   - 超过 baseline，但没有超过 `LCDU L3`
3. **强信号**
   - 明显超过 `LCDU L3`

只有强信号路线才有资格进入更高预算阶段。

## 5. 正交维度

本 spec 不按单一维度拆路线，而是同时考虑三种正交维度：

1. **表示层正交**
2. **优化器正交**
3. **系统层级正交**

但不做完全笛卡尔积展开。第一轮只选 4 条代表性主线。

## 6. 第一轮 4 条主线

### 6.1 主线 A：Segment Program Search

#### 目标

验证更强的 segment-level program，是否还能超出当前 `LCDU L3` 的表达上限。

#### 组合

1. 表示层：`prompt-anchor synchronized program`
2. 优化器：`启发式 / 小规模进化搜索`
3. 系统层级：`segment-level`

#### 特点

1. 离现有 `LCDU` 最近；
2. 工程成本最低；
3. 风险是容易重新掉回局部 patch 家族。

### 6.2 主线 B：Latent Response Program

#### 目标

验证更高层 latent 表示，是否能打破 axis-level patch 的失效边界。

#### 组合

1. 表示层：`latent response program`
2. 优化器：`结构化收窄 + program family prefilter`
3. 系统层级：`axis / segment hybrid`

#### 特点

1. 与 `LCDU L5` 明确区分；
2. 更像下一代方法层；
3. 当前已知风险是只能得到弱单轴信号。

### 6.3 主线 C：Constraint Program

#### 目标

验证是否应直接把更新对象上升为群体约束程序，而不是再修 persona / segment 文案。

#### 组合

1. 表示层：`distribution / ordering constraint program`
2. 优化器：`鲁棒筛选 / OR 风格约束选择`
3. 系统层级：`population-level`

#### 特点

1. 和当前 patch/program 家族真正正交；
2. 最接近 reviewer-facing 方法贡献；
3. 工程复杂度高于 A/B。

### 6.4 主线 D：Prototype / Retrieval Program

#### 目标

验证“从稳定原型中检索并重组更新程序”，是否比手工构造的 program family 更强。

#### 组合

1. 表示层：`prototype / retrieval`
2. 优化器：`retrieval + rerank`
3. 系统层级：`persona / segment hybrid`

#### 特点

1. 与 rule-based / latent-based 路线区分明显；
2. 有潜力形成新的技术壁垒；
3. 风险是退化成模板拼接。

## 7. 总轮次设计

### 7.1 总轮次

固定为 **3 轮**。

不建议超过 3 轮。  
3 轮结束后必须形成路线结论。

### 7.2 第 1 轮：粗筛

#### 目标

用 4 条正交主线快速判断哪一类组合最有潜力。

#### 每条主线的动作

1. 定义 L0/L1 候选族；
2. 跑单轴 prefilter；
3. 同时比较 baseline 和 `LCDU L3`；
4. 输出 `保留 / 观察 / 止损`。

#### 验收

本轮不是要找到最终主线，而是淘汰明显无效路线。

### 7.3 第 2 轮：强化

#### 目标

只保留第 1 轮最强的 2 条主线，继续收窄。

#### 每条保留主线的动作

1. 收窄 candidate family；
2. 优先追求单轴幅度；
3. 判断是否首次出现“明显超过 `LCDU L3`”的候选。

#### 验收

到这一轮结束，至少应该知道：

1. 是否存在新主线竞争者；
2. 哪些路线可以正式止损。

### 7.4 第 3 轮：终局判定

#### 目标

对最多 1 到 2 条最强路线做 final gate。

#### 动作

1. 若某路线已经显著超过 `LCDU L3`，进入 repeat/stability；
2. 若仍未超过 `LCDU L3`，停止扩展；
3. 形成最终结论：
   - 新主线成立；
   - 或 `LCDU L3` 继续作为主方法。

## 8. 止损规则

### 8.1 单路线止损

对任意主线：

1. 没过 baseline：立即停；
2. 连续两轮没超过 `LCDU L3`：停；
3. 只重复已有弱信号，不产生新机制信息：停。

### 8.2 全局止损

如果 3 轮结束后：

1. 没有任何路线明显超过 `LCDU L3`；
2. 或只有弱单轴信号，没有稳定升级迹象；

则本阶段新路线探索结束，Research / Product 都回到 `LCDU L3` 主线固化。

## 9. 分支策略

建议按主线开 branch，而不是按每个小实验开 branch。

### 9.1 分支结构

1. `research/mainline-lcdu`
2. `research/track-a-segment-program`
3. `research/track-b-latent-program`
4. `research/track-c-constraint-program`
5. `research/track-d-prototype-retrieval`

### 9.2 Product 策略

Product 不为每条线单独长期分叉。

做法是：

1. Product 保持统一 runtime 契约；
2. Research 哪条线打出强信号，再通过 candidate artifact 接入 Product；
3. Product 只吸收值得保留的方法能力。

## 10. 每轮必交付物

每一轮、每一条主线都必须交付：

1. candidate set artifact
2. 单轴 matrix artifact
3. 结论摘要：
   - 是否过 baseline
   - 是否超过 `LCDU L3`
   - 是否值得继续
4. `RESULTS.md` 回填

没有这 4 项，不算完成。

## 11. 最终希望得到的结论类型

本 spec 的最终目标不是“多做实验”，而是尽快把结果收成以下三类之一：

### 结论 A

存在一条新主线，明显超过 `LCDU L3`，成为下一阶段主方法。

### 结论 B

不存在明显超过 `LCDU L3` 的新主线，`LCDU L3` 继续作为主方法，其它路线作为负结果与备选资产归档。

### 结论 C

当前没有路线超过 `LCDU L3`，但某条路线暴露出更强的下一代表示层，值得进入下一阶段独立研究。

## 12. 当前建议

按当前已有证据，我建议：

1. 先不要继续在 `LRP` 单线里微调；
2. 先写出 4 条主线的第一轮 L0 目标和最小 candidate family；
3. 再正式进入第 1 轮并行粗筛。

这能避免继续在单一路线里僵持不下，也能让失败路线更早暴露。
