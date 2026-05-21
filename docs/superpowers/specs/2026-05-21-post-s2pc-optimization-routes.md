# 后 S2PC 阶段自动化更新路线比较

**日期：** 2026-05-21

**适用范围：** `cc-社会计算器` Research 线，面向 policy-reaction 校准与 Product 可迁移更新方法设计。

**当前状态：** 路线比较设计稿，不包含代码实现。

---

## 1. 背景与问题重述

当前项目已经得到一个比较稳定的事实：

1. `calibration_split_prompting` 仍然是当前最稳的 accepted 方法。
2. S2PC 证明了“自动化更新方向并非纯噪声”，因为它反复出现局部正向信号。
3. 但 S2PC 当前形式没有跨过“稳定方法成立”的门槛：
   - `c01` 有单点 improvement；
   - `trust_only` 有更窄的单点 improvement；
   - 但一旦扩到 `seed/scale`，结果转为 `mixed`；
   - 更细的参数级拆分没有带来更强、更稳的新信号。
4. TextGrad 在 policy-reaction 方向尚未形成 held-out accepted 证据。

因此，后续问题已经不再是：

> “还能不能找到更好的 prompt patch？”

而是：

> “如何把自动化更新问题重新表述成一个更适合稳定优化、可审计验收、可迁移到 Product 的方法路线问题？”

本设计文档的目标就是比较多条候选路线，而不是继续比较单个算法名。

---

## 2. 为什么单点算法比较意义不大

如果只比较“遗传算法 vs 贝叶斯优化 vs TextGrad”，很容易陷入两个误区：

1. **忽略优化对象差异**
   - 有的方法优化 prompt 文本；
   - 有的方法优化结构化参数；
   - 有的方法优化更新规则选择；
   - 有的方法优化群体约束或 latent state。

2. **忽略目标函数差异**
   - 有的方法优化单次 held-out loss；
   - 有的方法优化均值 + 方差；
   - 有的方法优化 worst-case；
   - 有的方法优化可解释性与复杂度约束。

所以后续应该比较的是**路线级方案**：

- 它优化什么对象；
- 它用什么目标函数；
- 它如何搜索；
- 它如何 gate；
- 它能否形成 research 贡献；
- 它能否形成 product 壁垒。

---

## 3. 统一比较框架

后续所有候选路线统一按以下维度比较：

1. **优化对象**
   - prompt 文本
   - persona 参数
   - segment prior
   - latent state
   - route / selector / update rule
   - prototype / constraint set

2. **目标函数**
   - 单次 held-out loss
   - mean loss
   - worst-case loss
   - mean + instability penalty
   - 多目标加权组合

3. **搜索空间类型**
   - 连续
   - 离散
   - 混合
   - 程序化组合

4. **评估方式**
   - 单次 `12x3 seed11`
   - repeat-aware
   - scale-aware
   - held-out gate

5. **Research 价值**
   - 是否像一个方法贡献
   - 是否容易解释
   - 是否能形成 reviewer-facing 证据链

6. **Product 价值**
   - 是否容易接 runtime
   - 是否容易做客户可解释报告
   - 是否能形成长期技术壁垒

7. **止损条件**
   - 什么情况下不值得继续投评估预算

---

## 4. 六条候选路线

### 4.1 路线 0：S2PC 当前路线

**定义**

- 语义残差挖掘
- semantic factor 检索
- 结构化参数 patch
- subset / selector / runtime effect / stability gate

**优化对象**

- factor-level persona parameter patch
- calibration anchor
- selector rule

**目标函数**

- 当前主要还是单次 held-out runtime loss
- 稳定性是后置 gate，不是前置目标

**优点**

- 已有完整 artifact 链
- 可解释性较强
- 与 Product 连接最成熟

**问题**

- 现在已知只形成局部正信号
- 目标函数没有原生地把稳定性纳入优化
- 搜索行为仍接近局部 patch search

**当前结论**

- 保留为对照线
- 不再继续深挖同一家族细分

---

### 4.2 路线 1：TextGrad / Prompt Rewrite 路线

**定义**

- 使用 LLM critique / text feedback / prompt rewrite 生成候选更新

**优化对象**

- prompt 文本
- persona 描述
- anchor 语言表达

**目标函数**

- 通常是单次 loss 改善
- 接受/拒绝依赖 held-out gate

**优点**

- 自动化程度高
- 实现快
- 容易快速出候选

**问题**

- 可解释性弱
- 变更空间过大
- 非常容易出现偶然命中
- 当前 policy-reaction 证据不足

**当前结论**

- 保留为对照线
- 不作为下一阶段主线

---

### 4.3 路线 A：结构化参数搜索 + 贝叶斯/进化搜索

**定义**

先把更新问题结构化，再用黑盒优化方法搜索：

