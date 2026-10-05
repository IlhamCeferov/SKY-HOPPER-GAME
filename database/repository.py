
"""Queries for the existing flight_game schema and game_save table."""

import json
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

    def load_game(self, save_name: str) -> GameState:
        connection = connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT s.game_id, s.state_json "
                    "FROM game_save AS s WHERE s.save_name = %s",
                    (save_name,),
                )
                record = cursor.fetchone()

                if record is None:
                    raise LookupError("Save not found.")

                payload = json.loads(record["state_json"])
                state = GameState.from_dict(payload)

                if (
                    state.game_id != record["game_id"]
                    or state.save_name != save_name
                ):
                    raise ValueError(
                        "Save data does not match its database record."
                    )

                return state
        finally:
            connection.close()

    def save_game(self, state: GameState) -> None:
        payload = json.dumps(
            state.to_save_payload(),
            ensure_ascii=True,
            separators=(",", ":"),
        )

        connection = connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO game "
                    "(id, co2_consumed, co2_budget, location, screen_name) "
                    "VALUES (%s, %s, %s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE "
                    "co2_consumed = VALUES(co2_consumed), "
                    "co2_budget = VALUES(co2_budget), "
                    "location = VALUES(location), "
                    "screen_name = VALUES(screen_name)",
                    (
                        state.game_id,
                        round(state.total_co2_kg),
                        round(state.co2_budget_kg),
                        state.current_airport,
                        state.screen_name,
                    ),
                )

                cursor.execute(
                    "SELECT game_id FROM game_save "
                    "WHERE game_id = %s FOR UPDATE",
                    (state.game_id,),
                )

                if cursor.fetchone() is None:
                    cursor.execute(
                        "INSERT INTO game_save "
                        "(game_id, save_name, state_json) "
                        "VALUES (%s, %s, %s)",
                        (
                            state.game_id,
                            state.save_name,
                            payload,
                        ),
                    )
                else:
                    cursor.execute(
                        "UPDATE game_save "
                        "SET save_name = %s, state_json = %s "
                        "WHERE game_id = %s",
                        (
                            state.save_name,
                            payload,
                            state.game_id,
                        ),
                    )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()