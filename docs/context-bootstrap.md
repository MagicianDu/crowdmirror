# Context Bootstrap

## 一句话定位

R6 当前是 Product-first 的发布前反应评估与发布后反馈学习产品：用强先验建立可信底座，用交互仿真发现静态数据盲区，用 evidence cards 和 claim boundary 控制产品结论，用真实 outcome 回填持续校正方法。

## 必读文件

1. `docs/active-spec.md`
2. `docs/CURRENT_STATE.md`
3. `docs/superpowers/specs/2026-06-16-r6-product-first-solid-value-spec.md`
4. `docs/superpowers/plans/2026-06-16-r6-product-first-solid-next-stage.md`

## 当前不要做

- 不继续优化 TextGrad / prompt / persona patch。
- 不把 R4/R5 负结果包装成主算法有效。
- 不把航空、平台、政策等单一场景写成方法本体。
- 不用旧 LCDU paper 草案覆盖 R6 方向。
- 不用全量旧测试结果证明 R6 成立。
- 不再把 CCF-A 主贡献作为默认目标。
- 不做无 artifact source 的 demo 文案或静态 narrative fallback。

## 当前要做

- 按 Product-first 计划补齐 scenario intake、story package、decision report 和 outcome review。
- 所有 Product 结论绑定 evidence cards、source refs、claim boundary 和 blocked claims。
- Research 继续提供理论定义、误差归因、机制传播和方法护栏，但服务于 Product 可信度。
- 保留 `field_outcome_validated=false`、`runtime_default_allowed=false`、`ccf_a_main_contribution_ready=false` 的边界，直到真实证据通过。