- 连续变量：anchor strength、latent parameter、threshold
- 离散变量：是否启用某个 update component、是否选某个 prototype
- 搜索器：贝叶斯优化、CMA-ES、小种群 GA、进化策略

**优化对象**

- persona latent parameter
- anchor strength
- prototype weight
- selector threshold
- segment prior weight

**目标函数**

- 第一阶段可用单次 held-out loss
- 第二阶段可升级为 mean loss 或多目标 loss

**优点**

- 比 prompt rewrite 更结构化
- 比 S2PC subset search 更像真正黑盒优化
- 容易控制搜索边界
- 可直接复用现有 held-out gate

**问题**

- 如果还只优化单次 loss，仍可能重复 S2PC 的“单点 improvement, repeat 不稳”
- 变量定义不好时，会退化成另一种 patch search

**适合的 MVP**

- 限制变量数在 `4-8` 个
- 先做 `12x3 seed11`
- 只与 `s02/trust_only` 和 baseline 比
- 若优于 `s02`，再进入 repeat

**判断**

- 是强候选
- 但更适合作为路线 B 的子组件，而不是单独的最终主线

---

### 4.4 路线 B：鲁棒目标 + 进化搜索

**定义**

不是单纯换搜索器，而是**先换目标函数**：

```text
robust_score =
  mean_heldout_loss
  + alpha * instability_penalty
  + beta * worst_case_loss
  + gamma * complexity_penalty
```

然后再用进化搜索或其他黑盒优化方法搜索结构化更新变量。

**优化对象**

- 与路线 A 相同，但更强调结构化变量而不是文本

**目标函数**

- mean loss
- variance / instability
- worst-case loss
- complexity penalty

**优点**

- 直接对准当前最大痛点：不稳
- 不会再先追单点 improvement 再事后补稳定性
- research 价值明显高于单次 loss search
- product 价值也更强，因为客户真正关心稳定

**问题**

- 每个候选评估成本更高
- 需要先定义 repeat budget 和鲁棒集
- 如果变量空间太大，成本会迅速膨胀

**适合的 MVP**

- 小变量空间
- 小种群
- 低代数
- repeat 轴只放 `12x3 seed11`, `12x3 seed17`, `16x3 seed11`
- 只接受明显优于现有 `s02` 的候选

**判断**

- **当前最推荐主线**
- 它既回答“怎么搜”，也回答“搜什么目标”

---

### 4.5 路线 3：OR 组合优化路线

**定义**

不直接优化 prompt 或参数数值，而是优化高层组合决策：

- 哪些 update rule 被激活
- 哪些 segment 使用哪种更新
- 哪些 prototype 被选中
- 哪些约束被启用

可视为：

- 外层：组合优化 / MIP / 启发式分配
- 内层：LLM black-box 评估

**优化对象**

- rule selection
- segment-to-update assignment
- prototype activation
- evaluation budget allocation

**目标函数**

- 组合成本
- 复杂度惩罚
- 稳定性优先的组合目标

**优点**

- 可解释性强
- 适合做“可审计更新程序”
- 很像真正的 OR + AI 融合路线

**问题**

- 不适合直接优化原始 prompt 文本
- 必须先有更稳定的底层 update primitive
- 否则只是把弱 primitive 排列组合

**判断**

- 适合作为第二阶段高层调度器
- 不适合作为立刻落地的第一个 MVP

---

### 4.6 路线 4：分布约束 / Latent State 更新路线

**定义**

不把 prompt 当主要优化对象，而是：

1. 定义群体级约束或 latent state；
2. 自动更新这些中间表示；
3. 再由程序化渲染层投射到 persona/runtime。

可用的 latent state 例子：

- trust
- cost pressure
- benefit immediacy
- policy complexity aversion

可用的群体约束例子：

- segment 排序约束
- 某政策支持率上下界
- segment 间差值约束
- 平滑/熵约束

**优化对象**

- group-level latent state
- distribution constraints
- segment prior program

**目标函数**

- 分布对齐
- 约束满足度
- 稳定性

**优点**

- 更新对象更稳定
- 更有研究创新潜力
- 更接近“社会计算模型”，而不是 prompt 工程

**问题**

- 需要新建中间表示层
- 工程改造比路线 A/B 大
- MVP 成本高于 A/B

**判断**

- 长期潜力很高
- 适合作为 A/B 后的下一阶段主线

---

## 5. 路线级比较结论

