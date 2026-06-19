# R6 趋势与风险区间定位修正

## 背景

R6 之前的若干讨论容易把人群模拟误读成“精准预测系统”，或者把 Research 验收压缩成“点预测是否 beat 静态先验”。这个定位过窄，也不符合真实人群行为的复杂性。

人群行为受个体差异、群体交互、信息传播、情绪反馈、外部事件和执行细节影响。系统不应承诺精确预测单点结果，而应在强静态先验基础上提供发布前决策所需的趋势、区间、风险分布和机制解释。

## 修正后的产品定位

Product 对外定位改为：

> 人群反应趋势与风险区间模拟器。

Product 不定位为：

> 精准预测系统。

产品核心能力仍然是人群模拟，但客户可见承诺必须是：

1. 预测趋势方向：上涨、下降、分化、扩散、收敛或不确定。
2. 给出可信数值区间：用区间表达不确定性，而不是给出单点承诺。
3. 识别风险分布：展示风险在群体、地区、身份、需求或关系网络中的分布。
4. 发现异常群体：识别静态平均先验容易掩盖的高敏感群体、反向群体和传播放大群体。
5. 解释机制路径：说明哪些先验、场景冲击、交互传播或反馈路径导致风险变化。
6. 支持结果回流：真实 outcome 回来后，做误差归因和受约束方法更新。

## 修正后的 Research 目标

Research 不再以“点预测 beat 静态先验”为唯一目标。静态人口、客户或群体先验是仿真底座，不是整体研究对手。

Research 的主要问题改为：

> 在强静态先验基础上，交互仿真是否能改善趋势判断、区间校准、风险排序、异常群体识别和决策价值。

因此 Research 验收指标应围绕：

1. `trend_direction_accuracy`：交互仿真对真实或 proxy outcome 的方向判断是否更稳。
2. `interval_coverage`：输出区间是否覆盖真实或 proxy outcome，区间是否不过宽。
3. `risk_ranking_quality`：高风险群体排序是否比静态先验更有决策价值。
4. `abnormal_segment_recall`：是否找出静态平均先验容易掩盖的异常群体。
5. `decision_value`：是否降低漏报、减少后悔决策、提高干预优先级质量。
6. `false_alarm_control`：是否能解释和约束交互仿真带来的误报。
7. `outcome_feedback_learning`：真实结果回流后，是否能生成可审计、受约束、可复核的方法更新。

## 方法边界

1. 点预测误差仍可作为诊断指标，但不能作为唯一成功标准。
2. `beat static prior` 只作为 runtime update guard：候选更新进入默认运行前，不能显著伤害强静态先验。
3. 若交互仿真没有提升点预测，但发现了静态先验没有暴露的高风险群体或风险传播路径，仍可能构成 Product 价值和 Research 正向信号。
4. 若交互仿真产生高误报，Product 必须展示 false-alarm diagnosis 和 blocked claim，Research 必须定位失败边界。
5. 没有 field outcome 或独立 holdout 前，不宣称 field validated、runtime default ready 或 accuracy superiority。

## 产品验收标准

下一阶段 Product 输出必须至少包含：

1. 静态先验基线。
2. 交互仿真后的趋势方向。
3. 风险数值区间和不确定性说明。
4. 群体风险分布和异常群体列表。
5. 机制解释路径。
6. source-backed evidence cards。
7. blocked claims 和 remaining gaps。
8. outcome review 入口，用于真实结果回流后的复盘和更新候选。

## Research 验收标准

下一阶段 Research artifact 必须至少报告：

1. 趋势方向是否与 outcome/proxy 一致。
2. 区间覆盖是否成立，区间宽度是否可接受。
3. 风险排序是否优于或补充静态先验。
4. 异常群体是否有证据支持。
5. 决策价值是否来自漏报恢复、风险排序或后悔决策降低，而不是单点误差包装。
6. 误报率、失败边界和 blocked update reason。
7. 是否允许进入 Product runtime default；默认必须 fail-closed。

## 当前结论

这次修正不是放弃人群模拟，而是把人群模拟从“精确预测单点结果”调整为“面向发布前决策的趋势、区间、风险分布和机制解释”。

这更符合产品价值，也更适合作为 Research 的扎实目标。
