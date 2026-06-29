"""Interaction prompt templates (θ_ρ) for multi-agent opinion dynamics.

The interaction prompt governs how an agent decides whether to adopt
a neighbor's opinion. This is the target of emergence TextGrad optimization.
"""

import json


INTERACTION_SYSTEM_PROMPT = """\
You are simulating an agent in a social network who may adopt a neighbor's opinion. \
Given your current opinion and the opinions of your neighbors, decide what your \
new opinion should be.

Rules:
- You may keep your current opinion or adopt one of your neighbors' opinions
- Consider social influence: if many neighbors hold a different opinion, you are \
more likely to switch
- Output ONLY valid JSON: {"new_opinion": <int>}
- Do NOT explain your reasoning, just output the JSON"""


INTERACTION_TEMPLATE = """\
You are agent {agent_id} in a social network.

Your current opinion: {agent_opinion}
Your neighbors' opinions: {neighbor_opinions}
Possible opinions: {possible_opinions}

Based on social influence dynamics, what is your new opinion? Output JSON:"""


def build_interaction_prompt(
    agent_id: int,
    agent_opinion: int,
    neighbor_opinions: list[int],
    n_opinions: int,
) -> str:
    possible = list(range(n_opinions))
    return INTERACTION_TEMPLATE.format(
        agent_id=agent_id,
        agent_opinion=agent_opinion,
        neighbor_opinions=neighbor_opinions,
        possible_opinions=", ".join(str(o) for o in possible),
    )


BAD_INTERACTION_PROMPT = """\
You are agent {agent_id}, an extremely stubborn individual who NEVER changes opinion. \
Current opinion: {agent_opinion}. Ignore neighbors: {neighbor_opinions}. \
Options: {possible_opinions}. Always keep your opinion. Output JSON:"""
