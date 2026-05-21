# Route-B 止损复盘

**日期：** 2026-05-21

**适用范围：** `cc-社会计算器` Research 线，policy-reaction 自动化更新方法从 S2PC 过渡到 Route-B 的探索总结。

**当前状态：** 复盘文档，记录已完成尝试、负结果证据和后续约束。

---

## 1. 为什么需要这份复盘

Route-B 不是一个孤立实验，而是一次明确的方法转向：

1. S2PC 已经证明“自动化更新”不是纯噪声；
2. 但 S2PC 当前形式没有形成稳定方法；
3. Route-B 的目标是把“稳定性”前置成优化目标，而不是只在后验 gate 中发现候选不稳。

现在这条线已经跑到一个足够清楚的结论：

> 当前 Route-B 家族在现有变量表示下，不值得继续追加评估预算。

这份文档的目的不是重复 `RESULTS.md`，而是把 Route-B 的尝试逻辑、失败原因和止损边界单独整理出来，供后续换范式时直接复用。

---

## 2. 转向 Route-B 的起点

Route-B 不是从零开始提出的，而是来自 S2PC 证据链里的两个硬事实：

1. `c01` 和 `s02=trust_only` 都出现过单点正向 signal；
2. 但一旦扩到 `seed/scale`，结果转为 `mixed`，说明当前问题不是“有没有局部好点”，而是“能不能稳定保住它”。

因此当时的判断是：

- 问题不该继续表述成“如何找到更好的 prompt patch”
- 而应该改成“如何在 repeat-aware 目标下搜索更稳的结构化更新候选”

Route-B 的核心假设是：

> 如果把目标函数从单次 held-out loss 改成鲁棒目标，那么搜索器就有机会避开那些单点命中但不稳的候选。

---

## 3. Route-B 的定义

Route-B 在方法上做了两件事：

1. **目标函数变更**
   - 不再只看单次 held-out loss
   - 增加：
     - mean loss
     - instability penalty
     - worst-case loss
     - complexity penalty

2. **搜索候选保守化**
   - 不做自由 prompt rewrite
   - 只在 Product 可消费的结构化候选空间里搜索

对应 artifact：

- robust baseline  
  [policy-reaction-route-b-robust-score-s02-current-001.json](/Users/dm/Documents/cc-社会计算器-worktrees/research/experiments/results/policy_reaction_benchmark/policy-reaction-route-b-robust-score-s02-current-001.json)

这个 baseline 很关键，因为它第一次明确把 `s02=trust_only` 从“单次正向候选”降级成“repeat-aware 条件下 blocked 的候选”。

---

## 4. generation-0 做了什么

generation-0 的设计比较克制：

- 仍以 `s02=trust_only` 为基点
- 只对两类 patch 变量做小种群搜索：
  - `prior_anchor_strength`
  - `trust_multiplier`

对应实现与结果：

- 生成器  
  [policy_reaction_route_b_generation0.py](/Users/dm/Documents/cc-社会计算器-worktrees/research/experiments/policy_reaction_route_b_generation0.py)
- matrix  
  [policy-reaction-route-b-generation0-matrix-gpt-oss-20b-12x3-heldout-001.json](/Users/dm/Documents/cc-社会计算器-worktrees/research/experiments/results/policy_reaction_benchmark/policy-reaction-route-b-generation0-matrix-gpt-oss-20b-12x3-heldout-001.json)

结果：

- `candidate_count=4`
- `improved_count=1`
- `regressed_count=3`
- best candidate: `g04`
- `g04` loss = `0.000112017956`

但这一步没有进入 repeat，原因很直接：

- `g04` 虽然优于 baseline
- 但仍弱于已有 `s02=trust_only`
  - `s02` loss = `0.000111545213`
  - `g04` loss = `0.000112017956`

所以 generation-0 暴露出的不是“Route-B 完全没用”，而是：

> Route-B 的目标函数成立，但当前变量还太低层。

---

## 5. 为什么会有 generation-1

generation-1 的动机不是“再多试一次”，而是验证一个更具体的假设：

> generation-0 失败，也许不是因为 Route-B 思路错了，而是因为搜索变量仍然太像 patch parameter tuning。

于是 generation-1 把变量重定义成机制级离散变量：

- `anchor_regime`
- `trust_mode`
- `uncertainty_mode`
- `focus_mode`

设计草案在：

- [2026-05-21-route-b-variable-redefinition.md](/Users/dm/Documents/cc-社会计算器-worktrees/research/docs/superpowers/specs/2026-05-21-route-b-variable-redefinition.md)

这一步的核心目标是排除第二种可能：

> 也许换成更高层、Product 可编译的机制变量后，Route-B 才会打开有效空间。

---

## 6. generation-1 实际结果

generation-1 已经完整执行，包括：

- 候选生成
- Product runtime cohort
- segment prediction 导出
- held-out benchmark
- runtime effect matrix

