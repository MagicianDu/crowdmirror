# 用户使用指南

这份指南面向第一次打开 CrowdMirror 的试用用户。你不需要理解代码，也不需要安装任何依赖，就可以先看在线 demo。

## 第一步：打开宣传页

访问：

[https://magiciandu.github.io/crowdmirror/demo/promo.html](https://magiciandu.github.io/crowdmirror/demo/promo.html)

宣传页主要回答三个问题：

1. 这个产品解决什么问题：发布前评估人群反应趋势、可信数值区间、风险分布、异常群体和机制解释。
2. 当前证据到什么程度：公开数据测试有效，但仍是 guarded claim。
3. 当前不会承诺什么：不承诺精确单点预测，不宣称客户 field validation 已完成，不默认自动上线校准更新。

如果只想快速了解项目能力，先读宣传页即可。

## 第二步：打开产品 demo

访问：

[https://magiciandu.github.io/crowdmirror/demo/](https://magiciandu.github.io/crowdmirror/demo/)

产品 demo 是可审计报告页面，不是空白模板。它会读取仓库中的 JSON artifact，并把当前能展示的结论、证据和边界直接渲染出来。

建议按页面顺序阅读：

1. 顶部状态：确认报告、研究支撑、产品就绪和 API 合同是否处于 guarded 状态。
2. 核心指标：先看趋势方向、风险区间、风险排序、误报率。
3. 异常群体：看哪些群体可能出现静态先验没有捕捉到的高风险。
4. 机制解释：看系统认为风险可能来自哪里。
5. R12 迁移验证：看公开数据上的次级证据和仍被阻断的结论。
6. 客户试运行：看企业数据回流后如何进入 intake、revalidation、feedback update、shadow replay 和 holdout review。
7. 阻断声明：看系统明确不能对外声称的内容。

## 第三步：读懂报告

报告里的核心指标可以这样理解：

| 指标 | 用途 | 怎么用 |
| --- | --- | --- |
| 趋势方向 | 判断风险大致会上升、下降还是稳定 | 用于判断是否需要提前干预 |
| 可信数值区间 | 给出可能范围，而不是单点预测 | 用于评估最乐观、基准、最坏情况 |
| 风险分布 | 比较风险在不同群体间如何分布 | 用于安排沟通、灰度或补偿优先级 |
| 风险排序 | 找出更值得优先关注的群体或场景 | 用于确定运营和策略处理顺序 |
| 误报率 | 衡量把低风险误判为高风险的代价 | 误报高时，只能作为诊断信号 |
| 异常群体 | 找出静态先验可能漏掉的人群 | 是产品价值重点，但必须配合误报边界看 |
| 机制解释 | 说明风险可能由哪些因素触发 | 用于业务讨论，不等同于因果证明 |

一个健康的试用结论不应该只看“有没有正向信号”，还要同时看：

- 正向信号来自公开数据、独立 holdout、客户 field slice 还是 synthetic rehearsal。
- 是否存在 high false alarm。
- 是否有 source refs 和 artifact 支撑。
- 是否仍然保持 `runtime_default_allowed=false`。

## 第四步：准备企业试用数据

公开 demo 不上传客户数据。企业试用时，需要客户在自己的流程中准备一份伪匿名 field slice，再交给 operator 做离线验证。

最低要求：

- 至少 10 个 cases。
- 必需字段：
  - `case_id`
  - `segment_id`
  - `scenario_id`
  - `prediction_share_or_score`
  - `observed_outcome`
  - `outcome_timestamp`
  - `customer_approval_reference`
- 不能包含手机号、邮箱、身份证、姓名、地址等直接个人标识。
- 每条记录都要有 `customer_approval_reference`，用于证明数据回流经过授权。

模板文件：

`experiments/results/r12_customer_field_slice_handoff_package/r12-customer-field-slice-template-current-001.csv`

产品 demo 里的“客户 field slice 校验”只在浏览器本地做预览，不上传服务器。预览通过后，系统会给出 operator handoff 命令形状，供离线环境执行正式 intake。

## LLM key 怎么配置

在线 demo 不需要配置 LLM key。

原因是当前公开页面运行在 GitHub Pages 上，只读取已经生成好的公开 artifact。浏览器端不会读取 `OPENROUTER_API_KEY`、`DEEPSEEK_API_KEY` 或任何其他 provider key，也不会把客户数据发给 LLM。

只有在下面这些场景才需要 key：

1. 研发人员要重新跑 LLM 驱动的人群仿真。
2. operator 要生成新的 feedback update candidate。
3. operator 要重新跑 TextGrad、prompt optimizer 或跨 provider 诊断。
4. 企业内部部署要把仿真服务接到自己的后端。

当前支持三类常见配置：

| 场景 | 配置方式 | 是否需要真实 key |
| --- | --- | --- |
| 本地 LM Studio | `--base-url http://127.0.0.1:1234/v1 --model openai/gpt-oss-20b` | 不需要，代码使用 `lm-studio` 占位 key |
| DeepSeek | `DEEPSEEK_API_KEY` + `--base-url https://api.deepseek.com` | 需要 |
| OpenRouter | `OPENROUTER_API_KEY` + `--base-url https://openrouter.ai/api/v1` | 需要 |

zsh 示例：

```bash
export DEEPSEEK_API_KEY="替换成你的 DeepSeek key"
export OPENROUTER_API_KEY="替换成你的 OpenRouter key"
```

DeepSeek 示例参数：

```bash
--base-url https://api.deepseek.com --model deepseek-v4-flash
```

本地 LM Studio 示例参数：

```bash
--base-url http://127.0.0.1:1234/v1 --model openai/gpt-oss-20b
```

不要把 key 写进 README、artifact、前端代码或提交记录。真实客户试用如果需要重新仿真，应由部署方或 operator 在受控后端环境配置 key。

## 人群模拟和 LLM 的关系

真实运行新场景的人群模拟需要 LLM，但 LLM 不是直接暴露给浏览器用户的组件。

更准确的架构是混合式：

1. 静态人口先验负责规模化底座，例如 segment、权重、历史统计和公开数据 proxy。
2. LLM 负责语义理解、角色反应和候选更新，例如理解“涨价”“服务规则变更”“政策发布”的情境差异。
3. 交互传播算子负责把个体或群体反应扩展成大规模 rollout。
4. 指标层负责输出趋势方向、可信数值区间、风险分布、异常群体和机制解释。
5. outcome 回流后，系统进入校准候选、shadow replay 和 holdout review，而不是直接把更新上线。

因此，在线 demo 不需要 LLM key；真正部署新场景仿真服务时，需要由 operator 或后端配置 LM Studio、DeepSeek、OpenRouter 等 provider。

## 第五步：验收一次试用

一次企业试用不能只看页面是否漂亮，应该按下面的验收顺序判断：

1. 场景是否清楚：要评估的是政策、价格、权益还是服务规则变化。
2. 人群先验是否明确：要模拟哪些群体、使用什么静态人口先验。
3. 报告是否有证据：趋势方向、风险区间、风险排序、异常群体和机制解释是否绑定 artifact。
4. outcome 是否回流：是否有真实客户 field slice 或独立 public target outcome。
5. intake 是否通过：字段、case 数、审批引用、PII、数值和时间戳是否通过校验。
6. revalidation 是否计算真实指标：是否计算 MAE、风险排序、区间覆盖、异常群体召回等指标。
7. feedback update 是否受控：候选更新是否区分 accepted/rejected，是否经过 shadow replay 和 holdout review。
8. 是否仍然守住边界：没有通过真实验证前，`runtime_default_allowed=false` 必须保持。

## 当前边界

当前可以说：

- 系统已在公开数据上跑通过 guarded 有效性测试。
- 产品 demo 已能展示趋势方向、风险区间、风险排序、异常群体、机制解释和证据边界。
- 离线校准与自优化候选链路已经具备生成、验证、接受或拒绝门禁。
- 企业试用的数据回流、intake、revalidation 和 feedback loop 已有可操作流程。

当前不能说：

- 不承诺精确单点预测。
- 不宣称客户 field validation 已完成。
- 不宣称校准更新可默认自动上线。
- 不把 synthetic rehearsal 包装成真实客户验证。
- 不在 `runtime_default_allowed=false` 的情况下暗示生产默认启用。

## 本地运行

如果你是研发或交付人员，可以在仓库根目录运行：

```bash
python3 -m http.server 8088 --bind 127.0.0.1
```

然后打开：

- 宣传页：`http://127.0.0.1:8088/demo/promo.html`
- 产品 demo：`http://127.0.0.1:8088/demo/`

如果页面提示 artifact 加载失败，优先检查：

1. 是否在仓库根目录启动 server。
2. `experiments/results/` 是否存在对应 JSON。
3. 浏览器是否阻止了本地静态文件请求。
