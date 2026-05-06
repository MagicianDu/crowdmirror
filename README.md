# Calibrated LLM Traveler Simulator

基于大语言模型的可校准旅客行为模拟器。

## 项目结构

本项目包含两个并行工作流：

- **research/** — 科研方向，目标：CCF-A 级别论文发表
- **product/** — 产品方向，目标：策略预审 / 红队测试 / 合规证据生成

## 核心思路

输入"场景上下文 + offer set + 信息集"，输出结构化的选择分布与行为轨迹，
通过小样本真实数据实现校准，使模拟器在统计意义上接近真实人群行为分布。

## 技术栈

- Python 3.11+
- TextGrad / ProTeGi（文本梯度 prompt 优化）
- DSPy（模块化 LLM 编程）
- 离散选择模型（MNL / Nested Logit）
