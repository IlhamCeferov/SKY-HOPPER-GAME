"""Skyhooper terminal game entry point."""

import argparse
import random
import sys
from math import floor

from pymysql import MySQLError

from database.repository import GameRepository
from database.setup import setup_database
from functions.display import show_status
from functions.input_helpers import ask_int, ask_text, ask_yes_no
from services.game import GameService
from services.levels import current_level
from services.models import GameState
from services.rules import AIRCRAFT_TYPES, FUEL_TYPES, WEATHER_EFFECTS, distance_km, estimate_flight, validate_load


def select_campaign(repository: GameRepository, airports: list[dict]) -> GameState | None:
    saves = repository.list_saves()
    if saves:
        print("\nSaved campaigns:")
        for index, record in enumerate(saves, 1):
            print(f"{index}. {record['save_name']} (at {record['location']}, saved {record['saved_at']})")
        print("N. Start a new campaign")
        print("0. Quit")
        while True:
            choice = input("Select a save or option: ").strip()
            if choice == "0":
                return None
            if choice.lower() == "n":
                break
            if choice.isdigit() and 1 <= int(choice) <= len(saves):
                return repository.load_game(saves[int(choice) - 1]["save_name"])
            print("Choose a listed save, N, or 0.")

    if not airports:
        raise RuntimeError("No airports with usable coordinates were found in the airport table.")
    existing_names = {record["save_name"].lower() for record in saves}
    while True:
        save_name = ask_text("New save name (max 40 characters): ")
        if save_name.lower() not in existing_names:
            break
        print("A save with that name already exists.")

    print("Choose your starting airport:")
    for index, airport in enumerate(airports[:12], 1):
        print(f"{index}. {airport['ident']} - {airport['name'] or airport['ident']}")
    airport_index = ask_int("Airport number: ", minimum=1, maximum=min(12, len(airports)))
    return repository.create_game(save_name, airports[airport_index - 1]["ident"])


def nearest_destinations(state: GameState, airports: list[dict]) -> list[tuple[dict, float]]:
    origin = next((item for item in airports if item["ident"] == state.current_airport), None)
    if origin is None:
        return []
    destinations = []
    for airport in airports:
        if airport["ident"] == state.current_airport:
            continue
        route_distance = distance_km(
            float(origin["latitude_deg"]),
            float(origin["longitude_deg"]),
            float(airport["latitude_deg"]),
            float(airport["longitude_deg"]),
        )
        if route_distance > 0:
            destinations.append((airport, route_distance))
    return sorted(destinations, key=lambda item: item[1])[:12]


def flight_action(state: GameState, airports: list[dict], repository: GameRepository, game: GameService) -> None:
    destinations = nearest_destinations(state, airports)
    if not destinations:
        print("No destination airports are available from the current location.")
        return

    print("\nDestinations:")
    for index, (airport, route_distance) in enumerate(destinations, 1):
        print(f"{index}. {airport['ident']} - {airport['name'] or airport['ident']} ({route_distance:,.0f} km)")
    destination_index = ask_int("Destination (0 cancels): ", minimum=0, maximum=len(destinations))
    if destination_index == 0:
        return
    destination, route_distance = destinations[destination_index - 1]

    while True:
        passengers = ask_int("Passengers (0-20): ", minimum=0, maximum=20)
        cargo = ask_int("Cargo kg (0-500; over 500 is penalized from level 2): ", minimum=0, maximum=1000)
        if cargo > 500:
            if state.level >= 2:
                game.apply_cargo_overload_penalty(state)
                repository.save_game(state)
                print("Cargo overload: EUR 500 fine and 5 reputation points lost. Save updated.")
            else:
                print("Maximum cargo is 500 kg.")
            continue
        try:
            validate_load(passengers, cargo)
            break
        except ValueError as error:
            print(error)

    weather = random.choice(list(WEATHER_EFFECTS)) if state.level >= 4 else "Normal"
    fuel_type = "standard"
    if state.level >= 4:
        print("Fuel: 1. standard, 2. biofuel")
        fuel_type = ("standard", "biofuel")[ask_int("Fuel type: ", minimum=1, maximum=2) - 1]

    remaining_budget = max(0.0, state.co2_budget_kg - state.total_co2_kg)
    estimate = estimate_flight(
        distance=route_distance,
        passengers=passengers,
        cargo_kg=cargo,
        weather=weather,
        fuel_type=fuel_type,
        aircraft_type=state.aircraft_type,
        co2_budget_remaining=remaining_budget,
    )
    print("\nFlight estimate")
    print(f"Weather: {weather}")
    print(f"Fuel required: {estimate.fuel_litres:.1f} L ({fuel_type})")
    print(f"Fuel cost: EUR {estimate.fuel_cost:,.2f}")
    print(f"Revenue: EUR {estimate.revenue:,.2f}")
    print(f"Carbon tax: EUR {estimate.carbon_tax:,.2f}")
    print(f"Estimated profit: EUR {estimate.profit:,.2f}")
    print(f"CO2: {estimate.emissions_kg:,.1f} kg")

    if state.fuel_stock.get(fuel_type, 0.0) + 1e-9 < estimate.fuel_litres:
        print("Not enough fuel in stock. Purchase fuel from the main menu first.")
        return
    if not ask_yes_no("Confirm flight"):
        return

    outcome = game.complete_flight(state, destination, estimate)
    repository.save_game(state)
    print(f"Flight completed. Profit: EUR {estimate.profit:,.2f}. Current location: {state.current_airport}.")
    if outcome is False:
        print("Level goal not reached before the flight limit. Campaign over.")
    elif outcome is True:
        if state.campaign_complete:
            print("SKYHOOPER championship complete!")
        else:
            print(f"Level completed. Moving to level {state.level}: {current_level(state).name}.")


