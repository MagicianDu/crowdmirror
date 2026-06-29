# Agent Instructions

- 非必要不使用英文，使用中文回复和生成文档。
- 当前 Research / Product 主线以 `docs/active-spec.md` 为唯一事实源。
- R6 之前的 LCDU、DCL-PRS、MCR-Gate、R4、R5、TextGrad、prompt/persona patch 文档和代码默认是历史材料或基础设施参考，不能作为当前实现目标。
- 继续开发前先确认 `docs/CURRENT_STATE.md` 中的 active / deprecated / conflict 边界。
- 当前实现主线已从 R6 的结果反馈约束先验锚定交互仿真，升级为 R7 的机制生成式交互风险仿真；R6 保留为 Product guard、diagnostic baseline 和 failure replay harness。
- 产品对外定位是“人群反应趋势与风险区间模拟器”，不是“精准预测系统”。
- 静态先验是仿真底座，不是整体研究目标的对手；`beat static prior` 只作为候选更新进入 runtime default 前的护栏。
- 当前 R6 的关键边界是：证据链完整但方法强度不足，learning counterfactual robustness 仍是 diagnostic blocked，不能包装成 Product core method fully supported。
- 当前目标已调整为 Product-first：Research 不再默认冲 CCF-A 主贡献，也不以“点预测 beat 静态先验”为唯一目标；Research 应验证交互仿真是否改善趋势判断、区间校准、风险排序、异常群体识别和决策价值。
- Product 客户可见输出必须包含趋势方向、可信数值区间、风险分布、异常群体和机制解释；不得承诺精确预测单点结果。
- 当前 Interaction Signal Validity / scoring candidate / R6 learning counterfactual calibration 已止损为 diagnostic baseline；Research 下一步按 `docs/superpowers/specs/2026-06-25-r7-mechanism-generative-risk-simulation-spec.md` 推进机制状态、交互传播、分布式 rollout、策略沙盘和 outcome-feedback learning。
- Product 的 failure diagnosis、false-alarm gate、claim boundary、evidence cards 是所有新 Research 方法的外层 guard，不能删除或降级。
