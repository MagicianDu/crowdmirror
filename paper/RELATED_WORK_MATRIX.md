# CIRCE Related Work Matrix

| Line | Representative family | What it explains | What it misses | CIRCE boundary |
| --- | --- | --- | --- | --- |
| LLM persona simulation | prompt-only synthetic users | qualitative persona variation | no causal calibration or emergence guarantees | CIRCE calibrates against explicit causal and emergence metrics |
| Agent-based modeling | voter, contagion, opinion dynamics | macro emergence under known rules | no LLM language policy adaptation | CIRCE uses ABM as controlled ground truth and calibrates LLM interaction prompts |
| Discrete choice calibration | MNL and transport-choice models | identifiable choice probabilities | weak macro social dynamics | CIRCE keeps choice calibration but adds emergence distortion |
| Prompt optimization | TextGrad-style feedback | iterative prompt improvement | no social-science evidence boundary by default | CIRCE wraps prompt updates in manifest-backed claims |
| Computational social science simulation | synthetic populations and policy experiments | scenario-level social analysis | often weak model auditability | CIRCE treats auditability as part of the method |
