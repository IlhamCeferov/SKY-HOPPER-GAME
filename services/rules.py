"""Pure game calculations, kept independent from the terminal and database."""

from dataclasses import dataclass
from math import asin, ceil, cos, radians, sin, sqrt

PASSENGER_REVENUE = 50.0
CARGO_REVENUE_PER_KG = 2.0
FUEL_PRICE_PER_LITRE = 2.0
BASE_FUEL_KM_PER_LITRE = 5.0
CO2_KG_PER_LITRE = 2.52
PASSENGER_CAPACITY = 20
CARGO_CAPACITY_KG = 500
CARBON_TAX_PER_KG = 0.05

WEATHER_EFFECTS = {
    "Clear": 0.8,
    "Normal": 1.0,
    "Rain": 1.1,
    "Strong wind": 1.2,
}

FUEL_TYPES = {
    "standard": {"price": 2.0, "emissions": 1.0},
    "biofuel": {"price": 3.0, "emissions": 0.4},
}

AIRCRAFT_TYPES = {
    "standard": {"cost": 0.0, "consumption": 1.0, "emissions": 1.0},
    "hybrid": {"cost": 10000.0, "consumption": 0.8, "emissions": 0.8},
    "electric": {"cost": 20000.0, "consumption": 0.5, "emissions": 0.1},
}


@dataclass(frozen=True)
class FlightEstimate:
    distance_km: float
    weather: str
    passengers: int
    cargo_kg: float
    fuel_type: str
    fuel_litres: float
    fuel_cost: float
    revenue: float
    emissions_kg: float
    carbon_tax: float
    profit: float


def distance_km(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    """Return great-circle distance using the haversine formula."""
    earth_radius_km = 6371.0
    lat_a, lat_b = radians(latitude_a), radians(latitude_b)
    delta_lat = radians(latitude_b - latitude_a)
    delta_lon = radians(longitude_b - longitude_a)
    haversine = sin(delta_lat / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin(delta_lon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(min(1.0, haversine)))


def validate_load(passengers: int, cargo_kg: float) -> None:
    if not 0 <= passengers <= PASSENGER_CAPACITY:
        raise ValueError(f"Passengers must be between 0 and {PASSENGER_CAPACITY}.")
    if not 0 <= cargo_kg <= CARGO_CAPACITY_KG:
        raise ValueError(f"Cargo must be between 0 and {CARGO_CAPACITY_KG} kg.")
    if passengers == 0 and cargo_kg == 0:
        raise ValueError("A flight must carry passengers or cargo.")


def estimate_flight(
    *,
    distance: float,
    passengers: int,
    cargo_kg: float,
    weather: str = "Normal",
    fuel_type: str = "standard",
    aircraft_type: str = "standard",
    co2_budget_remaining: float = 0.0,
) -> FlightEstimate:
    validate_load(passengers, cargo_kg)
    if distance <= 0:
        raise ValueError("Route distance must be greater than zero.")
    if weather not in WEATHER_EFFECTS:
        raise ValueError(f"Unknown weather: {weather}")
    if fuel_type not in FUEL_TYPES:
        raise ValueError(f"Unknown fuel type: {fuel_type}")
    if aircraft_type not in AIRCRAFT_TYPES:
        raise ValueError(f"Unknown aircraft type: {aircraft_type}")

    fuel = FUEL_TYPES[fuel_type]
    aircraft = AIRCRAFT_TYPES[aircraft_type]
    litres = distance / BASE_FUEL_KM_PER_LITRE
    litres *= WEATHER_EFFECTS[weather] * aircraft["consumption"]
    fuel_cost = litres * fuel["price"]
    revenue = passengers * PASSENGER_REVENUE + cargo_kg * CARGO_REVENUE_PER_KG
    emissions = litres * CO2_KG_PER_LITRE * fuel["emissions"] * aircraft["emissions"]
    taxable_emissions = max(0.0, emissions - max(0.0, co2_budget_remaining))
    carbon_tax = taxable_emissions * CARBON_TAX_PER_KG

    return FlightEstimate(
        distance_km=distance,
        weather=weather,
        passengers=passengers,
        cargo_kg=cargo_kg,
        fuel_type=fuel_type,
        fuel_litres=litres,
        fuel_cost=fuel_cost,
        revenue=revenue,
        emissions_kg=emissions,
        carbon_tax=carbon_tax,
        profit=revenue - fuel_cost - carbon_tax,
    )
