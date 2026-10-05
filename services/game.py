"""State transitions for purchases, upgrades, and completed flights."""

from math import ceil
from typing import Any

from services.levels import LEVELS, current_level, evaluate_level
from services.models import GameState
from services.rules import AIRCRAFT_TYPES, FUEL_TYPES, FlightEstimate


class GameService:
    def apply_cargo_overload_penalty(self, state: GameState) -> None:
        state.money -= 500.0
        state.reputation = max(0, state.reputation - 5)

    def purchase_fuel(self, state: GameState, fuel_type: str, litres: int) -> float:
        if fuel_type not in FUEL_TYPES:
            raise ValueError("Unknown fuel type.")
        if litres <= 0:
            raise ValueError("Fuel quantity must be positive.")
        cost = litres * FUEL_TYPES[fuel_type]["price"]
        if cost > state.money:
            raise ValueError("You do not have enough money for this fuel purchase.")
        state.money -= cost
        state.fuel_stock[fuel_type] = state.fuel_stock.get(fuel_type, 0.0) + litres
        return cost

    def upgrade_aircraft(self, state: GameState, aircraft_type: str) -> float:
        if aircraft_type not in AIRCRAFT_TYPES:
            raise ValueError("Unknown aircraft type.")
        if aircraft_type == state.aircraft_type:
            raise ValueError("That aircraft is already installed.")
        cost = AIRCRAFT_TYPES[aircraft_type]["cost"]
        if cost > state.money:
            raise ValueError("You do not have enough money for this upgrade.")
        state.money -= cost
        state.aircraft_type = aircraft_type
        state.total_profit -= cost
        state.level_profit -= cost
        return cost

    def complete_flight(
        self,
        state: GameState,
        destination: dict[str, Any],
        estimate: FlightEstimate,
    ) -> bool | None:
        if state.campaign_complete:
            raise ValueError("This campaign is already complete.")
        available_fuel = state.fuel_stock.get(estimate.fuel_type, 0.0)
        if available_fuel + 1e-9 < estimate.fuel_litres:
            raise ValueError("Not enough of the selected fuel. Purchase fuel before flying.")

        previous_budget = max(0.0, state.co2_budget_kg - state.total_co2_kg)
        origin = state.current_airport
        state.fuel_stock[estimate.fuel_type] = max(0.0, available_fuel - estimate.fuel_litres)
        state.money += estimate.revenue - estimate.carbon_tax
        state.total_profit += estimate.profit
        state.level_profit += estimate.profit
        state.level_cargo_kg += estimate.cargo_kg
        state.total_co2_kg += estimate.emissions_kg
        state.total_flights += 1
        state.flights_in_level += 1
        state.current_airport = destination["ident"]

        excess_emissions = max(0.0, estimate.emissions_kg - previous_budget)
        if excess_emissions > 0:
            state.reputation = max(0, state.reputation - 2)
        state.eco_score = max(0, state.eco_score - ceil(max(0.0, estimate.emissions_kg - 250.0) / 100.0))
        state.reputation = min(100, state.reputation + (1 if estimate.carbon_tax == 0 else 0))

        state.flight_history.append(
            {
                "from": origin,
                "to": destination["ident"],
                "distance_km": round(estimate.distance_km, 2),
                "passengers": estimate.passengers,
                "cargo_kg": estimate.cargo_kg,
                "fuel_type": estimate.fuel_type,
                "fuel_litres": round(estimate.fuel_litres, 2),
                "weather": estimate.weather,
                "revenue": round(estimate.revenue, 2),
                "profit": round(estimate.profit, 2),
                "co2_kg": round(estimate.emissions_kg, 2),
            }
        )
        result = evaluate_level(state)
        if result is None:
            return None
        if not result:
            state.campaign_complete = True
            state.campaign_won = False
            return False

        state.completed_levels.append(state.level)
        if state.level == len(LEVELS):
            state.campaign_complete = True
            state.campaign_won = True
            return True
        state.level += 1
        state.flights_in_level = 0
        state.level_profit = 0.0
        state.level_cargo_kg = 0.0
        return True


def flight_count_text(state: GameState) -> str:
    level = current_level(state)
    return f"{state.flights_in_level}/{level.flight_limit}"
