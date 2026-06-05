# Context Bootstrap

## 一句话定位

R6 是一个发布前反应评估与发布后反馈学习框架：用强先验建立可信底座，用交互仿真发现静态数据盲区，用真实 outcome 回填持续校正方法。

## 必读文件

1. `docs/active-spec.md`
2. `docs/CURRENT_STATE.md`
3. `docs/superpowers/specs/2026-06-05-r6-outcome-feedback-prior-anchored-interaction-simulation-spec.md`

## 当前不要做

- 不继续优化 TextGrad / prompt / persona patch。
- 不把 R4/R5 负结果包装成主算法有效。
- 不把航空、平台、政策等单一场景写成方法本体。
- 不用旧 LCDU paper 草案覆盖 R6 方向。
- 不用全量旧测试结果证明 R6 成立。

## 当前要做

- 新增 `r6_` 前缀的实验模块和测试。
- 建立七类 R6 artifact 合同。
- 生成行业无关 fixture。
- 保留 no-interaction control。
- 生成 risk shift report。
- 接入 outcome manifest。
- 生成 learning report。
- 用 update registry 阻断未验证更新。

