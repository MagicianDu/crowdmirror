# 第 1 轮并行正交主线执行计划

## 1. 计划目标

本计划对应 [2026-05-22-parallel-orthogonal-tracks-design.md](/Users/dm/Documents/cc-社会计算器-worktrees/research/docs/superpowers/specs/2026-05-22-parallel-orthogonal-tracks-design.md) 的第 1 轮执行层拆解。

本轮目标不是把 4 条路线都做深，而是：

1. 用统一 gate 跑出 4 条路线的第一版候选族；
2. 用单轴 prefilter 快速判断哪类路线有潜力；
3. 在本轮结束时形成 `保留 / 观察 / 止损` 结论；
4. 为第 2 轮只保留 2 条最强路线做准备。

## 2. 本轮统一规则

### 2.1 固定输入

所有路线共享：

1. 同一任务：`policy-reaction`
2. 同一模型配置：`openai/gpt-oss-20b`
3. 同一 prefilter 配置：`12x3 seed11`
4. 同一 baseline：
   - `calibration-split held-out baseline`
5. 同一对照主方法：
   - `LCDU L3 h02/i01`

### 2.2 本轮统一输出

每条路线都必须交付：

1. `candidate set artifact`
2. 单候选导出 artifact
3. Product cohort manifest
4. segment prediction artifact
5. official held-out benchmark
6. runtime effect artifact
7. route-level matrix
8. `RESULTS.md` 回填

### 2.3 本轮统一验收

每条路线按下列逻辑判断：

1. **失败**
   - 没有超过 baseline
2. **弱信号**
   - 超过 baseline，但没有超过 `LCDU L3`
3. **强信号**
   - 明显超过 `LCDU L3`

本轮只允许强信号路线直接晋级。弱信号路线最多保留一条进第 2 轮。

## 3. 路线 A：Segment Program Search

### 3.1 目标

验证更强的 segment-level synchronized program 是否还有超过 `LCDU L3` 的空间。

### 3.2 本轮实现边界

1. 不重新发明新的 latent 层；
2. 只在 segment-level prompt-anchor program 上做 family 设计；
3. 优化器只用小规模启发式组合，不引入复杂搜索基础设施。

### 3.3 L0 交付

1. 构造 4 个 `segment program family` 候选：
   - soft guard family
   - mixed numeric/qualitative family
   - segment crossover family
   - selective anchor-heavy family
2. 跑 `12x3 seed11` prefilter
3. 输出 matrix

### 3.4 成功标准

至少有 1 个候选：

1. 明显优于 baseline
2. 并且单轴上超过 `LCDU L3 i01`

### 3.5 止损标准

1. 全部回退，直接停；
2. 只有弱正向且结构上与 `LCDU L3` 没有本质区别，停。

## 4. 路线 B：Latent Response Program

### 4.1 目标

验证更高层 latent response 表示是否能摆脱 `axis patch` 的表示瓶颈。

### 4.2 当前起点

当前已有：

1. `LRP L0`
2. `LRP L1`

已知事实：

1. 有弱单轴正向；
2. 但没有超过 `LCDU L3`；
3. `L1` 只是收窄了爆炸面，没有提升上限。

### 4.3 本轮实现边界

1. 不继续做 `L2` 微调式修补；
2. 只允许重新定义更强的 `latent family`；
3. 重点是新的 program family，不是更细小参数搜索。

### 4.4 L0 交付

1. 设计 4 个新 `latent family`：
   - low-income dominant
   - high-price dominant
   - relief-priority hybrid
   - baseline-inertia suppressor
2. 跑 `12x3 seed11` prefilter
3. 输出 matrix

### 4.5 成功标准

至少有 1 个候选明显高于当前 `LRP L1` 上限，并接近或超过 `LCDU L3`。

### 4.6 止损标准

1. 仍然只在 `0.01` 级别弱正向徘徊，停；
2. 再次出现大面积爆炸回退，停。

## 5. 路线 C：Constraint Program

### 5.1 目标

验证是否应直接把更新对象提升为群体分布与排序约束程序，而不是 persona/segment patch。

### 5.2 本轮实现边界

1. 先做最小 `constraint program compiler`
2. 不直接做复杂 OR 求解器
3. 用一组小而明确的群体约束生成 candidate

### 5.3 L0 交付

1. 定义 4 个 constraint family：
   - low-income rank preservation
   - high-price distribution smoothing
   - dual-constraint balanced family
   - relief-dominant population family
2. 编译回 Product candidate artifact
3. 跑 `12x3 seed11` prefilter

### 5.4 成功标准

如果约束程序路线在第一轮就能超过 `LRP` 和 `L5`，即视为强候选。

### 5.5 止损标准

1. 若候选只是换名字的 patch，停；
2. 若全体回退，停。

## 6. 路线 D：Prototype / Retrieval Program

### 6.1 目标

验证“稳定原型检索 + 程序重组”是否能形成比手工 family 更强的单轴候选。

### 6.2 本轮实现边界

1. 只做最小 prototype catalog
2. 不引入复杂 embedding/外部检索基础设施
3. 先用已有 accepted / near-accepted 候选与失败候选做 prototype source

### 6.3 L0 交付

1. 建 4 类 prototype：
   - accepted stable prototype
   - weak-positive prototype
   - axis-failure prototype
   - constraint-heavy prototype
2. 生成 4 个 retrieval-recomposed candidates
3. 跑 `12x3 seed11` prefilter

### 6.4 成功标准

如果 retrieval 路线能比手工 family 更快打出超过 `LCDU L3` 的候选，则进入第 2 轮。

### 6.5 止损标准

1. 退化成模板拼接，停；
2. 只复制已有 `LCDU L3` 表达，不形成新增益，停。

## 7. 并行执行策略

### 7.1 并行层级

本轮不是 4 条路线完全同步到底，而是两层并行：

1. **设计与脚手架并行**
   - 4 条路线都先定义 L0 candidate family 和最小编译器
2. **prefilter 执行并行**
   - 谁先完成 candidate set，谁先跑 `12x3 seed11`

### 7.2 分支策略

建议按路线开 research 分支：

1. `research/track-a-segment-program`
2. `research/track-b-latent-program`
3. `research/track-c-constraint-program`
4. `research/track-d-prototype-retrieval`

当前主 worktree 保留为主控与结果汇总，不作为长期实验堆积点。

## 8. 本轮结束时必须回答的问题

第 1 轮结束后，必须明确回答：

1. 哪两条路线最有希望进入第 2 轮？
2. 哪些路线应当立即止损？
3. 当前是否已经有路线在单轴上超过 `LCDU L3`？
4. 如果没有，哪条路线最接近主线竞争资格？

## 9. 第 1 轮完成标准

只有满足下面条件，才算第 1 轮完成：

1. 4 条路线全部有 matrix artifact；
2. 每条路线都有 Research 结论摘要；
3. `RESULTS.md` 已回填；
4. 形成一份轮次总结，明确：
   - 晋级路线
   - 观察路线
   - 止损路线

## 10. 当前建议执行顺序

为了尽快看到结论，建议按下面顺序推进：

1. 路线 C：Constraint Program
   - 与当前方法族最正交，最值得先验证
2. 路线 D：Prototype / Retrieval Program
   - 第二个正交方向
3. 路线 A：Segment Program Search
   - 低成本补齐
4. 路线 B：Latent Response Program
   - 作为已有弱信号路线，最后补齐，不再先行独占预算

这样能最大程度避免继续在同一表示层里僵持。
