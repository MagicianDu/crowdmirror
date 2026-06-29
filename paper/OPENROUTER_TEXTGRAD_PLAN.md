# OpenRouter 免费模型 TextGrad 验证计划

本文记录 2026-05-17 从 OpenRouter Models API 查询到的免费文本模型候选，以及
CIRCE 后续验证 TextGrad 能力的执行边界。

## 当前免费模型候选

优先选择具备较大上下文、推理或结构化输出能力的免费模型：

| 角色 | 模型 id | 选择理由 |
| --- | --- | --- |
| 首选 TextGrad 候选 | `openai/gpt-oss-120b:free` | 与本地 `gpt-oss-20b` 同族，规模更大，适合作为反馈/候选 prompt 生成器 |
| 强代码/结构候选 | `qwen/qwen3-coder:free` | 大上下文，适合生成结构化 prompt diff 和 JSON 诊断 |
| 通用强基线 | `meta-llama/llama-3.3-70b-instruct:free` | 70B 通用 instruct 模型，可作为稳定自然语言反馈基线 |
| 大模型通用候选 | `nousresearch/hermes-3-llama-3.1-405b:free` | 参数规模大，适合测试复杂反馈理解能力 |
| 推理型候选 | `nvidia/nemotron-3-super-120b-a12b:free` | 支持 reasoning/structured outputs，可测试推理型 TextGrad 反馈 |
| 路由探索 | `openrouter/free` | 可发现可用免费路由，但不可控，不作为主证据模型 |

OpenRouter 文档说明，Models API 中 pricing 值为 `"0"` 表示免费；免费模型可用性会变化，
因此正式实验要保存模型列表快照、模型 id、时间和失败原因。

## 执行前提

Research 的 OpenAI-compatible LLM client 已支持：

- LM Studio 默认继续使用 `api_key=lm-studio`。
- 当 `base_url=https://openrouter.ai/api/v1` 时，从环境变量
  `OPENROUTER_API_KEY` 读取鉴权密钥。
- 当 `base_url=https://api.deepseek.com` 时，从环境变量
  `DEEPSEEK_API_KEY` 读取鉴权密钥；推荐优先验证 `deepseek-v4-pro`
  作为高质量候选生成器，`deepseek-v4-flash` 作为低成本 simulator。
  Research client 默认通过 `extra_body={"thinking":{"type":"disabled"}}`
  关闭 thinking，用于普通结构化 JSON 校准任务；需要推理型候选生成时再显式
  打开 thinking 并单独记录配置。
- 如果未设置 `OPENROUTER_API_KEY`，OpenRouter 调用会直接失败，避免误用
  `lm-studio` 作为远端 key。
- 如果未设置 `DEEPSEEK_API_KEY`，DeepSeek 调用也会直接失败，避免把远端
  DeepSeek 请求误记为本地 LM Studio evidence。

执行前需在当前 shell 注入密钥：

```bash
export OPENROUTER_API_KEY=...
export DEEPSEEK_API_KEY=...
```

不要把 key 写入仓库、manifest 或结果文件。

## 最小验证矩阵

第一轮只验证 TextGrad 是否能产生“被 acceptance gate 接受”的候选更新，不做论文级结论。

推荐先跑小矩阵：

| 维度 | 取值 |
| --- | --- |
| task | W3/W4 causal calibration |
| eval_size | `2`, `5` |
| max_iter | `2` |
| dataset_seed | `42`, `43` |
| prompt_baseline | `default`, `weak` |
| model | 上述免费模型候选 |

示例命令：

```bash
.venv/bin/python experiments/w3w4_causal_calibration.py \
  --local \
  --base-url https://openrouter.ai/api/v1 \
  --model openai/gpt-oss-120b:free \
  --max-iter 2 \
  --eval-size 2 \
  --dataset-seed 42 \
  --prompt-baseline weak \
  --request-timeout 180 \
  --run-id w3w4-openrouter-gpt-oss-120b-free-e2-s42-weak-r1
```

验收字段：

- `initial_loss`
- `best_loss`
- `final_loss`
- `candidate_accepted_count`
- `candidate_rejected_count`
- `candidate_acceptance_rate`
- `textgrad_output_budget_saturated`
- `textgrad_steps_json`

## 如何解释结果

TextGrad 不能直接被包装成正向效果。可接受的表述是：

- 如果 candidate 被接受：该模型在该配置下生成了一个通过 loss gate 的 prompt
  候选。
- 如果 candidate 被拒绝：该模型生成了候选，但没有带来可测改进，记录为负结果。
- 如果输出不合规或预算饱和：该模型暂不适合作为 TextGrad 候选生成器。

论文主贡献仍应是 acceptance-gated calibration/evidence contract；TextGrad 只是候选生成
组件之一。

## 没有 TextGrad 时的替代闭环

即使不使用 TextGrad，系统也可以通过反馈改进虚拟人 prompt：

1. 按 segment/persona 计算 residual：预测分布与 held-out observed distribution 的差。
2. 把 residual 转成结构化反馈：哪个 segment 高估/低估了哪类政策选择。
3. 由候选生成器自动提出 prompt/persona patch：可以是 LLM critique、规则模板、
   参数搜索或贝叶斯/进化搜索。
4. 在固定 evaluation split 上重新评估。
5. 只有 loss 改善且 coverage 完整时接受，否则回滚。

因此核心不是 TextGrad 这个名字，而是“反馈 -> 候选 prompt/persona 更新 -> 独立验收
-> 接受/拒绝”这个显式方法组件。TextGrad 的价值在于自动生成更有解释力的候选更新；
如果它不稳定，仍可用规则化 prompt patch、参数搜索或其他自动候选生成器替代。人工
review 只用于审计和解释，不作为主校准机制。
