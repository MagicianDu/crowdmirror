# LCDU L3 方法与实验小节草案

## 1. 方法动机

前序 S2PC 与 Route-B 结果表明，单纯围绕 prompt patch、factor subset 或局部参数搜索，虽然能够反复产生局部正信号，但难以稳定跨过 `seed/scale` repeat gate。问题不在于完全没有自动化更新信号，而在于更新对象过浅、更新规则过局部，导致方法容易命中单点改进却难以形成稳定优势。

LCDU 的核心转向是把更新对象从局部 prompt patch 提升为：

1. `latent state update`
2. `segment-level constraint program`
3. `prompt-anchor synchronized runtime realization`

在这一路线中，候选更新不是任意自然语言改写，而是一个可审计、可编译、可在 Product runtime 中消费的结构化程序。

## 2. LCDU L3 的核心思想

LCDU L3 并不尝试同时修复所有 segment，而是针对前序 repeat 里最不稳定的 segment 构造**定向 guard threshold reconstruction**。

其输入包括：

1. 先前已接受或接近接受的 LCDU 候选；
2. calibration-split 派生的 latent 方向；
3. held-out repeat 中暴露出的 segment-level instability pattern。

其输出是一个 `policy-reaction-s2pc-candidate-v1` 兼容 artifact，包含：

1. segment-level prompt components
2. calibration-anchor components
3. strict JSON response contract

与 S2PC 的差异在于，LCDU L3 不再把 update 视为“局部参数 patch 的集合”，而把它视为“对关键 segment 施加同步、数值化的 prompt-anchor guard program”。

## 3. 候选构造

LCDU L3 的第一阶段围绕 `working_family_price_stressed` 构造一组 guard-threshold 候选。其基本操作是：

1. 保留主候选的 latent direction；
2. 仅对目标 segment 添加 guard prompt 与 guard anchor；
3. 用数值边界约束关键政策概率的上界/下界；
4. 保持 Product 侧 schema 不变。

在这一阶段得到的 `h02` 首次通过了完整 repeat gate，说明：

1. LCDU 已经不只是单轴命中；
2. segment-targeted guarded program 可以稳定改善 held-out 对齐。

## 4. 解释性拆解

为了区分 LCDU L3 的有效性究竟来自 prompt、anchor，还是二者联动，我们进一步做了两层解释性拆解。

### 4.1 单组件 ablation

`anchor_only_guard` 在单轴上保留了弱正向，但在 repeat 上转为 `mixed`。这说明：

1. 数值化 anchor 本身有贡献；
2. 但 anchor 单独不足以解释稳定改善。

### 4.2 prompt-anchor interaction ablation

四组 interaction 候选表明：

1. `numeric_prompt + numeric_anchor` 最强；
2. `qualitative_prompt + numeric_anchor` 会回退；
3. `numeric_prompt + qualitative_anchor` 只保留弱正向；
4. `qualitative_prompt + qualitative_anchor` 虽有正向，但弱于 fully numeric 版本。

因此，LCDU L3 的有效性更准确地来自：

> 一个同步、数值化、segment-targeted 的 prompt-anchor guarded program

而不是单独 prompt，或单独 anchor。

## 5. 主要实验结论

当前最关键的两个稳定候选是：

1. `h02`
   - repeat mean 改善更强；
   - 是当前 update-method gate 下的最佳 accepted method。

2. `i01`
   - 单轴改善最强；
   - repeat 也通过 `stable_improvement`；
   - 为“数值化 prompt-anchor 联动”提供更直接的机制证据。

这两个候选共同支持一个更强的 reviewer-facing 结论：

> LCDU L3 的稳定性来源于同步约束程序，而不是脆弱的单边 patch。

## 6. 残余弱点与负结果

尽管 LCDU L3 已经拿到稳定改善，它并没有修复全部 segment。残余误差主要集中在 `low_income_food_insecure`。

这一弱点具有明确结构：

1. 排序未错，`rank_correlation=1.0`
2. 但分布形状偏差稳定存在：
   - `baseline_no_new_support` 偏高
   - `cash_cost_of_living_rebate` 偏低
   - `food_subsidy_expansion` 略偏高

进一步的 LCDU L4 定向修补尝试表明：

1. 强数值修补会破坏当前已接受主结构；
2. 弱 qualitative 修补最多接近 baseline；
3. 因此局部 residual repair 不应继续作为主线。

这组负结果非常重要，因为它限制了方法声明边界：LCDU L3 已经是成立的方法候选，但并不意味着所有 segment 都能靠局部修补继续单调改进。

## 7. 当前可宣称边界

目前可以保守宣称的是：

1. LCDU L3 在当前 policy-reaction public-data benchmark 上给出了稳定的 held-out 改善；
2. 这种改善来源于 segment-targeted、数值化的 prompt-anchor 同步约束程序；
3. 该方法可以被 Product runtime 直接消费并审计；
4. 其残余误差和失败修补路径也已经被显式记录。

当前不能宣称的是：

1. 跨任务通用性；
2. 跨数据集外推有效性；
3. 实地政策预测能力；
4. 所有 segment 都可继续通过局部修补提升。

## 8. 对论文结构的建议

如果将当前结果整理进正式论文，建议在方法与实验部分采用以下结构：

1. `Method`
   - LCDU 表示层
   - L3 segment-targeted guarded program
   - prompt-anchor synchronized candidate realization

2. `Experiments`
   - baseline 与 prior failed routes
   - LCDU L3 `h02` repeat validation
   - interaction ablation
   - residual weakness analysis
   - negative-result stop-loss on low-income repair

这样既能保留主方法的正向证据，也能保留边界清晰的负结果链条。
