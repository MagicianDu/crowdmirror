"""
Core data contracts for the simulator.
ScenarioSpec (input) and BehaviorTrace (output).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class TripPurpose(Enum):
    BUSINESS = "business"
    LEISURE = "leisure"
    VFR = "visiting_friends_relatives"
    MIXED = "mixed"


class ActionType(Enum):
    PURCHASE = "purchase"
    NO_PURCHASE = "no_purchase"
    DELAY = "delay"
    SUBSTITUTE = "substitute"


@dataclass
class Offer:
    offer_id: str
    price: float
    departure_time: str
    arrival_time: str
    duration_minutes: int
    carrier: str
    cabin_class: str
    refundable: bool
    stops: int
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HardConstraint:
    field: str
    op: str  # "<=", ">=", "==", "!="
    value: Any


@dataclass
class Context:
    trip_purpose: TripPurpose
    advance_days: int
    party_size: int
    flexible_dates: bool
    origin: str
    destination: str
    hard_constraints: List[HardConstraint] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InformationSet:
    has_compared_prices: bool = False
    seen_scarcity_signal: bool = False
    seen_competitor_price: Optional[float] = None
    loyalty_tier: Optional[str] = None
    previous_searches: int = 0


@dataclass
class Controls:
    segment_id: str = "default"
    random_seed: int = 42
    temperature: float = 1.0
    noise_scale: float = 0.1


@dataclass
class ScenarioSpec:
    context: Context
    offer_set: List[Offer]
    information_set: InformationSet
    controls: Controls


@dataclass
class BehaviorTrace:
    choice_probs: Dict[str, float]  # offer_id -> probability
    outside_option_prob: float
    action: ActionType
    chosen_offer_id: Optional[str]
    audit: Dict[str, Any] = field(default_factory=dict)
