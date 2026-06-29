# 路线 B 变量重定义草案

**日期：** 2026-05-21

**适用范围：** `cc-社会计算器` Research 线，policy-reaction 自动化更新方法在 Route-B 主线下的下一阶段实现。

**当前状态：** 设计草案，不包含代码实现。

---

## 1. 为什么现在需要重定义变量

Route-B 已经完成两件关键工作：

1. 定义了 repeat-aware robust objective；
2. 跑完了 generation-0 小种群单轴预筛。

当前结论不是“Route-B 失败”，而是：

> Route-B 的目标函数是对的，但 generation-0 使用的变量表示还不够好。

具体证据：

- `s02/trust_only` 在单次 `12x3 seed11` 上有正向信号；
- 但在 Route-B 的 repeat-aware robust score 下被 `blocked_by_stop_loss`；
- generation-0 的 4 个候选里，只有 `g04` 单次 improved；
- 但 `g04` 仍弱于原始 `s02`，因此不进入 repeat。

这说明问题更像是：

1. 不是目标函数没压住不稳定；
2. 而是当前变量仍然太接近 `patch parameter tuning`；
3. 搜索器只能在一个过窄、过浅的表示层里打转。

所以，下一步不该直接上 generation-1，而应先重定义变量。

---

## 2. 当前变量表示的局限

Route-B generation-0 当前实际搜索的是：

1. `prior_anchor_strength`
2. `trust_multiplier`
3. 少量对应的 `segment_prompt` 文本修饰

它的优点是：

- 易接 Product runtime；
- 搜索预算低；
- 容易审计。

但局限也很明显：

### 2.1 变量层级过低

当前变量本质上还是：

- “某个 trust patch 调多少”

而不是：

- “这个 segment 的判断机制该以什么方式变化”

这会导致：

- 搜索空间虽然小，
- 但表达能力也很弱，
- 最终只能得到局部小修补。

### 2.2 变量语义过于绑定当前候选

当前变量都来自 `s02/trust_only` 这一支：

- 一旦这支本身不稳，
- 后续搜索就只是围绕一个弱基点做局部扰动。

换句话说，generation-0 更像：

> 围绕 `s02` 的 trust 参数扰动

而不是：

> 面向 policy-reaction 机制的 Route-B 候选空间搜索

### 2.3 缺少“群体级控制变量”

当前变量没有显式表达：

- segment prior 应该多强；
- segment 间差异应保留多少；
- anchor 与 sampling 不确定性的关系；
- 最坏情况下应该优先牺牲什么。

于是 Route-B 虽然换了鲁棒目标，
但变量还是停留在 patch 层，目标和变量不匹配。

---

## 3. Route-B 下一阶段的变量设计原则

重定义后的变量必须满足以下原则：

### 3.1 比 patch 更高一层

变量不应只是某个参数值，而应尽量表达：

- segment-level prior policy
- uncertainty handling
- group-level trust regime
- update activation pattern

### 3.2 Product 可消费

变量最终仍要能落回 Product runtime，所以不能定义成完全抽象、无法渲染的 latent。

必须满足：

- 能编译到 `candidate_prompt_components`
- 或能编译到有限个结构化 patch
- 或能转成稳定的 segment prior text / anchor text

### 3.3 与鲁棒目标同层

既然 Route-B 优化的是：

- mean
- instability
- worst-case

那么变量也应该支持这些目标：

- 是否更保守
- 是否减少过强锚定
- 是否降低最坏情况波动
- 是否减少 segment 间过拟合差异

### 3.4 搜索预算可控

第一轮重定义后的变量数仍应保持在 `4-6` 个，
否则 generation-1 预算会迅速失控。

---

## 4. 建议放弃的变量

以下变量不建议再作为下一轮主变量：

1. 单独的 `prior_anchor_strength`
2. 单独的 `trust_multiplier`
3. 仅基于 `toward_min/toward_max/toward_mid` 的局部比例扰动
4. 仅依赖 segment suffix 的自然语言微调

原因很简单：

- 这些变量已经在 generation-0 中证明不足以打开新空间；
- 继续扩大这组变量，只会增加预算，不会显著提高表达能力。

---

## 5. 建议的新变量层级

下一轮 Route-B 建议把变量重定义到下面四类。

### 5.1 Segment Prior Regime

不再把变量写成单个 anchor 参数，而是写成：

- `anchor_regime`

候选取值：

1. `conservative`
2. `balanced`
3. `assertive`

语义：

- `conservative`：更弱锚定，更高不确定性保留
- `balanced`：保留现有 calibration split anchor，但不过度放大
- `assertive`：更强 anchor，更强调 segment-specific policy prior

