# Thread 1: Generative Agents & LLM Social Simulation

## Overview

Since Park et al.'s "Generative Agents" (UIST'23) demonstrated that GPT-3.5 agents in a Sims-like sandbox could produce believable individual and emergent social behaviors, a large literature has scaled the paradigm to entire societies, organizations, economies, and online platforms. The dominant evaluation paradigm in this thread is *believability* and *qualitative emergence* (party invitations spreading, coordinated activity), not statistical alignment with empirical population behavior. This is the field whose central methodological gap our work aims to close.

## Key Papers

1. **Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S.** (2023). *Generative Agents: Interactive Simulacra of Human Behavior.* UIST '23.
2. **Park, J. S., Zou, C. Q., Shaw, A., Hill, B. M., Cai, C., Morris, M. R., Willer, R., Liang, P., & Bernstein, M. S.** (2024). *Generative Agent Simulations of 1,000 People.* arXiv:2411.10109. (Replicates 1,000 real interview subjects' GSS responses; reports ~85% normalized accuracy.)
3. **Piao, J. et al.** (2025). *AgentSociety: Large-Scale Simulation of LLM-Driven Generative Agents Advances Understanding of Human Behaviors and Society.* arXiv:2502.08691. (Tsinghua THUFD; 10k+ agents on a city-scale platform; tests polarization, UBI, hurricane response.)
4. **Gao, C., Lan, X., Lu, Z., Mao, J., Piao, J., Wang, H., Jin, D., & Li, Y.** (2024). *S³: Social-network Simulation System with Large Language Model-Empowered Agents.* arXiv:2307.14984.
5. **Li, N., Gao, C., Li, Y., & Liao, Q.** (2024). *Large Language Model-Empowered Agents for Simulating Macroeconomic Activities (EconAgent).* ACL 2024.
6. **Horton, J. J.** (2023). *Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?* NBER Working Paper.
7. **Aher, G., Arriaga, R. I., & Kalai, A. T.** (2023). *Using Large Language Models to Simulate Multiple Humans and Replicate Human Subject Studies (Turing Experiments).* ICML 2023.
8. **Williams, R., Hosseinichimeh, N., Majumdar, A., & Ghaffarzadegan, N.** (2023). *Epidemic Modeling with Generative Agents.* arXiv:2307.04986.
9. **Hua, W., Fan, L., Li, L., Mei, K., Ji, J., Ge, Y., Hemphill, L., & Zhang, Y.** (2023). *War and Peace (WarAgent): LLM-based Multi-Agent Simulation of World Wars.* arXiv:2311.17227.
10. **Mou, X., Wei, Z., & Huang, X.** (2024). *Unveiling the Truth and Facilitating Change: Towards Agent-based Large-scale Social Movement Simulation.* ACL 2024.
11. **Yang, Z. et al.** (2024). *OASIS: Open Agent Social Interaction Simulations with One Million Agents.* arXiv:2411.11581. (CAMEL-AI; rumor spread, Twitter/Reddit dynamics.)
12. **Chen, W. et al.** (2024). *AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors in Agents.* ICLR 2024.
13. **Li, G., Hammoud, H. A. A. K., Itani, H., Khizbullin, D., & Ghanem, B.** (2023). *CAMEL: Communicative Agents for "Mind" Exploration of Large Scale Language Model Society.* NeurIPS 2023.
14. **Zhao, Q. et al.** (2024). *CompeteAI: Understanding the Competition Behaviors in Large Language Model-based Agents.* arXiv:2310.17512.
15. **Vezhnevets, A. S. et al.** (2023). *Generative Agent-Based Modeling with Actions Grounded in Physical, Social, or Digital Space using Concordia.* DeepMind, arXiv:2312.03664.
16. **Törnberg, P., Valeeva, D., Uitermark, J., & Bail, C.** (2023). *Simulating Social Media Using Large Language Models to Evaluate Alternative News Feed Algorithms.* arXiv:2310.05984.
17. **Zhou, X., Zhu, H., Mathur, L., Zhang, R., Yu, H., Qi, Z., Morency, L.-P., Bisk, Y., Fried, D., Neubig, G., & Sap, M.** (2024). *SOTOPIA: Interactive Evaluation for Social Intelligence in Language Agents.* ICLR 2024.
18. **Liu, R. et al.** (2024). *Skill Set Optimization: Reinforcing Language Model Behavior via Transferable Skills (and society sims).* ICML 2024.
19. **Kaiya, Z. et al.** (2023). *Lyfe Agents: Generative Agents for Low-cost Real-time Social Interactions.* arXiv:2310.02172.
20. **Anthis, J. R., Liu, R., Richardson, S. M., Kozlowski, A. C., Koch, B., Evans, J., Brynjolfsson, E., & Bernstein, M.** (2025). *LLM Social Simulations Are a Promising Research Method.* arXiv:2504.02234. (Position paper surveying the field, identifying calibration as a core open problem.)

## Main Findings

**Believable individual behavior is achievable.** Park et al. established that memory + reflection + planning architectures yield agents that pass observer-Turing tests for individual believability and produce qualitative emergent phenomena (information diffusion, coordinated parties, role-appropriate dialogue). Replications across Smallville-style sandboxes (Lyfe Agents, AgentVerse, Concordia) confirm this is robust to architecture choice given a sufficiently capable base model.

**Scale has grown by ~3 orders of magnitude.** From Park's 25-agent village to OASIS (1M agents), AgentSociety (10k agents on city OSM), and Park 2024 (1,000 interviewed personas). Engineering platforms now support city-scale simulations with mobility, networks, and LLM cognition.

**Domain coverage is broad.** Substantive applications include macroeconomics (EconAgent), epidemic spread, social movements, polarization, UBI experiments, war/diplomacy (WarAgent), social media algorithm A/B testing (Törnberg), market competition (CompeteAI), and disaster response.

**Emergent behaviors are reported as a feature, not measured.** Most papers narrate qualitative findings ("agents formed coalitions," "rumors propagated," "polarization emerged") and at most report directional agreement with stylized facts. EconAgent and Williams (epidemic) are partial exceptions that compare aggregate curves to known dynamics.

**Park 2024 is the closest to calibration.** It generates per-individual agents from 2-hour interviews and predicts GSS/Big Five/economic-game responses, reporting ~85% normalized accuracy at the individual level. But the work treats LLM behavior as fixed and does not optimize prompts/architectures against the data.

## Gaps & Limitations

1. **No closed-loop calibration.** Almost no work in this thread treats the LLM-agent simulator as a parametric model to be *fit* to empirical population data. Park 2024 evaluates a frozen pipeline; AgentSociety reports stylized-fact agreement; OASIS reports qualitative spread patterns. None update prompts, persona generators, or scaffolding to minimize a population-level loss against ground truth.
2. **Believability ≠ validity.** Observer Turing tests and "looks plausible" plots dominate evaluation. Standard CSS validity criteria (face, construct, predictive) are rarely operationalized.
3. **Population-level metrics are underused.** When ground truth exists, papers report point accuracy or correlation. KL/Wasserstein on choice distributions, calibration of marginals, joint distribution alignment, and counterfactual prediction quality are essentially absent.
4. **Persona generation is ad hoc.** Personas are sampled from census marginals or hand-written templates with little justification. The mapping from demographics → LLM persona prompt is itself an unidentified parametric family.
5. **No principled prompt search.** Architectural choices (memory, reflection, retrieval) are tuned by inspection. Automatic optimization (TextGrad/DSPy/ProTeGi) has not been brought to bear on social simulation pipelines.
6. **Reproducibility and base-model conflation.** Effects attributed to "agent architecture" often track base-model upgrades (GPT-3.5 → 4 → 4o); ablations holding base model fixed are rare.
7. **Single-shot vs. distributional outputs.** Most pipelines sample one trajectory per agent and read it as the prediction. Variance, sampling temperature effects, and seed sensitivity are seldom analyzed at the population level.

## Our Positioning

Our project takes the generative-agent paradigm but re-frames it as a *calibrated* statistical simulator. Specifically: (i) we treat the persona-conditioning prompt and the agent-architecture choices as parameters of a population-level generative model; (ii) we define an explicit population loss against held-out empirical distributions (choice marginals, joint distributions, counterfactual response patterns); (iii) we use modern prompt-optimization machinery (Thread 2) to fit those parameters; (iv) we evaluate with population-alignment metrics (Thread 5) rather than believability. This converts generative agents from *demonstrations* into *fitted simulators*, which is what CSS practice requires for them to substitute for or augment real surveys/experiments.
