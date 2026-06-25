# R7 机制生成式交互风险仿真 Spec

## 1. 背景判断

R6 已经把 Product 需要的证据链、claim boundary、false-alarm gate、source-backed report、outcome review 和 bounded update protocol 搭起来，但 Research 方法本身仍不够强。

最新证据显示：

- `r6-counterfactual-robustness-validation-current-001` 仍是 `counterfactual_robustness_diagnostic_blocked`。
- 9 个 local proxy perturbation 场景只通过 8 个，`robustness_pass_rate=0.889`。
- `min_false_alarm_reduction_rate=0.5`。
- `min_non_regression_rate=0.667`。
- `field_outcome_validated=false`。
- `runtime_default_allowed=false`。

这说明 R6 的学习型反事实机制仿真器有 current-proxy 正向信号，但仍依赖 floor、non-regression calibration 和 near-threshold patch。继续围绕 threshold、post-hoc calibration、scoring candidate 或局部 false-alarm 修补推进，只会让 artifact 看起来更完整，不会真正增强 Product 的核心技术支撑。

因此 Research 主线从 R6 的“结果反馈约束先验锚定交互仿真框架”升级为 R7：

> 以强静态先验为底座，以机制状态、交互传播和不确定性区间为核心的机制生成式交互风险仿真。

R7 不是替换 Product 定位，也不是回到精准预测。Product 仍定位为：

> 人群反应趋势与风险区间模拟器。

R7 的作用是让 Research 更有能力支撑 Product 的核心价值：趋势方向、可信区间、风险排序、异常群体、机制解释和结果反馈学习。

## 2. R6 保留与止损边界

### 2.1 R6 保留资产

R6 不删除。以下内容继续作为 Product 和 Research 的基础设施：

1. strong static prior / no-interaction control。
2. source-backed artifact chain。
3. Product evidence card。
4. false-alarm gate。
5. claim boundary / blocked claims。
6. outcome review。
7. bounded update registry。
8. learning counterfactual simulator 的 current-proxy diagnostic baseline。
9. robustness / ablation / stress grid 的失败边界记录。

### 2.2 R6 止损内容

以下内容不再作为 Research 主方法继续优化：

1. 通过 threshold-aware calibration 修补当前 near-threshold false alarm。
2. 继续调 `unseen_mechanism_transfer_floor` 或 `risk_preserving_calibration_target` 以通过当前 3 个 proxy。
3. 把 `learned_weights_only`、`unseen_floor_only` 或 `floor_plus_non_regression_calibration` 包装成通用学习算法。
4. 用更多同质 proxy 替代真正的方法升级。
5. 把 TextGrad、DSPy、prompt/persona patch 或 LCDU 重新提升为主算法。

R6 的合理角色是：

> Product guard + diagnostic baseline + failure replay harness。

R7 的合理角色是：

> Research 主方法 + Product 核心仿真能力候选。

## 3. R7 总目标

R7 的总目标不是给出单点精准预测，而是让系统能够在发布前回答以下问题：

1. 静态先验预计整体反应如何？
2. 场景冲击会激活哪些行为机制？
3. 哪些群体会通过交互传播被放大、缓和或反转？
4. 结果最可能落在哪个区间？
5. 哪些群体构成高风险、异常风险或二阶传播风险？
6. 如果采用不同缓释策略，风险排序和区间会如何变化？
7. 真实 outcome 回来后，哪些机制假设被证伪，哪些参数应被更新，哪些更新必须被阻断？

R7 要从“事后校准一个 prediction”升级为“生成一个可审计的交互过程分布”。

## 4. 方法核心

### 4.1 建模对象

R7 的建模对象不是 prompt，也不是单一 residual patch，而是一个带状态的群体反应过程：

```text
静态人群先验
  -> 场景冲击
  -> 机制激活
  -> 个体/群体状态更新
  -> 交互传播
  -> 风险分布与区间
  -> outcome 回流后的机制更新
```

