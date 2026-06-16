# Agent Instructions

- 非必要不使用英文，使用中文回复和生成文档。
- 当前 Research / Product 主线以 `docs/active-spec.md` 为唯一事实源。
- R6 之前的 LCDU、DCL-PRS、MCR-Gate、R4、R5、TextGrad、prompt/persona patch 文档和代码默认是历史材料或基础设施参考，不能作为当前实现目标。
- 继续开发前先确认 `docs/CURRENT_STATE.md` 中的 active / deprecated / conflict 边界。
- R6 实现只应围绕 `结果反馈约束的先验锚定交互仿真框架` 推进；foundation artifact chain 包括 prior manifest、scenario manifest、interaction trace、risk shift report、outcome manifest、learning report、update registry，当前阶段方法验收交付物包括 cross-case transfer protocol artifact、in-condition holdout ledger、Product evidence card contract、risk-discovery value report、decision-value metrics、risk-discovery holdout validation。
- 静态先验是仿真底座，不是整体研究目标的对手；`beat static prior` 只作为候选更新进入 runtime default 前的护栏。
- 当前 R6 的关键边界是：decision-value 指标已可计算，但当前结果是 partial positive + high false alarm + holdout failed，不能包装成 CCF-A 主贡献通过。
- 当前 Interaction Signal Validity / scoring candidate 已止损为 diagnostic baseline；Research 下一步转向 mechanism-driven interaction propagation、behavioral update operator 和 outcome-feedback learning。
- Product 的 failure diagnosis、false-alarm gate、claim boundary、evidence cards 是所有新 Research 方法的外层 guard，不能删除或降级。
