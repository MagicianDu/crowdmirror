"""Prompt templates for LLM choice simulation.

Two-layer prompt structure:
- P1 (Persona): Who is making the choice
- P2 (Utility): What are the alternatives and their attributes
The LLM outputs choice probabilities as JSON.
"""

import json

CHOICE_SYSTEM_PROMPT = """\
You are simulating a person's transportation choice behavior. Given a persona \
description and a set of alternatives with attributes, output the probability \
that this person would choose each alternative.

Rules:
- Probabilities must sum to 1.0
- Output ONLY valid JSON: {"alternative_name": probability, ...}
- Base your reasoning on how a real person with these characteristics would \
weigh travel time, cost, and convenience
- Do NOT explain your reasoning, just output the JSON"""

PERSONA_TEMPLATE = """\
Person profile:
- Segment: {segment}
- Demographics: {demographics}
- Trip context: {context}"""

UTILITY_TEMPLATE = """\
Available alternatives: {alternatives}

Attributes for each alternative:
{attributes}

Output the choice probabilities as JSON:"""


def build_choice_prompt(
    segment: str,
    demographics: dict,
    alternatives: list[str],
    attributes: dict[str, dict],
    context: dict,
) -> str:
    persona_block = PERSONA_TEMPLATE.format(
        segment=segment,
        demographics=json.dumps(demographics),
        context=json.dumps(context),
    )
    attrs_formatted = "\n".join(
        f"  {alt}: {json.dumps(attrs)}" for alt, attrs in attributes.items()
    )
    utility_block = UTILITY_TEMPLATE.format(
        alternatives=", ".join(alternatives),
        attributes=attrs_formatted,
    )
    return f"{persona_block}\n\n{utility_block}"