### 4.2 核心状态

每个群体单元至少包含：

1. `prior_state`：静态先验状态，例如支持率、流失倾向、敏感度、基线风险。
2. `mechanism_state`：机制状态，例如价格敏感、信任损失、公平感知、替代选项、身份认同、社交扩散敏感度。
3. `exposure_state`：冲击暴露程度，例如价格变化、权益变化、规则变化、沟通强度。
4. `interaction_state`：交互位置与影响关系，例如同质群体、弱连接群体、意见领袖、负面传播源。
5. `uncertainty_state`：不确定性来源，例如先验不确定、机制不确定、传播不确定、outcome proxy 不确定。

### 4.3 核心算子

R7 至少包含四类算子：

1. **机制激活算子**
   - 输入：场景冲击、群体属性、静态先验。
   - 输出：机制激活向量。
   - 作用：解释为什么某些群体对同一政策或产品变更反应更强。

2. **行为更新算子**
   - 输入：静态先验、机制激活、暴露强度。
   - 输出：无交互条件下的群体风险变化。
   - 作用：把场景冲击转为群体层反应，而不是直接套用全局 delta。

3. **交互传播算子**
   - 输入：群体网络、相似性、信任关系、传播敏感度。
   - 输出：交互后的风险扩散、缓和、极化或反转。
   - 作用：产生静态先验无法表达的二阶风险。

4. **结果反馈学习算子**
   - 输入：真实 outcome 或 public proxy、预测分布、机制 trace。
   - 输出：机制参数更新候选、失败归因、rollback 建议。
   - 作用：真实结果回来后，不是人工改 prompt，而是更新可审计机制假设。

## 5. R7 相对 R6 的关键增强

| 维度 | R6 当前状态 | R7 要解决的问题 |
| --- | --- | --- |
| 方法对象 | prediction / residual / calibration | 机制状态和交互过程分布 |
| 交互表达 | raw interaction delta + gate | network propagation / peer influence / contagion path |
| 不确定性 | 主要通过区间 artifact 表达 | 从先验、机制、传播和数据源分解不确定性 |
| 学习方式 | outcome residual 调权重 | outcome 归因到机制和传播算子 |
| Product 支撑 | guarded report | 风险发现、区间、异常群体、策略沙盘的核心能力候选 |
| 失败处理 | blocked claim | 失败边界、机制证伪、参数 rollback |

R7 的创新点不在“又换一个校准器”，而在：

> 把强静态先验之上的交互增量，从后处理分数重写为可解释、可传播、可回放、可反馈学习的机制生成过程。

## 6. Product 支撑目标

R7 必须直接支撑 Product 的六个客户可见输出。

| Product 输出 | R7 必须提供的内容 | 验收信号 |
| --- | --- | --- |
| 趋势方向 | 多次 rollout 后的方向分布 | 趋势方向命中率和不确定方向标记 |
| 可信区间 | 分解后的风险区间 | interval coverage、区间宽度、数据源说明 |
| 风险排序 | 群体和机制维度 ranking | top-k hit rate、false alarm rate、regret reduction |
| 异常群体 | 静态先验未暴露但交互后高风险的群体 | segment precision / recall / source refs |
| 机制解释 | 机制激活和传播路径 | mechanism ablation、trace replay |
| 策略沙盘 | 不同缓释方案下的风险变化 | counterfactual policy ranking、dominance / trade-off |

Product 可以展示：

- 当前仿真发现的风险分布。
- 哪些风险来自静态先验，哪些来自交互传播。
- 哪些群体是高风险或异常群体。
- 哪些策略可能降低风险区间或改变风险排序。
- 当前结论的证据等级、阻断声明和 remaining gaps。

Product 不得展示：

- 精准预测单点结果。
- field validated 声明，除非 field outcome gate 通过。
- runtime default ready 声明，除非 update guard 通过。
- 交互仿真一定比静态先验更准。