| 路线 | 优化对象 | 目标函数 | 稳定性潜力 | Research 潜力 | Product 潜力 | MVP 难度 | 当前建议 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S2PC 当前路线 | factor patch / selector | 单次 held-out loss | 低到中 | 中 | 中 | 已完成 | 只做对照 |
| TextGrad 路线 | prompt 文本 | 单次 loss | 低 | 低到中 | 低 | 低 | 只做对照 |
| 路线 A | 结构化参数 | 单次或多目标 | 中 | 中到高 | 高 | 中 | 可做候选 |
| 路线 B | 结构化参数 + 鲁棒目标 | mean + instability + worst-case | 高 | 高 | 高 | 中到高 | **优先主线** |
| OR 组合优化 | rule / prototype / assignment | 组合目标 | 中到高 | 高 | 高 | 高 | 第二阶段 |
| 分布约束 / latent state | latent / constraint | 约束满足 + 鲁棒性 | 高 | 很高 | 高 | 高 | 中长期主线 |

---

## 6. 推荐推进顺序

### 第一优先级：路线 B

原因：

1. 当前最大问题不是“不会搜索”，而是“搜索结果不稳”。
2. 路线 B 把稳定性直接放进目标，而不是事后补 gate。
3. 它可以复用路线 A 的结构化变量定义，不需要从零重建所有工程。

### 第二优先级：路线 A

原因：

1. 如果路线 B 太贵，A 可以先作为降配版 MVP。
2. A 也是构建 B 所需结构化变量空间的前置工作。

### 第三优先级：分布约束 / latent state 路线

原因：

1. 这条线 research 潜力最大；
2. 但新建中间表示层成本更高；
3. 更适合在 A/B 路线把结构化优化框架跑通后进入。

### 第四优先级：OR 组合优化

原因：

1. 需要已有较稳的底层 primitive；
2. 更像第二层调度与编排，而不是第一层 candidate generator。

---

## 7. 建议的 MVP 设计

### 7.1 路线 B MVP

**目标**

验证“鲁棒目标 + 小种群进化搜索”是否能比当前 `s02/trust_only` 更稳。

**变量**

限制在 `4-6` 个：

- `prior_anchor_strength`
- `trust_multiplier`
- `segment_prior_weight`
- `selector_gate_threshold`
- `prototype_activation_flag`（可选）

**目标函数**

```text
score =
  mean(loss over seed11, seed17, 16x3-seed11)
  + alpha * std(loss)
  + beta * max(loss)
  + gamma * update_complexity
```

**搜索器**

- 小种群进化搜索
- population 不超过 `8`
- generation 不超过 `3`

**接受标准**

必须同时满足：

1. `mean loss` 优于当前 `s02`
2. `worst-case loss` 不劣于 calibration baseline 的容忍阈值
3. 至少 `3` 个评估点里 `2` 个 improved 或 `1` improved + `2` no_change

**止损标准**

出现以下任一情况即停止：

1. 最佳候选仍然只有单点评估 improved
2. 平均改善不超过当前 `s02`
3. worst-case 明显恶化
4. 需要增加过多变量或代数才能勉强得到弱正向

---

### 7.2 路线 A MVP

如果路线 B 预算过高，则先做降级 MVP：

- 使用同一组结构化变量
- 但目标只看 `12x3 seed11`
- 搜索器用小规模贝叶斯或进化搜索

**注意**

路线 A 只在以下情况下才值得扩到 repeat：

1. 单次结果明显优于 `s02`
2. 幅度不是边际改善，而是至少显著高于当前 `0.011920716018`

否则直接止损，不再重复 S2PC 的路径。

---

## 8. 止损原则

后 S2PC 阶段必须显式执行止损，而不是无限追加搜索预算。

### 对所有路线共用的止损标准

1. **弱正向不扩 repeat**
   - 如果只是比 baseline 略好，但弱于现有最好候选，不继续。

2. **单点 improvement 不当作主线成立**
   - 必须看 repeat / scale。

3. **复杂度上升但收益不升**
   - 立即止损。

4. **只能靠 selector hindsight 才有效**
   - 不进入 Product 可部署路线。

### 对路线 B 的额外止损标准

如果鲁棒目标路线在第一轮 MVP 后仍然无法超过当前 `s02` 的单点效果，且 worst-case 没有更好表现，则说明问题可能不在搜索器，而在更新表示本身，需要转向 latent state / 分布约束路线。

---

## 9. 最终建议

当前阶段的推荐结论如下：

1. **停止继续深挖 S2PC 当前 patch 家族**
   - 证据已经足够说明这条线有局部信号，但不构成稳定方法。

2. **不再把“找更好的 prompt”当成主问题**
   - 更重要的是重新定义更新变量与目标函数。

3. **下一阶段主线建议切到路线 B**
   - 即：**鲁棒目标 + 结构化黑盒优化 + 小种群进化搜索**

4. **路线 A 作为路线 B 的降配版或前置脚手架**

5. **OR 组合优化与 latent state 路线保留为第二阶段扩展**
   - 当前不作为第一个 MVP

一句话总结：

> 后 S2PC 阶段，不应继续围绕单点 patch 搜索做更多变体，而应把问题提升为“面向稳定性目标的结构化黑盒优化”。

