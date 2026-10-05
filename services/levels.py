"""Level rules from the game brief."""

from dataclasses import dataclass

from services.models import GameState


@dataclass(frozen=True)
class Level:
    number: int
    name: str
    profit_target: float
    flight_limit: int
    cargo_target: float = 0.0
    reputation_target: int = 0
    eco_target: int = 0


LEVELS = (
    Level(1, "First Flight", 5000, 5),
    Level(2, "Cargo Challenge", 7500, 6, cargo_target=1000),
    Level(3, "Passengers vs Cargo", 12000, 8, reputation_target=40),
    Level(4, "Fuel Master", 15000, 8, eco_target=50),
    Level(5, "SKYHOOPER Final Challenge", 25000, 10, reputation_target=60, eco_target=60),
)


def current_level(state: GameState) -> Level:
    return LEVELS[state.level - 1]


def evaluate_level(state: GameState) -> bool | None:
    """Return None while active, otherwise whether the level was won."""
    level = current_level(state)
    if state.flights_in_level < level.flight_limit:
        return None
    return (
        state.level_profit >= level.profit_target
        and state.level_cargo_kg >= level.cargo_target
        and state.reputation >= level.reputation_target
        and state.eco_score >= level.eco_target
    )
