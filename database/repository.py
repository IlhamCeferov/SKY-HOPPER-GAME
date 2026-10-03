
"""Queries for the existing flight_game schema and game_save table."""

import uuid
from typing import Any

from database.connection import connect
from services.models import GameState


class GameRepository:
    def list_saves(self) -> list[dict[str, Any]]:
        connection = connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT s.save_name, s.game_id, s.saved_at, g.location "
                    "FROM game_save AS s JOIN game AS g ON g.id = s.game_id "
                    "ORDER BY s.save_name"
                )
                return list(cursor.fetchall())
        finally:
            connection.close()

    def get_airports(self, limit: int = 500) -> list[dict[str, Any]]:
        connection = connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT ident, type, name, latitude_deg, longitude_deg "
                    "FROM airport "
                    "WHERE latitude_deg IS NOT NULL "
                    "AND longitude_deg IS NOT NULL "
                    "AND type IN ('small_airport', 'medium_airport', 'large_airport') "
                    "ORDER BY CASE type "
                    "WHEN 'large_airport' THEN 0 "
                    "WHEN 'medium_airport' THEN 1 "
                    "ELSE 2 END, ident "
                    "LIMIT %s",
                    (limit,),
                )
                airports = list(cursor.fetchall())

                if not airports:
                    cursor.execute(
                        "SELECT ident, type, name, latitude_deg, longitude_deg "
                        "FROM airport "
                        "WHERE latitude_deg IS NOT NULL "
                        "AND longitude_deg IS NOT NULL "
                        "ORDER BY ident LIMIT %s",
                        (limit,),
                    )
                    airports = list(cursor.fetchall())

                return airports
        finally:
            connection.close()

    def create_game(
        self,
        save_name: str,
        airport_ident: str,
        co2_budget: int = 5000,
    ) -> GameState:
        game_id = uuid.uuid4().hex

        state = GameState(
            game_id=game_id,
            save_name=save_name,
            current_airport=airport_ident,
            screen_name=save_name,
            co2_budget_kg=float(co2_budget),
        )

        self.save_game(state)
        return state