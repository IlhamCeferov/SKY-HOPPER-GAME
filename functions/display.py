"""Small display helpers shared by terminal screens."""

from services.levels import current_level
from services.models import GameState


def show_status(state: GameState) -> None:
    level = current_level(state)
    print("\n--- Airline status ---")
    print(f"Save: {state.save_name} | Player: {state.screen_name}")
    print(f"Cash: EUR {state.money:,.2f} | Reputation: {state.reputation}/100 | Eco-score: {state.eco_score}/100")
    print(f"Location: {state.current_airport} | Aircraft: {state.aircraft_type}")
    print(f"Level {state.level}: {level.name} | Flights: {state.flights_in_level}/{level.flight_limit}")
    print(f"Level profit: EUR {state.level_profit:,.2f} / EUR {level.profit_target:,.2f}")
    print(f"Fuel: standard {state.fuel_stock.get('standard', 0):.1f} L, biofuel {state.fuel_stock.get('biofuel', 0):.1f} L")
    print(f"CO2: {state.total_co2_kg:,.1f} / {state.co2_budget_kg:,.1f} kg")