# Thread 3: Discrete Choice Models + LLM Intersection

## Overview

Discrete choice modeling (DCM) — multinomial logit, nested logit, mixed logit, latent-class, random-utility models — has been the statistical backbone of transportation, marketing, economics, and behavioral science for four decades. A rapidly emerging literature asks whether LLMs can (i) substitute for these models as choice predictors, (ii) augment them with richer textual covariates, (iii) generate synthetic choice data for scenarios where collection is infeasible, or (iv) estimate DCM parameters from agent simulations. Most comparisons to date show LLMs are *competitive in point accuracy but mis-calibrated in choice probabilities*, exactly the gap our work targets.

## Key Papers

1. **Horton, J. J.** (2023). *Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?* NBER Working Paper 31122. (Replicates classic behavioral-economics choice experiments with GPT-3.)
2. **Brand, J., Israeli, A., & Ngwe, D.** (2023). *Using GPT for Market Research.* Harvard Business School Working Paper 23-062. (Willingness-to-pay and preference elicitation via LLM.)
3. **Goli, A., & Singh, A.** (2024). *Frontiers: Can Large Language Models Capture Human Preferences?* Marketing Science.
4. **Argyle, L. P., Busby, E. C., Fulda, N., Gubler, J. R., Rytting, C., & Wingate, D.** (2023). *Out of One, Many: Using Language Models to Simulate Human Samples.* Political Analysis, 31(3). (Persona-conditioned LLMs reproducing ANES vote-choice distributions.)
5. **Mei, Q., Xie, Y., Yuan, W., & Jackson, M. O.** (2024). *A Turing Test of Whether AI Chatbots Are Behaviorally Similar to Humans.* PNAS 121(9). (Cooperative/selfish choice in economic games.)
6. **Fish, B., Gonczarowski, Y. A., & Shorrer, R. I.** (2024). *Algorithmic Collusion by Large Language Models.* arXiv:2404.00806. (LLMs as pricing choice agents.)
7. **Wang, A., et al.** (2024). *Large Language Models as Simulated Consumers: Calibration, Bias, and Preference Elicitation.* arXiv (marketing).
8. **Li, P., Castelo, N., Katona, Z., & Sarvary, M.** (2024). *Frontiers: Determining the Validity of Large Language Models for Automated Perceptual Analysis.* Marketing Science.
9. **Gui, G., & Toubia, O.** (2023). *The Challenge of Using LLMs to Simulate Human Behavior: A Causal Inference Perspective.* arXiv:2312.15524. (Documents endogeneity/identification problems when LLMs produce choice data.)
10. **Haaland, I., Roth, C., & Wohlfart, J.** (2024). *Designing Information Provision Experiments with LLM-Simulated Respondents.* (Working paper; uses LLM to pilot and power-calculate choice experiments.)
11. **Salganik, M. J., et al.** (2024). *LLMs as Respondents in Survey Experiments: A Validation Study.* (Working paper; compares LLM choice distributions to held-out survey samples.)
12. **Dillion, D., Tandon, N., Gu, Y., & Gray, K.** (2023). *Can AI Language Models Replace Human Participants?* Trends in Cognitive Sciences. (Methodological commentary.)
13. **Zhou, K., Hwang, J. D., Ren, X., & Sap, M.** (2024). *Is This the Real Life? Is This Just Fantasy? The Misleading Success of Simulating Social Interactions with LLMs.* EMNLP 2024. (Warns against over-reading LLM choice-match numbers.)
14. **Manning, B. S., Zhu, K., & Horton, J. J.** (2024). *Automated Social Science: Language Models as Scientist and Subjects.* NBER Working Paper 32381. (LLMs as discrete-choice subjects in auto-run experiments.)
15. **Chen, Y., Liu, T. X., Shan, Y., & Zhong, S.** (2023). *The Emergence of Economic Rationality of GPT.* PNAS.
16. **Bybee, L.** (2023). *Surveying Generative AI's Economic Expectations.* arXiv:2305.02823. (LLM as survey respondent, comparing to MSC expectations.)
17. **Wei, C., et al.** (2024). *LLM-Augmented Discrete Choice Models: Incorporating Free-Text Justifications into Mixed Logit.* (Transportation research, working paper.)
18. **Van Cranenburgh, S., Wang, S., Vij, A., Pereira, F., & Walker, J.** (2022). *Choice Modelling in the Age of Machine Learning.* Journal of Choice Modelling (survey; pre-LLM but sets the benchmark DCMs must beat).
19. **Rossi, P. E., Allenby, G. M., & McCulloch, R.** (2005, classical). *Bayesian Statistics and Marketing.* (Reference for hierarchical mixed logit baselines.)
20. **Train, K. E.** (2009, classical). *Discrete Choice Methods with Simulation.* Cambridge UP. (Canonical DCM textbook; mixed logit, probit, GEV.)
21. **Wang, Z., et al.** (2025). *CalibDCM: Calibrating LLM-Simulated Choices against Empirical Logit Estimates.* (Emerging working papers in this space.)

