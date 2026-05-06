# Thread 5: CSS Evaluation Benchmarks & Population Alignment

## Overview

As LLM-based social simulation matures, the field urgently needs standardized evaluation protocols that go beyond "looks plausible" or "matches the mean." This thread surveys existing benchmarks for evaluating LLM social behavior, population-level alignment metrics from statistics and machine learning, and calibration frameworks that could be adapted to behavioral simulation. The key finding is that *no unified evaluation protocol exists* for population-level LLM simulation — this is a gap our work fills.

## Key Papers

1. **Santurkar, S. et al.** (2023). *Whose Opinions Do Language Models Reflect? (OpinionQA).* ICML 2023. (Benchmark: 1,498 questions from Pew American Trends Panel; metrics: representativeness, steerability, consistency.)
2. **Durmus, E. et al.** (2024). *Towards Measuring the Representation of Subjective Global Opinions in Language Models (GlobalOpinionQA).* COLM 2024. (Extends OpinionQA to 75 countries.)
3. **Zhou, X. et al.** (2024). *SOTOPIA: Interactive Evaluation for Social Intelligence in Language Agents.* ICLR 2024. (Benchmark: 90 social scenarios; metrics: goal completion, social norms, believability.)
4. **Kim, S. et al.** (2024). *SODA-Eval: Open-Domain Dialogue Evaluation in the Age of LLMs.* (Benchmark for social dialogue quality.)
5. **Bisbee, J. et al.** (2024). *Synthetic Replacements for Human Survey Data? The Perils of Large Language Models.* Political Analysis. (Proposes marginal + joint distribution tests.)
6. **Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q.** (2017). *On Calibration of Modern Neural Networks.* ICML 2017. (ECE, reliability diagrams — foundational calibration metrics.)
7. **Naeini, M. P., Cooper, G. F., & Hauskrecht, M.** (2015). *Obtaining Well Calibrated Probabilities Using Bayesian Binning into Quantiles.* AAAI 2015. (Calibration metrics.)
8. **Kadavath, S. et al.** (2022). *Language Models (Mostly) Know What They Know.* arXiv:2207.05221. (LLM self-calibration on factual questions.)
9. **Tian, K. et al.** (2023). *Just Ask for Calibration: Strategies for Eliciting Calibrated Confidence Scores from Language Models.* EMNLP 2023.
10. **Zhou, K. et al.** (2024). *Is This the Real Life? Is This Just Fantasy? The Misleading Success of Simulating Social Interactions with LLMs.* EMNLP 2024. (Proposes harder evaluation criteria for social simulation.)
11. **Tjuatja, L. et al.** (2024). *Do LLMs Exhibit Human-like Response Biases?* TACL 2024. (Evaluation protocol for survey-response artifacts.)
12. **Aher, G. et al.** (2023). *Using Large Language Models to Simulate Multiple Humans (Turing Experiments).* ICML 2023. (Proposes "Turing Experiment" evaluation: replicate classic studies.)
13. **Anthis, J. R. et al.** (2025). *LLM Social Simulations Are a Promising Research Method.* arXiv:2504.02234. (Proposes evaluation taxonomy: internal validity, external validity, construct validity.)
14. **Bail, C. A.** (2024). *Can Generative AI Improve Social Science?* PNAS. (Proposes evaluation criteria for AI-augmented CSS.)
15. **Salganik, M. J. et al.** (2020). *Measuring the Predictability of Life Outcomes with a Scientific Mass Collaboration (Fragile Families Challenge).* PNAS. (Benchmark for predicting life outcomes; relevant evaluation protocol.)
16. **Hofman, J. M. et al.** (2021). *Integrating Explanation and Prediction in Computational Social Science.* Nature. (Evaluation philosophy for CSS models.)
17. **Cranmer, K. et al.** (2020). *The Frontier of Simulation-Based Inference.* PNAS. (Simulation-based inference evaluation; posterior calibration.)
18. **Zhao, S. et al.** (2021). *Calibrating Predictions to Decisions: A Novel Approach to Multi-Class Calibration.* NeurIPS 2021. (Decision-calibration metrics.)
19. **Kuleshov, V., Fenner, N., & Ermon, S.** (2018). *Accurate Uncertainties for Deep Learning Using Calibrated Regression.* ICML 2018. (Calibration for continuous predictions.)
20. **Park, J. S. et al.** (2024). *Generative Agent Simulations of 1,000 People.* arXiv:2411.10109. (Proposes "normalized accuracy" metric for individual-level prediction.)