## 7. R7 第一阶段工作包

### WP1：R7 artifact contract

目标：定义 R7 的最小可审计输出，先让 Product 和测试有稳定契约。

新增 artifact：

- `r7_mechanism_state_manifest`
- `r7_interaction_graph_manifest`
- `r7_rollout_distribution`
- `r7_risk_interval_report`
- `r7_segment_anomaly_report`
- `r7_counterfactual_policy_sandbox`
- `r7_outcome_feedback_update_candidate`
- `r7_product_support_report`

验收标准：

- 每个 artifact 必须包含 `artifact_id`、`run_id`、`schema_version`、`source_refs`、`claim_boundary`。
- 所有客户可见字段必须能追溯到 source artifact。
- 缺少 source refs 时 fail closed。

### WP2：机制状态层

目标：把 scenario shock 映射到群体机制激活，而不是直接映射到 prediction。

最小机制集合：

1. `price_sensitivity`
2. `trust_loss`
3. `fairness_perception`
4. `substitution_option`
5. `identity_alignment`
6. `social_diffusion_sensitivity`

验收标准：

- 每个 case 输出 segment-level mechanism state。
- 每个机制必须说明来源：先验、规则、LLM judge、历史 outcome 或人工 domain config。
- 机制激活必须可消融。

### WP3：交互传播层

目标：引入真实的传播结构，证明交互仿真不是 post-hoc scoring。

第一阶段用可审计的轻量图，不追求复杂 ABM：

- node：群体 segment。
- edge：相似性、暴露关系、信任关系或传播关系。
- update：同步或异步传播若干步。

验收标准：

- 有 no-interaction control。
- 有 interaction-on rollout。
- 能报告每一步风险变化。
- 能识别风险被放大、缓和、扩散或反转的路径。

### WP4：分布式 rollout 与区间

目标：从单次输出升级为多次 rollout 分布。

第一阶段 uncertainty 来源：

1. static prior uncertainty。
2. mechanism activation uncertainty。
3. propagation strength uncertainty。
4. outcome proxy uncertainty。

验收标准：

- 每个 case 至少输出 50 次 deterministic-seeded rollout。
- 输出 median、p10、p90、interval width。
- 报告 interval coverage 和 over-wide penalty。
- 如果区间只是靠扩大宽度通过，必须降级。

### WP5：风险排序与异常群体

目标：让 Product 的“谁最危险、为什么危险”有方法支撑。

验收标准：

- 输出 top-k segment risk ranking。
- 输出 static-hidden risk：静态先验低估但交互后升高的群体。
- 输出 interaction-amplified risk：交互传播导致进一步升高的群体。
- 输出 false-alarm diagnosis：高风险预测但 outcome/proxy 不支持的群体。

### WP6：策略沙盘

目标：把 Product 从“看风险”升级为“比较行动方案”。

最小策略类型：

1. 降低冲击强度。
2. 改变沟通策略。
3. 针对高风险群体做补偿或缓释。
4. 限制负面传播路径。

验收标准：

- 每个 case 至少输出 3 个策略方案。
- 每个策略输出风险区间变化、top segment 变化、机制解释。
- 报告 dominance / trade-off，而不是只输出一个推荐。

### WP7：outcome feedback learning

目标：真实 outcome 或 proxy 回来后，系统能更新机制假设，而不是人工改 prompt。

验收标准：

- 输出误差归因：prior error、mechanism error、propagation error、interval error。
- 输出 bounded update candidate。
- 输出 rollback condition。
- 更新候选不得直接进入 runtime default。
- 必须通过 holdout non-regression 和 Product guard 才能升级。

## 8. 第一阶段验收标准

R7 第一阶段不是要求 field validated，而是要求方法形态明显强于 R6 的后处理校准。

必须通过：