好处：

- 比单个 `prior_anchor_strength` 更符合 Product 可解释逻辑；
- 更适合和 worst-case 风险对齐。

---

### 5.2 Trust Mediation Mode

把 `trust_multiplier` 从数值变量提升成机制变量：

- `trust_mode`

候选取值：

1. `direct`
2. `capped`
3. `gated`

语义：

- `direct`：直接放大 trust signal
- `capped`：trust 只能在一定范围内起作用
- `gated`：只有当 segment prior 超过阈值时才启用 trust 强化

好处：

- 能直接针对 generation-0 暴露出的“trust 放大过强导致最坏情况恶化”问题；
- 比数值微调更能表达鲁棒策略。

---

### 5.3 Uncertainty Retention Mode

新增一类当前完全缺失的变量：

- `uncertainty_mode`

候选取值：

1. `retain`
2. `moderate`
3. `collapse`

语义：

- `retain`：保留更多分布不确定性，避免过强尖峰
- `moderate`：适度压缩
- `collapse`：更接近确定性偏好

为什么重要：

- 当前很多 regression 本质上像“候选过度自信”
- 这是 Route-B 的鲁棒目标必须显式控制的变量

---

### 5.4 Segment Policy Focus Mode

新增一类群体级变量：

- `focus_mode`

候选取值：

1. `single_policy_focus`
2. `paired_policy_balance`
3. `distributional_balance`

语义：

- `single_policy_focus`：突出主政策
- `paired_policy_balance`：主政策与次优政策共同考虑
- `distributional_balance`：尽量保留全分布结构

为什么重要：

- 当前搜索空间默认围绕 `food_subsidy_expansion` 单点展开；
- 这可能本身就在放大不稳定。

---

## 6. 下一轮最小变量集合

为了控制预算，generation-1 不建议一次引入所有变量。

建议的最小集合是：

1. `anchor_regime`
2. `trust_mode`
3. `uncertainty_mode`
4. `focus_mode`

这是一个 `4` 变量、每个 `3` 值左右的离散搜索空间。

第一轮不需要全组合穷举，而是只取一个小种群：

1. `balanced + capped + retain + distributional_balance`
2. `conservative + gated + retain + paired_policy_balance`
3. `balanced + gated + moderate + distributional_balance`
4. `assertive + capped + moderate + single_policy_focus`

设计思路：

- 前 3 个更偏鲁棒保守；
- 最后 1 个保留一个偏激进候选作为负控/探索项。

---

## 7. 编译到 Product 的方式

这些变量不能停留在抽象层，必须可编译。

建议的编译方式：

### `anchor_regime`

编译到：

- calibration anchor 文本强弱
- anchor 相关 patch 数值上限

### `trust_mode`

编译到：

- `trust_multiplier` 的上限/截断规则
- 是否需要 gate phrase

### `uncertainty_mode`

编译到：

- `segment_prompt` 中对不确定性的显式保留语句
- response distribution 的保守提示

### `focus_mode`

编译到：

- calibration anchor 是只强调主政策，还是强调主次政策关系，还是强调分布平衡

这意味着：

下一轮 Route-B 的 candidate 仍然是 Product 可消费的 `policy-reaction-s2pc-candidate-v1`，
只是 `candidate_prompt_components` 的来源不再是 patch 参数微调，而是机制变量编译。

---

## 8. 下一轮评估规则

重定义变量后，下一轮仍然遵守当前止损策略：

### 第一关：单轴预筛

- 只跑 `12x3 seed11`
- 只有当候选：
  - 优于 baseline
  - 且不弱于当前 `s02`
  才进入第二关

### 第二关：repeat-aware route-B

- `12x3 seed11`
- `12x3 seed17`
- `16x3 seed11`

并且继续使用：

- mean loss
- instability penalty
- worst-case loss
- complexity penalty

### 直接止损条件

出现以下任一情况立即止损：

1. generation-1 最优候选仍弱于 `s02`
2. 单轴预筛只有极弱 improvement
3. 大多数候选再次出现大幅 regression
4. 新变量虽然更复杂，但解释性没有同步提高

---

## 9. 推荐结论

当前 Route-B 最合理的下一步不是继续 generation-1 的参数扰动，而是：

> 把变量从“patch 参数值”重定义为“机制级、群体级、可编译的离散更新变量”。

一句话总结：

> Route-B generation-0 失败，不是因为鲁棒目标没有价值，而是因为我们还在用过低层的 patch 变量去优化一个高层稳定性目标。