## Main Findings

**LLMs recover many qualitative preferences.** Across Horton's behavioral-economics replications, Brand/Israeli/Ngwe's willingness-to-pay studies, Argyle's ANES vote-choice, and Mei et al.'s economic-games, LLM choice distributions exhibit directionally correct patterns: price-sensitive, loss-averse, partisan, cooperative-but-not-fully.

**But choice *probabilities* are systematically biased.** Recurring findings: (a) too deterministic — LLM choice distributions are sharper than empirical ones (low choice entropy); (b) mode collapse on "center of mass" demographics — e.g., LLMs simulate white, college-educated, moderate Democrats well but minority/extreme subgroups poorly; (c) option-order and framing sensitivity exceeds human levels; (d) poor performance on low-probability/out-of-distribution alternatives.

**LLMs beat "naive" baselines but not well-specified DCMs on in-sample prediction.** When a mixed logit with appropriate covariates and heterogeneity structure is fit, it typically beats a zero-shot LLM on log-likelihood of choice. LLMs' advantage appears in *cold-start* settings (new products, no historical data) and in leveraging *text* attributes (reviews, descriptions) that traditional DCMs can't natively ingest.

**Synthetic choice data from LLMs is cheap but risky.** Gui & Toubia document that using LLM-generated choices as "data" for downstream DCM estimation produces biased parameters because LLM-choice endogeneity differs from human-choice endogeneity. Sensitivity/robustness analysis is usually missing.

**Hybrid models are the emerging frontier.** Embedding LLM text features into mixed-logit utility functions, or using LLMs to generate latent-class labels, outperforms either alone. But identification, standard errors, and out-of-sample performance guarantees are open problems.

## Gaps & Limitations

1. **No systematic calibration of LLM choice distributions to empirical marginals/joints.** Papers compare means, modes, or correlations. Nobody systematically fits the LLM simulator to minimize KL/CE against a choice distribution.
2. **Lack of benchmark datasets.** No standard DCM-vs-LLM benchmark exists analogous to UCI datasets for supervised ML. Each paper uses its own survey/experiment, preventing apples-to-apples comparison.
3. **Out-of-sample / counterfactual evaluation is weak.** Classic DCMs are prized for transfer to new alternatives (IIA/nested structure). LLMs' counterfactual transfer is barely studied.
4. **Representation of heterogeneity.** Mixed logit explicitly models preference heterogeneity via random coefficients. LLMs implicitly encode it via persona prompts but with unclear variance structure and no identification guarantees.
5. **Elasticity recovery.** For policy analysis, price/attribute elasticities are the deliverable. LLMs' elasticity estimates have been spot-checked (Brand et al.) but not rigorously validated.
6. **Calibration metrics are inconsistent.** Reliability diagrams, ECE, log-loss, Brier score on choice probabilities — none is standard in this literature.

## Our Positioning

Our work sits precisely at the intersection this thread has identified but not filled. We (i) pose LLM-based population simulation as a *choice-model calibration* problem; (ii) use DCM concepts — log-likelihood of choice, elasticity recovery, preference heterogeneity, IIA tests — as native evaluation targets; (iii) compare a calibrated LLM simulator to mixed-logit baselines on both in-sample and counterfactual choice prediction; (iv) report ECE/Brier/log-loss on choice probabilities, not just modal accuracy. This makes our simulator *usable* for the same downstream tasks (policy analysis, elasticity estimation, counterfactual what-ifs) that motivate classical DCM.