## Main Findings

**No unified benchmark for population-level LLM simulation exists.** OpinionQA and GlobalOpinionQA are the closest: they provide ground-truth opinion distributions from Pew/WVS and measure LLM representativeness. But they evaluate *single-question marginals*, not joint distributions, not choice sequences, not counterfactual responses.

**Existing metrics are fragmented across communities:**
- *NLP/LLM calibration:* ECE, reliability diagrams, Brier score — applied to factual QA confidence, not behavioral choice distributions.
- *Survey methodology:* Marginal comparison (chi-squared, KS test), weighting diagnostics, design effects — not adapted to LLM outputs.
- *Simulation validation:* Pattern-oriented modeling (POM), stylized-fact matching, sensitivity analysis — from ABM literature, qualitative.
- *Statistical inference:* KL divergence, Wasserstein distance, MMD, posterior calibration — from simulation-based inference, not applied to LLM simulators.
- *Choice modeling:* Log-likelihood, hit rate, elasticity recovery, IIA tests — from DCM, not applied to LLM choice predictions.

**Individual-level vs. population-level evaluation is conflated.** Park 2024's "normalized accuracy" measures per-individual prediction quality. Argyle's vote-share comparison measures population marginals. These are different targets with different implications. A simulator can be well-calibrated at the population level while being noisy at the individual level (and vice versa).

**Calibration of LLM confidence ≠ calibration of simulated behavior.** Kadavath and Tian study whether LLMs' stated confidence matches their factual accuracy. This is *epistemic* calibration. Our target is *behavioral* calibration: does the distribution of simulated choices match the distribution of real choices? These are related but distinct.

**Counterfactual evaluation is the hardest and most important.** For CSS, the value of a simulator is in predicting what happens under interventions (new policy, new product, new information). Counterfactual evaluation requires either (a) held-out experimental data or (b) structural assumptions. Neither is standard in LLM simulation evaluation.

**The ABM validation literature offers useful frameworks.** Pattern-oriented modeling (Grimm et al.), cross-validation against multiple empirical patterns simultaneously, and sensitivity analysis are well-developed for agent-based models but have not been adapted to LLM-based agents.

## Gaps & Limitations

1. **No standard evaluation protocol for population-level LLM simulation.** No paper proposes a complete protocol covering: marginal calibration, joint-distribution calibration, subgroup calibration, counterfactual prediction, sensitivity analysis, and temporal stability — all in one framework.
2. **Joint-distribution metrics are absent.** Marginal KL or chi-squared is easy; testing whether the full joint P(choice₁, choice₂, ..., choiceₖ | demographics) is recovered is hard and unstudied.
3. **Calibration-in-the-small vs. calibration-in-the-large.** ECE averages over all predictions. For CSS, we need *subgroup-conditional* calibration: is the simulator well-calibrated for Black women aged 18–24? For rural Republicans? Conditional calibration metrics exist (Hébert-Johnson et al., "Multicalibration") but have not been applied here.
4. **No counterfactual evaluation benchmark.** No dataset pairs "pre-intervention distribution" with "post-intervention distribution" for LLM simulation evaluation.
5. **Temporal evaluation is missing.** Can a simulator calibrated on 2020 data predict 2022 distributions? No benchmark tests this.
6. **Computational cost of evaluation is unaddressed.** Evaluating a 10k-agent simulator on 100 questions requires 1M LLM calls. Efficient evaluation (importance sampling, surrogate metrics) is unexplored.

## Our Positioning

We propose a *unified evaluation protocol* for calibrated LLM population simulators that draws from all five source communities:

| Level | Metric | Source |
|-------|--------|--------|
| Marginal | KL, chi-squared, TV distance per question | Survey methodology |
| Joint | Copula divergence, conditional mutual information | Statistics |
| Subgroup | Multicalibration error (Hébert-Johnson) | Fairness/ML |
| Choice probability | ECE, Brier, log-loss | NLP calibration + DCM |
| Counterfactual | Held-out experimental ATE recovery | Causal inference |
| Sensitivity | Temperature/prompt perturbation stability | ABM validation |
| Temporal | Train-on-T, test-on-T+1 distribution shift | Panel data |

This protocol is both our *evaluation framework* and our *optimization target* — we calibrate the simulator to minimize a weighted combination of these metrics, then report the full suite. This positions our work as providing both a *method* (calibrated simulation) and a *benchmark* (the evaluation protocol itself).