对应实现：

- [policy_reaction_route_b_generation1.py](/Users/dm/Documents/cc-社会计算器-worktrees/research/experiments/policy_reaction_route_b_generation1.py)

对应核心 artifact：

- candidate set  
  [policy-reaction-route-b-generation1-current-001.json](/Users/dm/Documents/cc-社会计算器-worktrees/research/experiments/results/policy_reaction_benchmark/policy-reaction-route-b-generation1-current-001.json)
- effect matrix  
  [policy-reaction-route-b-generation1-matrix-gpt-oss-20b-12x3-heldout-001.json](/Users/dm/Documents/cc-社会计算器-worktrees/research/experiments/results/policy_reaction_benchmark/policy-reaction-route-b-generation1-matrix-gpt-oss-20b-12x3-heldout-001.json)

结果比 generation-0 更强烈，而且是负向的：

- `candidate_count=4`
- `improved_count=0`
- `regressed_count=4`
- `overall_status=all_candidates_regressed`

四个候选的 held-out loss：

- `h01 -> 0.01481642642`
- `h02 -> 0.030763241376`
- `h03 -> 0.011526513378`
- `h04 -> 0.086475999947`

对照 baseline：

- baseline loss = `0.000112890954`

最好的 `h03` 也远差于 baseline，`relative_loss_reduction = -101.103073813771`。

这说明：

> generation-1 不是“没有优于 s02”，而是“连 baseline 都没有接近”。

---

## 7. Route-B 到底失败在什么地方

这里需要说得更严格。

当前证据**不能**支持的说法：

- 不能说“所有鲁棒优化思路都失败了”
- 不能说“所有黑盒结构化搜索都失败了”

当前证据**能够**支持的说法是：

### 7.1 当前 Route-B 变量表示失败

不管是：

- generation-0 的 patch-level 变量
- 还是 generation-1 的 mechanism-level 离散变量

都没有在当前 held-out 目标上形成值得继续投入的候选。

### 7.2 当前 Route-B 搜索空间没有打开稳定正信号

generation-0 还能找到一个弱于 `s02` 的小正向点；
generation-1 连这一层都没有。

这说明当前问题不太像：

- “只差更大预算”

而更像：

- “表示层本身不对”

### 7.3 当前 Route-B 不适合作为下一阶段主线

因为它已经连续跨过两层止损线：

1. generation-0 没打赢 `s02`
2. generation-1 全面回退

在这种情况下继续做 generation-2，研究价值和工程价值都偏低。

---

## 8. 当前可以保留下来的经验

虽然结果是负向，但有几条经验是明确可复用的。

### 8.1 鲁棒目标是必要的

Route-B 最重要的正贡献不是找到好候选，而是把一个长期存在的问题显式化了：

> 单次 held-out improvement 不足以支持方法成立。

这一点应该保留给后续所有新范式。

### 8.2 Product 可编译约束是必要的

无论后面换成什么方法，候选都应继续满足：

- 可编译到 `candidate_prompt_components`
- 可进入 Product runtime
- 可回到 held-out benchmark

这条约束是正确的，不应放弃。

### 8.3 单轴预筛仍然有价值

generation-1 之所以值得做，是因为它用相对低预算排除了一个看起来合理的假设。

所以：

- 先做 `12x3 seed11`
- 再决定是否进入 repeat

这个 stop-loss 流程本身应该继续保留。

---

## 9. 明确不建议继续的路线

基于当前证据，下面这些方向不建议继续投入：

1. Route-B generation-2
2. 继续扩 generation-1 的 mechanism 组合数
3. 在当前 Route-B 家族内继续做更细的数值微调
4. 只靠增加更多本地 LLM 运行预算来试图“撞出”一个好点

原因很简单：

- generation-0 已经说明 patch-level 不够
- generation-1 已经说明当前 mechanism-level 也不够
- 再继续扩展，只会增加搜索成本，不会改变表示错误这个核心问题

---

## 10. 对下一阶段的约束

后续新范式必须满足至少三条要求：

1. **优化对象不能再只是当前 Route-B 这类局部 patch / 当前机制变量**
2. **目标函数必须继续保留 repeat-aware / robust 约束**
3. **候选必须保留 Product 可消费、Research 可审计的 artifact 形式**

换句话说，下一阶段要换的不是：

- 是否继续做 strict artifact
- 是否继续做 held-out gate

而是：

- **更新表示**
- **更新程序**
- **候选构造机制**

---

## 11. 当前结论

一句话总结：

> Route-B 的失败不是“鲁棒目标没有价值”，而是“当前 Route-B 家族在现有表示下已经没有继续投入的价值”。

这条线现在最适合的定位是：

- 已完成探索
- 已形成负结果证据
- 应当止损归档
- 作为后续新范式设计的反例与约束来源

这也正是它的研究价值所在。
