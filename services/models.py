"""Serializable state for a single Skyhooper campaign."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class GameState:
    game_id: str
    save_name: str
    current_airport: str
    screen_name: str
    money: float = 10000.0
    reputation: int = 50
    eco_score: int = 100
    level: int = 1
    flights_in_level: int = 0
    total_flights: int = 0
    level_profit: float = 0.0
    level_cargo_kg: float = 0.0
    total_profit: float = 0.0
    total_co2_kg: float = 0.0
    co2_budget_kg: float = 5000.0
    fuel_stock: dict[str, float] = field(default_factory=lambda: {"standard": 0.0, "biofuel": 0.0})
    aircraft_type: str = "standard"
    completed_levels: list[int] = field(default_factory=list)
    campaign_complete: bool = False
    campaign_won: bool = False
    flight_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        data = dict(data)
        version = data.pop("version", 1)
        if version != 1:
            raise ValueError(f"Unsupported save version: {version}")
        return cls(**data)

    def to_save_payload(self) -> dict[str, Any]:
        return {"version": 1, **self.to_dict()}
