# Agent Instructions

- 非必要不使用英文，使用中文回复和生成文档。
- 当前 Research / Product 主线以 `docs/active-spec.md` 为唯一事实源。
- R6 之前的 LCDU、DCL-PRS、MCR-Gate、R4、R5、TextGrad、prompt/persona patch 文档和代码默认是历史材料或基础设施参考，不能作为当前实现目标。
- 继续开发前先确认 `docs/CURRENT_STATE.md` 中的 active / deprecated / conflict 边界。
- R6 实现只应围绕 `Product-first 的结果反馈约束先验锚定交互仿真框架` 推进；既有 foundation 和方法验收 artifact 作为基础设施，当前新增工作优先补齐 Product scenario intake、story package、decision report、outcome review 与可审计 evidence card 链路。
- 静态先验是仿真底座，不是整体研究目标的对手；`beat static prior` 只作为候选更新进入 runtime default 前的护栏。
- 当前 R6 的关键边界是：decision-value 指标已可计算，但当前结果是 partial positive + high false alarm + holdout failed，不能包装成 CCF-A 主贡献通过。
- 当前目标已调整为 Product-first：Research 不再默认冲 CCF-A 主贡献，而是为 Product 提供理论、证据边界、误差归因和方法护栏；后续优先补齐 scenario intake、story package、decision report 和 outcome review。
- 当前 Interaction Signal Validity / scoring candidate 已止损为 diagnostic baseline；Research 下一步转向 mechanism-driven interaction propagation、behavioral update operator 和 outcome-feedback learning。
- Product 的 failure diagnosis、false-alarm gate、claim boundary、evidence cards 是所有新 Research 方法的外层 guard，不能删除或降级。
