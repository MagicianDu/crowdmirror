# Thread 2: LLM Calibration & Prompt Optimization

## Overview

A fast-moving thread of work treats prompts, scaffolds, and demonstration sets as *parameters* of an LLM program and applies optimization — gradient-like text feedback, evolutionary search, RL, or Bayesian methods — to fit them to a task objective. The flagship systems are TextGrad, ProTeGi, DSPy, and PromptBreeder, with a steady stream of newer optimizers (OPRO, EvoPrompt, GRIPS, AutoPrompt, MIPROv2, GEPA). Almost all of this work targets standard NLP benchmarks (GSM8K, BIG-Bench, HotpotQA, MMLU). To our knowledge, *none* has been used to calibrate a generative-agent social simulator against population-level empirical distributions.

## Key Papers

1. **Yuksekgonul, M., Bianchi, F., Boen, J., Liu, S., Huang, Z., Guestrin, C., & Zou, J.** (2024). *TextGrad: Automatic "Differentiation" via Text.* arXiv:2406.07496. (Backprop-style natural-language feedback through compound LLM systems.)
2. **Pryzant, R., Iter, D., Li, J., Lee, Y. T., Zhu, C., & Zeng, M.** (2023). *Automatic Prompt Optimization with "Gradient Descent" and Beam Search (ProTeGi).* EMNLP 2023, arXiv:2305.03495.
3. **Khattab, O., Singhvi, A., Maheshwari, P., Zhang, Z., Santhanam, K., A, S. V., Haq, S., Sharma, A., Joshi, T. T., Moazam, H., Miller, H., Zaharia, M., & Potts, C.** (2024). *DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines.* ICLR 2024 (workshop) / arXiv:2310.03714.
4. **Opsahl-Ong, K., Ryan, M. J., Purtell, J., Broman, D., Potts, C., Zaharia, M., & Khattab, O.** (2024). *Optimizing Instructions and Demonstrations for Multi-Stage Language Model Programs (MIPROv2).* EMNLP 2024.
5. **Fernando, C., Banarse, D., Michalewski, H., Osindero, S., & Rocktäschel, T.** (2023). *Promptbreeder: Self-Referential Self-Improvement via Prompt Evolution.* arXiv:2309.16797.
6. **Yang, C., Wang, X., Lu, Y., Liu, H., Le, Q. V., Zhou, D., & Chen, X.** (2023). *Large Language Models as Optimizers (OPRO).* arXiv:2309.03409.
7. **Guo, Q., Wang, R., Guo, J., Li, B., Song, K., Tan, X., Liu, G., Bian, J., & Yang, Y.** (2023). *Connecting Large Language Models with Evolutionary Algorithms Yields Powerful Prompt Optimizers (EvoPrompt).* ICLR 2024.
8. **Prasad, A., Hase, P., Zhou, X., & Bansal, M.** (2022). *GrIPS: Gradient-free, Edit-based Instruction Search.* EACL 2023.
9. **Shin, T., Razeghi, Y., Logan IV, R. L., Wallace, E., & Singh, S.** (2020). *AutoPrompt: Eliciting Knowledge from Language Models with Automatically Generated Prompts.* EMNLP 2020.
10. **Zhou, Y., Muresanu, A. I., Han, Z., Paster, K., Pitis, S., Chan, H., & Ba, J.** (2023). *Large Language Models Are Human-Level Prompt Engineers (APE).* ICLR 2023.
11. **Agrawal, L. A., Tan, S. P., Soylu, D., Ziems, N., Khare, R., Opsahl-Ong, K., Singhvi, A., Shandilya, H., Ryan, M. J., Jiang, M., Potts, C., Sen, K., Suchara, A. M., Khattab, O., & Zaharia, M.** (2025). *GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning.* arXiv:2507.19457.
12. **Cheng, J., Liu, X., Zheng, K., Ke, P., Wang, H., Dong, Y., Tang, J., & Huang, M.** (2023). *Black-Box Prompt Optimization: Aligning Large Language Models without Model Training.* ACL 2024.
13. **Wang, X., Li, C., Wang, Z., Bai, F., Luo, H., Zhang, J., Jojic, N., Xing, E. P., & Hu, Z.** (2024). *PromptAgent: Strategic Planning with Language Models Enables Expert-level Prompt Optimization.* ICLR 2024.
14. **Zhang, T., Wang, X., Zhou, D., Schuurmans, D., & Gonzalez, J. E.** (2023). *TEMPERA: Test-Time Prompt Editing via Reinforcement Learning.* ICLR 2023.
15. **Lin, X., Wu, Z., Dai, Z., Hu, W., Shu, Y., Ng, S.-K., Jaillet, P., & Low, B. K. H.** (2024). *Use Your INSTINCT: INSTruction optimization usIng Neural bandits Coupled with Transformers.* ICML 2024.
16. **Sordoni, A., Yuan, X., Côté, M.-A., Pereira, M., Trischler, A., Xiao, Z., Hosseini, A., Niedtner, F., & Le Roux, N.** (2023). *Joint Prompt Optimization of Stacked LLMs using Variational Inference (DLN-2).* NeurIPS 2023.
17. **Zhou, Y., Lin, J., Liu, R., Wang, X., & Wu, Y.** (2025). *Trace: A Framework for End-to-End Optimization of Generative Optimization Workflows.* NeurIPS 2024 / arXiv:2406.16218.
18. **Hu, Z., Lan, Y., Wang, L., Xu, W., Lim, E.-P., Lee, R. K.-W., Bing, L., Xu, X., & Poria, S.** (2023). *LLM-Adapters / Soft Prompt Tuning Survey.* arXiv:2304.01933.
19. **Zhao, T. Z. et al.** (2024). *DSPy Assertions: Computational Constraints for Self-Refining Language Model Pipelines.* (Builds DSPy-style optimization with constraint satisfaction.)
20. **Schluntz, E., & Zhang, B.** (2024). *Building Effective Agents.* (Anthropic engineering report; canonical reference for "compound system" framing that motivates prompt optimization.)

