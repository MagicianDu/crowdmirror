# 路线组合覆盖账本

## 1. 目的

这份账本用来约束后续结论边界：

> 只有当本文定义的有限组合集全部完成或明确阻塞后，才允许对“非 LCDU 路线是否能挑战 LCDU L3”下阶段性结论。

这里的“全部组合”不是无限的算法空间，也不是完整笛卡尔积。当前项目以
`2026-05-22-parallel-orthogonal-tracks-design.md` 为边界，采用：

1. 4 条主线；
2. 3 个轮次；
3. 共 12 个 route-round 单元。

完整 `表示层 x 优化器 x 系统层级` 笛卡尔积不在本账本内；若要执行，需要另起大型实验计划。

## 2. 统一 gate

每个 route-round 单元必须至少记录：

1. candidate set artifact；
2. 单候选 runtime artifact；
3. route-level matrix；
4. 是否优于 calibration-split held-out baseline；
5. 是否超过当前 accepted mainline：`LCDU L3 h02/i01`；
6. route 结论：`promote`、`keep_as_weak_signal`、`stop`、`blocked`。

## 3. 覆盖矩阵

| 轮次 | 单元 | 表示层 | 优化器 | 系统层级 | 当前状态 | 下一步 |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | A | prompt-anchor synchronized program | heuristic small family | segment-level | done: weak signal | 已归档 |
| R1 | B | latent response program | structured family prefilter | axis/segment hybrid | done: stop | 已归档 |
| R1 | C | distribution/ordering constraint program | robust/OR-style selection | population-level | done: stop | 已归档 |
| R1 | D | prototype/retrieval program | retrieval + rerank | persona/segment hybrid | done: weak signal | 已归档 |
| R2 | A | narrowed segment program | focused heuristic narrowing | segment/axis hybrid | done: weak signal | 已归档 |
| R2 | B | narrowed latent response program | conservative latent recomposition | axis/segment hybrid | done: weak signal | 已归档 |
| R2 | C | narrowed constraint program | conservative constraint recomposition | population/axis hybrid | done: weak signal | 已归档 |
| R2 | D | narrowed prototype program | conservative retrieval recomposition | persona/segment hybrid | done: stop | 已归档 |
| R3 | A | segment + latent hybrid | cross-family recomposition | segment/axis hybrid | done: weak signal | 已归档 |
| R3 | B | segment + constraint hybrid | cross-family recomposition | segment/population hybrid | done: weak signal | 已归档 |
| R3 | C | latent + prototype hybrid | cross-family recomposition | axis/persona hybrid | done: weak signal | 已归档 |
| R3 | D | constraint + prototype hybrid | cross-family recomposition | population/persona hybrid | done: weak signal | 已归档 |

## 4. 当前已知事实

1. R1 四条路线已经完成。
2. R2 四条路线已经完成。
3. R3 四个 cross-family 单元已经完成。
4. 12 个 route-round 单元内，没有任何候选超过 `LCDU L3`。
5. 12 个 route-round 单元内，最好的非 LCDU 候选都停在旧弱上限
   `0.000111545213`，即 `relative_loss_reduction=0.011920716018`。

## 5. 完成标准

本账本完成需要满足：

1. R2-B、R2-C、R3-A、R3-B、R3-C、R3-D 都有 matrix artifact；
2. `RESULTS.md` 回填 12 个 route-round 单元的状态；
3. 至少运行本轮新增测试；
4. `git diff --check` 通过；
5. research/product worktree 干净。

## 6. 覆盖结论

在本账本定义的有限组合空间内，组合覆盖已经完成。

可以下的结论：

1. 12 个 route-round 单元均已尝试；
2. 非 LCDU 路线没有产生超过 `LCDU L3` 的候选；
3. 多数组合只能复现旧弱信号上限；
4. 强修正组合容易回退或明显崩塌；
5. `LCDU L3` 仍是当前 research/product 双主线的 active mainline。

不能下的结论：

1. 不能说完整算法空间都已穷尽；
2. 不能说完整 `表示层 x 优化器 x 系统层级` 笛卡尔积都已跑完；
3. 不能说其它未来方法一定不可能超过 `LCDU L3`。

