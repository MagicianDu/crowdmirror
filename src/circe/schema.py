"""Domain-agnostic data contracts for CIRCE."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Alternative:
    id: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChoiceSet:
    alternatives: list[Alternative]


@dataclass
class PersonaSpec:
    segment: str
    demographics: dict[str, Any] = field(default_factory=dict)
    preferences: dict[str, float] = field(default_factory=dict)


@dataclass
class ScenarioSpec:
    choice_set: ChoiceSet
    persona: PersonaSpec
    context: dict[str, Any] = field(default_factory=dict)
    scenario_id: str = ""


@dataclass
class BehaviorTrace:
    scenario_id: str
    choice_probs: dict[str, float] = field(default_factory=dict)
    chosen_id: str | None = None
    audit: dict[str, Any] = field(default_factory=dict)


@dataclass
class CounterfactualQuery:
    base_scenario_id: str
    intervention: dict[str, Any] = field(default_factory=dict)
    target_variable: str = "choice_probs"


@dataclass
class GroundTruth:
    scenario_id: str
    factual_probs: dict[str, float] = field(default_factory=dict)
    counterfactual_probs: dict[str, float] = field(default_factory=dict)
    ate: float | None = None
    cate: dict[str, float] = field(default_factory=dict)
