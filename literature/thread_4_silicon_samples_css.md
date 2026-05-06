# Thread 4: LLM Simulating Human Responses (CSS Empirical)

## Overview

A growing empirical literature in computational social science evaluates whether LLMs, when conditioned on demographic personas, can serve as "silicon samples" — synthetic survey respondents that reproduce the marginal and joint distributions of real human populations. Argyle et al.'s "Out of One, Many" inaugurated the optimistic case; Santurkar et al.'s OpinionQA revealed systematic mis-alignment with US public opinion; subsequent work has triangulated where LLMs succeed (educated/centrist majorities, factual prompts) and where they fail (minorities, extreme positions, joint distributions, sensitive topics). This is the *empirical* foundation our calibration project builds on and improves.

## Key Papers

1. **Argyle, L. P., Busby, E. C., Fulda, N., Gubler, J. R., Rytting, C., & Wingate, D.** (2023). *Out of One, Many: Using Language Models to Simulate Human Samples.* Political Analysis 31(3): 337–351.
2. **Santurkar, S., Durmus, E., Ladhak, F., Lee, C., Liang, P., & Hashimoto, T.** (2023). *Whose Opinions Do Language Models Reflect? (OpinionQA).* ICML 2023.
3. **Durmus, E., Nguyen, K., Liao, T. I., Schiefer, N., Askell, A., Bakhtin, A., Chen, C., Hatfield-Dodds, Z., Hernandez, D., Joseph, N., Lovitt, L., McCandlish, S., Sikder, O., Tamkin, A., Thamkul, J., Kaplan, J., Clark, J., & Ganguli, D.** (2024). *Towards Measuring the Representation of Subjective Global Opinions in Language Models (GlobalOpinionQA).* COLM 2024.
4. **Hwang, E. J., Jeong, S., Kwak, H., Hu, T., & Choi, Y.** (2023). *Aligning Language Models to User Opinions.* EMNLP Findings 2023.
5. **Sun, S. et al.** (2024). *Random Silicon Sampling: Simulating Human Sub-population Opinion Using a Large Language Model based on Group-level Demographic Information.* arXiv:2402.18144.
6. **Bisbee, J., Clinton, J. D., Dorff, C., Kenkel, B., & Larson, J. M.** (2023). *Synthetic Replacements for Human Survey Data? The Perils of Large Language Models.* Political Analysis (2024).
7. **Park, J. S., Zou, C. Q., Shaw, A., Hill, B. M., Cai, C., Morris, M. R., Willer, R., Liang, P., & Bernstein, M. S.** (2024). *Generative Agent Simulations of 1,000 People.* arXiv:2411.10109.
8. **Aher, G., Arriaga, R. I., & Kalai, A. T.** (2023). *Using Large Language Models to Simulate Multiple Humans and Replicate Human Subject Studies.* ICML 2023.
9. **Dillion, D., Tandon, N., Gu, Y., & Gray, K.** (2023). *Can AI Language Models Replace Human Participants?* Trends in Cognitive Sciences 27(7): 597–600.
10. **Crockett, M. J., & Messeri, L.** (2023). *Should Large Language Models Replace Human Participants?* PsyArXiv. (Methodological warning.)
11. **Boelaert, J. et al.** (2024). *Machine Bias: How Does GPT Reflect the General Population's Opinions?* (Working paper, OECD/EU survey replication.)
12. **Bail, C. A.** (2024). *Can Generative AI Improve Social Science?* PNAS 121(21).
13. **Tjuatja, L., Chen, V., Wu, S. T., Talwalkar, A., & Neubig, G.** (2024). *Do LLMs Exhibit Human-like Response Biases? A Case Study in Survey Design.* TACL 2024.
14. **Hartmann, J., Schwenzow, J., & Witte, M.** (2023). *The Political Ideology of Conversational AI.* arXiv:2301.01768.
15. **Motoki, F., Pinho Neto, V., & Rodrigues, V.** (2024). *More Human than Human: Measuring ChatGPT Political Bias.* Public Choice.
16. **Cheng, M., Durmus, E., & Jurafsky, D.** (2023). *Marked Personas: Using Natural Language Prompts to Measure Stereotypes in Language Models.* ACL 2023.
17. **Wang, A. et al.** (2024). *Large Language Models Cannot Replace Human Participants Because They Cannot Portray Identity Groups.* arXiv:2402.01908.
18. **Sun, Z. et al.** (2024). *Persona-Bench: Evaluating LLMs' Ability to Adopt Personas.* arXiv (NeurIPS workshop).
19. **Atari, M., Xue, M. J., Park, P. S., Blasi, D. E., & Henrich, J.** (2023). *Which Humans?* PsyArXiv. (Demonstrates LLMs' WEIRD bias against non-Western populations.)
20. **Kim, J., & Lee, B.** (2024). *AI-Augmented Surveys: Leveraging Large Language Models and Surveys for Opinion Prediction.* arXiv:2305.09620.
21. **Salganik, M. J. et al.** (2024). *Replicating the Fragile Families Challenge with LLMs.* (Working paper.)

## Main Findings

**LLMs reproduce mainstream opinion well, minorities poorly.** Argyle showed GPT-3 conditioned on ANES demographics reproduced 2012/2016 vote-choice marginals quite well within mainstream demographic cells; Santurkar showed default LLM opinions track college-educated, liberal, US-centric subgroups; Durmus extended this globally and found a strong English-speaking, Western tilt. Atari ("Which Humans?") demonstrated WEIRD bias on moral foundations. Wang (2024) shows LLMs *misportray* identity groups in qualitative interviews.

**Joint distributions are worse than marginals.** Even when an LLM reproduces marginal vote share or marginal opinion frequency, the *joint* distribution across demographics (e.g., Black evangelical vote × age × income) collapses or distorts. Bisbee et al. document that LLM "samples" can pass marginal tests while failing joint tests catastrophically.

**Persona conditioning helps but with diminishing returns.** Adding more demographic detail to a persona prompt improves marginal alignment for majority groups but does not eliminate the under-representation of minority/extreme positions. Park 2024's interview-based personas (2-hour interviews → persona) push individual-level accuracy higher (~85% normalized) but require costly interview data.

**LLMs exhibit response biases similar but not identical to humans.** Tjuatja et al. show LLMs share some human survey artifacts (acquiescence) but differ on others (order effects, satisficing). This complicates "synthetic respondent" use because the biases are not the same biases survey methodology has been built to handle.

**Temporal validity is fragile.** LLMs reflect a snapshot of training data; opinions on dynamic issues (e.g., Ukraine, abortion post-Dobbs) drift away from current populations.

**Replication of classic experiments is mixed.** Aher's Turing Experiments replicate Milgram, Ultimatum, etc., qualitatively. But quantitative effect sizes differ from human meta-analyses, and replication failures cluster in experiments that depend on minority or out-group identification.

**Standard "alignment" interventions distort survey behavior.** RLHF tends to push opinions toward perceived consensus, reducing variance and making LLMs *less* representative of real human heterogeneity than base models. Hartmann/Motoki document strong center-left tilt in RLHF'd models.

## Gaps & Limitations

1. **Few interventions to *fix* the alignment.** Papers measure mis-alignment but rarely propose methods that *modify* the simulator to better match a target population. The few that do (Hwang's "Aligning Language Models to User Opinions") use fine-tuning, which is expensive and not portable across base models.
2. **No principled treatment of the persona → distribution mapping.** It is taken for granted that demographic prompts induce a draw from the conditional distribution P(opinion | demographics). The induced distribution is whatever the LLM happens to give. There is no estimation theory.
3. **Sample-size and power analysis are absent.** How many simulated respondents are needed to estimate a marginal to ±2pp? Variance scaling with persona diversity, temperature, and prompting strategy is unstudied.
4. **Joint-distribution evaluation is not standardized.** Most papers report marginals or pairwise. Higher-order joint tests, copula recovery, dependence structure tests are not used.
5. **Counterfactual / hypothetical question handling.** LLMs answering "what if X were the policy" diverge from human responses to the same question — but this is exactly the use case for which synthetic respondents are most attractive.
6. **No clean separation between "simulator imperfection" and "ground truth noise".** Survey data has finite-sample noise, mode effects, weighting choices. Comparisons rarely propagate this uncertainty.

## Our Positioning

Our work directly addresses the central failure mode this thread documents: LLM-simulated populations are mis-calibrated, especially on minorities and joint distributions. We propose a methodology that (i) takes empirical survey data as the calibration target; (ii) uses prompt optimization (Thread 2) to fit persona-generator and decision-policy prompts to *reduce* marginal and joint divergence; (iii) treats the persona-conditioning prompt as an estimable parameter rather than a fixed convention; (iv) reports the population-alignment metrics this thread implicitly demands but does not standardize (Thread 5). Where Argyle/Santurkar diagnose the problem and Park 2024 demonstrates a costly interview-based fix, we offer a *cheap, optimization-based* fix that operates on prompts rather than fine-tuning weights.