## Main Findings

**Prompt programs are differentiable in a useful sense.** TextGrad and ProTeGi formalize the idea that an LLM critic can produce textual analogs of gradients: directional edits to prompts that reduce a downstream loss. With beam search or evolutionary acceptance, this reliably improves prompts on standard NLP tasks.

**Compound systems benefit most.** DSPy's central claim — and the empirical pattern across MIPROv2, GEPA, Trace — is that multi-module pipelines (retriever + reasoner + verifier) gain more from joint optimization than single-prompt tasks. Optimization shifts from prompt-engineering folklore to a compilation step.

**Optimizers are converging in capability.** GEPA (2025) reports that reflective prompt evolution can match or exceed RL fine-tuning on agent tasks at a fraction of the cost; MIPROv2 reports SOTA across many DSPy benchmarks; PromptBreeder remains competitive without LLM critics. The methods differ in exploration strategy but agree that text-feedback + acceptance-based search is sample-efficient.

**Targets are overwhelmingly accuracy / EM / F1.** GSM8K, MATH, HotpotQA, BBH, MMLU, classification accuracy. A handful of papers target preference/reward models. Almost none target *distributional* losses over agent outputs.

**Few examples in agent / simulation settings.** GEPA optimizes agent traces; some DSPy work tunes ReAct-style agents. But the targets are still task success (did the agent solve the puzzle?), not *match a distribution of human behavior*.

## Gaps & Limitations

1. **No distributional / population losses.** Existing optimizers minimize task accuracy on i.i.d. labeled examples. Calibration of a *simulator* requires losses over distributions (KL, Wasserstein, MMD, calibration error on choice probabilities, joint-distribution divergence). This requires non-trivial extensions: differentiating through stochastic sampling, accounting for finite-sample noise, regularizing against overfitting to marginals at the cost of joints.
2. **No persona/agent calibration application.** No published work optimizes the *persona-generation prompt* or *agent scaffold* to make a population of agents match an empirical demographic distribution. The closest analog is in-context learning ICL example selection for classification — far from population calibration.
3. **Identifiability and overfitting are unaddressed at population scale.** With ~5–10 prompts and a finite empirical distribution, what is the effective parameter count of a prompt-optimized simulator? When does it overfit? No theory exists.
4. **Computational cost.** Optimization runs typically require 10²–10⁴ LLM calls. For a 10k-agent simulator with full prompt rollout, naive application is infeasible; surrogate or amortized approaches are unexplored.
5. **Joint optimization with persona inference.** When personas themselves are inferred from data (e.g., from interview transcripts à la Park 2024), the persona generator and the agent scaffold must be co-optimized. No existing optimizer handles this.
6. **Stability across base models.** Optimized prompts often fail to transfer between base models. For CSS, where simulation may need to track model upgrades, transferability is essential.

## Our Positioning

We are, to the best of our knowledge, the first to apply text-gradient / DSPy-style optimization to a *generative-agent population simulator* with a *population-alignment objective*. Concretely: (i) we cast our simulator as a DSPy/TextGrad-compatible program with persona-generator, decision-policy, and aggregation modules; (ii) we define population losses (Thread 5) that compare simulated and empirical choice distributions; (iii) we adapt MIPROv2/GEPA-style optimizers to this distributional setting, with regularization to avoid marginal-overfitting; (iv) we report transferability across base models. This bridges Threads 1 and 2 — the generative-agent community has the simulator architecture but not the optimizer; the prompt-optimization community has the optimizer but has not seen population-distribution targets.