1. `r7_*` artifacts 全部落盘。
2. Product 六类输出都能从 R7 artifact 读取。
3. 至少一个 current proxy case 展示 interaction-on 相对 no-interaction 的风险发现增量。
4. 至少一个 case 展示策略沙盘能改变风险排序或区间。
5. 至少一个 failure case 被正确识别为 false alarm 或 unsupported interaction。
6. 所有 claims 保持 guarded，不允许 field validated 或 runtime default。

强正向信号：

1. trend direction 不低于 R6。
2. interval coverage 不低于 R6，且区间宽度不过度膨胀。
3. risk ranking quality 高于 R6。
4. false alarm rate 低于 raw interaction。
5. segment anomaly report 能定位静态先验看不到的风险群体。

止损信号：

1. R7 只能复刻 R6 的校准结果，不能产生传播 trace。
2. R7 的风险区间只能靠无限扩大取得 coverage。
3. R7 的策略沙盘不能改变任何决策排序。
4. R7 的异常群体全是 false alarm。
5. outcome feedback 仍只能变成人工 patch 或 hard-coded rule。

## 9. 测试方案

第一阶段测试采用 contract-first：

1. `tests/test_r7_mechanism_state_manifest.py`
   - 验证机制状态 schema、source refs、消融字段。

2. `tests/test_r7_interaction_graph_manifest.py`
   - 验证 no-interaction 与 interaction-on 同时存在。
   - 验证传播 step 可回放。

3. `tests/test_r7_rollout_distribution.py`
   - 验证 seeded rollout 可复现。
   - 验证 p10 / median / p90 区间合法。

4. `tests/test_r7_product_support_report.py`
   - 验证 Product 六类输出都有 source-backed evidence。
   - 验证 blocked claims 不被移除。

5. `tests/test_r7_outcome_feedback_update_candidate.py`
   - 验证 update candidate 默认 blocked。
   - 验证 rollback condition 存在。

第一轮不要求所有指标优于 R6，但必须证明 R7 的数据结构和仿真过程已经从后处理校准升级为机制生成式交互过程。

## 10. 与 Product 的关系

R7 不是论文优先的孤立算法。R7 每个 artifact 都必须能进入 Product：

1. `r7_risk_interval_report` 进入客户报告的趋势与区间模块。
2. `r7_segment_anomaly_report` 进入风险群体模块。
3. `r7_interaction_graph_manifest` 进入机制解释和传播路径模块。
4. `r7_counterfactual_policy_sandbox` 进入行动方案比较模块。
5. `r7_outcome_feedback_update_candidate` 进入发布后复盘和学习模块。

Product 对外仍只能说：

> 系统提供趋势、区间、风险排序、异常群体和机制解释；它帮助客户提前发现静态先验可能掩盖的风险，并在真实结果回来后持续复盘和更新。

不得说：

> 系统能精确预测人群反应。

## 11. 用户侧需要提供的帮助

R7 可以先用当前 public proxy 和合成 scenario fixture 启动，但要走向更强 Product 支撑，后续最好获得：

1. 典型客户场景模板：价格变更、权益变更、规则变更、服务降级、沟通策略变化。
2. 客户关心的决策输出格式：报告、仪表盘、会议材料或 API。
3. 可回流 outcome 类型：转化率、流失率、投诉率、退款率、支持率、舆情负面率、复购率。
4. 至少一个匿名化 pilot case，哪怕只有聚合 outcome。
5. 对风险偏好的选择：宁愿多报风险，还是宁愿少报风险。

没有这些输入，R7 仍可推进方法 MVP，但 Product 说服力会停在 guarded proxy evidence。

## 12. 下一步

下一步不做 R6 near-threshold calibration patch。

下一步先做：

1. R7 artifact contract。
2. R7 mechanism state manifest。
3. R7 interaction graph manifest。
4. R7 rollout distribution。
5. R7 Product support report。

这五项完成后，再判断 R7 是否拿到比 R6 更强的正向信号。如果没有，及时止损，保留 Product guard 和报告能力，重新评估是否需要引入真实 customer pilot outcome。