def fuel_action(state: GameState, repository: GameRepository, game: GameService) -> None:
    choices = ["standard"] + (["biofuel"] if state.level >= 4 else [])
    print("\nFuel prices:")
    for index, fuel_type in enumerate(choices, 1):
        print(f"{index}. {fuel_type}: EUR {FUEL_TYPES[fuel_type]['price']:.2f}/L")
    fuel_index = ask_int("Fuel type: ", minimum=1, maximum=len(choices))
    fuel_type = choices[fuel_index - 1]
    maximum = floor(state.money / FUEL_TYPES[fuel_type]["price"])
    if maximum < 1:
        print("You do not have enough money to buy one litre.")
        return
    litres = ask_int(f"Litres to buy (1-{maximum}): ", minimum=1, maximum=maximum)
    quoted_cost = litres * FUEL_TYPES[fuel_type]["price"]
    print(f"Purchase {litres} L for EUR {quoted_cost:,.2f}?")
    if not ask_yes_no("Confirm fuel purchase"):
        return
    cost = game.purchase_fuel(state, fuel_type, litres)
    repository.save_game(state)
    print(f"Bought {litres} L of {fuel_type} for EUR {cost:,.2f}. Saved.")


def upgrade_action(state: GameState, repository: GameRepository, game: GameService) -> None:
    if state.level < 5:
        print("Aircraft upgrades unlock at level 5.")
        return
    choices = list(AIRCRAFT_TYPES)
    for index, aircraft_type in enumerate(choices, 1):
        details = AIRCRAFT_TYPES[aircraft_type]
        print(f"{index}. {aircraft_type}: EUR {details['cost']:,.0f}")
    aircraft_index = ask_int("Aircraft (0 cancels): ", minimum=0, maximum=len(choices))
    if aircraft_index == 0:
        return
    aircraft_type = choices[aircraft_index - 1]
    cost = game.upgrade_aircraft(state, aircraft_type)
    repository.save_game(state)
    print(f"Installed {aircraft_type} for EUR {cost:,.2f}. Saved.")


def play(state: GameState, airports: list[dict], repository: GameRepository) -> None:
    game = GameService()
    while not state.campaign_complete:
        print(f"\n{state.save_name} | Level {state.level}: {current_level(state).name}")
        print("1. Fly   2. Buy fuel   3. Status   4. Upgrade aircraft   0. Save and quit")
        choice = ask_int("Choose: ", minimum=0, maximum=4)
        try:
            if choice == 0:
                repository.save_game(state)
                print("Game saved. Goodbye.")
                return
            if choice == 1:
                flight_action(state, airports, repository, game)
            elif choice == 2:
                fuel_action(state, repository, game)
            elif choice == 3:
                show_status(state)
            elif choice == 4:
                upgrade_action(state, repository, game)
        except (ValueError, LookupError) as error:
            print(f"Action could not be completed: {error}")
    repository.save_game(state)
    print("Campaign results")
    print(f"Outcome: {'won' if state.campaign_won else 'not completed'}")
    print(f"Total profit: EUR {state.total_profit:,.2f}")
    print(f"Money: EUR {state.money:,.2f} | Reputation: {state.reputation} | Eco-score: {state.eco_score}")
    print(f"Total CO2: {state.total_co2_kg:,.1f} kg | Flights: {state.total_flights}")


def main() -> int:
    parser = argparse.ArgumentParser(description="SKYHOOPER terminal airline management game")
    parser.add_argument("--setup-db", action="store_true", help="create the new game_save table")
    args = parser.parse_args()
    try:
        if args.setup_db:
            setup_database()
            print("game_save table is ready.")
            return 0
        repository = GameRepository()
        airports = repository.get_airports()
        state = select_campaign(repository, airports)
        if state is not None:
            play(state, airports, repository)
        return 0
    except (RuntimeError, OSError) as error:
        print(f"Startup error: {error}", file=sys.stderr)
        return 1
    except MySQLError as error:
        print(f"MariaDB error: {error}", file=sys.stderr)
        print("Check the DB_* settings and run `python main.py --setup-db` once.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted. Any previously saved progress is safe.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())